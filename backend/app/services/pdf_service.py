import fitz  # PyMuPDF for text extraction
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  

VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")  
FAISS_INDEX_PATH = os.path.join(VECTOR_STORE_DIR, "faiss_index.bin") 
DOCUMENTS_PATH = os.path.join(VECTOR_STORE_DIR, "documents.pkl")

os.makedirs(VECTOR_STORE_DIR, exist_ok=True)


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


dimension = 384  

def load_faiss_index():
    """Loads the FAISS index from disk, or creates a new one if missing."""
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            print("Loading FAISS index from file...")
            return faiss.read_index(FAISS_INDEX_PATH)
        except Exception as e:
            print(f"Failed to load FAISS index, creating a new one: {e}")
    return faiss.IndexFlatL2(dimension)

index = load_faiss_index()

documents = []

def extract_text_from_pdf(pdf_path):
    """Extracts text from a given PDF and prints it."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    

    print("Extracted Text from PDF:\n", text)

    return text

def store_text_embedding(text):
    """Encodes and stores text embeddings in FAISS index along with original text."""
    global index, documents
    
    documents.append(text)

    with open(DOCUMENTS_PATH, "wb") as f:
        pickle.dump(documents, f)

    embedding = embedding_model.encode([text])
    index.add(np.array(embedding, dtype=np.float32))

    faiss.write_index(index, FAISS_INDEX_PATH)
    print("FAISS index and documents saved successfully.")

