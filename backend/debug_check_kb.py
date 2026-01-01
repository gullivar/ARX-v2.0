import chromadb
from chromadb.utils import embedding_functions

try:
    client = chromadb.PersistentClient(path="./data/chroma_db")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_collection(name="threat_intel_kb", embedding_function=ef)
    print(f"Total Count: {collection.count()}")
    
    print("\n--- Searching for www.naver.com ---")
    res = collection.query(query_texts=["www.naver.com"], n_results=3)
    print(res)

    print("\n--- Searching for sollcs01.com ---")
    res2 = collection.query(query_texts=["sollcs01.com"], n_results=5)
    for i in range(len(res2['ids'][0])):
        print(f"ID: {res2['ids'][0][i]}")
        print(f"Meta: {res2['metadatas'][0][i]}")
        print(f"Dist: {res2['distances'][0][i]}")

except Exception as e:
    print(e)
