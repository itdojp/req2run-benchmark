"""Custom widgets for TUI dashboard"""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import deque

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Label, ProgressBar, Sparkline, Log, Input, ListView, ListItem
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.table import Table
from rich.console import RenderableType
import plotext as plt

from .data_source import DataSource


class MetricsWidget(Widget):
    """Widget displaying real-time metrics cards"""
    
    metrics = reactive({})
    
    def __init__(
        self,
        title: str = "Metrics",
        data_source: Optional[DataSource] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.data_source = data_source
        self.border_title = title
    
    def on_mount(self) -> None:
        """Start metrics updates on mount"""
        if self.data_source:
            self.set_interval(1.0, self.update_metrics)
    
    async def update_metrics(self) -> None:
        """Update metrics from data source"""
        if self.data_source:
            self.metrics = await self.data_source.get_metrics()
            self.refresh()
    
    def render(self) -> RenderableType:
        """Render metrics cards"""
        table = Table(show_header=False, show_edge=False, padding=1)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in self.metrics.items():
            table.add_row(key, str(value))
        
        return table


class ChartWidget(Widget):
    """Widget displaying real-time charts"""
    
    data_points = reactive([])
    
    def __init__(
        self,
        title: str = "Chart",
        data_source: Optional[DataSource] = None,
        max_points: int = 50,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.data_source = data_source
        self.max_points = max_points
        self.data_buffer = deque(maxlen=max_points)
        self.border_title = title
    
    def on_mount(self) -> None:
        """Start chart updates on mount"""
        if self.data_source:
            self.set_interval(0.5, self.update_chart)
    
    async def update_chart(self) -> None:
        """Update chart data from data source"""
        if self.data_source:
            new_data = await self.data_source.get_chart_data()
            self.data_buffer.extend(new_data)
            self.data_points = list(self.data_buffer)
            self.refresh()
    
    def render(self) -> RenderableType:
        """Render chart using plotext"""
        if not self.data_points:
            return "No data available"
        
        # Create ASCII chart
        plt.clf()
        plt.theme("dark")
        plt.plot(self.data_points, marker="braille")
        plt.title(self.title)
        plt.plotsize(self.size.width - 4, self.size.height - 4)
        
        # Return as string
        return plt.build()


class LogsWidget(ScrollableContainer):
    """Scrollable logs widget with filtering"""
    
    def __init__(
        self,
        title: str = "Logs",
        data_source: Optional[DataSource] = None,
        max_lines: int = 1000,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.data_source = data_source
        self.max_lines = max_lines
        self.log_lines = deque(maxlen=max_lines)
        self.border_title = title
        self.log = Log(id="log-content", highlight=True, markup=True)
    
    def compose(self) -> ComposeResult:
        """Compose log widget"""
        yield self.log
    
    def on_mount(self) -> None:
        """Start log updates on mount"""
        if self.data_source:
            self.set_interval(0.5, self.update_logs)
    
    async def update_logs(self) -> None:
        """Update logs from data source"""
        if self.data_source:
            new_logs = await self.data_source.get_logs()
            for log_entry in new_logs:
                self.add_log(log_entry)
    
    def add_log(self, entry: Dict[str, Any]) -> None:
        """Add a log entry"""
        timestamp = entry.get("timestamp", datetime.now().isoformat())
        level = entry.get("level", "INFO")
        message = entry.get("message", "")
        
        # Color based on level
        color_map = {
            "ERROR": "red",
            "WARNING": "yellow",
            "INFO": "green",
            "DEBUG": "dim",
        }
        color = color_map.get(level, "white")
        
        formatted = f"[{color}]{timestamp} [{level}] {message}[/{color}]"
        self.log.write_line(formatted)
    
    def clear(self) -> None:
        """Clear all logs"""
        self.log.clear()
        self.log_lines.clear()


class SystemMonitorWidget(Widget):
    """System monitoring widget with CPU, memory, etc."""
    
    system_data = reactive({})
    
    def __init__(
        self,
        title: str = "System Monitor",
        data_source: Optional[DataSource] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.data_source = data_source
        self.border_title = title
    
    def on_mount(self) -> None:
        """Start system monitoring on mount"""
        if self.data_source:
            self.set_interval(2.0, self.update_system_data)
    
    async def update_system_data(self) -> None:
        """Update system data from data source"""
        if self.data_source:
            self.system_data = await self.data_source.get_system_info()
            self.refresh()
    
    def render(self) -> RenderableType:
        """Render system information"""
        table = Table(show_header=True, show_edge=False)
        table.add_column("Resource", style="cyan")
        table.add_column("Usage", style="green")
        table.add_column("Bar", style="blue")
        
        for resource, value in self.system_data.items():
            if isinstance(value, (int, float)):
                # Create progress bar representation
                bar_length = 20
                filled = int(value * bar_length / 100)
                bar = "█" * filled + "░" * (bar_length - filled)
                table.add_row(resource, f"{value:.1f}%", bar)
            else:
                table.add_row(resource, str(value), "")
        
        return table


class CommandPalette(Widget):
    """Command palette with fuzzy search"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.commands = [
            ("Export Data", "export"),
            ("Toggle Theme", "toggle_theme"),
            ("Clear Logs", "clear_logs"),
            ("Refresh Dashboard", "refresh"),
            ("Show Help", "help"),
            ("Quit", "quit"),
        ]
        self.filtered_commands = self.commands.copy()
    
    def compose(self) -> ComposeResult:
        """Compose command palette"""
        with Vertical():
            yield Input(
                placeholder="Type to search commands...",
                id="command-input"
            )
            yield ListView(
                *[ListItem(Label(cmd[0])) for cmd in self.commands],
                id="command-list"
            )
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter commands based on input"""
        query = event.value.lower()
        
        if not query:
            self.filtered_commands = self.commands.copy()
        else:
            # Simple fuzzy search
            self.filtered_commands = [
                cmd for cmd in self.commands
                if query in cmd[0].lower()
            ]
        
        # Update list view
        list_view = self.query_one("#command-list", ListView)
        list_view.clear()
        for cmd in self.filtered_commands:
            list_view.append(ListItem(Label(cmd[0])))
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Execute selected command"""
        index = event.index
        if 0 <= index < len(self.filtered_commands):
            command = self.filtered_commands[index][1]
            await self.app.action(command)
            await self.app.pop_screen()


class NotificationWidget(Widget):
    """Notification area for user feedback"""
    
    notifications = reactive([])
    
    def __init__(self, max_notifications: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.max_notifications = max_notifications
        self.notification_queue = deque(maxlen=max_notifications)
    
    def notify(
        self,
        message: str,
        severity: str = "info",
        duration: float = 3.0
    ) -> None:
        """Add a notification"""
        notification = {
            "message": message,
            "severity": severity,
            "timestamp": datetime.now(),
        }
        self.notification_queue.append(notification)
        self.notifications = list(self.notification_queue)
        self.refresh()
        
        # Auto-dismiss after duration
        self.set_timer(duration, lambda: self.dismiss_oldest())
    
    def dismiss_oldest(self) -> None:
        """Dismiss the oldest notification"""
        if self.notification_queue:
            self.notification_queue.popleft()
            self.notifications = list(self.notification_queue)
            self.refresh()
    
    def render(self) -> RenderableType:
        """Render notifications"""
        if not self.notifications:
            return ""
        
        severity_colors = {
            "error": "red",
            "warning": "yellow",
            "success": "green",
            "info": "blue",
        }
        
        lines = []
        for notif in self.notifications:
            color = severity_colors.get(notif["severity"], "white")
            lines.append(f"[{color}]● {notif['message']}[/{color}]")
        
        return "\n".join(lines)