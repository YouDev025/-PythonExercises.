#!/usr/bin/env python3
"""
API Data Collector with Storage
A complete tool to fetch data from APIs and store in SQLite database
"""

import json
import sqlite3
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not found. Using simulation mode.")
    print("Install requests with: pip install requests\n")


class DatabaseManager:
    """Handle all database operations"""

    def __init__(self, db_name: str = "data.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Create database and tables if they don't exist"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_id TEXT UNIQUE,
                    data_field_1 TEXT,
                    data_field_2 TEXT,
                    status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def insert_data(self, api_id: str, field1: str, field2: str, status: str) -> bool:
        """Insert data into database, avoiding duplicates"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO api_data (api_id, data_field_1, data_field_2, status, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (api_id, field1, field2, status, datetime.now()))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def get_all_records(self) -> List[Dict]:
        """Retrieve all stored records"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM api_data ORDER BY timestamp DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_records_by_status(self, status: str) -> List[Dict]:
        """Retrieve records filtered by status"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM api_data WHERE status = ? ORDER BY timestamp DESC", (status,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_all_records(self) -> bool:
        """Clear all records from database"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM api_data")
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False


class APIClient:
    """Handle API requests and data parsing"""

    DEFAULT_API = "https://jsonplaceholder.typicode.com/posts/1"

    def __init__(self):
        self.session = requests.Session() if REQUESTS_AVAILABLE else None

    def fetch_data(self, url: str) -> Optional[Dict]:
        """Fetch data from API endpoint"""
        if not REQUESTS_AVAILABLE:
            return self.simulate_api_response(url)

        try:
            print(f"Fetching data from: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("Error: Request timeout. The API is not responding.")
        except requests.exceptions.ConnectionError:
            print("Error: Connection error. Check your internet connection.")
        except requests.exceptions.HTTPError as e:
            print(f"Error: HTTP error occurred: {e}")
        except json.JSONDecodeError:
            print("Error: Invalid JSON response from API.")
        except Exception as e:
            print(f"Error: Unexpected error: {e}")
        return None

    def simulate_api_response(self, url: str) -> Dict:
        """Simulate API response when requests is not available"""
        print(f"SIMULATION MODE: Fetching from {url}")
        time.sleep(1)  # Simulate network delay

        # Generate realistic mock data
        return {
            "id": 1,
            "name": "Sample Data Item",
            "status": "active",
            "title": "API Data Collector Demo",
            "body": "This is simulated API data for testing purposes.",
            "userId": 100,
            "timestamp": datetime.now().isoformat()
        }

    def parse_data(self, raw_data: Dict) -> Optional[Dict]:
        """Extract relevant fields from API response"""
        try:
            # Safely extract fields with fallbacks
            api_id = str(raw_data.get('id', raw_data.get('userId', 'unknown')))

            # Try multiple possible field names
            field1 = (
                    raw_data.get('name') or
                    raw_data.get('title') or
                    raw_data.get('data_field_1', 'No name provided')
            )

            field2 = (
                    raw_data.get('body') or
                    raw_data.get('description') or
                    raw_data.get('data_field_2', 'No description provided')
            )

            status = raw_data.get('status', raw_data.get('completed', 'unknown'))

            return {
                'api_id': api_id,
                'field1': str(field1)[:500],  # Limit length
                'field2': str(field2)[:1000],
                'status': str(status)
            }
        except Exception as e:
            print(f"Error parsing data: {e}")
            return None


class DataCollectorApp:
    """Main application class"""

    def __init__(self):
        self.db = DatabaseManager()
        self.api = APIClient()
        self.current_api_url = self.api.DEFAULT_API

    def display_menu(self):
        """Display main menu options"""
        print("\n" + "=" * 50)
        print("   API DATA COLLECTOR WITH STORAGE")
        print("=" * 50)
        print("1. Fetch and store API data")
        print("2. View stored records")
        print("3. Filter records by status")
        print("4. Export data to JSON file")
        print("5. Schedule periodic collection")
        print("6. Change API URL")
        print("7. Delete all records")
        print("8. Exit")
        print("=" * 50)
        print(f"Current API: {self.current_api_url}")
        print("=" * 50)

    def fetch_and_store(self, url: Optional[str] = None):
        """Fetch data from API and store in database"""
        api_url = url or self.current_api_url

        # Fetch raw data
        raw_data = self.api.fetch_data(api_url)
        if not raw_data:
            print("Failed to fetch data from API.")
            return

        # Parse data
        parsed_data = self.api.parse_data(raw_data)
        if not parsed_data:
            print("Failed to parse API response.")
            return

        # Store in database
        success = self.db.insert_data(
            parsed_data['api_id'],
            parsed_data['field1'],
            parsed_data['field2'],
            parsed_data['status']
        )

        if success:
            print(f"✓ Data successfully stored!")
            print(f"  ID: {parsed_data['api_id']}")
            print(f"  Status: {parsed_data['status']}")
            print(f"  Field 1: {parsed_data['field1'][:100]}...")
        else:
            print("⚠ Data already exists in database (duplicate detected).")

    def view_records(self, records: Optional[List[Dict]] = None):
        """Display records in formatted output"""
        if records is None:
            records = self.db.get_all_records()

        if not records:
            print("\n📭 No records found in database.")
            return

        print(f"\n📊 Found {len(records)} record(s):")
        print("-" * 80)

        for idx, record in enumerate(records, 1):
            print(f"\n[{idx}] Record ID: {record['id']}")
            print(f"    API ID: {record['api_id']}")
            print(f"    Status: {record['status']}")
            print(f"    Timestamp: {record['timestamp']}")
            print(f"    Field 1: {record['data_field_1'][:150]}")
            print(f"    Field 2: {record['data_field_2'][:150]}...")
            print("-" * 80)

    def filter_by_status(self):
        """Filter and display records by status"""
        status = input("Enter status to filter (e.g., active, completed, unknown): ").strip()
        records = self.db.get_records_by_status(status)

        if records:
            print(f"\n📊 Found {len(records)} record(s) with status '{status}':")
            self.view_records(records)
        else:
            print(f"\nNo records found with status '{status}'.")

    def export_to_json(self):
        """Export all records to JSON file"""
        records = self.db.get_all_records()

        if not records:
            print("No records to export.")
            return

        filename = f"api_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(records, f, indent=2, default=str)
            print(f"✓ Successfully exported {len(records)} records to {filename}")
        except Exception as e:
            print(f"Error exporting to JSON: {e}")

    def schedule_collection(self):
        """Schedule periodic API calls"""
        try:
            interval = int(input("Enter interval in seconds between API calls: "))
            count = int(input("Enter number of calls (0 for infinite): "))
        except ValueError:
            print("Invalid input. Please enter numbers only.")
            return

        print(f"\nStarting scheduled collection every {interval} seconds...")
        print("Press Ctrl+C to stop.\n")

        call_count = 0
        try:
            while count == 0 or call_count < count:
                call_count += 1
                print(f"\n--- Call #{call_count} at {datetime.now().strftime('%H:%M:%S')} ---")
                self.fetch_and_store()

                if call_count < count or count == 0:
                    print(f"Waiting {interval} seconds...")
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nScheduled collection stopped by user.")
        except Exception as e:
            print(f"\nError in scheduled collection: {e}")

    def change_api_url(self):
        """Change the API endpoint URL"""
        print(f"\nCurrent URL: {self.current_api_url}")
        print("Enter new API URL (or press Enter to keep current):")
        new_url = input().strip()

        if new_url:
            # Validate URL format
            if new_url.startswith(('http://', 'https://')):
                self.current_api_url = new_url
                print(f"✓ API URL updated to: {self.current_api_url}")
            else:
                print("⚠ Invalid URL format. URL must start with http:// or https://")

    def delete_all_records(self):
        """Delete all records from database"""
        confirm = input("⚠ Are you sure you want to delete ALL records? (yes/no): ")

        if confirm.lower() == 'yes':
            if self.db.delete_all_records():
                print("✓ All records have been deleted.")
            else:
                print("Failed to delete records.")
        else:
            print("Deletion cancelled.")

    def run(self):
        """Main application loop"""
        print("\n🚀 API Data Collector Started")
        print(f"📁 Database: {self.db.db_name}")
        print(f"🔌 Requests library: {'Available' if REQUESTS_AVAILABLE else 'Not available (simulation mode)'}")

        while True:
            self.display_menu()
            choice = input("\nEnter your choice (1-8): ").strip()

            if choice == '1':
                use_custom = input("Use custom URL? (y/n): ").lower()
                if use_custom == 'y':
                    url = input("Enter API URL: ").strip()
                    if url:
                        self.fetch_and_store(url)
                    else:
                        print("No URL provided.")
                else:
                    self.fetch_and_store()

            elif choice == '2':
                self.view_records()

            elif choice == '3':
                self.filter_by_status()

            elif choice == '4':
                self.export_to_json()

            elif choice == '5':
                self.schedule_collection()

            elif choice == '6':
                self.change_api_url()

            elif choice == '7':
                self.delete_all_records()

            elif choice == '8':
                print("\n👋 Goodbye!")
                sys.exit(0)

            else:
                print("Invalid choice. Please enter 1-8.")

            input("\nPress Enter to continue...")


if __name__ == "__main__":
    app = DataCollectorApp()
    app.run()