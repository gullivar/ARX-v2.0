
import json
import sqlite3
import os
import sys
import glob

# Add backend to path to import services if needed
sys.path.append("/root/project/ARX-v2.0/backend")
os.chdir("/root/project/ARX-v2.0/backend")

from app.services.vector_service import vector_service

DATA_DIR = "/root/project/ARX-v2.0/public_LLM"
DB_PATH = "w_intel.db"

def import_results():
    result_files = glob.glob(f"{DATA_DIR}/batch_*_result.json")
    print(f"Found {len(result_files)} result files to import.")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    for r_file in result_files:
        try:
            with open(r_file, 'r') as f:
                data = json.load(f)
            
            fqdns_to_update = []
            
            for item in data:
                fqdn = item.get('fqdn')
                category = item.get('category_main', 'Uncategorized')
                is_malicious = item.get('is_malicious', False) # Default assumption
                summary = item.get('summary', 'No summary')
                
                # Update Vector DB
                if fqdn:
                    print(f"Importing {fqdn}...")
                    vector_service.add_item(
                        fqdn=fqdn,
                        content_summary=summary,
                        category=category,
                        is_malicious=is_malicious
                    )
                    fqdns_to_update.append(fqdn)
            
            # Update SQL DB
            if fqdns_to_update:
                placeholders = ','.join(['?'] * len(fqdns_to_update))
                cur.execute(f"UPDATE pipeline_items SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE fqdn IN ({placeholders})", fqdns_to_update)
                conn.commit()
                
            # Rename processed file to avoid re-procesing
            # os.rename(r_file, r_file + ".imported")
            
        except Exception as e:
            print(f"Error importing {r_file}: {e}")
            
    conn.close()
    print("Import cycle complete.")

if __name__ == "__main__":
    import_results()
