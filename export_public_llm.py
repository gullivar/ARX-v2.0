
import sqlite3
import json
import os
import sys

# Add backend to path to import services if needed, but for export we just need DB access
DB_PATH = "/root/project/ARX-v2.0/backend/w_intel.db"
# This is where the relative paths in DB are based from
BASE_CONTENT_DIR = "/root/project/ARX-v2.0/backend" 
OUT_DIR = "/root/project/ARX-v2.0/public_LLM"
BATCH_SIZE = 20

def export_data():
    print(f"Connecting to DB: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Select items that need analysis
        query = """
            SELECT p.fqdn, c.title, c.html_content_path
            FROM pipeline_items p
            JOIN crawl_results c ON p.id = c.item_id
            WHERE p.status = 'CRAWLED_SUCCESS'
        """
        cur.execute(query)
        rows = cur.fetchall()
        print(f"Found {len(rows)} items to export.")
        
        batch = []
        file_count = 0
        total_exported = 0
        
        for row in rows:
            fqdn = row['fqdn']
            rel_path = row['html_content_path']
            title = row['title'] or "No Title"
            
            content = ""
            full_path = ""
            if rel_path:
                # Construct absolute path
                if os.path.isabs(rel_path):
                    full_path = rel_path
                else:
                    full_path = os.path.join(BASE_CONTENT_DIR, rel_path)

                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', errors='ignore') as f:
                            # Limit content to 8000 chars
                            content = f.read()[:8000] 
                    except Exception as e:
                        content = f"Error reading content: {str(e)}"
                else:
                    content = f"File not found at: {full_path}"
            else:
                content = "No content path in DB."
            
            batch.append({
                "fqdn": fqdn,
                "title": title,
                "content": content
            })
            
            # When batch is full, write file
            if len(batch) >= BATCH_SIZE:
                file_count += 1
                filename = f"{OUT_DIR}/batch_{file_count:04d}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(batch, f, indent=2, ensure_ascii=False)
                # print(f"Saved {filename}")
                total_exported += len(batch)
                batch = []
        
        # Save remaining items
        if batch:
            file_count += 1
            filename = f"{OUT_DIR}/batch_{file_count:04d}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(batch, f, indent=2, ensure_ascii=False)
            total_exported += len(batch)
            
        print(f"✅ Export Complete!")
        print(f"Total Items: {total_exported}")
        print(f"Total Files: {file_count}")
        print(f"Output Directory: {OUT_DIR}")
        
    except Exception as e:
        print(f"❌ Export Failed: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    export_data()
