
import asyncio
import os
import sqlite3
import logging
from datetime import datetime
from crawl4ai import AsyncWebCrawler

# Configuration
DB_PATH = "/root/project/ARX-v2.0/backend/w_intel.db"
DATA_DIR = "/root/project/ARX-v2.0/backend/data/crawled_content"
LOG_FILE = "/root/project/ARX-v2.0/backend/crawl_priority.log"
BATCH_SIZE = 10  # Number of URLs to fetch in parallel

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PriorityCrawler")

os.makedirs(DATA_DIR, exist_ok=True)

async def crawl_and_save(crawler, fqdn):
    url = f"https://{fqdn}"
    logger.info(f"🕸️ Crawling: {url}")
    
    try:
        result = await crawler.arun(url=url)
        
        if result and result.success:
            # Save HTML
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{fqdn}_{timestamp}.html"
            filepath = os.path.join(DATA_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result.html)
            
            return {
                "success": True,
                "fqdn": fqdn,
                "url": url,
                "title": result.metadata.get("title", "No Title"),
                "filepath": filepath,
                "length": len(result.html)
            }
        else:
            logger.warning(f"❌ Failed to crawl {url}: {result.error_message if result else 'Unknown error'}")
            return {"success": False, "fqdn": fqdn, "error": str(result.error_message if result else 'Unknown')}
            
    except Exception as e:
        logger.error(f"🔥 Exception crawling {url}: {e}")
        return {"success": False, "fqdn": fqdn, "error": str(e)}

async def main():
    logger.info("🚀 Starting Standalone Priority Crawler...")
    
    # Initialize Crawler
    async with AsyncWebCrawler(verbose=False) as crawler:
        while True:
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                # 1. Fetch Candidates (Locking candidates to avoid race conditions with other crawlers is hard in pure SQL without transactions, 
                # but for now we assume single crawler instance. To be safe, we can use 'CRAWLING' state immediately.)
                
                # Fetch DISCOVERED items
                cur.execute("SELECT id, fqdn FROM pipeline_items WHERE status = 'DISCOVERED' LIMIT ?", (BATCH_SIZE,))
                rows = cur.fetchall()
                
                if not rows:
                    logger.info("😴 No items to crawl. Sleeping 10s...")
                    conn.close()
                    await asyncio.sleep(10)
                    continue
                
                # 2. Mark as CRAWLING
                item_ids = [row['id'] for row in rows]
                fqdns = [row['fqdn'] for row in rows]
                placeholders = ','.join(['?'] * len(item_ids))
                cur.execute(f"UPDATE pipeline_items SET status = 'CRAWLING', updated_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})", item_ids)
                conn.commit()
                conn.close() # Close DB while crawling to avoid locks
                
                logger.info(f"🔄 Processing batch of {len(fqdns)}: {fqdns}")
                
                # 3. Crawl in Parallel
                tasks = [crawl_and_save(crawler, fqdn) for fqdn in fqdns]
                results = await asyncio.gather(*tasks)
                
                # 4. Update Results to DB
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                
                for res in results:
                    fqdn = res['fqdn']
                    if res['success']:
                        # Insert into crawl_results
                        # We need item_id. Map fqdn back to id? Or cleaner to pass id in task.
                        # Let's verify item_id from DB again or simple map. 
                        # Simple map:
                        item_id = next(row['id'] for row in rows if row['fqdn'] == fqdn)
                        
                        cur.execute("""
                            INSERT INTO crawl_results (item_id, url, html_content_path, title, crawled_at)
                            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (item_id, res['url'], res['filepath'], res['title']))
                        
                        # Update status
                        cur.execute("UPDATE pipeline_items SET status = 'CRAWLED_SUCCESS', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
                        logger.info(f"✅ Success: {fqdn} ({res['length']} bytes)")
                    else:
                        item_id = next(row['id'] for row in rows if row['fqdn'] == fqdn)
                        cur.execute("UPDATE pipeline_items SET status = 'CRAWLED_FAIL', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
                        logger.info(f"🚫 Fail: {fqdn}")

                conn.commit()
                conn.close()
                
                # Rate limit / Courtesy sleep
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"☠️ Main Loop Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
