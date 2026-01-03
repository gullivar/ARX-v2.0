
import json
import sqlite3
import os
import sys
import glob
import time
import argparse
import re

# Add backend to path to import services if needed
sys.path.append("/root/project/ARX-v2.0/backend")
os.chdir("/root/project/ARX-v2.0/backend")

from app.services.vector_service import vector_service

DATA_DIR = "/root/project/ARX-v2.0/public_LLM"
DB_PATH = "w_intel.db"

def import_results(start_batch, end_batch):
    print(f"Starting Import for Batches {start_batch} to {end_batch}...")
    
    # Get all result files
    all_files = glob.glob(f"{DATA_DIR}/batch_*_result.json")
    target_files = []
    
    # Filter by range
    for f_path in all_files:
        match = re.search(r'batch_(\d+)_result.json', f_path)
        if match:
            batch_num = int(match.group(1))
            if start_batch <= batch_num <= end_batch:
                target_files.append(f_path)
    
    target_files.sort()
    
    if not target_files:
        print("No files found in this range.")
        return

    print(f"Found {len(target_files)} files to import.")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    processed_count = 0
    error_count = 0
    
    for r_file in target_files:
        try:
            with open(r_file, 'r') as f:
                data = json.load(f)
            
            fqdns_to_update = []
            
            for item in data:
                fqdn = item.get('fqdn')
                category = item.get('category_main', 'Uncategorized')
                is_malicious = item.get('is_malicious', False)
                summary = item.get('summary', 'No summary')
                
                # Update Vector DB
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
                        # Continue even if one fails
                        print(f"Vector Add Error ({fqdn}): {ve}")
                        error_count += 1
            
            # Update SQL DB - Bulk Update
            if fqdns_to_update:
                placeholders = ','.join(['?'] * len(fqdns_to_update))
                cur.execute(f"UPDATE pipeline_items SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE fqdn IN ({placeholders})", fqdns_to_update)
                conn.commit()
                processed_count += len(fqdns_to_update)
                
            # print(f"Imported {os.path.basename(r_file)} ({len(fqdns_to_update)} items)")
            
        except Exception as e:
            print(f"File Error {r_file}: {e}")
            
    conn.close()
    print(f"Total Imported in this chunk: {processed_count}")
    print(f"Total Errors: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    args = parser.parse_args()
    
    import_results(args.start, args.end)
