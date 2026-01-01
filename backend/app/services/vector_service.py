import logging
import uuid
import time
import random
from typing import List, Dict, Any

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
from chromadb.utils import embedding_functions


logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        # Persistent storage for ChromaDB
        self.db_path = "./data/chroma_db"
        try:
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=chromadb.config.Settings(anonymized_telemetry=False)
            )
            
            # Use SentenceTransformer explicitly to avoid ONNX/tokenizers issues on Python 3.14
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            
            self.collection = self.client.get_or_create_collection(
                name="threat_intel_kb",
                embedding_function=ef
            )
            logger.info(f"VectorService initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize VectorService: {e}")
            self.collection = None

    def add_item(self, fqdn: str, content_summary: str, category: str, is_malicious: bool):
        """
        Add or Update an item in the Vector Cache.
        Embedding is handled automatically by Chroma's default embedding function (all-MiniLM-L6-v2) usually,
        or we can allow it to download.
        """
        if not self.collection:
            logger.warning("Vector collection not available.")
            return

        try:
            # Metadata for filtering/context
            metadata = {
                "fqdn": fqdn,
                "category": category,
                "is_malicious": str(is_malicious), # Chroma needs string/int/float/bool primitives usually safe
                "source": "w-intel-v2"
            }
            
            # Use FQDN as ID to ensure uniqueness/updates
            self.collection.upsert(
                ids=[fqdn],
                documents=[f"{fqdn} - {category}: {content_summary}"], # The text to embed
                metadatas=[metadata]
            )
            logger.info(f"VectorService: Indexed {fqdn}")
        except Exception as e:
            logger.error(f"VectorService Index Error for {fqdn}: {e}")
    def get_item(self, fqdn: str) -> Dict[str, Any]:
        """
        Retrieve a specific item by FQDN (Exact Match).
        """
        if not self.collection:
            logger.warning("Collection is None during get_item")
            return None

        retries = 3
        for attempt in range(retries):
            try:
                # logger.info(f"VectorService: Executing collection.get for {fqdn} (Attempt {attempt+1})")
                results = self.collection.get(ids=[fqdn])
                # logger.info(f"VectorService: Got results for {fqdn}")
                
                if not results['ids']:
                    return None
                
                # Extract first match
                return {
                    "id": results['ids'][0],
                    "fqdn": results['metadatas'][0].get("fqdn"),
                    "category": results['metadatas'][0].get("category"),
                    "is_malicious": results['metadatas'][0].get("is_malicious"),
                    "snippet": results['documents'][0],
                    "distance": 0.0,
                    "score": 1.0 # Exact match
                }
            except Exception as e:
                if "locked" in str(e).lower() and attempt < retries - 1:
                    logger.warning(f"Vector DB locked, retrying... ({attempt+1}/{retries})")
                    time.sleep(random.uniform(0.1, 0.5))
                    continue
                logger.error(f"VectorService Get Error for {fqdn}: {e}")
                return None
        return None

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic Search.
        """
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            # Format results
            # results is a dict of lists
            parsed_results = []
            
            # Check safely
            if not results['ids']:
                return []

            ids = results['ids'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0] # Similarity distance
            documents = results['documents'][0]
            
            for i in range(len(ids)):
                parsed_results.append({
                    "id": ids[i],
                    "fqdn": metadatas[i].get("fqdn"),
                    "category": metadatas[i].get("category"),
                    "is_malicious": metadatas[i].get("is_malicious"),
                    "snippet": documents[i],
                    "distance": distances[i],
                    "score": 1 - distances[i] # Rough conversion if needed, lower distance = better
                })
                
            return parsed_results
            
        except Exception as e:
            logger.error(f"VectorService Search Error: {e}")
            return []

vector_service = VectorService()
