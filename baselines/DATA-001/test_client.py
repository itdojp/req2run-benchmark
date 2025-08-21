#!/usr/bin/env python3
"""
Test client for DATA-001 log aggregation pipeline.
Generates various types of logs and sends them to the aggregator.
"""

import os
import json
import time
import random
import socket
import requests
from datetime import datetime
import threading


class LogGenerator:
    """Generates test logs."""
    
    def __init__(self, host="localhost"):
        self.host = os.environ.get("LOG_AGGREGATOR_HOST", host)
        self.http_url = f"http://{self.host}:8000"
        self.tcp_port = 5514
        self.udp_port = 514
        
        self.sources = ["web-server", "app-server", "database", "cache", "queue"]
        self.users = ["alice", "bob", "charlie", "diana", "eve"]
        self.actions = ["login", "logout", "create", "update", "delete", "read"]
        self.endpoints = ["/api/users", "/api/products", "/api/orders", "/api/reports"]
    
    def generate_json_log(self):
        """Generate a JSON format log."""
        level = random.choices(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            weights=[10, 60, 20, 8, 2]
        )[0]
        
        log = {
            "timestamp": time.time(),
            "level": level,
            "source": random.choice(self.sources),
            "message": self._generate_message(level),
            "user": random.choice(self.users),
            "action": random.choice(self.actions),
            "duration_ms": random.randint(10, 5000),
            "status": "success" if level in ["DEBUG", "INFO"] else "failure"
        }
        
        if level == "ERROR":
            log["error_code"] = random.choice(["E001", "E002", "E003"])
            log["stack_trace"] = "Exception in module.function at line 123"
        
        return json.dumps(log)
    
    def generate_syslog(self):
        """Generate a syslog format message."""
        facility = 16  # Local0
        severity = random.randint(0, 7)
        priority = facility * 8 + severity
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        hostname = f"server-{random.randint(1, 10)}.example.com"
        app = random.choice(["nginx", "mysql", "redis", "app"])
        pid = random.randint(1000, 9999)
        
        message = self._generate_message_by_severity(severity)
        
        return f"<{priority}>1 {timestamp} {hostname} {app} {pid} - {message}"
    
    def generate_apache_log(self):
        """Generate Apache/Nginx access log format."""
        ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        timestamp = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        endpoint = random.choice(self.endpoints)
        protocol = "HTTP/1.1"
        status = random.choices([200, 201, 400, 404, 500], weights=[60, 10, 10, 15, 5])[0]
        size = random.randint(100, 100000)
        
        return f'{ip} - - [{timestamp}] "{method} {endpoint} {protocol}" {status} {size}'
    
    def _generate_message(self, level):
        """Generate a message based on level."""
        messages = {
            "DEBUG": [
                "Entering function process_request",
                "Cache hit for key: user_123",
                "SQL query executed in 23ms"
            ],
            "INFO": [
                "User login successful",
                "Order processed successfully",
                "Database connection established",
                "Cache warmed up"
            ],
            "WARNING": [
                "High memory usage detected: 85%",
                "Slow query detected: 5.2s",
                "Rate limit approaching for user",
                "Deprecated API endpoint called"
            ],
            "ERROR": [
                "Failed to connect to database",
                "Invalid authentication token",
                "Payment processing failed",
                "File not found: config.yml"
            ],
            "CRITICAL": [
                "System out of memory",
                "Database connection pool exhausted",
                "Disk space critical: 95% full",
                "Security breach detected"
            ]
        }
        return random.choice(messages.get(level, ["Unknown event"]))
    
    def _generate_message_by_severity(self, severity):
        """Generate message based on syslog severity."""
        if severity <= 2:  # Emergency, Alert, Critical
            return "Critical system failure detected"
        elif severity == 3:  # Error
            return "Error processing request"
        elif severity == 4:  # Warning
            return "Warning: Resource usage high"
        else:  # Notice, Info, Debug
            return "Normal operation"
    
    def send_http_log(self, log_data):
        """Send log via HTTP API."""
        try:
            if isinstance(log_data, str):
                # Parse JSON string
                log_obj = json.loads(log_data)
            else:
                log_obj = log_data
            
            response = requests.post(
                f"{self.http_url}/logs",
                json=log_obj,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"HTTP send error: {e}")
            return False
    
    def send_tcp_log(self, log_data):
        """Send log via TCP."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.tcp_port))
                sock.send(f"{log_data}\n".encode())
            return True
        except Exception as e:
            print(f"TCP send error: {e}")
            return False
    
    def send_udp_log(self, log_data):
        """Send log via UDP (syslog)."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(log_data.encode(), (self.host, self.udp_port))
            return True
        except Exception as e:
            print(f"UDP send error: {e}")
            return False
    
    def run_test(self, duration=60, rate=100):
        """Run test for specified duration and rate."""
        print(f"Starting log generation test...")
        print(f"Target: {self.host}")
        print(f"Duration: {duration}s")
        print(f"Rate: {rate} logs/second")
        
        start_time = time.time()
        sent_count = 0
        error_count = 0
        
        while time.time() - start_time < duration:
            # Generate different types of logs
            log_type = random.choice(["json", "syslog", "apache"])
            
            if log_type == "json":
                log_data = self.generate_json_log()
                protocol = random.choice(["http", "tcp"])
                
                if protocol == "http":
                    success = self.send_http_log(log_data)
                else:
                    success = self.send_tcp_log(log_data)
            
            elif log_type == "syslog":
                log_data = self.generate_syslog()
                success = self.send_udp_log(log_data)
            
            else:  # apache
                log_data = self.generate_apache_log()
                success = self.send_tcp_log(log_data)
            
            if success:
                sent_count += 1
            else:
                error_count += 1
            
            # Rate limiting
            time.sleep(1.0 / rate)
            
            # Print progress
            if sent_count % 100 == 0:
                elapsed = time.time() - start_time
                actual_rate = sent_count / elapsed if elapsed > 0 else 0
                print(f"Sent: {sent_count}, Errors: {error_count}, Rate: {actual_rate:.1f}/s")
        
        # Final stats
        elapsed = time.time() - start_time
        print(f"\nTest completed!")
        print(f"Total sent: {sent_count}")
        print(f"Total errors: {error_count}")
        print(f"Average rate: {sent_count/elapsed:.1f} logs/second")
        
        # Query stats from API
        try:
            response = requests.get(f"{self.http_url}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"\nPipeline stats:")
                print(f"  Total processed: {stats.get('total_logs', 0)}")
                print(f"  Processing rate: {stats.get('logs_per_second', 0):.1f}/s")
                print(f"  Alerts triggered: {stats.get('alerts_triggered', 0)}")
                print(f"  Errors: {stats.get('errors', 0)}")
        except Exception as e:
            print(f"Failed to get stats: {e}")
    
    def run_query_test(self):
        """Test query functionality."""
        print("\nTesting query functionality...")
        
        try:
            # Test basic query
            response = requests.get(
                f"{self.http_url}/logs/query",
                params={"limit": 10}
            )
            if response.status_code == 200:
                logs = response.json()
                print(f"Retrieved {len(logs)} recent logs")
            
            # Test filtered query
            response = requests.get(
                f"{self.http_url}/logs/query",
                params={"level": "ERROR", "limit": 10}
            )
            if response.status_code == 200:
                logs = response.json()
                print(f"Found {len(logs)} ERROR logs")
            
            # Test aggregation
            response = requests.post(
                f"{self.http_url}/logs/aggregate",
                json={
                    "group_by": "level",
                    "time_range": "5m",
                    "operation": "count"
                }
            )
            if response.status_code == 200:
                result = response.json()
                print(f"Aggregation results: {result.get('results', {})}")
            
            # Test alerts
            response = requests.get(f"{self.http_url}/alerts/recent")
            if response.status_code == 200:
                alerts = response.json()
                print(f"Recent alerts: {len(alerts)}")
        
        except Exception as e:
            print(f"Query test error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Log aggregation test client")
    parser.add_argument("--host", default="localhost", help="Aggregator host")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--rate", type=int, default=100, help="Logs per second")
    parser.add_argument("--test-queries", action="store_true", help="Test query functionality")
    
    args = parser.parse_args()
    
    generator = LogGenerator(args.host)
    
    # Wait for service to be ready
    print("Waiting for service to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"http://{args.host}:8000/health")
            if response.status_code == 200:
                print("Service is ready!")
                break
        except:
            pass
        time.sleep(1)
    
    # Run test
    generator.run_test(args.duration, args.rate)
    
    # Test queries if requested
    if args.test_queries:
        generator.run_query_test()


if __name__ == "__main__":
    main()