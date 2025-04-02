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
from neo4j import GraphDatabase
import spacy
import uuid

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

PINECONE_API_KEY = os.getenv("PINECONE_SECRET_KEY")
nlp = spacy.load("en_core_web_sm")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_USER = os.getenv("NEO4J_USERNAME")

INDEX_NAME = "insurance-data"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

d = 384 
documents = []  


def extract_keywords(text):
    """Extract insurance-related keywords from text using spaCy NER & Noun detection."""
    doc = nlp(text)
    keywords = set()
    
    # Extract named entities (NER)
    for ent in doc.ents:
        keywords.add(ent.text.lower())  # Convert to lowercase for consistency

    # Extract relevant nouns (some important words might not be detected by NER)
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and token.is_alpha:
            keywords.add(token.text.lower())

    return list(keywords)

def add_insurance_type_if_new(insurance_type):
    """Check if an insurance type exists in Neo4j, add it if it doesn't."""
    with driver.session() as session:
        query = """
        MERGE (t:InsuranceType {name: $type})
        RETURN t.name
        """
        session.run(query, type=insurance_type)

def add_documents_to_graph(doc_text):
    """Insert a document as a node and dynamically extract & link insurance types."""
    try:
        if not isinstance(doc_text, str):
            raise ValueError("Input document must be a string.")

        with driver.session() as session:
            doc_id = str(uuid.uuid4())  # Generate a unique ID for the document
            
            # Extract dynamic keywords from the document text
            extracted_keywords = extract_keywords(doc_text)  
            print(f"Extracted Keywords: {extracted_keywords}")

            for keyword in extracted_keywords:
                try:
                    add_insurance_type_if_new(keyword)  # Insert only if new

                    query = """
                    MERGE (d:Document {id: $id, text: $text})
                    MERGE (t:InsuranceType {name: $type})
                    MERGE (d)-[:BELONGS_TO]->(t)
                    """
                    session.run(query, id=doc_id, text=doc_text, type=keyword)

                except Exception as e:
                    print(f"Error linking keyword '{keyword}' to document {doc_id}: {e}")

        print("Inserted document and linked extracted entities.")

    except Exception as e:
        print(f"Error in processing document: {e}")


def search_context(question, top_k=3):
    """Find relevant insurance policies based on the question."""
    with driver.session() as session:
        query = """
        MATCH (t:InsuranceType)<-[:BELONGS_TO]-(d:Document)
        WHERE toLower(t.name) CONTAINS toLower($question)
        RETURN d.text LIMIT $top_k
        """
        result = session.run(query, question=question, top_k=top_k) 

        contexts = [record["d.text"] for record in result]
        return "\n".join(contexts) if contexts else "No relevant policy found."



def remove_think_tags(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def generate_response(question):
    """Generates a response using Ollama with and without Pinecone context."""
    context = search_context(question)
    prompt_with_context = f"Based on the following context, provide a direct and concise answer.\n\nContext: {context}\n\nQuestion: {question}\n\n"
    prompt_without_context = f"Provide a direct and concise answer.\n\nQuestion: {question}\n\n"
    
    # Get responses
    response_with_context = remove_think_tags(run_ollama(prompt_with_context)) if context else "No relevant context found."
    response_without_context = remove_think_tags(run_ollama(prompt_without_context))

    return {
        "response_with_context": response_with_context,
        "response_without_context": response_without_context
    }


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

# def search_pinecone(question, top_k=5):
#     """Search Pinecone for relevant context using embeddings."""
#     question_embedding = embedding_model.encode(question).tolist()
    
#     # Query Pinecone
#     response = pinecone_index.query(vector=question_embedding, top_k=top_k, include_metadata=True)

#     if response and "matches" in response:
#         return " ".join(match["metadata"]["text"] for match in response["matches"] if "text" in match["metadata"])
#     return ""
# 
# def search_context(question, top_k=2):
#     """Finds the most relevant PDF text for the question."""
#     question_embedding = np.array(embedding_model.encode([question]), dtype=np.float32)

#     # Debugging
#     print(" Question Vector Shape:", question_embedding.shape)
#     print("Documents Available:", len(documents))
#     print(" FAISS Index Size (ntotal):", index.ntotal)

#     if index.ntotal == 0:
#         return "No relevant context found (empty index)."

#     # Perform similarity search in FAISS
#     distances, indices = index.search(question_embedding, top_k)
    
#     print("Search Indices:", indices)
#     print("Search Distances:", distances)
    
#     if indices is None or indices.size == 0 or np.all(indices == -1):
#         return "No relevant context found."

    # Retrieve top-matching texts
    # relevant_texts = [documents[i] for i in indices[0] if 0 <= i < len(documents)]
    # return "\n".join(relevant_texts) if relevant_texts else "No relevant context found."