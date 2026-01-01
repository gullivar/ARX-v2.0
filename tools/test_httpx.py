import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_crawl(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10.0, verify=False) as client:
        try:
            print(f"Testing {url}...")
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
                print(f"Content length: {len(text)}")
                print(f"Preview: {text[:200]}...")
            else:
                print(f"Failed Body length: {len(response.text)}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_crawl("https://www.naver.com"))
    asyncio.run(test_crawl("https://www.google.com"))
