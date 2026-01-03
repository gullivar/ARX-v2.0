
print("DEBUG: process_batch_llm.py STARTED")
import sys
import os
print(f"DEBUG: CWD: {os.getcwd()}")
print(f"DEBUG: sys.path: {sys.path}")

try:
    import app.services.llm_service
    print(f"DEBUG: Imported llm_service from: {app.services.llm_service.__file__}")
except Exception as e:
    print(f"DEBUG: Import Error: {e}")

# Force reload to be safe
import importlib
importlib.reload(app.services.llm_service)
from app.services.llm_service import llm_service

import asyncio
import json
import sqlite3
import datetime
from app.services.vector_service import vector_service

# Optimized for Local Batching
BATCH_SIZE = 10 
DB_PATH = "w_intel.db"
RESULTS_DIR = "data/analysis_results"

os.makedirs(RESULTS_DIR, exist_ok=True)

async def process_batch():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    while True:
        try:
            # Re-check connectivity every batch to pick up changes/recover
            if not llm_service.get_base_url():
                print("❌ LLM Service Not Connected. Retrying in 5s...")
                await asyncio.sleep(5)
                continue

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
                print("🎉 No more items. Waiting 10s...")
                await asyncio.sleep(10)
                continue

            print(f"\n🔄 Processing Batch of {len(rows)} items via Local LLM...")
            
            batch_items = []
            fqdn_map = {}
            
            for row in rows:
                fqdn = row['fqdn']
                path = row['html_content_path']
                content = ""
                if path and os.path.exists(path):
                    try:
                        with open(path, 'r', errors='ignore') as f:
                            content = f.read()[:2000] # reduced for batch context limits
                    except: pass
                
                batch_items.append({
                    'fqdn': fqdn,
                    'title': row['title'] or "No Title",
                    'content': content
                })
                fqdn_map[fqdn] = row

            # Execute Batch
            results = await llm_service.analyze_batch_async(batch_items)
            
            # Save Results
            processed_fqdns = []
            valid_results = []
            
            for res in results:
                fqdn = res.get('fqdn')
                if fqdn and fqdn in fqdn_map:
                    processed_fqdns.append(fqdn)
                    valid_results.append(res)
                    
                    # Vector DB
                    vector_service.add_item(
                        fqdn=fqdn,
                        content_summary=res.get('summary', 'No summary'),
                        category=res.get('category_main', 'Uncategorized'),
                        is_malicious=res.get('is_malicious', False)
                    )

            # Log to file
            if valid_results:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(f"{RESULTS_DIR}/batch_{ts}.json", 'w') as f:
                    json.dump(valid_results, f, indent=2)

            # Update DB Status
            if processed_fqdns:
                placeholders = ','.join(['?'] * len(processed_fqdns))
                cur.execute(f"UPDATE pipeline_items SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE fqdn IN ({placeholders})", processed_fqdns)
                conn.commit()
                print(f"✅ Completed {len(processed_fqdns)} items.")
            else:
                print("⚠️ 0 items completed in this batch (LLM failure?).")
                await asyncio.sleep(2) 

        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(5)

    conn.close()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process_batch())
