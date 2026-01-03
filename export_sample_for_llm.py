
import sqlite3
import json
import os

DB_PATH = "backend/w_intel.db"
OUTPUT_FILE = "pub_llm.json"
SAMPLE_SIZE = 100

def export_sample():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Join pipeline_items and crawl_results
    # Note: content is stored in a file path in 'html_content_path'
    query = """
        SELECT 
            p.fqdn,
            c.url,
            c.title,
            c.html_content_path
        FROM pipeline_items p
        JOIN crawl_results c ON p.id = c.item_id
        WHERE p.status = 'CRAWLED_SUCCESS'
        LIMIT ?
    """
    
    cur.execute(query, (SAMPLE_SIZE,))
    rows = cur.fetchall()
    
    export_data = []
    
    for row in rows:
        # Read content from file
        content_path = row['html_content_path']
        content = ""
        full_path = os.path.join("backend", content_path)
        
        if content_path and os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Truncate content if too long for sample (e.g. 5000 chars)
                    content = content[:5000]
            except Exception as e:
                content = f"[Error reading file: {e}]"
        else:
            content = "[Content file missing]"

        export_data.append({
            "fqdn": row['fqdn'],
            "url": row['url'],
            "title": row['title'] or "No Title",
            "content_snippet": content
        })
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully exported {len(export_data)} items to {OUTPUT_FILE}")
    conn.close()

if __name__ == "__main__":
    export_sample()
