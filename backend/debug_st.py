from sentence_transformers import SentenceTransformer
print("Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")
emb = model.encode(["test"])
print(f"Embedding shape: {emb.shape}")
