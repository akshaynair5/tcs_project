import subprocess
import re
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
from pinecone import Pinecone, ServerlessSpec
import time

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")  
FAISS_INDEX_PATH = os.path.join(VECTOR_STORE_DIR, "faiss_index.bin")  # FAISS index path
DOCUMENTS_PATH = os.path.join(VECTOR_STORE_DIR, "documents.pkl") 

os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

PINECONE_API_KEY = os.getenv("PINECONE_SECRET_KEY")
print(f"🔑 Pinecone API key: {PINECONE_API_KEY}")
INDEX_NAME = "insurance-data"

# ✅ Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# ✅ Connect to index
pinecone_index = pc.Index(INDEX_NAME)


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


d = 384 
if not os.path.exists(FAISS_INDEX_PATH):
    print("FAISS index file not found. Creating a new one...")
    index = faiss.IndexFlatL2(d) 
    faiss.write_index(index, FAISS_INDEX_PATH)  
else:
    index = faiss.read_index(FAISS_INDEX_PATH)  

documents = []  

def save_faiss_index():
    """Saves FAISS index and associated documents."""
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(DOCUMENTS_PATH, "wb") as f:
        pickle.dump(documents, f)
    print("✅ FAISS index and documents saved successfully.")

def load_faiss_index():
    global index, documents
    
    if os.path.exists(FAISS_INDEX_PATH):
        index = faiss.read_index(FAISS_INDEX_PATH)
        print(f"Loaded FAISS index with {index.ntotal} vectors.")
    else:
        print("FAISS index file not found. Creating a new one...")
        index = faiss.IndexFlatL2(d)

    if os.path.exists(DOCUMENTS_PATH):
        with open(DOCUMENTS_PATH, "rb") as f:
            try:
                documents = pickle.load(f)
            except Exception as e:
                print("⚠️ Error loading documents.pkl:", str(e))
                documents = []
        print(f"Loaded {len(documents)} documents.")
        print("Sample Document:", documents[:2])  # Debugging
    else:
        print("⚠️ No documents file found. Initializing an empty list and saving it.")
        documents = []
        with open(DOCUMENTS_PATH, "wb") as f:
            pickle.dump(documents, f)


load_faiss_index()

def add_documents_to_index(new_documents):
    """Encodes new documents and adds them to FAISS index."""
    global index, documents
    
    if not new_documents:
        print("No new documents to add.")
        return
    
    new_embeddings = np.array([embedding_model.encode(doc) for doc in new_documents], dtype=np.float32)
 
    if index.ntotal == 0:
        index = faiss.IndexFlatL2(d)
    
    index.add(new_embeddings) 
    documents.extend(new_documents) 
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"Added {len(new_documents)} new documents to FAISS index.")

def search_context(question, top_k=2):
    """Finds the most relevant PDF text for the question."""
    question_embedding = np.array(embedding_model.encode([question]), dtype=np.float32)

    # Debugging
    print(" Question Vector Shape:", question_embedding.shape)
    print("Documents Available:", len(documents))
    print(" FAISS Index Size (ntotal):", index.ntotal)

    if index.ntotal == 0:
        return "No relevant context found (empty index)."

    # Perform similarity search in FAISS
    distances, indices = index.search(question_embedding, top_k)
    
    print("Search Indices:", indices)
    print("Search Distances:", distances)
    
    if indices is None or indices.size == 0 or np.all(indices == -1):
        return "No relevant context found."

    # Retrieve top-matching texts
    relevant_texts = [documents[i] for i in indices[0] if 0 <= i < len(documents)]
    return "\n".join(relevant_texts) if relevant_texts else "No relevant context found."

def remove_think_tags(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

# def generate_response(question):
#     """Generates a response using Ollama, with PDF content as context."""
#     context = search_context(question)
#     prompt = f"Based on the following context, provide a direct and concise answer.\n\nQuestion: {question}\n\n"

#     try:
#         result = subprocess.run(
#             ['ollama', 'run', 'deepseek-r1:1.5b', prompt],
#             capture_output=True,
#             text=True,
#             check=True,
#             encoding='utf-8' 
#         )
#         return {"response_with_context":remove_think_tags(result.stdout)}
#     except subprocess.CalledProcessError as e:
#         return f"Command failed with error: {e.stderr}"
#     except FileNotFoundError:
#         return "Error: 'ollama' command not found."
#     except Exception as e:
#         return f"Error: {str(e)}"

def generate_response(question):
    """Generates a response using Ollama with and without Pinecone context."""
    context = search_pinecone(question)
    prompt_with_context = f"Based on the following context, provide a direct and concise answer.\n\nContext: {context}\n\nQuestion: {question}\n\n"
    prompt_without_context = f"Provide a direct and concise answer.\n\nQuestion: {question}\n\n"
    
    # Get responses
    response_with_context = remove_think_tags(run_ollama(prompt_with_context)) if context else "No relevant context found."
    response_without_context = remove_think_tags(run_ollama(prompt_without_context))

    return {
        "response_with_context": response_with_context,
        "response_without_context": response_without_context
    }

def search_pinecone(question, top_k=5):
    """Search Pinecone for relevant context using embeddings."""
    question_embedding = embedding_model.encode(question).tolist()
    
    # Query Pinecone
    response = pinecone_index.query(vector=question_embedding, top_k=top_k, include_metadata=True)

    if response and "matches" in response:
        return " ".join(match["metadata"]["text"] for match in response["matches"] if "text" in match["metadata"])
    return ""

def run_ollama(prompt):
        """Helper function to run Ollama and fetch a response."""
        try:
            result = subprocess.run(
                ['ollama', 'run', 'deepseek-r1:1.5b', prompt],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Command failed with error: {e.stderr}"
        except FileNotFoundError:
            return "Error: 'ollama' command not found."
        except Exception as e:
            return f"Error: {str(e)}"