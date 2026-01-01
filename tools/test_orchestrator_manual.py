import sys
import os
import asyncio
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

from app.services.orchestrator import orchestrator
from app.database import SessionLocal
from app.models.pipeline import PipelineItem, PipelineStatus

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ManualTest")

async def run_test():
    logger.info("Starting Manual Analysis Loop Test")
    
    # Check DB count
    db = SessionLocal()
    count = db.query(PipelineItem).filter(PipelineItem.status == PipelineStatus.CRAWLED_SUCCESS).count()
    print(f"Items ready for analysis: {count}")
    db.close()
    
    if count == 0:
        print("No items to analyze.")
        return

    # Run loop
    await orchestrator.analysis_loop()
    
    logger.info("Manual Test Complete")

if __name__ == "__main__":
    asyncio.run(run_test())
