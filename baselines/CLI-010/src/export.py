"""Data export functionality"""
import json
import csv
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ExportManager:
    """Manages data export to various formats"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def export(
        self,
        data: Dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None
    ) -> Path:
        """Export data to specified format"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dashboard_export_{timestamp}"
        
        # Add appropriate extension
        if not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"
        
        file_path = self.output_dir / filename
        
        if format == "json":
            return await self._export_json(data, file_path)
        elif format == "csv":
            return await self._export_csv(data, file_path)
        elif format == "yaml":
            return await self._export_yaml(data, file_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def _export_json(self, data: Dict[str, Any], file_path: Path) -> Path:
        """Export data as JSON"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return file_path
    
    async def _export_csv(self, data: Dict[str, Any], file_path: Path) -> Path:
        """Export data as CSV"""
        # Flatten nested data for CSV
        flat_data = self._flatten_dict(data)
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write headers
            writer.writerow(["Key", "Value"])
            
            # Write data
            for key, value in flat_data.items():
                writer.writerow([key, value])
        
        return file_path
    
    async def _export_yaml(self, data: Dict[str, Any], file_path: Path) -> Path:
        """Export data as YAML"""
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return file_path
    
    def _flatten_dict(
        self,
        data: Dict[str, Any],
        parent_key: str = "",
        separator: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        
        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(
                    self._flatten_dict(value, new_key, separator).items()
                )
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.extend(
                            self._flatten_dict(
                                item,
                                f"{new_key}[{i}]",
                                separator
                            ).items()
                        )
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, value))
        
        return dict(items)
    
    def get_supported_formats(self) -> list:
        """Get list of supported export formats"""
        return ["json", "csv", "yaml"]
    
    def get_exports(self) -> list:
        """Get list of existing exports"""
        exports = []
        for file in self.output_dir.iterdir():
            if file.is_file():
                exports.append({
                    "filename": file.name,
                    "size": file.stat().st_size,
                    "modified": datetime.fromtimestamp(file.stat().st_mtime),
                    "path": str(file)
                })
        return exports