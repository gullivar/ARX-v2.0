
import os
import time
import glob
import sqlite3

DATA_DIR = "/root/project/ARX-v2.0/public_LLM"
DB_PATH = "/root/project/ARX-v2.0/backend/w_intel.db"

def monitor():
    while True:
        os.system('clear')
        print(f"=== Agent Analysis Monitor ===")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. File Status
        total_batches = len(glob.glob(f"{DATA_DIR}/batch_*.json"))
        total_results = len(glob.glob(f"{DATA_DIR}/batch_*_result.json"))
        
        print(f"\n[Files]")
        print(f"Total Batches : {total_batches}")
        print(f"Processed     : {total_results}")
        print(f"Remaining     : {total_batches - total_results}")
        
        # 2. DB Status
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT status, count(*) FROM pipeline_items GROUP BY status")
            rows = cur.fetchall()
            conn.close()
            
            print(f"\n[Database Status]")
            for status, count in rows:
                print(f"{status:<15}: {count}")
                
        except Exception as e:
            print(f"DB Check Error: {e}")

        print(f"\n(Refreshes every 5s. Ctrl+C to minimize)")
        time.sleep(5)

if __name__ == "__main__":
    monitor()
