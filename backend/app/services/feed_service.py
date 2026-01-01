import logging
import httpx
import csv
import io
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.feed import FeedSource, FeedType
from app.models.pipeline import PipelineItem, PipelineStatus, PipelineLog, PriorityLevel
from app.core.database import SessionLocal
import feedparser # Need to ensure this is installed, otherwise fallback or skip RSS for now

logger = logging.getLogger(__name__)

class FeedService:
    async def fetch_feed(self, feed_id: int):
        db = SessionLocal()
        try:
            feed = db.query(FeedSource).filter(FeedSource.id == feed_id).first()
            if not feed:
                logger.error(f"Feed {feed_id} not found")
                return

            logger.info(f"Fetching feed: {feed.name} ({feed.url})")
            
            # Update status
            feed.last_status = "fetching"
            db.commit()

            new_items_count = 0
            
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.get(feed.url)
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}")
                
                content = response.text
                extracted_urls = []

                # Parse based on type
                if feed.source_type == FeedType.CSV:
                    # Heuristic: assume column 0 or find 'url' header
                    f = io.StringIO(content)
                    reader = csv.reader(f)
                    for row in reader:
                        if not row: continue
                        if row[0].startswith("http"): # Simple heuristic
                            extracted_urls.append(row[0])
                        # Handle specific formats like URLHaus (id,dateadded,url,...)
                        elif len(row) > 1 and row[2].startswith("http"): 
                             extracted_urls.append(row[2])

                elif feed.source_type == FeedType.TEXT:
                    for line in content.splitlines():
                        line = line.strip()
                        if line.startswith("http"):
                            extracted_urls.append(line)

                elif feed.source_type == FeedType.RSS:
                    # Using feedparser synchronously if needed, or simple XML parsing
                    # allowing simple XML check
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(content)
                        # RSS 2.0 / Atom generic
                        for link in root.findall(".//item/link"):
                             extracted_urls.append(link.text)
                        for link in root.findall(".//entry/link"):
                             extracted_urls.append(link.attrib.get('href'))
                    except:
                        pass
                
                # Deduplicate and Insert
                for url in extracted_urls:
                    try:
                        # Extract domain/fqdn logic (simplified)
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        fqdn = parsed.netloc
                        if not fqdn: continue
                        
                        # Check exist
                        exists = db.query(PipelineItem).filter(PipelineItem.fqdn == fqdn).first()
                        if not exists:
                            item = PipelineItem(
                                fqdn=fqdn,
                                source=f"feed:{feed.name}",
                                status=PipelineStatus.DISCOVERED,
                                priority=PriorityLevel.HIGH # Feeds are usually fresh threats
                            )
                            db.add(item)
                            db.add(PipelineLog(item=item, stage="FEED", level="INFO", message=f"Discovered from {feed.name}"))
                            new_items_count += 1
                    except:
                        continue
                
                db.commit()
                
                # Update Feed Stats
                feed.last_fetched_at = datetime.now()
                feed.total_items_found += new_items_count
                feed.last_status = "success"
                feed.last_error = None
                db.commit()
                
                logger.info(f"Feed {feed.name} processing complete. Added {new_items_count} new items.")
                return new_items_count

        except Exception as e:
            logger.error(f"Feed {feed_id} failed: {e}")
            if feed:
                feed.last_status = "error"
                feed.last_error = str(e)
                feed.last_fetched_at = datetime.now()
                db.commit()
        finally:
            db.close()

    async def fetch_all_active(self):
        db = SessionLocal()
        feeds = db.query(FeedSource).filter(FeedSource.is_active == True).all()
        db.close()
        
        for feed in feeds:
            # Check interval
            if feed.last_fetched_at:
                diff = (datetime.now() - feed.last_fetched_at).total_seconds() / 60
                if diff < feed.fetch_interval_minutes:
                    continue
            
            await self.fetch_feed(feed.id)

feed_service = FeedService()
