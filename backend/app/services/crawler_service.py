
import logging
import asyncio
from typing import Optional, Dict, Any
from crawl4ai import AsyncWebCrawler

logger = logging.getLogger(__name__)

class CrawlerService:
    def __init__(self):
        # Allow passing custom headers, though Crawl4AI handles most
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    async def crawl_page(self, url: str) -> Dict[str, Any]:
        """
        Crawl a page using Crawl4AI.
        Returns a standardized dictionary.
        """
        logger.info(f"Crawling {url} using Crawl4AI...")
        
        try:
            # Crawl4AI handles browser lifecycle management internally via context manager
            # This is much more stable than managing our own Playwright instance
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(
                    url=url,
                    bypass_cache=True, # Always fetch fresh
                    word_count_threshold=10, # Ignore very short pages
                )

                if result.success:
                    # Successfully crawled
                    content = result.markdown
                    if not content or len(content) < 50:
                        # Fallback to text if markdown is empty
                        content = result.cleaned_html
                    
                    # Double check content length
                    if not content or len(content) < 50:
                        return {
                            "url": url,
                            "status": 200, # Technically success, but empty
                            "content": None,
                            "error": "Content too short or empty",
                            "method": "crawl4ai"
                        }

                    return {
                        "url": result.url,
                        "status": 200,
                        "content": content,
                        "html": result.html,
                        "media": result.media,
                        "links": result.links,
                        "method": "crawl4ai"
                    }
                else:
                    # Internal failure in Crawl4AI (e.g. Timeout, Network Error)
                    return {
                        "url": url,
                        "status": 0,
                        "content": None,
                        "error": result.error_message or "Unknown Crawl4AI error",
                        "method": "crawl4ai"
                    }

        except Exception as e:
            logger.error(f"Crawl4AI Critical Failure for {url}: {e}")
            return {
                "url": url,
                "status": 0,
                "content": None,
                "error": str(e),
                "method": "crawl4ai"
            }

    async def start(self):
        # Crawl4AI manages lifecycle per request or session, 
        # so explicit start/stop is less critical but kept for interface compatibility
        pass

    async def stop(self):
        pass

crawler_service = CrawlerService()
