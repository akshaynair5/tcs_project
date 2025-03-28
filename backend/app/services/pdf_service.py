import fitz  # PyMuPDF for text extraction
from neo4j import GraphDatabase
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import pickle
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  

VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")  
FAISS_INDEX_PATH = os.path.join(VECTOR_STORE_DIR, "faiss_index.bin") 
DOCUMENTS_PATH = os.path.join(VECTOR_STORE_DIR, "documents.pkl")

os.makedirs(VECTOR_STORE_DIR, exist_ok=True)


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_USER = os.getenv("NEO4J_USERNAME")


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Sentence Transformer Model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
dimension = 384  # Embedding size

def extract_text_from_pdf(pdf_path):
    """Extracts text from a given PDF."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"

    print("Extracted Text from PDF:\n", text[:500], "...")  # Print preview of extracted text
    return text.strip()

def store_text_in_neo4j(text):
    """Encodes text and stores it in Neo4j along with its embedding."""
    embedding = embedding_model.encode([text])[0].tolist()  # Convert to list for storage
    
    with driver.session() as session:
        query = """
        MERGE (d:Document {text: $text, embedding: $embedding})
        RETURN d
        """
        session.run(query, text=text, embedding=embedding)

    print("✅ Document stored in Neo4j.")

def process_pdf_and_store(pdf_path):
    """Extracts text from a PDF and stores it in Neo4j."""
    text = extract_text_from_pdf(pdf_path)
    if text:
        store_text_in_neo4j(text)




# dimension = 384  

# def load_faiss_index():
#     """Loads the FAISS index from disk, or creates a new one if missing."""
#     if os.path.exists(FAISS_INDEX_PATH):
#         try:
#             print("Loading FAISS index from file...")
#             return faiss.read_index(FAISS_INDEX_PATH)
#         except Exception as e:
#             print(f"Failed to load FAISS index, creating a new one: {e}")
#     return faiss.IndexFlatL2(dimension)

# index = load_faiss_index()

# documents = []

# def extract_text_from_pdf(pdf_path):
#     """Extracts text from a given PDF and prints it."""
#     text = ""
#     with fitz.open(pdf_path) as doc:
#         for page in doc:
#             text += page.get_text("text") + "\n"
    

#     print("Extracted Text from PDF:\n", text)

#     return text

# def store_text_embedding(text):
#     """Encodes and stores text embeddings in FAISS index along with original text."""
#     global index, documents
    
#     documents.append(text)

#     with open(DOCUMENTS_PATH, "wb") as f:
#         pickle.dump(documents, f)

#     embedding = embedding_model.encode([text])
#     index.add(np.array(embedding, dtype=np.float32))

#     faiss.write_index(index, FAISS_INDEX_PATH)
#     print("FAISS index and documents saved successfully.")

