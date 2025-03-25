from pinecone import Pinecone, ServerlessSpec
import os
import time
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from backend.app.services.insurance_data import insurance_documents  # Import data

load_dotenv()
# ⬇️ Replace with your Pinecone API details
PINECONE_API_KEY = os.getenv("PINECONE_SECRET_KEY")
print(f"🔑 Pinecone API key: {PINECONE_API_KEY}")
INDEX_NAME = "insurance-data"

# ✅ Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# ✅ Create index if it doesn’t exist
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,  # Matches SentenceTransformer output size
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    time.sleep(5)  # Wait for index to be ready

# ✅ Connect to index
pinecone_index = pc.Index(INDEX_NAME)

# ✅ Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ Convert texts to embeddings and upload to Pinecone
vectors = []
for doc in insurance_documents:
    vector = embedding_model.encode(doc["text"]).tolist()
    vectors.append((doc["id"], vector, {"text": doc["text"]}))

pinecone_index.upsert(vectors)
print(f"✅ Successfully added {len(vectors)} documents to Pinecone!")

# ✅ Perform a test query
query_text = "What does comprehensive insurance cover?"
query_vector = embedding_model.encode(query_text).tolist()

# Search in Pinecone
results = pinecone_index.query(vector=query_vector, top_k=3, include_metadata=True)

# ✅ Print results
print("\n🔍 Search Results:")
for match in results.matches:
    print(f"🔹 Score: {match.score:.4f}, Text: {match.metadata['text']}")
