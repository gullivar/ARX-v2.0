import chromadb
import os

NEW_DB_PATH = "/Users/joseph/Dev_project/07.ARX/v2.0_new/backend/data/chroma_db"
NEW_COLLECTION = "threat_intel_kb"

client = chromadb.PersistentClient(path=NEW_DB_PATH)
try:
    coll = client.get_collection(NEW_COLLECTION)
    print(f"Items in '{NEW_COLLECTION}': {coll.count()}")
except Exception as e:
    print(f"Error: {e}")
