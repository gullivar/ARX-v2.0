import logging

# --- Pydantic v2 Compatibility Patch for ChromaDB/LangChain ---
# Must be applied BEFORE any module imports chromadb
import pydantic
try:
    from pydantic_settings import BaseSettings
    if not hasattr(pydantic, 'BaseSettings'):
        pydantic.BaseSettings = BaseSettings
except ImportError:
    pass
# --------------------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="W-Intel v2.0 API", version="2.0.0")

# CORS Setup
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "version": "2.0.0", "message": "W-Intel v2.0 API is running"}

@app.get("/health")
def health_check():
    # TODO: Check DB Connection
    return {"status": "healthy"}

from app.api import pipeline, policies, intelligence
from app.services.orchestrator import orchestrator

@app.on_event("startup")
async def startup_event():
    from app.services.orchestrator import orchestrator
    from app.services.health_monitor import health_monitor
    import asyncio
    
    # Start orchestrator
    orchestrator.start()
    
    # Start health monitor
    asyncio.create_task(health_monitor.start())
    
    logging.info("Application started with Orchestrator and Health Monitor")

@app.on_event("shutdown")
async def shutdown_event():
    from app.services.health_monitor import health_monitor
    await health_monitor.stop()
    orchestrator.stop()
    await orchestrator.crawler.stop()

app.include_router(pipeline.router, prefix="/api/v2/pipeline", tags=["pipeline"])
app.include_router(policies.router, prefix="/api/v2/policies", tags=["policies"])
app.include_router(intelligence.router, prefix="/api/v2/intelligence", tags=["intelligence"])
from app.api import knowledge_base
app.include_router(knowledge_base.router, prefix="/api/v2/kb", tags=["kb"])
from app.api import categories
app.include_router(categories.router, prefix="/api/v2/categories", tags=["categories"])
from app.api import feeds
app.include_router(feeds.router, prefix="/api/v2/feeds", tags=["feeds"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
