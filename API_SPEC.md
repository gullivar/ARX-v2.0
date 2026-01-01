# W-Intel v2.0 API & Menu Specification

## 1. Frontend Menu Structure (Sidebar)

| Icon | Menu Name | Description |
| :--- | :--- | :--- |
| 📊 | **Dashboard** | Real-time "NOC" view. Pipeline health, active threads, CPM, bottleneck alerts. |
| 🏭 | **Pipeline** | The detailed work queue. Detailed list of items in `QUEUED`, `CRAWLING`, etc. Manual interventions. |
| 🧠 | **Intel Explorer** | The Knowledge Base. Advanced search, filtering by category, viewing Screenshots/HTML. |
| 🛡️ | **Policies** | White/Blacklist management. Regex support for excluding domains. |
| ⚙️ | **Settings** | System config. Crawler threads, LLM selection, Schedule intervals. |

---

## 2. API Specifications (FastAPI)

Base URL: `/api/v2`

### 2.1 Pipeline Control (`/pipeline`)
*   `GET /pipeline/stats`: Returns aggregated counts by status (e.g., {"QUEUED": 100, "CRAWLING": 5}).
*   `GET /pipeline/items`: List items with pagination, filtering by `status`, `logs`.
*   `GET /pipeline/items/{id}`: Detailed view including timeline logs.
*   `POST /pipeline/items/{id}/retry`: Manually trigger a retry for a specific item.
*   `POST /pipeline/control/{action}`: Global switch. `PAUSE`, `RESUME`, `FLUSH_QUEUE`.

### 2.2 Intelligence Data (`/intel`)
*   `GET /intel/search`: Vector search / Keyword search for completed items.
*   `GET /intel/domain/{fqdn}`: Full dossier on a domain (Whois + Crawl + LLM Analysis).
*   `GET /intel/categories`: Stats per category (e.g., "Phishing": 120, "Gambling": 45).

### 2.3 Policy Management (`/policy`)
*   `GET /policy/filters`: List all whitelists/blacklists.
*   `POST /policy/filters`: Add a new rule (e.g., `*google.com` -> WHITELIST).
*   `DELETE /policy/filters/{id}`: Remove a rule.

### 2.4 System Health (`/system`)
*   `GET /system/health`: Watchdog report. CPU/RAM, Docker Container status.
*   `GET /system/logs`: Stream of backend logs (Websocket optionally).

---

## 3. Data Flow Example

1.  **User** adds `example.com` via GUI -> `POST /pipeline/items`.
2.  **API** creates `PipelineItem(status='DISCOVERED')`.
3.  **Scheduler** (Background) sees new item -> Changes status to `QUEUED`.
4.  **Crawler Worker** picks up item -> Status `CRAWLING`.
    *   *If success*: Status `CRAWLED_SUCCESS`, saves `CrawlResult`.
    *   *If fail*: Status `CRAWLED_FAIL`, increments `retry_count`, logs error.
5.  **Analyzer Worker** picks up `CRAWLED_SUCCESS` -> Status `ANALYZING`.
    *   Calls LLM -> Saves `AnalysisResult`.
6.  **Indexer Worker** picks up -> Status `INDEXED`.

All state changes are pushed to `PipelineLog` and visible in **Pipeline** menu instantly.
