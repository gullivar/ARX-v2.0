
import logging
import asyncio
from typing import Optional, Dict, Any
from crawl4ai import AsyncWebCrawler

logger = logging.getLogger(__name__)

class CrawlerService:
    def __init__(self):
        self.crawler = None
        self.is_running = False
        # Headers managed by Crawl4AI or Browser
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async def start(self):
        """
        Initialize the crawler instance and keep the browser open.
        This provides significant speedup over opening a browser for every request.
        """
        if self.is_running and self.crawler:
            return

        logger.info("🚀 Starting CrawlerService (Persistent Browser Session)...")
        try:
            # Initialize AsyncWebCrawler
            # verbose=True helps with debugging, headless=True is default
            self.crawler = AsyncWebCrawler(verbose=True)
            await self.crawler.start()
            self.is_running = True
            logger.info("✅ CrawlerService Started.")
        except Exception as e:
            logger.error(f"❌ Failed to start CrawlerService: {e}")
            self.is_running = False

    async def stop(self):
        """
        Close the browser session.
        """
        if self.crawler:
            logger.info("🛑 Stopping CrawlerService...")
            await self.crawler.close()
            self.crawler = None
            self.is_running = False
            logger.info("✅ CrawlerService Stopped.")

    async def crawl_page(self, url: str) -> Dict[str, Any]:
        """
        Crawl a page using the persistent Crawl4AI session.
        """
        if not self.is_running or not self.crawler:
            # Auto-restart if not running
            await self.start()

        logger.info(f"🕸️ Crawling {url}...")
        
        try:
            # arun reuses the existing browser session
            result = await self.crawler.arun(
                url=url,
                bypass_cache=True,
                word_count_threshold=10,
                # Magic mode can be enabled for better extraction if needed
                # magic=True, 
            )

            if result.success:
                content = result.markdown
                if not content or len(content) < 50:
                    content = result.cleaned_html
                
                if not content or len(content) < 50:
                    return {
                        "url": url,
                        "status": 200,
                        "content": None,
                        "error": "Content too short or empty",
                        "method": "crawl4ai_fast"
                    }

                return {
                    "url": result.url,
                    "status": 200,
                    "content": content,
                    "html": result.html,
                    "media": result.media,
                    "links": result.links,
                    "method": "crawl4ai_fast"
                }
            else:
                return {
                    "url": url,
                    "status": 0,
                    "content": None,
                    "error": result.error_message or "Unknown error",
                    "method": "crawl4ai_fast"
                }

        except Exception as e:
            logger.error(f"🔥 Crawl Critical Failure for {url}: {e}")
            # If critical error (e.g. browser crash), restart crawler
            await self.stop()
            return {
                "url": url,
                "status": 0,
                "content": None,
                "error": str(e),
                "method": "crawl4ai_fast"
            }

crawler_service = CrawlerService()
