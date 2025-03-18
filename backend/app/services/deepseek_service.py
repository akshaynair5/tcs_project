import subprocess
import re
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import os

# Define paths inside the /app directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the directory where this script is located
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")  # Now correctly inside backend/app/vector_store
FAISS_INDEX_PATH = os.path.join(VECTOR_STORE_DIR, "faiss_index.bin")  # FAISS index path
DOCUMENTS_PATH = os.path.join(VECTOR_STORE_DIR, "documents.pkl")  # File to store document texts
# Ensure vector_store directory exists
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Check if FAISS index file exists, otherwise create a new one
d = 384  # Dimension of embeddings (for all-MiniLM-L6-v2)
if not os.path.exists(FAISS_INDEX_PATH):
    print("FAISS index file not found. Creating a new one...")
    index = faiss.IndexFlatL2(d)  # Create an empty FAISS index
    faiss.write_index(index, FAISS_INDEX_PATH)  # Save new index to file
else:
    index = faiss.read_index(FAISS_INDEX_PATH)  # Load existing FAISS index

# Store document texts in a list (for retrieving original content)
documents = []  # Load this from wherever you're storing raw PDF text

def save_faiss_index():
    """Saves FAISS index and associated documents."""
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(DOCUMENTS_PATH, "wb") as f:
        pickle.dump(documents, f)
    print("✅ FAISS index and documents saved successfully.")

def load_faiss_index():
    """Loads FAISS index and associated documents."""
    global index, documents
    if os.path.exists(FAISS_INDEX_PATH):
        index = faiss.read_index(FAISS_INDEX_PATH)
        print(f"📂 Loaded FAISS index with {index.ntotal} vectors.")
    else:
        print("⚠️ FAISS index file not found. Creating a new one...")
        index = faiss.IndexFlatL2(d)

    if os.path.exists(DOCUMENTS_PATH):
        with open(DOCUMENTS_PATH, "rb") as f:
            documents = pickle.load(f)
        print(f"📂 Loaded {len(documents)} documents.")
        print("🔍 Sample Document:", documents[:2])  # Print first 2 docs for debugging
    else:
        print("⚠️ No documents file found. Initializing an empty list and saving it.")
        documents = []
        with open(DOCUMENTS_PATH, "wb") as f:
            pickle.dump(documents, f)


# Load FAISS index and documents at startup
load_faiss_index()

def add_documents_to_index(new_documents):
    """Encodes new documents and adds them to FAISS index."""
    global index, documents
    
    if not new_documents:
        print("No new documents to add.")
        return
    
    new_embeddings = np.array([embedding_model.encode(doc) for doc in new_documents], dtype=np.float32)
    
    # Ensure FAISS index is initialized
    if index.ntotal == 0:
        index = faiss.IndexFlatL2(d)
    
    index.add(new_embeddings)  # Add new embeddings to FAISS
    documents.extend(new_documents)  # Store raw text for retrieval
    faiss.write_index(index, FAISS_INDEX_PATH)  # Save index
    print(f"Added {len(new_documents)} new documents to FAISS index.")

def clean_response(response):
    """Removes HTML-like tags from the response."""
    return re.sub(r'<.*?>', '', response)

def search_context(question, top_k=2):
    """Finds the most relevant PDF text for the question."""
    question_embedding = np.array(embedding_model.encode([question]), dtype=np.float32)

    # Debugging information
    print("🔹 Question Vector Shape:", question_embedding.shape)
    print("🔹 Documents Available:", len(documents))
    print("🔹 FAISS Index Size (ntotal):", index.ntotal)

    if index.ntotal == 0:
        return "No relevant context found (empty index)."

    # Perform similarity search in FAISS
    distances, indices = index.search(question_embedding, top_k)
    
    print("🔹 Search Indices:", indices)
    print("🔹 Search Distances:", distances)
    
    if indices is None or indices.size == 0 or np.all(indices == -1):
        return "No relevant context found."

    # Retrieve top-matching texts
    relevant_texts = [documents[i] for i in indices[0] if 0 <= i < len(documents)]
    return "\n".join(relevant_texts) if relevant_texts else "No relevant context found."

def generate_response(question):
    """Generates a response using Ollama, with PDF content as context."""
    context = search_context(question)
    prompt = f"Based on the following context, provide a direct and concise answer.\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer concisely:"

    try:
        result = subprocess.run(
            ['ollama', 'run', 'deepseek-r1:1.5b', prompt],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'  # Fix UnicodeDecodeError
        )
        return clean_response(result.stdout)
    except subprocess.CalledProcessError as e:
        return f"Command failed with error: {e.stderr}"
    except FileNotFoundError:
        return "Error: 'ollama' command not found."
    except Exception as e:
        return f"Error: {str(e)}"
