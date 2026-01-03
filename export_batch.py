
import sqlite3
import json
import os
import sys

DB_PATH = "w_intel.db"
OUTPUT_FILE = "batch_to_analyze.json"
BATCH_SIZE = 30

def export_next_batch():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
        SELECT p.fqdn, c.title, c.html_content_path
        FROM pipeline_items p
        JOIN crawl_results c ON p.id = c.item_id
        WHERE p.status = 'CRAWLED_SUCCESS'
        LIMIT ?
    """
    cur.execute(query, (BATCH_SIZE,))
    rows = cur.fetchall()
    
    if not rows:
        print("NO_DATA")
        conn.close()
        return

    export_data = []
    fqdns = []
    for row in rows:
        fqdns.append(row['fqdn'])
        path = row['html_content_path']
        content = ""
        if path and os.path.exists(path):
            try:
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()[:5000] 
            except: 
                content = ""
                
        export_data.append({
            "fqdn": row['fqdn'],
            "title": row['title'],
            "content": content
        })
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
        
    # Mark as PROCESSING to avoid re-fetching immediately (optional, or just rely on 'CRAWLED_SUCCESS' filter)
    # But for this simulation, we leave them as CRAWLED_SUCCESS until import confirms completion.
    
    print(f"EXPORTED {len(export_data)}")
    conn.close()

if __name__ == "__main__":
    export_next_batch()
