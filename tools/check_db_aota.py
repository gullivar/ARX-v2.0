
import sys
import os
sys.path.append('/Users/joseph/Dev_project/07.ARX/v2.0_new/backend')
from app.core.database import SessionLocal
from app.models.pipeline import PipelineItem
from sqlalchemy import text

def check_db():
    db = SessionLocal()
    try:
        # Check specifically for aota.org or similar
        query = text("SELECT * FROM pipeline_items WHERE fqdn LIKE '%aota.org%'")
        results = db.execute(query)
        for row in results:
            print(f"ID: {row.id}, FQDN: {row.fqdn}, Status: {row.status}, Priority: {row.priority}, Updated At: {row.updated_at}")
            
            # Get logs
            log_query = text(f"SELECT * FROM pipeline_logs WHERE item_id = {row.id} ORDER BY timestamp DESC LIMIT 5")
            logs = db.execute(log_query)
            print("  [Logs]:")
            for log in logs:
                print(f"    - {log.timestamp} [{log.level}] {log.stage}: {log.message}")
            
            # Get crawl result
            crawl_query = text(f"SELECT * FROM crawl_results WHERE item_id = {row.id}")
            crawls = db.execute(crawl_query)
            print("  [Crawl Result]:")
            for crawl in crawls:
                print(f"    - Status: {crawl.http_status}, URL: {crawl.url}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
