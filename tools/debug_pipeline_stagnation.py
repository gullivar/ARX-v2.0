from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta

# DB Setup
DB_PATH = os.path.abspath("backend/w_intel.db")
DB_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DB_URL)

def check_pipeline_stats():
    with engine.connect() as conn:
        print(f"--- Pipeline Status Check ({datetime.now()}) ---")
        
        # 1. Count by Status
        result = conn.execute(text("SELECT status, count(*) FROM pipeline_items GROUP BY status"))
        rows = result.fetchall()
        print("\n[Item Counts by Status]")
        for status, count in rows:
            print(f"  {status}: {count}")
            
        # 2. Check 'ANALYZING' items (Stuck check)
        print("\n[Stuck Analysis Check]")
        stuck_query = text("""
            SELECT id, fqdn, updated_at 
            FROM pipeline_items 
            WHERE status IN ('ANALYZING', 'CRAWLING', 'PROCESSING')
            ORDER BY updated_at ASC
            LIMIT 10
        """)
        stuck_items = conn.execute(stuck_query).fetchall()
        if not stuck_items:
            print("  No items currently in active state (Stuck or otherwise).")
        else:
            for row in stuck_items:
                item_id, fqdn, updated = row
                print(f"  ID: {item_id} | FQDN: {fqdn} | Status: {row.status if hasattr(row, 'status') else 'Active'} | Updated: {updated}")
                
        # 3. Check Discovered but not queued
        # Why aren't we picking up more?
        # Maybe priority?
        print("\n[Discovered Sample]")
        disc_query = text("SELECT fqdn, priority, retry_count FROM pipeline_items WHERE status='DISCOVERED' LIMIT 5")
        disc_items = conn.execute(disc_query).fetchall()
        for row in disc_items:
            print(f"  {row}")

if __name__ == "__main__":
    check_pipeline_stats()
