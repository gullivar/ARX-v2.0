# W-Intel v2.0 Architecture Design

## 1. Core Philosophy
*   **Reliability First**: Systems will fail. The architecture must handle failures gracefully (Self-Healing).
*   **Total Observability**: Every step of the pipeline must be visible in real-time.
*   **Modular "Lego" Design**: Each component (Crawler, Analyzer, API) must be independent.
*   **Automated by Default**: No manual scripts for daily tasks.

## 2. System Architecture

### 2.1 Backend (Python + FastAPI)
Instead of a monolithic `main.py`, we split services:

1.  **Orchestrator (The "Brain")**
    *   Manages the Global State Machine.
    *   Schedules tasks (Crawl -> Process -> Analyze -> Index).
    *   *Tech*: APScheduler + State DB.
2.  **Collector Service**
    *   Fetches FQDNs from feeds (URLHaus, PhishStats, User Input).
    *   *Feature*: Whitelist/Blacklist filtering *before* DB entry.
3.  **Crawler Service (The "Worker")**
    *   Headless Browser (Playwright) or Requests.
    *   *Robustness*: Handles timeouts, retries (Exponential Backoff), and "Dead Letter" logic for unresponsive sites.
4.  **Intelligence Service (The "Analyst")**
    *   LLM Interface (Ollama/Gemini/GPT).
    *   *Optimization*: Batch processing to keep GPU busy but not overloaded.
5.  **Vector Store (The "Memory")**
    *   ChromaDB / Qdrant for RAG.
    *   *Verification*: "Golden Set" validation to check KB quality.

### 2.2 Frontend (React + Vite)
*   **Framework**: Upgrade to React 18 + Vite for speed.
*   **Design System**: TailwindCSS + Shadcn/UI (Clean, Modern, Reliable).
*   **Key Pages**:
    1.  **Pipeline Dashboard**: Real-time Gantt-style view of the pipeline (e.g., "50 domains crawling, 20 analyzing...").
    2.  **Bottleneck Inspector**: "Why are these 10 domains stuck?" (Click to see logs).
    3.  **Whitelist Manager**: CRUD interface for allowed domains.
    4.  **KB Quality Monitor**: View confidence scores of RAG retrievals.

### 2.3 Infrastructure (Docker)
*   **Watchdog**: A separate lightweight container observing the Healthcheck API.
*   **Docker Healthchecks**: Native `healthcheck` in `docker-compose.yml`.

## 3. Data Pipeline Flow (The "State Machine")

Every FQDN moves through strictly defined states:
1.  `DISCOVERED`: Found in feed.
2.  `QUEUED`: Scheduled for crawl.
3.  `CRAWLING`: Active browser session.
4.  `CRAWLED_SUCCESS` / `CRAWLED_FAIL`: Outcome.
5.  `ANALYZING`: LLM is reading.
6.  `INDEXED`: Added to KB.
7.  `ARCHIVED`: Done.

## 4. Addressing Pain Points

| Problem | v2.0 Solution |
| :--- | :--- |
| **"Dead Menus"** | API-driven UI. If API is down, UI shows "Offline" badge, not broken links. |
| **"Spaghetti Code"** | Strict `Service` pattern. `CrawlerService` knows nothing about `LLM`. |
| **"Invisible Bottlenecks"** | DB logs every state change with a timestamp. Dashboard highlights items stuck in state > X mins. |
| **"Manual Handling"** | `RetryPolicy` configurable in GUI. If fail 3x -> Alert User -> Move to "Manual Review". |
| **"Docker Crashes"** | `restart: always` + Application-level Exception Catching + Watchdog. |

## 5. Migration Plan
1.  **Extract Data**: Script to pull valid FQDNs + Manual classifications from v1.0 DB.
2.  **Verify Data**: Run a quick validation pass (ping domains).
3.  **Load to v2.0**: Seed the new clean database.

## 6. Directory Structure
```
v2.0_new/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, Logging, Database
│   │   ├── services/       # Crawler, LLM, Vector modules
│   │   ├── api/            # FastAPI Routes
│   │   └── models/         # Pydantic/SQLAlchemy Models
│   ├── worker/             # Background Task Workers
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── features/       # Pipeline, Dashboard, Settings
│   │   └── hooks/
│   └── vite.config.ts
├── infra/
│   └── docker-compose.yml
└── tools/
    └── migration_v1_to_v2.py
```
