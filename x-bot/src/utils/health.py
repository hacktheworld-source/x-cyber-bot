from datetime import datetime, timedelta
from typing import Dict
import psutil
import asyncio
from loguru import logger

class HealthMonitor:
    def __init__(self):
        self.last_cve_check = datetime.min
        self.last_post_attempt = datetime.min
        self.last_successful_post = datetime.min
        self.errors_last_hour = 0
        self.error_timestamps = []
        
    def record_cve_check(self):
        """Record a CVE check attempt."""
        self.last_cve_check = datetime.utcnow()
        
    def record_post_attempt(self, success: bool = True):
        """Record a post attempt."""
        self.last_post_attempt = datetime.utcnow()
        if success:
            self.last_successful_post = datetime.utcnow()
            
    def record_error(self):
        """Record an error occurrence."""
        now = datetime.utcnow()
        self.error_timestamps.append(now)
        
        # Clean up old error timestamps
        hour_ago = now - timedelta(hours=1)
        self.error_timestamps = [ts for ts in self.error_timestamps if ts > hour_ago]
        self.errors_last_hour = len(self.error_timestamps)
        
    async def get_health_status(self) -> Dict:
        """Get current health status of the bot."""
        now = datetime.utcnow()
        
        # Get system metrics
        process = psutil.Process()
        memory_info = process.memory_info()
        
        status = {
            "status": "healthy",
            "last_cve_check_minutes_ago": (now - self.last_cve_check).total_seconds() / 60,
            "last_post_attempt_minutes_ago": (now - self.last_post_attempt).total_seconds() / 60,
            "last_successful_post_minutes_ago": (now - self.last_successful_post).total_seconds() / 60,
            "errors_last_hour": self.errors_last_hour,
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
        
        # Determine health status
        if self.errors_last_hour > 10:
            status["status"] = "degraded"
            logger.warning("Health status degraded: Too many errors")
            
        if (now - self.last_successful_post).total_seconds() > 3600 * 8:
            status["status"] = "degraded"
            logger.warning("Health status degraded: No successful posts recently")
            
        if (now - self.last_cve_check).total_seconds() > 3600 * 2:
            status["status"] = "degraded"
            logger.warning("Health status degraded: No recent CVE checks")
            
        if status["memory_usage_mb"] > 1000:  # 1GB
            status["status"] = "degraded"
            logger.warning("Health status degraded: High memory usage")
            
        return status

    async def monitor_loop(self):
        """Background task to monitor health metrics."""
        while True:
            try:
                status = await self.get_health_status()
                if status["status"] != "healthy":
                    logger.warning(f"Health check failed: {status}")
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)  # Shorter sleep on error 