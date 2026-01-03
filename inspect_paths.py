
import sqlite3
import os

DB_PATH = "/root/project/ARX-v2.0/backend/w_intel.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

query = """
    SELECT p.fqdn, c.html_content_path 
    FROM pipeline_items p
    JOIN crawl_results c ON p.id = c.item_id
    WHERE p.status = 'CRAWLED_SUCCESS'
    LIMIT 5
"""
cur.execute(query)
rows = cur.fetchall()

print(f"CWD: {os.getcwd()}")
if not rows:
    print("No CRAWLED_SUCCESS items found via JOIN.")

for row in rows:
    fqdn = row['fqdn']
    path = row['html_content_path']
    exists = os.path.exists(path) if path else False
    print(f"FQDN: {fqdn}")
    print(f"  Path in DB: {path}")
    print(f"  Exists?   : {exists}")
    if path and not exists:
        # Try prepending project root to see if it's relative
        abs_path = os.path.join("/root/project/ARX-v2.0/backend", path)
        print(f"  Abs Path Check ({abs_path}): {os.path.exists(abs_path)}")
        
conn.close()
