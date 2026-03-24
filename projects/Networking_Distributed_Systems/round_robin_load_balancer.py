"""
Round Robin Load Balancer Simulation
A Python implementation of a load balancer using round-robin algorithm
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
import logging
from enum import Enum
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ServerStatus(Enum):
    """Enum for server status"""
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class Server:
    """Server class representing a backend server"""
    server_id: str
    address: str
    status: ServerStatus = ServerStatus.ACTIVE
    current_load: int = 0
    total_requests_handled: int = 0

    def __post_init__(self):
        """Initialize server with a unique ID if not provided"""
        if not self.server_id:
            self.server_id = str(uuid.uuid4())[:8]

    def increment_load(self):
        """Increment the current load of the server"""
        self.current_load += 1
        self.total_requests_handled += 1

    def decrement_load(self):
        """Decrement the current load of the server"""
        if self.current_load > 0:
            self.current_load -= 1

    def activate(self):
        """Activate the server"""
        self.status = ServerStatus.ACTIVE
        logging.info(f"Server {self.server_id} activated")

    def deactivate(self):
        """Deactivate the server"""
        self.status = ServerStatus.INACTIVE
        logging.info(f"Server {self.server_id} deactivated")

    def __str__(self):
        return f"Server(ID: {self.server_id}, Address: {self.address}, Status: {self.status.value}, Load: {self.current_load}, Total: {self.total_requests_handled})"


@dataclass
class Request:
    """Request class representing incoming requests"""
    request_id: str
    client_ip: str
    payload: str
    timestamp: datetime = None

    def __post_init__(self):
        """Initialize request with timestamp if not provided"""
        if not self.request_id:
            self.request_id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = datetime.now()

    def __str__(self):
        return f"Request(ID: {self.request_id}, Client: {self.client_ip}, Payload: {self.payload[:50]}...)"


class LoadBalancer:
    """Load Balancer class implementing round-robin algorithm"""

    def __init__(self):
        self.servers: List[Server] = []
        self.current_index: int = 0
        self.request_history: List[tuple] = []  # Store (request, server) pairs

    def add_server(self, server: Server) -> bool:
        """Add a server to the load balancer"""
        if any(s.server_id == server.server_id for s in self.servers):
            logging.warning(f"Server {server.server_id} already exists")
            return False

        self.servers.append(server)
        logging.info(f"Server {server.server_id} added to load balancer")
        return True

    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the load balancer"""
        for i, server in enumerate(self.servers):
            if server.server_id == server_id:
                removed = self.servers.pop(i)
                logging.info(f"Server {server_id} removed from load balancer")
                # Reset index if necessary
                if self.current_index >= len(self.servers) and self.servers:
                    self.current_index = 0
                return True
        logging.warning(f"Server {server_id} not found")
        return False

    def get_next_server(self) -> Optional[Server]:
        """Get the next available server using round-robin algorithm"""
        if not self.servers:
            logging.warning("No servers available")
            return None

        # Find the next active server
        active_servers = [s for s in self.servers if s.status == ServerStatus.ACTIVE]

        if not active_servers:
            logging.warning("No active servers available")
            return None

        # Reset index if it's out of range
        if self.current_index >= len(self.servers):
            self.current_index = 0

        # Find the next active server starting from current_index
        start_index = self.current_index
        for i in range(len(self.servers)):
            index = (start_index + i) % len(self.servers)
            if self.servers[index].status == ServerStatus.ACTIVE:
                self.current_index = (index + 1) % len(self.servers)
                return self.servers[index]

        return None

    def distribute_request(self, request: Request) -> Optional[Server]:
        """Distribute a request to a server using round-robin"""
        server = self.get_next_server()

        if server:
            server.increment_load()
            self.request_history.append((request, server))
            logging.info(f"Request {request.request_id} distributed to server {server.server_id}")
            return server
        else:
            logging.error(f"Request {request.request_id} could not be distributed - no active servers")
            return None

    def complete_request(self, server_id: str) -> bool:
        """Mark a request as completed on a server"""
        for server in self.servers:
            if server.server_id == server_id:
                server.decrement_load()
                logging.info(f"Request completed on server {server_id}")
                return True
        return False

    def get_statistics(self) -> Dict:
        """Get load balancer statistics"""
        total_requests = len(self.request_history)
        server_stats = []

        for server in self.servers:
            server_stats.append({
                'server_id': server.server_id,
                'address': server.address,
                'status': server.status.value,
                'current_load': server.current_load,
                'total_handled': server.total_requests_handled,
                'percentage': (server.total_requests_handled / total_requests * 100) if total_requests > 0 else 0
            })

        return {
            'total_servers': len(self.servers),
            'active_servers': sum(1 for s in self.servers if s.status == ServerStatus.ACTIVE),
            'total_requests': total_requests,
            'server_statistics': server_stats
        }


class BalancerManager:
    """Manager class for the load balancer system"""

    def __init__(self):
        self.load_balancer = LoadBalancer()
        self.request_counter = 0

    def add_server(self, address: str, server_id: str = None) -> bool:
        """Add a new server to the system"""
        try:
            if not address:
                raise ValueError("Server address cannot be empty")

            server = Server(
                server_id=server_id or str(uuid.uuid4())[:8],
                address=address
            )
            return self.load_balancer.add_server(server)
        except Exception as e:
            logging.error(f"Error adding server: {e}")
            return False

    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the system"""
        try:
            if not server_id:
                raise ValueError("Server ID cannot be empty")
            return self.load_balancer.remove_server(server_id)
        except Exception as e:
            logging.error(f"Error removing server: {e}")
            return False

    def toggle_server_status(self, server_id: str) -> bool:
        """Toggle server status between active and inactive"""
        try:
            for server in self.load_balancer.servers:
                if server.server_id == server_id:
                    if server.status == ServerStatus.ACTIVE:
                        server.deactivate()
                    else:
                        server.activate()
                    return True
            logging.warning(f"Server {server_id} not found")
            return False
        except Exception as e:
            logging.error(f"Error toggling server status: {e}")
            return False

    def simulate_request(self, client_ip: str, payload: str) -> Optional[Server]:
        """Simulate an incoming request"""
        try:
            if not client_ip:
                raise ValueError("Client IP cannot be empty")
            if not payload:
                raise ValueError("Request payload cannot be empty")

            self.request_counter += 1
            request = Request(
                request_id=f"REQ_{self.request_counter}",
                client_ip=client_ip,
                payload=payload
            )

            server = self.load_balancer.distribute_request(request)

            # Simulate request processing
            if server:
                import threading
                timer = threading.Timer(0.5, self.load_balancer.complete_request, args=[server.server_id])
                timer.daemon = True
                timer.start()

            return server
        except Exception as e:
            logging.error(f"Error simulating request: {e}")
            return None

    def view_distribution_history(self) -> None:
        """Display the distribution history"""
        if not self.load_balancer.request_history:
            print("\nNo requests have been processed yet.")
            return

        print("\n" + "=" * 80)
        print("REQUEST DISTRIBUTION HISTORY")
        print("=" * 80)
        print(f"{'Request ID':<12} {'Client IP':<15} {'Server ID':<10} {'Server Address':<15} {'Timestamp':<20}")
        print("-" * 80)

        for request, server in self.load_balancer.request_history[-20:]:  # Show last 20 requests
            print(
                f"{request.request_id:<12} {request.client_ip:<15} {server.server_id:<10} {server.address:<15} {request.timestamp.strftime('%H:%M:%S')}")

        if len(self.load_balancer.request_history) > 20:
            print(f"\n... and {len(self.load_balancer.request_history) - 20} more requests")

    def display_metrics(self) -> None:
        """Display load distribution metrics"""
        stats = self.load_balancer.get_statistics()

        print("\n" + "=" * 80)
        print("LOAD BALANCER METRICS")
        print("=" * 80)
        print(f"Total Servers: {stats['total_servers']}")
        print(f"Active Servers: {stats['active_servers']}")
        print(f"Total Requests Processed: {stats['total_requests']}")

        if stats['server_statistics']:
            print("\nServer Statistics:")
            print("-" * 80)
            print(
                f"{'Server ID':<12} {'Address':<15} {'Status':<10} {'Current Load':<12} {'Total Handled':<13} {'Percentage':<10}")
            print("-" * 80)

            for server_stat in stats['server_statistics']:
                print(f"{server_stat['server_id']:<12} {server_stat['address']:<15} "
                      f"{server_stat['status']:<10} {server_stat['current_load']:<12} "
                      f"{server_stat['total_handled']:<13} {server_stat['percentage']:.1f}%")

        if stats['total_requests'] > 0:
            print(f"\nAverage Load per Server: {stats['total_requests'] / max(stats['active_servers'], 1):.2f}")

    def list_servers(self) -> None:
        """Display all servers in the system"""
        if not self.load_balancer.servers:
            print("\nNo servers configured.")
            return

        print("\n" + "=" * 80)
        print("SERVER LIST")
        print("=" * 80)
        for server in self.load_balancer.servers:
            print(server)

    def interactive_menu(self) -> None:
        """Interactive console menu for the load balancer"""
        while True:
            print("\n" + "=" * 80)
            print("ROUND ROBIN LOAD BALANCER")
            print("=" * 80)
            print("1. Add Server")
            print("2. Remove Server")
            print("3. Toggle Server Status")
            print("4. List Servers")
            print("5. Simulate Request")
            print("6. View Distribution History")
            print("7. Display Metrics")
            print("8. Exit")
            print("=" * 80)

            choice = input("\nEnter your choice (1-8): ").strip()

            if choice == '1':
                address = input("Enter server address (e.g., 192.168.1.1:8080): ").strip()
                if self.add_server(address):
                    print(f"✓ Server added successfully")
                else:
                    print("✗ Failed to add server")

            elif choice == '2':
                self.list_servers()
                server_id = input("Enter server ID to remove: ").strip()
                if self.remove_server(server_id):
                    print(f"✓ Server {server_id} removed successfully")
                else:
                    print(f"✗ Failed to remove server {server_id}")

            elif choice == '3':
                self.list_servers()
                server_id = input("Enter server ID to toggle status: ").strip()
                if self.toggle_server_status(server_id):
                    print(f"✓ Server status toggled successfully")
                else:
                    print(f"✗ Failed to toggle server status")

            elif choice == '4':
                self.list_servers()

            elif choice == '5':
                client_ip = input("Enter client IP (e.g., 192.168.1.100): ").strip()
                payload = input("Enter request payload: ").strip()
                server = self.simulate_request(client_ip, payload)
                if server:
                    print(f"✓ Request distributed to server: {server.server_id}")
                else:
                    print("✗ Failed to distribute request - no active servers")

            elif choice == '6':
                self.view_distribution_history()

            elif choice == '7':
                self.display_metrics()

            elif choice == '8':
                print("\nExiting load balancer. Goodbye!")
                break

            else:
                print("Invalid choice. Please enter a number between 1 and 8.")


def main():
    """Main function to run the load balancer simulation"""
    print("Initializing Round Robin Load Balancer...")
    manager = BalancerManager()

    # Add some sample servers for demonstration
    manager.add_server("192.168.1.10:8080", "SRV1")
    manager.add_server("192.168.1.11:8080", "SRV2")
    manager.add_server("192.168.1.12:8080", "SRV3")

    # Start interactive menu
    manager.interactive_menu()


if __name__ == "__main__":
    main()