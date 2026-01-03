
import sqlite3
import os

DB_PATH = "/root/project/ARX-v2.0/backend/w_intel.db"

try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT status, COUNT(*) FROM pipeline_items GROUP BY status")
    rows = cur.fetchall()
    
    print("--- Database Status Counts ---")
    for status, count in rows:
        print(f"{status}: {count}")
        
    cur.execute("SELECT count(*) FROM pipeline_items WHERE status='CRAWLED_SUCCESS'")
    pending = cur.fetchone()[0]
    print(f"Pending Analysis (CRAWLED_SUCCESS): {pending}")
    
    conn.close()
except Exception as e:
    print(f"Error checking DB: {e}")
