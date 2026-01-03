
import json
import sqlite3
import os
import sys
import argparse

# Add backend to path to import services if needed
sys.path.append("/root/project/ARX-v2.0/backend")
os.chdir("/root/project/ARX-v2.0/backend")

from app.services.vector_service import vector_service

DATA_DIR = "/root/project/ARX-v2.0/public_LLM"
DB_PATH = "w_intel.db"

def import_single_file(batch_num):
    filename = f"batch_{batch_num:04d}_result.json"
    file_path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Processing SINGLE batch: {filename}")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        fqdns_to_update = []
        
        for item in data:
            fqdn = item.get('fqdn')
            category = item.get('category_main', 'Uncategorized')
            is_malicious = item.get('is_malicious', False)
            summary = item.get('summary', 'No summary')
            
            if fqdn:
                try:
                    vector_service.add_item(
                        fqdn=fqdn,
                        content_summary=summary,
                        category=category,
                        is_malicious=is_malicious
                    )
                    fqdns_to_update.append(fqdn)
                except Exception as ve:
                    print(f"Warning: Vector Add Error ({fqdn}): {ve}")
        
        if fqdns_to_update:
            placeholders = ','.join(['?'] * len(fqdns_to_update))
            cur.execute(f"UPDATE pipeline_items SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE fqdn IN ({placeholders})", fqdns_to_update)
            conn.commit()
            print(f"Success: Updated {len(fqdns_to_update)} items.")
            
    except Exception as e:
        print(f"Critical Error importing {filename}: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, required=True)
    args = parser.parse_args()
    
    import_single_file(args.batch)
