
import asyncio
import logging
from playwright.async_api import async_playwright
import httpx
from bs4 import BeautifulSoup

# Define logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_crawler")

URL_TO_TEST = "https://www.aota.org"  # Try with www and without

async def _crawl_httpx(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    print(f"Testing HTTPX for {url}...")
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10.0, verify=False) as client:
        try:
            response = await client.get(url)
            print(f"HTTPX Status: {response.status_code}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
                print(f"HTTPX Content Length: {len(text)}")
                if len(text) < 100:
                    print("HTTPX Content too short.")
                    return None
                return {"success": True, "method": "httpx", "content_len": len(text)}
            return None
        except Exception as e:
            print(f"HTTPX Failed: {e}")
            return None

async def _crawl_playwright(url: str) -> dict:
    print(f"Testing Playwright for {url}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        # Replicate the blocking logic
        await context.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
            else route.continue_())

        page = await context.new_page()
        try:
            # Replicate timeout logic
            async with asyncio.timeout(20):
                response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                if response:
                    print(f"Playwright Status: {response.status}")
                    text_content = await page.evaluate("document.body.innerText")
                    print(f"Playwright Content Length: {len(text_content)}")
                    return {"success": True, "method": "playwright", "content_len": len(text_content)}
        except Exception as e:
            print(f"Playwright Failed: {e}")
        finally:
            await browser.close()

async def main():
    # Test 1: aota.org
    url = "https://aota.org"
    res = await _crawl_httpx(url)
    if not res:
        await _crawl_playwright(url)
    
    # Test 2: www.aota.org
    url2 = "https://www.aota.org"
    res2 = await _crawl_httpx(url2)
    if not res2:
        await _crawl_playwright(url2)

if __name__ == "__main__":
    asyncio.run(main())
