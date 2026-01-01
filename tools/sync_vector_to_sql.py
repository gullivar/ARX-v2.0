import os
import sys
import logging

# --- Pydantic v2 Compatibility Patch for ChromaDB ---
import pydantic
try:
    from pydantic_settings import BaseSettings
    if not hasattr(pydantic, 'BaseSettings'):
        pydantic.BaseSettings = BaseSettings
except ImportError:
    pass
# ----------------------------------------------------

import chromadb
# from chromadb.utils import embedding_functions # Not needed for simple read
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Adjust paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.append(BACKEND_DIR)

# Correct import path
from app.models.pipeline import Base, PipelineItem, PipelineStatus, AnalysisResult, CrawlResult

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
VECTOR_DB_PATH = os.path.join(BACKEND_DIR, "data/chroma_db")
SQL_DB_URL = f"sqlite:///{os.path.join(BACKEND_DIR, 'w_intel.db')}"

def sync_vector_to_sql():
    # 1. Connect to Vector DB
    logger.info(f"Connecting to Vector DB at {VECTOR_DB_PATH}...")
    try:
        client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        # Optimization: Don't load embedding function, we only need metadata/text
        collection = client.get_collection(name="threat_intel_kb") 
        count = collection.count()
        logger.info(f"Found {count} items in Vector DB.")
    except Exception as e:
        logger.error(f"Failed to load Vector DB: {e}")
        return

    # 2. Connect to SQL DB
    logger.info(f"Connecting to SQL DB at {SQL_DB_URL}...")
    engine = create_engine(SQL_DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # 3. Iterate and Sync
    BATCH_SIZE = 100
    offset = 0
    synced_count = 0
    
    while offset < count:
        logger.info(f"Syncing batch {offset}...")
        batch = collection.get(
            limit=BATCH_SIZE,
            offset=offset,
            include=["metadatas", "documents"]
        )
        
        ids = batch['ids']
        metadatas = batch['metadatas']
        documents = batch['documents']
        
        if not ids:
            break
            
        for i, doc_id in enumerate(ids):
            fqdn = doc_id
            meta = metadatas[i] if metadatas else {}
            doc_text = documents[i] if documents else ""
            
            category = meta.get('category', 'Unknown')
            is_malicious_str = meta.get('is_malicious', 'False')
            is_malicious = str(is_malicious_str).lower() == 'true'
            summary = doc_text[:500] if doc_text else "No content"
            
            # A. Ensure PipelineItem
            item = session.query(PipelineItem).filter(PipelineItem.fqdn == fqdn).first()
            if not item:
                item = PipelineItem(
                    fqdn=fqdn,
                    status=PipelineStatus.COMPLETED,
                    priority=1,
                    source="legacy_migration"
                )
                session.add(item)
                session.flush() # Get ID
            else:
                if item.status != PipelineStatus.COMPLETED:
                    item.status = PipelineStatus.COMPLETED
                    session.add(item)
            
            # B. Ensure AnalysisResult
            # Check if analysis exists for this item
            analysis = session.query(AnalysisResult).filter(AnalysisResult.item_id == item.id).first()
            
            if not analysis:
                analysis = AnalysisResult(
                    item_id=item.id,
                    category_main=category,
                    is_malicious=is_malicious,
                    confidence_score=1.0, # Assumed trusted
                    summary=summary,
                    vector_id=fqdn,
                    analyzed_at=datetime.now()
                )
                session.add(analysis)
                synced_count += 1
            else:
                # Update if missing vector_id
                if not analysis.vector_id:
                    analysis.vector_id = fqdn
                    session.update(analysis) # .add() works for update in standard Session
                    session.add(analysis)
        
        try:
            session.commit()
            logger.info(f"Batch synced.")
        except Exception as e:
            logger.error(f"Failed to commit batch: {e}")
            session.rollback()
            
        offset += BATCH_SIZE
        
    logger.info(f"Sync Complete. Synced {synced_count} entries to SQL DB.")
    session.close()

if __name__ == "__main__":
    sync_vector_to_sql()
