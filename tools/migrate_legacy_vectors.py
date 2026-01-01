import sys
import os
import logging
import chromadb
from chromadb.utils import embedding_functions

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
# Note: Run this from project root or adjust paths relative to where you run it.
# We assume running from v2.0_new/backend usually, or adjusting absolute paths.
# Let's use absolute paths based on the User's workspace info to be safe.
LEGACY_DB_PATH = "/Users/joseph/Dev_project/07.ARX/v1.0_legacy/arx-w-intel/chroma_storage"
NEW_DB_PATH = "/Users/joseph/Dev_project/07.ARX/v2.0_new/backend/data/chroma_db"

LEGACY_COLLECTION = "domain_knowledge"
NEW_COLLECTION = "threat_intel_kb"

def migrate():
    # 1. Connect to Legacy DB
    if not os.path.exists(LEGACY_DB_PATH):
        logger.error(f"Legacy DB path not found: {LEGACY_DB_PATH}")
        return

    logger.info(f"Connecting to Legacy ChromaDB at {LEGACY_DB_PATH}...")
    try:
        legacy_client = chromadb.PersistentClient(path=LEGACY_DB_PATH)
        legacy_coll = legacy_client.get_collection(LEGACY_COLLECTION)
        count = legacy_coll.count()
        logger.info(f"Found {count} items in Legacy collection '{LEGACY_COLLECTION}'")
        
        if count == 0:
            logger.info("Nothing to migrate.")
            return

    except Exception as e:
        logger.error(f"Failed to load Legacy DB: {e}")
        return

    # 2. Connect to New DB
    # We need to ensure the directory exists
    os.makedirs(NEW_DB_PATH, exist_ok=True)

    logger.info(f"Connecting to New ChromaDB at {NEW_DB_PATH}...")
    try:
        new_client = chromadb.PersistentClient(path=NEW_DB_PATH)
        
        # IMPORTANT: Use the NEW embedding model logic
        # v2.0 uses 'all-MiniLM-L6-v2' via SentenceTransformer
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        new_coll = new_client.get_or_create_collection(
            name=NEW_COLLECTION,
            embedding_function=ef
        )
    except Exception as e:
        logger.error(f"Failed to load New DB: {e}")
        return

    # 3. Batch Process
    BATCH_SIZE = 100
    offset = 0
    
    total_migrated = 0

    while offset < count:
        logger.info(f"Processing batch {offset} to {min(offset + BATCH_SIZE, count)}...")
        
        # Fetch from Legacy
        # Note: legacy get() might return None for missing fields if not specified, 
        # but default get() gets everything (embeddings, metadatas, documents)
        # We DON'T need legacy 'embeddings' because we must re-embed.
        batch = legacy_coll.get(
            limit=BATCH_SIZE,
            offset=offset,
            include=["metadatas", "documents"]
        )
        
        ids = batch['ids']
        metadatas = batch['metadatas']
        documents = batch['documents']
        
        if not ids:
            break
            
        # Prepare for New DB
        new_ids = []
        new_docs = []
        new_metas = []
        
        for i, doc_id in enumerate(ids):
            meta = metadatas[i] if metadatas else {}
            doc_text = documents[i] if documents else ""
            
            fqdn = meta.get('fqdn', doc_id) # Fallback to ID if fqdn missing
            category = meta.get('category', 'Unknown')
            summary = meta.get('summary', '') or doc_text[:500] # Use doc snippet if summary missing
            
            # Map Metadata to v2 Schema
            # v2 Schema: fqdn, category, is_malicious, source
            
            # Guess is_malicious based on category
            safe_categories = ['Safe', 'Whitelisted', 'General']
            is_malicious = category not in safe_categories
            
            new_meta = {
                "fqdn": fqdn,
                "category": category,
                "is_malicious": str(is_malicious),
                "source": "legacy_migration"
            }
            
            # Construct Document Text for Embedding (Matching v2.0 logic)
            # v2 logic: f"{fqdn} - {category}: {content_summary}"
            # In legacy, 'doc_text' was usually "Domain: ... | Category: ... | ..." (enriched doc)
            # We can just reuse that enriched doc text as it contains the semantic info, 
            # Or reconstruct it. Reusing is safer for semantic preservation.
            final_doc_text = doc_text 
            
            new_ids.append(fqdn) # ID is FQDN
            new_docs.append(final_doc_text)
            new_metas.append(new_meta)
            
        # Insert into New DB
        # Chroma handles embedding generation automatically via the 'ef' we set on the collection
        try:
            new_coll.upsert(
                ids=new_ids,
                documents=new_docs,
                metadatas=new_metas
            )
            total_migrated += len(new_ids)
        except Exception as e:
            logger.error(f"Failed to upsert batch: {e}")
        
        offset += BATCH_SIZE
        
    logger.info(f"Migration Complete. Total items migrated: {total_migrated}")

if __name__ == "__main__":
    migrate()
