"""Configuration for TUI dashboard"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import yaml


@dataclass
class WidgetConfig:
    """Configuration for a dashboard widget"""
    type: str
    title: str
    position: Dict[str, int]
    size: Dict[str, int]
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThemeConfig:
    """Theme configuration"""
    name: str
    colors: Dict[str, str]
    styles: Dict[str, str]


@dataclass
class DashboardConfig:
    """Main dashboard configuration"""
    title: str = "TUI Dashboard"
    refresh_rate: float = 1.0
    max_fps: int = 30
    
    # Widget configurations
    widgets: List[WidgetConfig] = field(default_factory=list)
    
    # Theme configurations
    themes: List[ThemeConfig] = field(default_factory=list)
    default_theme: str = "dark"
    
    # Data source settings
    data_source: Dict[str, Any] = field(default_factory=dict)
    
    # Export settings
    export: Dict[str, Any] = field(default_factory=dict)
    
    # Keyboard bindings
    keybindings: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "DashboardConfig":
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path("config/dashboard.yaml")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
                return cls.from_dict(data)
        
        # Return default configuration
        return cls.default()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardConfig":
        """Create configuration from dictionary"""
        config = cls()
        
        # Basic settings
        config.title = data.get("title", config.title)
        config.refresh_rate = data.get("refresh_rate", config.refresh_rate)
        config.max_fps = data.get("max_fps", config.max_fps)
        
        # Widget configurations
        widgets_data = data.get("widgets", [])
        config.widgets = [
            WidgetConfig(**widget) for widget in widgets_data
        ]
        
        # Theme configurations
        themes_data = data.get("themes", [])
        config.themes = [
            ThemeConfig(**theme) for theme in themes_data
        ]
        config.default_theme = data.get("default_theme", config.default_theme)
        
        # Other settings
        config.data_source = data.get("data_source", {})
        config.export = data.get("export", {})
        config.keybindings = data.get("keybindings", {})
        
        return config
    
    @classmethod
    def default(cls) -> "DashboardConfig":
        """Create default configuration"""
        return cls(
            title="Interactive TUI Dashboard",
            refresh_rate=1.0,
            max_fps=30,
            widgets=[
                WidgetConfig(
                    type="metrics",
                    title="System Metrics",
                    position={"row": 0, "col": 0},
                    size={"width": 50, "height": 10}
                ),
                WidgetConfig(
                    type="chart",
                    title="Performance Chart",
                    position={"row": 0, "col": 50},
                    size={"width": 50, "height": 10}
                ),
                WidgetConfig(
                    type="logs",
                    title="Application Logs",
                    position={"row": 10, "col": 0},
                    size={"width": 100, "height": 20}
                ),
            ],
            themes=[
                ThemeConfig(
                    name="dark",
                    colors={
                        "background": "#1e1e1e",
                        "foreground": "#d4d4d4",
                        "primary": "#007acc",
                        "secondary": "#68217a",
                        "success": "#4ec9b0",
                        "warning": "#ce9178",
                        "error": "#f44747"
                    },
                    styles={}
                ),
                ThemeConfig(
                    name="light",
                    colors={
                        "background": "#ffffff",
                        "foreground": "#000000",
                        "primary": "#0066cc",
                        "secondary": "#6b46c1",
                        "success": "#10b981",
                        "warning": "#f59e0b",
                        "error": "#ef4444"
                    },
                    styles={}
                ),
            ],
            data_source={
                "type": "mock",
                "update_interval": 1.0
            },
            export={
                "formats": ["json", "csv", "yaml"],
                "default_format": "json",
                "output_dir": "exports"
            },
            keybindings={
                "quit": "q",
                "help": "f1",
                "command_palette": "ctrl+p",
                "export": "ctrl+e",
                "toggle_theme": "ctrl+t"
            }
        )
    
    def save(self, config_path: Path) -> None:
        """Save configuration to YAML file"""
        data = {
            "title": self.title,
            "refresh_rate": self.refresh_rate,
            "max_fps": self.max_fps,
            "widgets": [
                {
                    "type": w.type,
                    "title": w.title,
                    "position": w.position,
                    "size": w.size,
                    "options": w.options
                }
                for w in self.widgets
            ],
            "themes": [
                {
                    "name": t.name,
                    "colors": t.colors,
                    "styles": t.styles
                }
                for t in self.themes
            ],
            "default_theme": self.default_theme,
            "data_source": self.data_source,
            "export": self.export,
            "keybindings": self.keybindings
        }
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)