# W-Intel v2.0

## Status: Active Development
**Current Phase**: v2.0 Backend & Frontend Verification

## Quick Start

### 1. Backend (FastAPI)
```bash
cd backend
# Ensure venv is active
source ../../venv/bin/activate
# Run Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Health Check**: [http://localhost:8000/](http://localhost:8000/)

### 2. Frontend (React + Vite)
```bash
cd frontend
npm run dev
```
*   **Dashboard**: [http://localhost:5173](http://localhost:5173)

## Project Structure
*   `backend/`: FastAPI application, SQLAlchmey models, Services.
    *   `app/models/pipeline.py`: Main DB Schema.
    *   `app/api/pipeline.py`: Pipeline endpoints.
    *   `w_intel.db`: SQLite Database.
*   `frontend/`: React application.
*   `tools/`: Utility scripts (e.g., `migration_v1_to_v2.py`).

## Data
*   **Database**: Migrated 98k+ records from v1.0.
*   **Crawled Data**: Stored in `data/crawled/`.
