"""
CLI-010: Interactive TUI Dashboard with Real-Time Updates
Main application entry point
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, DataTable, Button, Input, Log, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from textual.screen import Screen
from rich.text import Text

from .widgets import (
    MetricsWidget,
    ChartWidget,
    LogsWidget,
    SystemMonitorWidget,
    CommandPalette,
    NotificationWidget
)
from .data_source import DataSource
from .config import DashboardConfig
from .themes import ThemeManager
from .export import ExportManager


class DashboardScreen(Screen):
    """Main dashboard screen with widgets"""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+p", "command_palette", "Command Palette"),
        Binding("ctrl+e", "export", "Export Data"),
        Binding("ctrl+t", "toggle_theme", "Toggle Theme"),
        Binding("tab", "focus_next", "Next Widget"),
        Binding("shift+tab", "focus_previous", "Previous Widget"),
        Binding("ctrl+l", "clear_logs", "Clear Logs"),
        Binding("f1", "help", "Help"),
    ]
    
    def __init__(self, config: DashboardConfig):
        super().__init__()
        self.config = config
        self.data_source = DataSource(config)
        self.theme_manager = ThemeManager(config)
        self.export_manager = ExportManager()
        
    def compose(self) -> ComposeResult:
        """Compose the dashboard layout"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Horizontal(id="top-row"):
                # Metrics cards
                yield MetricsWidget(
                    id="metrics",
                    title="System Metrics",
                    data_source=self.data_source
                )
                
                # Real-time chart
                yield ChartWidget(
                    id="chart",
                    title="Performance Chart",
                    data_source=self.data_source
                )
            
            with Horizontal(id="middle-row"):
                # System monitor
                yield SystemMonitorWidget(
                    id="system-monitor",
                    title="System Monitor",
                    data_source=self.data_source
                )
                
                # Data table
                yield DataTable(
                    id="data-table",
                    show_header=True,
                    show_row_labels=True,
                    zebra_stripes=True,
                    cursor_type="row"
                )
            
            # Scrollable logs at bottom
            yield LogsWidget(
                id="logs",
                title="Application Logs",
                data_source=self.data_source,
                max_lines=1000
            )
        
        # Notification area
        yield NotificationWidget(id="notifications")
        
        # Footer with key bindings
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize dashboard on mount"""
        # Start data updates
        self.data_source.start()
        
        # Initialize data table
        table = self.query_one(DataTable)
        table.add_columns("Timestamp", "Event", "Value", "Status")
        
        # Set initial theme
        self.app.theme = self.theme_manager.current_theme
        
        # Start update loop
        self.set_interval(1.0, self.update_dashboard)
    
    async def update_dashboard(self) -> None:
        """Update dashboard widgets with new data"""
        # Update is handled by individual widgets through data_source
        pass
    
    async def action_command_palette(self) -> None:
        """Show command palette"""
        await self.app.push_screen(CommandPalette())
    
    async def action_export(self) -> None:
        """Export dashboard data"""
        data = await self.data_source.get_current_data()
        file_path = await self.export_manager.export(data)
        
        notifications = self.query_one(NotificationWidget)
        notifications.notify(f"Data exported to {file_path}", severity="success")
    
    async def action_toggle_theme(self) -> None:
        """Toggle between themes"""
        self.theme_manager.toggle_theme()
        self.app.theme = self.theme_manager.current_theme
        
        notifications = self.query_one(NotificationWidget)
        notifications.notify(f"Theme changed to {self.theme_manager.current_theme_name}", severity="info")
    
    async def action_clear_logs(self) -> None:
        """Clear log widget"""
        logs = self.query_one(LogsWidget)
        logs.clear()
        
        notifications = self.query_one(NotificationWidget)
        notifications.notify("Logs cleared", severity="info")
    
    async def action_help(self) -> None:
        """Show help screen"""
        await self.app.push_screen(HelpScreen())


class HelpScreen(Screen):
    """Help screen with keyboard shortcuts"""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose help screen"""
        yield Header(show_clock=False)
        
        with ScrollableContainer():
            yield Static("""
# TUI Dashboard Help

## Keyboard Shortcuts

### Navigation
- `Tab` - Focus next widget
- `Shift+Tab` - Focus previous widget
- `Arrow Keys` - Navigate within widgets
- `Enter` - Select/Activate
- `Escape` - Cancel/Back

### Actions
- `Ctrl+P` - Open command palette
- `Ctrl+E` - Export data
- `Ctrl+T` - Toggle theme
- `Ctrl+L` - Clear logs
- `F1` - Show this help
- `Q` - Quit application

### Widget-Specific
- In tables: `j/k` - Move up/down
- In logs: `g/G` - Go to top/bottom
- In charts: `+/-` - Zoom in/out

## Mouse Support
- Click to focus widgets
- Scroll to navigate scrollable content
- Click and drag to select text

## Command Palette
Access all commands through the command palette (Ctrl+P).
Type to fuzzy search commands.

## Data Export
Export formats supported:
- JSON
- CSV
- YAML

## Themes
Available themes:
- Dark (default)
- Light
- High Contrast
- Solarized
            """, id="help-content")
        
        yield Footer()
    
    async def action_close(self) -> None:
        """Close help screen"""
        await self.app.pop_screen()


class TUIDashboard(App):
    """Main TUI Dashboard Application"""
    
    CSS_PATH = "dashboard.css"
    TITLE = "Interactive TUI Dashboard"
    
    def __init__(self, config_path: Optional[Path] = None):
        super().__init__()
        self.config = DashboardConfig.load(config_path)
        
    def on_mount(self) -> None:
        """Initialize app on mount"""
        # Push main dashboard screen
        self.push_screen(DashboardScreen(self.config))
    
    async def on_resize(self, event: events.Resize) -> None:
        """Handle terminal resize"""
        # Widgets will automatically reflow with Textual's responsive layout
        pass


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive TUI Dashboard")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/dashboard.yaml"),
        help="Path to configuration file"
    )
    parser.add_argument(
        "--theme",
        choices=["dark", "light", "high-contrast", "solarized"],
        default="dark",
        help="Initial theme"
    )
    
    args = parser.parse_args()
    
    # Create and run app
    app = TUIDashboard(config_path=args.config)
    app.run()


if __name__ == "__main__":
    main()