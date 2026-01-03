
import asyncio
import json
import sqlite3
import os
import sys

# Change to the backend directory context
sys.path.append("/root/project/ARX-v2.0/backend")
os.chdir("/root/project/ARX-v2.0/backend")

try:
    from app.services.llm_service import llm_service
    from app.services.vector_service import vector_service
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

BATCH_SIZE = 5
DB_PATH = "w_intel.db"

async def test_batch():
    print("--- Starting Single Batch Test ---")
    
    # 1. Check DB
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
    conn.close()
    
    if not rows:
        print("No items to process.")
        return

    print(f"Fetched {len(rows)} items.")
    
    batch_items = []
    for row in rows:
        fqdn = row['fqdn']
        print(f" - Preparing {fqdn}")
        path = row['html_content_path']
        content = ""
        if path and os.path.exists(path):
            with open(path, 'r', errors='ignore') as f:
                content = f.read()[:500]
        
        batch_items.append({
            'fqdn': fqdn,
            'title': row['title'] or "No Title",
            'content': content
        })

    # 2. Call LLM Service
    print("Calling analyze_batch_async...")
    try:
        results = await llm_service.analyze_batch_async(batch_items)
        print(f"LLM returned {len(results)} results.")
        print(f"Result Snippet: {results[:1]}")
    except Exception as e:
        print(f"LLM Call Failed: {e}")
        return

    # 3. Simulate Updates (Don't actually commit to avoid interference if needed, or commit to prove it works)
    # Let's commit to progress.
    if results:
        fqdns = [r['fqdn'] for r in results]
        print(f"Updating Status for: {fqdns}")
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        placeholders = ','.join(['?'] * len(fqdns))
        sql = f"UPDATE pipeline_items SET status = 'COMPLETED' WHERE fqdn IN ({placeholders})"
        cur.execute(sql, fqdns)
        conn.commit()
        print(f"Updated {cur.rowcount} rows.")
        conn.close()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_batch())
