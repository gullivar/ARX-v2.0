
import sqlite3
import time
import os
import sys

# Define database path
DB_PATH = "/root/project/ARX-v2.0/backend/w_intel.db"

def watch_db():
    print(f"👀 Monitoring COMPLETED count in {DB_PATH}")
    print("Press Ctrl+C to stop.\n")
    
    last_count = -1
    
    try:
        while True:
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                
                # Get COMPLETED count
                cur.execute("SELECT COUNT(*) FROM pipeline_items WHERE status='COMPLETED'")
                completed = cur.fetchone()[0]
                
                # Get total count (for percentage)
                cur.execute("SELECT COUNT(*) FROM pipeline_items")
                total = cur.fetchone()[0]
                
                # Get other important statuses for context
                cur.execute("SELECT COUNT(*) FROM pipeline_items WHERE status='CRAWLED_SUCCESS'")
                pending_crawl = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM pipeline_items WHERE status='ANALYSIS_FAIL'")
                failed = cur.fetchone()[0]
                
                conn.close()
                
                # Print status line
                timestamp = time.strftime("%H:%M:%S")
                
                # Calculate diff
                diff_str = ""
                if last_count != -1:
                    diff = completed - last_count
                    if diff > 0:
                        diff_str = f"(+{diff} 🔼)"
                    elif diff == 0:
                        diff_str = "(-)"
                
                print(f"[{timestamp}] COMPLETED: {completed:<6} {diff_str:<10} | Pending Analysis: {pending_crawl:<6} | Failed: {failed}")
                
                last_count = completed
                
            except Exception as e:
                print(f"Error querying DB: {e}")
            
            # Update every 5 seconds
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nStopped monitoring.")

if __name__ == "__main__":
    watch_db()
