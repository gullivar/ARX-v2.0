import asyncio
import logging
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.pipeline import PipelineItem, PipelineStatus

logger = logging.getLogger(__name__)

class HealthMonitor:
    """
    Monitors pipeline health and auto-recovers from stalls
    """
    def __init__(self):
        self.last_activity = {
            "crawl": datetime.now(),
            "analysis": datetime.now()
        }
        self.is_running = False
        
    async def start(self):
        """Start health monitoring loop"""
        self.is_running = True
        logger.info("Health Monitor started")
        
        while self.is_running:
            try:
                await self.check_health()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Health Monitor error: {e}")
                await asyncio.sleep(10)
    
    async def check_health(self):
        """Check for stuck items and zombie processes"""
        db = SessionLocal()
        try:
            now = datetime.now()
            
            # 1. Check for stuck CRAWLING items (>10 minutes)
            stuck_crawling = db.query(PipelineItem).filter(
                PipelineItem.status == PipelineStatus.CRAWLING,
                PipelineItem.updated_at < now - timedelta(minutes=10)
            ).count()
            
            if stuck_crawling > 0:
                logger.warning(f"Found {stuck_crawling} stuck CRAWLING items, resetting...")
                db.query(PipelineItem).filter(
                    PipelineItem.status == PipelineStatus.CRAWLING,
                    PipelineItem.updated_at < now - timedelta(minutes=10)
                ).update({
                    "status": PipelineStatus.DISCOVERED,
                    "retry_count": PipelineItem.retry_count + 1
                })
                db.commit()
            
            # 2. Check for stuck ANALYZING items (>10 minutes)
            stuck_analyzing = db.query(PipelineItem).filter(
                PipelineItem.status == PipelineStatus.ANALYZING,
                PipelineItem.updated_at < now - timedelta(minutes=10)
            ).count()
            
            if stuck_analyzing > 0:
                logger.warning(f"Found {stuck_analyzing} stuck ANALYZING items, resetting...")
                db.query(PipelineItem).filter(
                    PipelineItem.status == PipelineStatus.ANALYZING,
                    PipelineItem.updated_at < now - timedelta(minutes=10)
                ).update({
                    "status": PipelineStatus.CRAWLED_SUCCESS,
                    "retry_count": PipelineItem.retry_count + 1
                })
                db.commit()
            
            # 3. Check orchestrator activity
            from app.services.orchestrator import orchestrator
            status = orchestrator.get_status()
            
            # If no crawl activity in 5 minutes, log warning
            if status["last_crawl_run"]:
                crawl_idle = (now - status["last_crawl_run"]).total_seconds()
                if crawl_idle > 300:
                    logger.error(f"Crawler has been idle for {int(crawl_idle)}s - possible stall!")
            
            # If no analysis activity in 5 minutes, log warning
            if status["last_analysis_run"]:
                analysis_idle = (now - status["last_analysis_run"]).total_seconds()
                if analysis_idle > 300:
                    logger.error(f"Analyzer has been idle for {int(analysis_idle)}s - possible stall!")
                    
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        finally:
            db.close()
    
    async def stop(self):
        """Stop health monitoring"""
        self.is_running = False
        logger.info("Health Monitor stopped")

health_monitor = HealthMonitor()
