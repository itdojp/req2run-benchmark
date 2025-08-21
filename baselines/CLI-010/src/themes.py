"""Theme management for TUI dashboard"""
from typing import Dict, Any, List
from .config import DashboardConfig, ThemeConfig


class ThemeManager:
    """Manages dashboard themes"""
    
    def __init__(self, config: DashboardConfig):
        self.config = config
        self.themes = {theme.name: theme for theme in config.themes}
        self.current_theme_name = config.default_theme
        
        # Add built-in themes if not in config
        self._add_builtin_themes()
    
    def _add_builtin_themes(self) -> None:
        """Add built-in themes"""
        builtin_themes = [
            ThemeConfig(
                name="dark",
                colors={
                    "background": "#1e1e1e",
                    "foreground": "#d4d4d4",
                    "primary": "#007acc",
                    "secondary": "#68217a",
                    "success": "#4ec9b0",
                    "warning": "#ce9178",
                    "error": "#f44747",
                    "border": "#3c3c3c",
                    "highlight": "#264f78"
                },
                styles={
                    "border": "rounded",
                    "shadow": True
                }
            ),
            ThemeConfig(
                name="light",
                colors={
                    "background": "#ffffff",
                    "foreground": "#333333",
                    "primary": "#0066cc",
                    "secondary": "#6b46c1",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444",
                    "border": "#e0e0e0",
                    "highlight": "#e6f2ff"
                },
                styles={
                    "border": "rounded",
                    "shadow": False
                }
            ),
            ThemeConfig(
                name="high-contrast",
                colors={
                    "background": "#000000",
                    "foreground": "#ffffff",
                    "primary": "#00ff00",
                    "secondary": "#ffff00",
                    "success": "#00ff00",
                    "warning": "#ffff00",
                    "error": "#ff0000",
                    "border": "#ffffff",
                    "highlight": "#0000ff"
                },
                styles={
                    "border": "heavy",
                    "shadow": False
                }
            ),
            ThemeConfig(
                name="solarized",
                colors={
                    "background": "#002b36",
                    "foreground": "#839496",
                    "primary": "#268bd2",
                    "secondary": "#2aa198",
                    "success": "#859900",
                    "warning": "#b58900",
                    "error": "#dc322f",
                    "border": "#073642",
                    "highlight": "#073642"
                },
                styles={
                    "border": "rounded",
                    "shadow": True
                }
            )
        ]
        
        for theme in builtin_themes:
            if theme.name not in self.themes:
                self.themes[theme.name] = theme
    
    @property
    def current_theme(self) -> str:
        """Get current theme as CSS string"""
        theme = self.themes.get(self.current_theme_name)
        if not theme:
            return ""
        
        css_rules = []
        
        # Generate CSS from theme colors
        for color_name, color_value in theme.colors.items():
            css_var = f"--{color_name.replace('_', '-')}"
            css_rules.append(f"    {css_var}: {color_value};")
        
        # Add styles
        if theme.styles.get("border") == "rounded":
            css_rules.append("    --border-style: rounded;")
        elif theme.styles.get("border") == "heavy":
            css_rules.append("    --border-style: heavy;")
        else:
            css_rules.append("    --border-style: solid;")
        
        if theme.styles.get("shadow"):
            css_rules.append("    --shadow: 0 2px 4px rgba(0,0,0,0.2);")
        
        # Build CSS
        css = f"""
Screen {{
{chr(10).join(css_rules)}
}}

/* Widget styles */
Widget {{
    background: var(--background);
    color: var(--foreground);
}}

.success {{
    color: var(--success);
}}

.warning {{
    color: var(--warning);
}}

.error {{
    color: var(--error);
}}

/* Border styles */
Widget.bordered {{
    border: var(--border-style) var(--border);
}}

/* Focus styles */
Widget:focus {{
    border: var(--border-style) var(--primary);
}}

/* Button styles */
Button {{
    background: var(--primary);
    color: var(--background);
}}

Button:hover {{
    background: var(--secondary);
}}

/* Input styles */
Input {{
    background: var(--background);
    border: solid var(--border);
}}

Input:focus {{
    border: solid var(--primary);
}}

/* Table styles */
DataTable {{
    background: var(--background);
}}

DataTable > .datatable--header {{
    background: var(--highlight);
    color: var(--foreground);
}}

DataTable > .datatable--cursor {{
    background: var(--primary);
    color: var(--background);
}}

/* Scrollbar styles */
ScrollBar {{
    background: var(--border);
}}

ScrollBar > .scrollbar--thumb {{
    background: var(--primary);
}}
"""
        return css
    
    def toggle_theme(self) -> None:
        """Toggle to next theme"""
        theme_names = list(self.themes.keys())
        current_index = theme_names.index(self.current_theme_name)
        next_index = (current_index + 1) % len(theme_names)
        self.current_theme_name = theme_names[next_index]
    
    def set_theme(self, theme_name: str) -> bool:
        """Set specific theme"""
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            return True
        return False
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names"""
        return list(self.themes.keys())
    
    def get_theme_config(self, theme_name: str) -> Optional[ThemeConfig]:
        """Get theme configuration"""
        return self.themes.get(theme_name)