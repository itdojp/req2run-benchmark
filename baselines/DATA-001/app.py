#!/usr/bin/env python3
"""
DATA-001: Real-time Log Aggregation Pipeline
Baseline implementation of a log aggregation system with ingestion,
processing, storage, and query capabilities.
"""

import asyncio
import json
import time
import re
import gzip
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
import socket
import struct
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: float
    source: str
    level: str
    message: str
    fields: Dict[str, Any]
    raw: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class LogParser:
    """Parses different log formats."""
    
    def __init__(self):
        self.patterns = {
            'json': self._parse_json,
            'syslog': self._parse_syslog,
            'apache': self._parse_apache,
            'nginx': self._parse_nginx,
            'plain': self._parse_plain
        }
        
        # Syslog pattern (RFC 5424)
        self.syslog_pattern = re.compile(
            r'<(\d+)>(\d+) (\S+) (\S+) (\S+) (\S+) (\S+) - (.+)'
        )
        
        # Apache/Nginx common log format
        self.apache_pattern = re.compile(
            r'(\S+) \S+ \S+ \[([\w:/]+\s[+\-]\d{4})\] "(\S+) (\S+) (\S+)" (\d{3}) (\d+)'
        )
    
    def parse(self, data: str, source: str = 'unknown') -> Optional[LogEntry]:
        """Parse log data and return LogEntry."""
        # Try JSON first
        entry = self._parse_json(data, source)
        if entry:
            return entry
        
        # Try syslog
        entry = self._parse_syslog(data, source)
        if entry:
            return entry
        
        # Try Apache/Nginx
        entry = self._parse_apache(data, source)
        if entry:
            return entry
        
        # Fallback to plain text
        return self._parse_plain(data, source)
    
    def _parse_json(self, data: str, source: str) -> Optional[LogEntry]:
        """Parse JSON log format."""
        try:
            obj = json.loads(data)
            return LogEntry(
                timestamp=obj.get('timestamp', time.time()),
                source=obj.get('source', source),
                level=obj.get('level', 'info').upper(),
                message=obj.get('message', ''),
                fields=obj,
                raw=data
            )
        except (json.JSONDecodeError, KeyError):
            return None
    
    def _parse_syslog(self, data: str, source: str) -> Optional[LogEntry]:
        """Parse syslog format (RFC 5424)."""
        match = self.syslog_pattern.match(data)
        if match:
            priority = int(match.group(1))
            facility = priority // 8
            severity = priority % 8
            
            level_map = {
                0: 'EMERGENCY', 1: 'ALERT', 2: 'CRITICAL', 3: 'ERROR',
                4: 'WARNING', 5: 'NOTICE', 6: 'INFO', 7: 'DEBUG'
            }
            
            return LogEntry(
                timestamp=time.time(),
                source=match.group(4),
                level=level_map.get(severity, 'INFO'),
                message=match.group(8),
                fields={
                    'facility': facility,
                    'severity': severity,
                    'hostname': match.group(4),
                    'app': match.group(5),
                    'pid': match.group(6)
                },
                raw=data
            )
        return None
    
    def _parse_apache(self, data: str, source: str) -> Optional[LogEntry]:
        """Parse Apache/Nginx common log format."""
        match = self.apache_pattern.match(data)
        if match:
            status_code = int(match.group(6))
            level = 'ERROR' if status_code >= 400 else 'INFO'
            
            return LogEntry(
                timestamp=time.time(),
                source=source,
                level=level,
                message=f"{match.group(3)} {match.group(4)}",
                fields={
                    'remote_ip': match.group(1),
                    'timestamp_str': match.group(2),
                    'method': match.group(3),
                    'path': match.group(4),
                    'protocol': match.group(5),
                    'status': status_code,
                    'size': int(match.group(7))
                },
                raw=data
            )
        return None
    
    def _parse_plain(self, data: str, source: str) -> LogEntry:
        """Parse plain text log."""
        # Extract key=value pairs
        fields = {}
        pattern = re.compile(r'(\w+)=([^\s]+)')
        for match in pattern.finditer(data):
            fields[match.group(1)] = match.group(2)
        
        # Detect log level
        level = 'INFO'
        data_lower = data.lower()
        for lvl in ['error', 'warning', 'critical', 'debug']:
            if lvl in data_lower:
                level = lvl.upper()
                break
        
        return LogEntry(
            timestamp=time.time(),
            source=source,
            level=level,
            message=data.strip(),
            fields=fields,
            raw=data
        )


class LogAggregator:
    """Aggregates logs using time windows."""
    
    def __init__(self):
        self.windows = {}
        self.lock = threading.Lock()
    
    def add_window(self, name: str, window_type: str, size: int):
        """Add an aggregation window."""
        with self.lock:
            self.windows[name] = {
                'type': window_type,
                'size': size,
                'data': defaultdict(list),
                'start_time': time.time()
            }
    
    def process(self, log: LogEntry) -> Dict[str, Any]:
        """Process log through aggregation windows."""
        results = {}
        
        with self.lock:
            for name, window in self.windows.items():
                if window['type'] == 'tumbling':
                    # Fixed interval windows
                    window_id = int(log.timestamp // window['size'])
                    window['data'][window_id].append(log)
                    results[name] = self._calculate_metrics(window['data'][window_id])
                
                elif window['type'] == 'sliding':
                    # Overlapping windows
                    current_time = log.timestamp
                    cutoff_time = current_time - window['size']
                    
                    # Remove old entries
                    for wid in list(window['data'].keys()):
                        window['data'][wid] = [
                            l for l in window['data'][wid]
                            if l.timestamp > cutoff_time
                        ]
                    
                    window['data'][0].append(log)
                    results[name] = self._calculate_metrics(window['data'][0])
        
        return results
    
    def _calculate_metrics(self, logs: List[LogEntry]) -> Dict[str, Any]:
        """Calculate metrics for a window."""
        if not logs:
            return {'count': 0}
        
        levels = defaultdict(int)
        for log in logs:
            levels[log.level] += 1
        
        return {
            'count': len(logs),
            'levels': dict(levels),
            'start_time': min(log.timestamp for log in logs),
            'end_time': max(log.timestamp for log in logs)
        }


class AlertManager:
    """Manages alerts based on rules."""
    
    def __init__(self):
        self.rules = []
        self.alerts = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    def add_rule(self, rule: Dict[str, Any]):
        """Add an alert rule."""
        with self.lock:
            self.rules.append(rule)
    
    def check(self, log: LogEntry, metrics: Dict[str, Any]) -> List[Dict]:
        """Check if log triggers any alerts."""
        triggered = []
        
        with self.lock:
            for rule in self.rules:
                if self._evaluate_rule(rule, log, metrics):
                    alert = {
                        'timestamp': time.time(),
                        'rule': rule['name'],
                        'type': rule['type'],
                        'log': log.to_dict(),
                        'metrics': metrics
                    }
                    self.alerts.append(alert)
                    triggered.append(alert)
        
        return triggered
    
    def _evaluate_rule(self, rule: Dict, log: LogEntry, metrics: Dict) -> bool:
        """Evaluate if a rule is triggered."""
        rule_type = rule.get('type')
        
        if rule_type == 'threshold':
            # Check threshold-based rules
            field = rule.get('field')
            operator = rule.get('operator', '>')
            value = rule.get('value')
            
            if field in metrics:
                metric_value = metrics[field]
                if operator == '>' and metric_value > value:
                    return True
                elif operator == '<' and metric_value < value:
                    return True
                elif operator == '==' and metric_value == value:
                    return True
        
        elif rule_type == 'pattern':
            # Check pattern matching
            pattern = rule.get('pattern')
            if pattern and re.search(pattern, log.message):
                return True
        
        elif rule_type == 'anomaly':
            # Simple anomaly detection (spike in error rate)
            if 'levels' in metrics:
                error_count = metrics['levels'].get('ERROR', 0)
                total_count = metrics.get('count', 1)
                error_rate = error_count / total_count if total_count > 0 else 0
                
                if error_rate > rule.get('threshold', 0.1):
                    return True
        
        return False


class LogStorage:
    """Stores logs with retention policies."""
    
    def __init__(self, db_path: str = 'logs.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    source TEXT,
                    level TEXT,
                    message TEXT,
                    fields TEXT,
                    raw TEXT,
                    created_at REAL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_level ON logs(level)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_source ON logs(source)
            ''')
            self.conn.commit()
    
    def store(self, log: LogEntry):
        """Store a log entry."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO logs (timestamp, source, level, message, fields, raw, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                log.timestamp,
                log.source,
                log.level,
                log.message,
                json.dumps(log.fields),
                log.raw,
                time.time()
            ))
            self.conn.commit()
    
    def query(self, 
              start_time: Optional[float] = None,
              end_time: Optional[float] = None,
              level: Optional[str] = None,
              source: Optional[str] = None,
              search: Optional[str] = None,
              limit: int = 100) -> List[Dict]:
        """Query stored logs."""
        with self.lock:
            query = "SELECT * FROM logs WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if level:
                query += " AND level = ?"
                params.append(level)
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            if search:
                query += " AND message LIKE ?"
                params.append(f"%{search}%")
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                result['fields'] = json.loads(result['fields'])
                results.append(result)
            
            return results
    
    def apply_retention(self, policy: Dict[str, Any]):
        """Apply retention policy."""
        with self.lock:
            cursor = self.conn.cursor()
            
            if policy.get('type') == 'time':
                # Time-based retention
                days = policy.get('days', 7)
                cutoff = time.time() - (days * 86400)
                cursor.execute("DELETE FROM logs WHERE created_at < ?", (cutoff,))
            
            elif policy.get('type') == 'size':
                # Size-based retention
                max_size = policy.get('max_size_mb', 1000) * 1024 * 1024
                
                # Get current database size
                cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
                current_size = cursor.fetchone()[0]
                
                if current_size > max_size:
                    # Delete oldest logs
                    cursor.execute("""
                        DELETE FROM logs WHERE id IN (
                            SELECT id FROM logs ORDER BY timestamp ASC LIMIT ?
                        )
                    """, (10000,))  # Delete 10k oldest logs
            
            self.conn.commit()
            
            # Compress old data
            if policy.get('compress', False):
                self._compress_old_data(policy.get('compress_after_days', 1))
    
    def _compress_old_data(self, days: int):
        """Compress old log data."""
        cutoff = time.time() - (days * 86400)
        cursor = self.conn.cursor()
        
        # Select old uncompressed logs
        cursor.execute("""
            SELECT id, raw FROM logs 
            WHERE created_at < ? AND raw NOT LIKE 'COMPRESSED:%'
            LIMIT 1000
        """, (cutoff,))
        
        for row in cursor.fetchall():
            log_id, raw = row
            compressed = gzip.compress(raw.encode())
            compressed_str = f"COMPRESSED:{compressed.hex()}"
            
            cursor.execute(
                "UPDATE logs SET raw = ? WHERE id = ?",
                (compressed_str, log_id)
            )
        
        self.conn.commit()


class LogPipeline:
    """Main log aggregation pipeline."""
    
    def __init__(self):
        self.parser = LogParser()
        self.aggregator = LogAggregator()
        self.alert_manager = AlertManager()
        self.storage = LogStorage()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Statistics
        self.stats = {
            'total_logs': 0,
            'logs_per_second': 0,
            'errors': 0,
            'alerts_triggered': 0
        }
        self.stats_lock = threading.Lock()
        
        # Setup default aggregation windows
        self.aggregator.add_window('1min', 'tumbling', 60)
        self.aggregator.add_window('5min', 'sliding', 300)
        
        # Setup default alert rules
        self.alert_manager.add_rule({
            'name': 'high_error_rate',
            'type': 'anomaly',
            'threshold': 0.1
        })
        self.alert_manager.add_rule({
            'name': 'critical_error',
            'type': 'pattern',
            'pattern': r'(critical|fatal|emergency)'
        })
    
    def process_log(self, data: str, source: str = 'unknown'):
        """Process a single log entry."""
        try:
            # Parse log
            log = self.parser.parse(data, source)
            if not log:
                return
            
            # Update stats
            with self.stats_lock:
                self.stats['total_logs'] += 1
            
            # Aggregate
            metrics = self.aggregator.process(log)
            
            # Check alerts
            alerts = self.alert_manager.check(log, metrics)
            if alerts:
                with self.stats_lock:
                    self.stats['alerts_triggered'] += len(alerts)
                logger.info(f"Alerts triggered: {len(alerts)}")
            
            # Store
            self.storage.store(log)
            
        except Exception as e:
            logger.error(f"Error processing log: {e}")
            with self.stats_lock:
                self.stats['errors'] += 1
    
    async def start_tcp_server(self, port: int = 5514):
        """Start TCP log receiver."""
        async def handle_client(reader, writer):
            addr = writer.get_extra_info('peername')
            logger.info(f"TCP client connected from {addr}")
            
            try:
                while True:
                    data = await reader.readline()
                    if not data:
                        break
                    
                    self.executor.submit(
                        self.process_log,
                        data.decode('utf-8').strip(),
                        f"tcp:{addr[0]}"
                    )
            except Exception as e:
                logger.error(f"TCP client error: {e}")
            finally:
                writer.close()
                await writer.wait_closed()
        
        server = await asyncio.start_server(handle_client, '0.0.0.0', port)
        logger.info(f"TCP server listening on port {port}")
        
        async with server:
            await server.serve_forever()
    
    def start_udp_server(self, port: int = 514):
        """Start UDP syslog receiver."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', port))
        logger.info(f"UDP server listening on port {port}")
        
        while True:
            try:
                data, addr = sock.recvfrom(65535)
                self.executor.submit(
                    self.process_log,
                    data.decode('utf-8').strip(),
                    f"udp:{addr[0]}"
                )
            except Exception as e:
                logger.error(f"UDP server error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        with self.stats_lock:
            return self.stats.copy()


def main():
    """Main entry point."""
    pipeline = LogPipeline()
    
    # Start UDP server in background thread
    udp_thread = threading.Thread(
        target=pipeline.start_udp_server,
        args=(514,),
        daemon=True
    )
    udp_thread.start()
    
    # Apply retention policy periodically
    def retention_worker():
        while True:
            time.sleep(3600)  # Every hour
            pipeline.storage.apply_retention({
                'type': 'time',
                'days': 7,
                'compress': True,
                'compress_after_days': 1
            })
    
    retention_thread = threading.Thread(target=retention_worker, daemon=True)
    retention_thread.start()
    
    # Start TCP server (blocking)
    try:
        asyncio.run(pipeline.start_tcp_server(5514))
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == '__main__':
    main()