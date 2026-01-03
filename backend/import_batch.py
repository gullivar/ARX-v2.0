
import sqlite3
import json
import os
import sys
from app.services.vector_service import vector_service

DB_PATH = "w_intel.db"
INPUT_FILE = "batch_analyzed.json"

def import_batch():
    if not os.path.exists(INPUT_FILE):
        print("ERROR: Input file not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    fqdns_updated = []
    
    for item in data:
        fqdn = item['fqdn']
        category = item.get('category_main', 'Uncategorized')
        is_malicious = item.get('is_malicious', False)
        summary = item.get('summary', '')
        
        # 1. Update Vector DB
        vector_service.add_item(fqdn, summary, category, is_malicious)
        
        # 2. Add to logs (optional, but good for record)
        # 3. Mark Pipeline Item as COMPLETED
        fqdns_updated.append(fqdn)

    if fqdns_updated:
        placeholders = ','.join(['?'] * len(fqdns_updated))
        # Update status to COMPLETED
        cur.execute(f"UPDATE pipeline_items SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE fqdn IN ({placeholders})", fqdns_updated)
        conn.commit()
        print(f"IMPORTED {len(fqdns_updated)} items.")
    else:
        print("IMPORTED 0 items.")
        
    conn.close()

if __name__ == "__main__":
    import_batch()
