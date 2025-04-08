import subprocess
import re
import numpy as np
import faiss
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
from pinecone import Pinecone, ServerlessSpec
import time
from neo4j import GraphDatabase
import spacy
from keybert import KeyBERT
from sklearn.metrics.pairwise import cosine_similarity
from ragas import SingleTurnSample
from ragas.evaluation import evaluate
from ragas.metrics import answer_relevancy, faithfulness, context_precision
import uuid
import math

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

PINECONE_API_KEY = os.getenv("PINECONE_SECRET_KEY")
nlp = spacy.load("en_core_web_sm")
kw_model = KeyBERT()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_USER = os.getenv("NEO4J_USERNAME")

INDEX_NAME = "insurance-data"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

d = 384 
documents = []
evaluation_data = []
EVALUATION_CSV_PATH = "ragas_evaluation_log.csv"

def clean_ground_truth(gt):
    if gt is None:
        return None
    if isinstance(gt, float) and math.isnan(gt):
        return None
    if isinstance(gt, str):
        stripped = gt.strip().lower()
        if not stripped or stripped == "nan":
            return None
        return gt.strip()
    return gt

def extract_keywords(text, top_n=5):
    """Extracts insurance-related keywords using KeyBERT and spaCy NER/Noun detection."""
    doc = nlp(text)
    keywords = set()

    # Extract named entities (NER)
    for ent in doc.ents:
        keywords.add(ent.text.lower())  

    # Extract nouns (sometimes important words are not recognized as named entities)
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and token.is_alpha:
            keywords.add(token.text.lower())

    # Use KeyBERT to extract additional important keywords
    bert_keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1,2), stop_words='english')
    keywords.update([kw[0] for kw in bert_keywords[:top_n]])  # Add extracted terms

    return list(keywords)

def find_similar_keywords(keywords, threshold=0.7):
    """Finds similar keywords based on cosine similarity to avoid redundancy."""
    vectors = embedding_model.encode(keywords)  # Convert keywords to vectors
    sim_matrix = cosine_similarity(vectors)

    related_keywords = {}
    for i, keyword in enumerate(keywords):
        related_keywords[keyword] = [
            keywords[j] for j in range(len(keywords))
            if sim_matrix[i][j] > threshold and i != j  # Avoid self-matching
        ]
    
    return related_keywords

def add_insurance_type_if_new(insurance_type):
    """Check if an insurance type exists in Neo4j and add it if not."""
    with driver.session() as session:
        query = """
        MERGE (t:InsuranceType {name: $type})
        RETURN t
        """
        session.run(query, type=insurance_type)

def add_documents_to_graph(doc_text):
    """Insert a document as a node, store its embedding, and link insurance types."""
    try:
        if not isinstance(doc_text, str):
            raise ValueError("Input document must be a string.")

        # Generate embedding for the full document
        embedding = embedding_model.encode([doc_text])[0].tolist()

        with driver.session() as session:
            doc_id = str(uuid.uuid4())  # Generate unique document ID
            extracted_keywords = extract_keywords(doc_text)  # Extract keywords
            similar_keywords = find_similar_keywords(extracted_keywords)  # Find similar terms

            print(f"Extracted Keywords: {extracted_keywords}")
            print(f"Related Keywords: {similar_keywords}")

            for keyword in extracted_keywords:
                try:
                    add_insurance_type_if_new(keyword)  # Insert insurance type if new

                    # Store the document with text and embedding, and link to the insurance type
                    query = """
                    MERGE (d:Document {id: $id})
                    SET d.text = $text, d.embedding = $embedding
                    MERGE (t:InsuranceType {name: $type})
                    MERGE (d)-[:BELONGS_TO]->(t)
                    """
                    session.run(query, id=doc_id, text=doc_text, embedding=embedding, type=keyword)

                    # Create relationships between similar keywords
                    for related_keyword in similar_keywords.get(keyword, []):
                        query = """
                        MATCH (t1:InsuranceType {name: $keyword}), (t2:InsuranceType {name: $related_keyword})
                        MERGE (t1)-[:RELATED_TO]->(t2)
                        MERGE (t2)-[:RELATED_TO]->(t1)
                        """
                        session.run(query, keyword=keyword, related_keyword=related_keyword)

                except Exception as e:
                    print(f"Error linking keyword '{keyword}' to document {doc_id}: {e}")

        print("Document inserted and linked successfully.")

    except Exception as e:
        print(f"Error in processing document: {e}")


def search_context(question, top_k=3):
    """Find relevant insurance policies based on semantic similarity."""
    
    # Generate question embedding
    question_embedding = embedding_model.encode([question])[0].tolist()

    with driver.session() as session:
        query = """
        MATCH (d:Document)
        RETURN d.text, d.embedding
        """
        result = session.run(query)

        documents = []
        document_embeddings = []

        # Extract documents and embeddings from Neo4j
        for record in result:
            text = record["d.text"]
            embedding = record["d.embedding"]

            # Skip if embedding is missing, invalid, or contains NaN
            if (
                embedding is None
                or not isinstance(embedding, list)
                or any(np.isnan(embedding))
            ):
                continue

            documents.append(text)
            document_embeddings.append(embedding)

        if not documents:
            return "No documents found."

        # Compute cosine similarity
        similarities = cosine_similarity([question_embedding], document_embeddings)[0]

        # Get top-k most similar documents
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        top_contexts = [documents[i] for i in top_indices]

        return "\n".join(top_contexts) if top_contexts else "No relevant policy found."


def remove_think_tags(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def evaluate_and_store(sample_dict):
    df = pd.DataFrame([sample_dict])

    df.dropna(subset=['question', 'answer', 'contexts'], inplace=True)
    df = df[df['contexts'].apply(lambda x: isinstance(x, list) and all(isinstance(c, str) and c.strip() for c in x))]
    df = df[df['question'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    df = df[df['answer'].apply(lambda x: isinstance(x, str) and x.strip() != "")]
    
    if 'ground_truth' in df.columns:
        df['ground_truth'] = df['ground_truth'].apply(lambda x: x if isinstance(x, str) and x.strip() else None)

    if df.empty:
        print("Skipped evaluation: Invalid sample.")
        return

    sample = SingleTurnSample(
        user_input=df.iloc[0]['question'],
        retrieved_contexts=df.iloc[0]['contexts'],
        response=df.iloc[0]['answer'],
        reference=df.iloc[0].get('ground_truth')
    )

    results = evaluate([sample], metrics=[answer_relevancy, faithfulness, context_precision])
    results_df = results.to_pandas()

    if not os.path.exists(EVALUATION_CSV_PATH):
        results_df.to_csv(EVALUATION_CSV_PATH, index=False)
    else:
        results_df.to_csv(EVALUATION_CSV_PATH, mode='a', header=False, index=False)

    print(f"Evaluation result saved for question: '{sample.user_input}'")

def generate_response(question, ground_truth=None):
    context = search_context(question)
    print(f"Context found: {context}")
    prompt_with_context = f"Based on the following context, provide a direct and concise answer.\n\nContext: {context}\n\nQuestion: {question}\n\n"
    prompt_without_context = f"Provide a direct and concise answer.\n\nQuestion: {question}\n\n"

    response_with_context = remove_think_tags(run_ollama(prompt_with_context)) if context else "No relevant context found."
    response_without_context = remove_think_tags(run_ollama(prompt_without_context))

    # cleaned_ground_truth = clean_ground_truth(ground_truth)

    if (
        context and context.strip().lower() != "no relevant context found."
        and isinstance(question, str) and question.strip()
        and isinstance(response_with_context, str) and response_with_context.strip()
    ):
        sample = {
            "question": question.strip(),
            "answer": response_with_context.strip(),
            "contexts": [context.strip()],
            "ground_truth": clean_ground_truth(ground_truth)
        }
        # evaluate_and_store(sample)
    else:
        print(f"Skipped logging: Invalid or missing data for question: '{question}'")

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