import sqlite3
import os
from datetime import datetime

# Use correct path
DB_PATH = "../backend/w_intel.db"

def reset_failures():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Checking for ANALYSIS_FAIL items...")
    
    # Check count
    cursor.execute("SELECT COUNT(*) FROM pipeline_items WHERE status='ANALYSIS_FAIL'")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("No ANALYSIS_FAIL items found.")
        conn.close()
        return

    print(f"Found {count} failed items. Resetting to CRAWLED_SUCCESS...")
    
    # Reset
    cursor.execute("""
        UPDATE pipeline_items 
        SET status='CRAWLED_SUCCESS', 
            retry_count = retry_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE status='ANALYSIS_FAIL'
    """)
    
    conn.commit()
    print(f"Successfully reset {cursor.rowcount} items.")
    
    # Log it
    # We can't easy insert into pipeline_logs without item_id, keeping it simple.
    
    conn.close()

if __name__ == "__main__":
    reset_failures()
