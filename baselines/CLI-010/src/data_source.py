"""Data source for dashboard widgets"""
import asyncio
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque
import psutil
import json
from pathlib import Path

from .config import DashboardConfig


class DataSource:
    """Manages data for all dashboard widgets"""
    
    def __init__(self, config: DashboardConfig):
        self.config = config
        self.running = False
        self.metrics_data = {}
        self.chart_buffer = deque(maxlen=100)
        self.log_buffer = deque(maxlen=1000)
        self.system_info = {}
        self.start_time = time.time()
    
    def start(self) -> None:
        """Start data generation"""
        self.running = True
        asyncio.create_task(self._generate_data())
    
    def stop(self) -> None:
        """Stop data generation"""
        self.running = False
    
    async def _generate_data(self) -> None:
        """Generate mock data for demonstration"""
        while self.running:
            # Update metrics
            self.metrics_data = {
                "Requests/sec": random.randint(100, 500),
                "Response Time": f"{random.uniform(10, 100):.2f}ms",
                "Error Rate": f"{random.uniform(0, 5):.1f}%",
                "Active Users": random.randint(50, 200),
                "Uptime": self._format_uptime(),
            }
            
            # Add chart data points
            self.chart_buffer.append(random.uniform(20, 80))
            
            # Generate log entries
            if random.random() < 0.3:  # 30% chance of new log
                log_entry = self._generate_log_entry()
                self.log_buffer.append(log_entry)
            
            # Update system info
            self.system_info = await self._get_system_info()
            
            await asyncio.sleep(0.5)
    
    def _format_uptime(self) -> str:
        """Format uptime string"""
        uptime_seconds = int(time.time() - self.start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _generate_log_entry(self) -> Dict[str, Any]:
        """Generate a mock log entry"""
        levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        messages = [
            "Request processed successfully",
            "Database connection established",
            "Cache hit for key: user_123",
            "API rate limit approaching",
            "Failed to connect to external service",
            "User authentication successful",
            "Background job completed",
            "Memory usage above threshold",
        ]
        
        level = random.choice(levels)
        if level == "ERROR":
            weight = 0.1
        elif level == "WARNING":
            weight = 0.2
        else:
            weight = 0.7
        
        return {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": random.choice(messages),
        }
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get real system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "CPU": cpu_percent,
                "Memory": memory.percent,
                "Disk": disk.percent,
                "Processes": len(psutil.pids()),
                "Network": f"{psutil.net_io_counters().bytes_sent / 1024 / 1024:.1f} MB",
            }
        except Exception as e:
            # Return mock data if psutil fails
            return {
                "CPU": random.uniform(10, 90),
                "Memory": random.uniform(30, 80),
                "Disk": random.uniform(20, 70),
                "Processes": random.randint(100, 300),
                "Network": f"{random.uniform(10, 100):.1f} MB",
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics_data.copy()
    
    async def get_chart_data(self) -> List[float]:
        """Get new chart data points"""
        # Return last few points
        if len(self.chart_buffer) > 0:
            return [self.chart_buffer[-1]]
        return []
    
    async def get_logs(self) -> List[Dict[str, Any]]:
        """Get new log entries"""
        # Return and clear buffer
        logs = list(self.log_buffer)
        self.log_buffer.clear()
        return logs
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return self.system_info.copy()
    
    async def get_current_data(self) -> Dict[str, Any]:
        """Get all current data for export"""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": await self.get_metrics(),
            "chart_data": list(self.chart_buffer),
            "system_info": await self.get_system_info(),
            "recent_logs": list(self.log_buffer)[-20:],  # Last 20 logs
        }
    
    def load_from_file(self, file_path: Path) -> None:
        """Load data from a file"""
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Load metrics
                if "metrics" in data:
                    self.metrics_data = data["metrics"]
                
                # Load chart data
                if "chart_data" in data:
                    self.chart_buffer.extend(data["chart_data"])
                
                # Load logs
                if "logs" in data:
                    self.log_buffer.extend(data["logs"])