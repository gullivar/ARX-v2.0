import chromadb
from chromadb.utils import embedding_functions
import os

# Disable Telemetry to prevent hanging
os.environ["ANONYMIZED_TELEMETRY"] = "False"

try:
    client = chromadb.PersistentClient(path="./data/chroma_db")
    # We don't even need the embedding function just to get the count
    collection = client.get_collection(name="threat_intel_kb") 
    print(f"Total Count: {collection.count()}")
except Exception as e:
    print(f"Error: {e}")
