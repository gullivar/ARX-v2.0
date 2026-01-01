
import asyncio
import os
from crawl4ai import AsyncWebCrawler

# List of domains that failed in the current pipeline
FAILED_DOMAINS = [
    "https://webgarden.com",
    "https://pornflip.com",
    "https://elar.ru",
    "https://mmtro.com",
    "https://tmhp.com",
    "https://clickhouse.cloud",
    "https://idc1.cn",
    "https://masterbetter.eu"
]

REPORT_FILE = "crawl_comparison_report.md"

async def test_crawl4ai():
    print(f"Starting Crawl4AI Test on {len(FAILED_DOMAINS)} domains...")
    
    results = []
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        for url in FAILED_DOMAINS:
            print(f"Crawling {url}...")
            try:
                # Basic crawl with minimal config, similar to what we'd use in prod
                result = await crawler.arun(url=url)
                
                status = "SUCCESS" if result.success else "FAIL"
                content_len = len(result.markdown) if result.markdown else 0
                error_msg = result.error_message if not result.success else ""
                
                results.append({
                    "url": url,
                    "status": status,
                    "length": content_len,
                    "title": result.metadata.get("title", "No Title"),
                    "error": error_msg
                })
                print(f"  -> {status} (Len: {content_len})")
                
            except Exception as e:
                print(f"  -> EXCEPTION: {e}")
                results.append({
                    "url": url,
                    "status": "EXCEPTION",
                    "length": 0,
                    "title": "Error",
                    "error": str(e)
                })

    # Generate Report
    with open(REPORT_FILE, "w") as f:
        f.write("# Crawl4AI Performance Verification Report\n\n")
        f.write(f"**Test Date:** {os.popen('date').read().strip()}\n")
        f.write("**Target:** Previously FAILED domains in current pipeline\n\n")
        
        f.write("| URL | Crawl4AI Status | Content Length | Title | Error |\n")
        f.write("|---|---|---|---|---|\n")
        
        for r in results:
            # Escape pipes in generic text
            title = r['title'].replace("|", "-") if r['title'] else ""
            error = r['error'].replace("|", "-") if r['error'] else ""
            f.write(f"| {r['url']} | **{r['status']}** | {r['length']} | {title} | {error} |\n")
            
        f.write("\n\n## Summary\n")
        success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
        f.write(f"- **Total Tested:** {len(FAILED_DOMAINS)}\n")
        f.write(f"- **Success:** {success_count}\n")
        f.write(f"- **Success Rate:** {success_count / len(FAILED_DOMAINS) * 100:.1f}%\n")

    print(f"\nReport generated at {REPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(test_crawl4ai())
