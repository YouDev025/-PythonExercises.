#!/usr/bin/env python3
"""
interactive_terminal_dashboard.py
A terminal-based system monitoring dashboard with interactive widgets
Supports both Windows and Unix-like systems
"""

import sys
import os
import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import signal
from datetime import datetime
import platform

try:
    import psutil
except ImportError:
    print("Please install psutil: pip install psutil")
    sys.exit(1)

# Platform-specific terminal handling
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    try:
        import colorama
        from colorama import Fore, Back, Style, init

        init()
        # For Windows, we'll use a simple console-based approach
        USE_CURSES = False
    except ImportError:
        print("Installing colorama for Windows support...")
        os.system("pip install colorama")
        import colorama
        from colorama import Fore, Back, Style, init

        init()
        USE_CURSES = False
else:
    try:
        import curses

        USE_CURSES = True
    except ImportError:
        print("Curses not available, falling back to simple console mode")
        USE_CURSES = False
        try:
            import colorama
            from colorama import Fore, Back, Style, init

            init()
        except ImportError:
            pass


class DataProvider:
    """Provides real-time system metrics"""

    def __init__(self):
        self._lock = threading.Lock()
        self._last_update = {}

    def get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU metrics"""
        with self._lock:
            return {
                'percent': psutil.cpu_percent(interval=0.1),
                'cores': psutil.cpu_count(),
                'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                'per_cpu': psutil.cpu_percent(interval=0.1, percpu=True)
            }

    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory metrics"""
        with self._lock:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {
                'total': mem.total,
                'available': mem.available,
                'percent': mem.percent,
                'used': mem.used,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent
            }

    def get_processes(self, limit: int = 10, sort_by: str = 'cpu') -> List[Dict[str, Any]]:
        """Get top processes sorted by CPU or memory"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                proc_info = proc.info
                processes.append({
                    'pid': proc_info['pid'],
                    'name': proc_info['name'] or 'N/A',
                    'cpu': proc_info['cpu_percent'] or 0,
                    'memory': proc_info['memory_percent'] or 0,
                    'status': proc_info['status'] or 'N/A'
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        sort_key = 'cpu' if sort_by == 'cpu' else 'memory'
        processes.sort(key=lambda x: x[sort_key], reverse=True)
        return processes[:limit]

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        with self._lock:
            return {
                'hostname': psutil.users()[0].host if psutil.users() else 'localhost',
                'boot_time': datetime.fromtimestamp(psutil.boot_time()),
                'users': len(psutil.users()),
                'network': psutil.net_io_counters()
            }


class Widget(ABC):
    """Base class for all dashboard widgets"""

    def __init__(self, x: int, y: int, width: int, height: int, title: str):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self._active = True
        self._data = {}
        self._last_update = 0
        self._update_interval = 1.0

    @abstractmethod
    def update(self, data_provider: DataProvider) -> None:
        """Update widget data"""
        pass

    @abstractmethod
    def render(self, stdscr) -> None:
        """Render the widget"""
        pass

    def set_active(self, active: bool) -> None:
        """Set widget active state"""
        self._active = active

    def is_active(self) -> bool:
        """Check if widget is active"""
        return self._active


class CPUWidget(Widget):
    """Widget for displaying CPU information"""

    def update(self, data_provider: DataProvider) -> None:
        self._data = data_provider.get_cpu_metrics()

    def render(self, stdscr) -> None:
        if not self._active:
            return

        # Draw border and title
        print(f"\033[{self.y};{self.x}H", end='')
        print(f"+{'-' * (self.width - 2)}+")
        print(f"\033[{self.y + 1};{self.x}H| {self.title.center(self.width - 4)} |")

        # Display CPU information
        y_offset = self.y + 2
        x_offset = self.x + 2

        cpu_percent = self._data.get('percent', 0)
        cores = self._data.get('cores', 0)
        frequency = self._data.get('frequency', 0)

        print(f"\033[{y_offset};{x_offset}H", end='')
        print(f"Overall CPU: {cpu_percent:5.1f}% ", end='')

        # Create a simple bar graph
        bar_length = self.width - 15
        filled = int(bar_length * cpu_percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"[{bar}]")

        print(f"\033[{y_offset + 1};{x_offset}HCores: {cores}")
        print(f"\033[{y_offset + 2};{x_offset}HFrequency: {frequency:.0f} MHz")

        # Display per-core usage
        per_cpu = self._data.get('per_cpu', [])
        if per_cpu:
            y_offset += 3
            print(f"\033[{y_offset};{x_offset}HPer Core:")
            y_offset += 1
            for i, core_usage in enumerate(per_cpu[:self.height - 6]):
                bar_len = min(self.width - 15, 20)
                filled = int(bar_len * core_usage / 100)
                bar = '█' * filled + '░' * (bar_len - filled)
                print(f"\033[{y_offset + i};{x_offset}HCore {i:2d}: {core_usage:5.1f}% {bar}")

        # Draw bottom border
        print(f"\033[{self.y + self.height - 1};{self.x}H+{'-' * (self.width - 2)}+")


class MemoryWidget(Widget):
    """Widget for displaying memory information"""

    def update(self, data_provider: DataProvider) -> None:
        self._data = data_provider.get_memory_metrics()

    def render(self, stdscr) -> None:
        if not self._active:
            return

        # Draw border and title
        print(f"\033[{self.y};{self.x}H", end='')
        print(f"+{'-' * (self.width - 2)}+")
        print(f"\033[{self.y + 1};{self.x}H| {self.title.center(self.width - 4)} |")

        # Display memory information
        y_offset = self.y + 2
        x_offset = self.x + 2

        total = self._data.get('total', 0) / (1024 ** 3)
        used = self._data.get('used', 0) / (1024 ** 3)
        percent = self._data.get('percent', 0)

        print(f"\033[{y_offset};{x_offset}H", end='')
        print(f"RAM: {used:5.2f} GB / {total:5.2f} GB ({percent:5.1f}%) ", end='')

        # Create memory bar
        bar_length = self.width - 35
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"[{bar}]")

        # Swap information
        swap_total = self._data.get('swap_total', 0) / (1024 ** 3)
        swap_used = self._data.get('swap_used', 0) / (1024 ** 3)
        swap_percent = self._data.get('swap_percent', 0)

        y_offset += 2
        print(f"\033[{y_offset};{x_offset}H", end='')
        print(f"Swap: {swap_used:5.2f} GB / {swap_total:5.2f} GB ({swap_percent:5.1f}%) ", end='')

        # Swap bar
        filled = int(bar_length * swap_percent / 100) if swap_total > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"[{bar}]")

        # Draw bottom border
        print(f"\033[{self.y + self.height - 1};{self.x}H+{'-' * (self.width - 2)}+")


class ProcessWidget(Widget):
    """Widget for displaying top processes"""

    def __init__(self, x: int, y: int, width: int, height: int, title: str):
        super().__init__(x, y, width, height, title)
        self._sort_by = 'cpu'
        self._filter = ''

    def update(self, data_provider: DataProvider) -> None:
        self._data = data_provider.get_processes(
            limit=self.height - 3,
            sort_by=self._sort_by
        )

    def render(self, stdscr) -> None:
        if not self._active:
            return

        # Draw border and title
        print(f"\033[{self.y};{self.x}H", end='')
        print(f"+{'-' * (self.width - 2)}+")
        print(f"\033[{self.y + 1};{self.x}H| {self.title.center(self.width - 4)} |")

        y_offset = self.y + 2
        x_offset = self.x + 2

        # Display sort indicator
        sort_indicator = f"Sort: {self._sort_by.upper()} | Filter: {self._filter or 'None'}"
        print(f"\033[{y_offset};{x_offset}H{sort_indicator[:self.width - 4]}")

        y_offset += 1

        # Display headers
        print(f"\033[{y_offset};{x_offset}H{'PID':<8} {'CPU%':<8} {'MEM%':<8} {'NAME'}")
        y_offset += 1

        # Display processes
        for proc in self._data:
            if self._filter and self._filter.lower() not in proc['name'].lower():
                continue

            if y_offset >= self.y + self.height - 1:
                break

            line = f"{proc['pid']:<8} {proc['cpu']:>6.1f}% {proc['memory']:>6.1f}% {proc['name'][:self.width - 30]}"
            print(f"\033[{y_offset};{x_offset}H{line[:self.width - 4]}")
            y_offset += 1

        # Draw bottom border
        print(f"\033[{self.y + self.height - 1};{self.x}H+{'-' * (self.width - 2)}+")

    def set_sort(self, sort_by: str) -> None:
        """Set sorting method"""
        if sort_by in ['cpu', 'memory']:
            self._sort_by = sort_by

    def set_filter(self, filter_text: str) -> None:
        """Set process name filter"""
        self._filter = filter_text


class LogWidget(Widget):
    """Widget for displaying system logs"""

    def __init__(self, x: int, y: int, width: int, height: int, title: str):
        super().__init__(x, y, width, height, title)
        self._logs = []
        self._max_logs = 100

    def update(self, data_provider: DataProvider) -> None:
        # Simulate log entries
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._logs.append(f"[{timestamp}] System update - CPU: {data_provider.get_cpu_metrics()['percent']}%")

        if len(self._logs) > self._max_logs:
            self._logs.pop(0)

    def render(self, stdscr) -> None:
        if not self._active:
            return

        # Draw border and title
        print(f"\033[{self.y};{self.x}H", end='')
        print(f"+{'-' * (self.width - 2)}+")
        print(f"\033[{self.y + 1};{self.x}H| {self.title.center(self.width - 4)} |")

        y_offset = self.y + 2
        x_offset = self.x + 2

        # Display logs (most recent at bottom)
        display_logs = self._logs[-(self.height - 2):]
        for log in display_logs:
            if y_offset >= self.y + self.height - 1:
                break
            print(f"\033[{y_offset};{x_offset}H{log[:self.width - 4]}")
            y_offset += 1

        # Draw bottom border
        print(f"\033[{self.y + self.height - 1};{self.x}H+{'-' * (self.width - 2)}+")

    def add_log(self, message: str) -> None:
        """Add custom log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._logs.append(f"[{timestamp}] {message}")
        if len(self._logs) > self._max_logs:
            self._logs.pop(0)


class SimpleTerminal:
    """Simple terminal handler for Windows"""

    def __init__(self):
        self._running = True
        self._input_thread = None

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if IS_WINDOWS else 'clear')

    def hide_cursor(self):
        """Hide cursor (Windows doesn't support this easily)"""
        if not IS_WINDOWS:
            print('\033[?25l', end='')

    def show_cursor(self):
        """Show cursor"""
        if not IS_WINDOWS:
            print('\033[?25h', end='')

    def getch(self):
        """Get a single character input"""
        if IS_WINDOWS:
            import msvcrt
            return msvcrt.getch().decode('ascii', errors='ignore')
        else:
            import sys
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch


class Dashboard:
    """Main dashboard class managing the UI"""

    def __init__(self):
        self._running = True
        self._data_provider = DataProvider()
        self._widgets: List[Widget] = []
        self._active_widget_index = 0
        self._update_thread = None
        self._terminal = SimpleTerminal()

        # Get terminal size
        self._terminal_size = self._get_terminal_size()

    def _get_terminal_size(self):
        """Get terminal size"""
        if IS_WINDOWS:
            from shutil import get_terminal_size
            return get_terminal_size()
        else:
            import shutil
            return shutil.get_terminal_size()

    def _setup_layout(self):
        """Setup widgets based on terminal size"""
        self._widgets.clear()

        height, width = self._terminal_size.lines, self._terminal_size.columns

        # Calculate widget dimensions
        half_width = width // 2
        quarter_height = height // 4

        # Create widgets
        self._widgets.append(CPUWidget(0, 0, half_width, quarter_height, "CPU Monitor"))
        self._widgets.append(MemoryWidget(half_width, 0, half_width, quarter_height, "Memory Monitor"))
        self._widgets.append(ProcessWidget(0, quarter_height, width, quarter_height * 2, "Process Monitor"))
        self._widgets.append(LogWidget(0, quarter_height * 3, width, quarter_height, "System Logs"))

        self._active_widget_index = 0
        for i, widget in enumerate(self._widgets):
            widget.set_active(i == self._active_widget_index)

    def _update_data(self):
        """Update all widgets with new data"""
        while self._running:
            for widget in self._widgets:
                try:
                    widget.update(self._data_provider)
                except Exception as e:
                    if isinstance(widget, LogWidget):
                        widget.add_log(f"Error updating: {str(e)}")
            time.sleep(0.5)

    def _handle_input(self):
        """Handle keyboard input"""
        import threading

        def input_handler():
            while self._running:
                try:
                    ch = self._terminal.getch()
                    if ch == 'q' or ch == 'Q':
                        self._running = False
                        break
                    elif ch == '\t':  # Tab key
                        self._active_widget_index = (self._active_widget_index + 1) % len(self._widgets)
                        for i, widget in enumerate(self._widgets):
                            widget.set_active(i == self._active_widget_index)
                    elif ch == 's' and isinstance(self._widgets[self._active_widget_index], ProcessWidget):
                        current_sort = self._widgets[self._active_widget_index]._sort_by
                        new_sort = 'memory' if current_sort == 'cpu' else 'cpu'
                        self._widgets[self._active_widget_index].set_sort(new_sort)
                    elif ch == 'f' and isinstance(self._widgets[self._active_widget_index], ProcessWidget):
                        # Simple filter input
                        print(
                            f"\033[{self._widgets[self._active_widget_index].y + self._widgets[self._active_widget_index].height - 1};{self._widgets[self._active_widget_index].x + 2}HFilter: ",
                            end='')
                        filter_input = input()
                        self._widgets[self._active_widget_index].set_filter(filter_input)
                except:
                    pass

        input_thread = threading.Thread(target=input_handler, daemon=True)
        input_thread.start()

    def _render(self):
        """Render all widgets"""
        self._terminal.clear_screen()
        self._terminal.hide_cursor()

        height, width = self._terminal_size.lines, self._terminal_size.columns

        # Display help bar
        help_text = "Tab: Switch Widget | Q: Quit | S: Sort Processes | F: Filter Processes"
        print(f"\033[{height - 1};0H", end='')
        print(f"{'=' * width}")
        print(f"\033[{height};0H", end='')
        print(help_text[:width - 1])

        # Render all widgets
        for widget in self._widgets:
            try:
                widget.render(None)
            except Exception as e:
                pass

    def run(self):
        """Main dashboard loop"""
        try:
            self._setup_layout()

            # Start update thread
            self._update_thread = threading.Thread(target=self._update_data, daemon=True)
            self._update_thread.start()

            # Start input handler
            self._handle_input()

            # Main render loop
            while self._running:
                self._render()
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up"""
        self._running = False
        self._terminal.show_cursor()
        print("\033[?25h", end='')  # Show cursor
        print("\033[2J\033[H", end='')  # Clear screen


def main():
    """Main entry point"""
    print("Starting System Dashboard...")
    print("If you're on Windows, install windows-curses for better experience: pip install windows-curses")
    time.sleep(2)

    dashboard = Dashboard()
    dashboard.run()


if __name__ == "__main__":
    main()