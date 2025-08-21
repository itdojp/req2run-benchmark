"""Audit logging for authorization decisions"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import structlog

from models import AuditLog, AuthorizationRequest, AuthorizationDecision

logger = structlog.get_logger()


class AuditManager:
    """Manages audit logging for authorization system"""
    
    def __init__(self):
        self.logs: List[AuditLog] = []
        self.max_logs = 10000  # Maximum logs to keep in memory
        
    async def log(self, audit_log: AuditLog):
        """Log an audit entry"""
        self.logs.append(audit_log)
        
        # Trim if too many logs
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Log to structured logger
        logger.info("Authorization audit",
                   user_id=audit_log.user_id,
                   request_action=audit_log.request.action,
                   request_resource=audit_log.request.resource,
                   decision_allowed=audit_log.decision.allowed,
                   evaluation_time_ms=audit_log.decision.evaluation_time_ms)
    
    async def get_logs(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with optional filters"""
        filtered_logs = self.logs
        
        # Filter by user
        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        
        # Filter by time range
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.created_at >= start_time]
        
        if end_time:
            filtered_logs = [log for log in filtered_logs if log.created_at <= end_time]
        
        # Sort by most recent first
        filtered_logs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit
        return filtered_logs[:limit]
    
    async def cleanup_old_logs(self, days: int = 30):
        """Remove logs older than specified days"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        old_count = len(self.logs)
        self.logs = [log for log in self.logs if log.created_at >= cutoff_time]
        removed_count = old_count - len(self.logs)
        
        if removed_count > 0:
            logger.info("Cleaned up old audit logs", removed=removed_count)
    
    async def export_logs(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """Export logs in specified format"""
        logs = await self.get_logs(start_time=start_time, end_time=end_time, limit=self.max_logs)
        
        if format == "json":
            return json.dumps([log.dict() for log in logs], default=str, indent=2)
        elif format == "csv":
            # Simple CSV export
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "timestamp", "user_id", "action", "resource",
                "allowed", "evaluation_time_ms", "policies"
            ])
            
            # Data
            for log in logs:
                writer.writerow([
                    log.created_at.isoformat(),
                    log.user_id,
                    log.request.action,
                    log.request.resource,
                    log.decision.allowed,
                    log.decision.evaluation_time_ms,
                    ",".join(log.decision.matched_policies)
                ])
            
            return output.getvalue()
        
        raise ValueError(f"Unsupported format: {format}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        if not self.logs:
            return {
                "total_requests": 0,
                "allowed": 0,
                "denied": 0,
                "avg_evaluation_time_ms": 0
            }
        
        allowed = sum(1 for log in self.logs if log.decision.allowed)
        denied = len(self.logs) - allowed
        avg_time = sum(log.decision.evaluation_time_ms for log in self.logs) / len(self.logs)
        
        return {
            "total_requests": len(self.logs),
            "allowed": allowed,
            "denied": denied,
            "allow_rate": (allowed / len(self.logs)) * 100,
            "avg_evaluation_time_ms": avg_time,
            "min_evaluation_time_ms": min(log.decision.evaluation_time_ms for log in self.logs),
            "max_evaluation_time_ms": max(log.decision.evaluation_time_ms for log in self.logs)
        }