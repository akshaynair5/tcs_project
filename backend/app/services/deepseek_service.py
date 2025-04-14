import subprocess
import re
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
from openai import OpenAI
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
from rapidfuzz import fuzz
from better_profanity import profanity

profanity.load_censor_words()


load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

PINECONE_API_KEY = os.getenv("PINECONE_SECRET_KEY")
nlp = spacy.load("en_core_web_sm")
kw_model = KeyBERT()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
api_key = os.getenv("LLM_API_KEY")
print(api_key)
# Initialize OpenAI client for OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

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


    for ent in doc.ents:
        keywords.add(ent.text.lower())  
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and token.is_alpha:
            keywords.add(token.text.lower())


    bert_keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1,2), stop_words='english')
    keywords.update([kw[0] for kw in bert_keywords[:top_n]])  # Add extracted terms

    return list(keywords)

def find_similar_keywords(keywords, threshold=0.7):
    """Finds similar keywords based on cosine similarity to avoid redundancy."""
    vectors = embedding_model.encode(keywords) 
    sim_matrix = cosine_similarity(vectors)

    related_keywords = {}
    for i, keyword in enumerate(keywords):
        related_keywords[keyword] = [
            keywords[j] for j in range(len(keywords))
            if sim_matrix[i][j] > threshold and i != j 
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

def split_paragraphs(doc_text):
    return [para.strip() for para in re.split(r'\n\s*\n', doc_text.strip()) if para]

def smart_chunk(text, max_words=150, overlap=30):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words - overlap):
        chunk_words = words[i:i + max_words]
        if chunk_words:
            chunks.append(" ".join(chunk_words))
    return chunks


# Main function to add document to graph
def add_documents_to_graph(doc_text_by_page):
    try:
        with driver.session() as session:
            for page_num, page_text in enumerate(doc_text_by_page, start=1):
                chunks = smart_chunk(page_text)

                for index, chunk in enumerate(chunks):
                    embedding = embedding_model.encode([chunk])[0].tolist()
                    doc_id = str(uuid.uuid4())
                    extracted_keywords = extract_keywords(chunk)
                    similar_keywords = find_similar_keywords(extracted_keywords)

                    for keyword in extracted_keywords:
                        add_insurance_type_if_new(keyword)

                        session.run("""
                            MERGE (d:Document {id: $id})
                            SET d.text = $text,
                                d.embedding = $embedding,
                                d.page = $page,
                                d.chunk_index = $chunk_index
                            MERGE (t:InsuranceType {name: $type})
                            MERGE (d)-[:BELONGS_TO]->(t)
                        """, {
                            "id": doc_id,
                            "text": chunk,
                            "embedding": embedding,
                            "page": page_num,
                            "chunk_index": index,
                            "type": keyword
                        })

                        for related_keyword in similar_keywords.get(keyword, []):
                            session.run("""
                                MATCH (t1:InsuranceType {name: $keyword}),
                                      (t2:InsuranceType {name: $related_keyword})
                                MERGE (t1)-[:RELATED_TO]->(t2)
                                MERGE (t2)-[:RELATED_TO]->(t1)
                            """, keyword=keyword, related_keyword=related_keyword)

        print("Document chunks inserted with metadata successfully.")

    except Exception as e:
        print(f"Error inserting document: {e}")

def fetch_structured_tables():
    tables = []
    with driver.session() as session:
        result = session.run("""
            MATCH (t:Table)<-[:IN_TABLE]-(r:Row)<-[:IN_ROW]-(c:Cell)
            RETURN t.title AS title, t.page AS page, r.index AS rowIndex, c.column AS column, c.value AS value
        """)
        
        raw = {}
        for record in result:
            title = record["title"]
            page = record.get("page", 0)
            row_index = record["rowIndex"]
            column = record["column"]
            value = record["value"]

            key = (title, page)
            raw.setdefault(key, {}).setdefault(row_index, {})[column] = value

        for (title, page), rows_dict in raw.items():
            sorted_rows = [rows_dict[i] for i in sorted(rows_dict)]
            if not sorted_rows:
                continue

            header_row = sorted_rows[0]
            headers = list(header_row.keys())
            data_rows = sorted_rows[1:]

            table_text = format_table_for_context(data_rows, headers)

            tables.append({
                "title": title,
                "page": page,
                "text": table_text,
                "headers": headers,
                "rows": data_rows
            })

    return tables

def format_table_for_context(rows, headers):
    formatted_rows = ["\t".join(headers)]
    for row in rows:
        formatted_rows.append("\t".join([str(row.get(h, "")) for h in headers]))
    return "\n".join(formatted_rows)


def format_structured_table(headers, rows):
    formatted_rows = ["\t".join(headers)]
    for row in rows:
        formatted_rows.append("\t".join([str(row.get(h, "")) for h in headers]))
    return "\n".join(formatted_rows)

def search_context(question, max_tokens=700, similarity_threshold=0.5):
    try:
        question_embedding = embedding_model.encode([question])[0].tolist()

        # Text chunk retrieval
        with driver.session() as session:
            result = session.run("""
                MATCH (d:Document)
                RETURN d.text AS text, d.embedding AS embedding, d.page AS page, d.chunk_index AS chunk_index
            """)
            chunks, embeddings = [], []
            for record in result:
                embedding = record["embedding"]
                if embedding and isinstance(embedding, list) and not any(np.isnan(embedding)):
                    chunks.append({
                        "text": record["text"],
                        "embedding": embedding,
                        "page": record.get("page", 0),
                        "chunk_index": record.get("chunk_index", 0)
                    })
                    embeddings.append(embedding)

        # Structured table embedding
        tables = fetch_structured_tables()

        print("Tables: ", tables)
        table_embeddings = [embedding_model.encode([table["text"]])[0].tolist() for table in tables]

        # Score text chunks
        text_scores = []
        if embeddings:
            similarities = cosine_similarity([question_embedding], embeddings)[0]
            for i, chunk in enumerate(chunks):
                if similarities[i] >= similarity_threshold:
                    fuzzy_score = fuzz.partial_ratio(question.lower(), chunk["text"].lower()) / 100
                    final_score = 0.8 * similarities[i] + 0.2 * fuzzy_score
                    text_scores.append((chunk["text"], final_score))

        # Score tables
        table_scores = []
        if table_embeddings:
            similarities = cosine_similarity([question_embedding], table_embeddings)[0]
            for i, table in enumerate(tables):
                if similarities[i] >= similarity_threshold:
                    fuzzy_score = fuzz.partial_ratio(question.lower(), table["text"].lower()) / 100
                    header_score = fuzz.partial_ratio(question.lower(), " ".join(table["headers"]).lower()) / 100
                    final_score = 0.7 * similarities[i] + 0.2 * fuzzy_score + 0.1 * header_score
                    table_scores.append((
                        {
                            "type": "table",
                            "title": table["title"],
                            "page": table["page"],
                            "headers": table["headers"],
                            "rows": table["rows"]
                        },
                        final_score
                    ))

        all_scores = text_scores + table_scores
        all_scores.sort(key=lambda x: x[1], reverse=True)

        # Build token-bounded context
        context = []
        current_tokens = 0
        for item, _ in all_scores:
            if isinstance(item, str):
                word_count = len(item.split())
                if current_tokens + word_count > max_tokens:
                    break
                context.append(item)
                current_tokens += word_count
            elif isinstance(item, dict) and item.get("type") == "table":
                table_str = format_structured_table(item["headers"], item["rows"])
                block = f"[Table: {item['title']} (Page {item['page']})]\n{table_str}"
                word_count = len(block.split())
                if current_tokens + word_count > max_tokens:
                    break
                context.append(block)
                current_tokens += word_count

        return "\n\n".join(context) if context else "No relevant information found."

    except Exception as e:
        return f"Error in search: {e}"


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

def is_profane(text: str) -> bool:
    return profanity.contains_profanity(text)

def is_sensitive_or_harmful(text: str) -> bool:
    # Add minimal regex for malicious/unsafe patterns (expand as needed)
    harmful_patterns = [
        r"\b(hack|exploit|bypass|ddos|phish)\b",
        r"\b(kill|suicide|murder|bomb|terrorist)\b",
        r"\bpassword|ssn|social security number|credit card\b",
        r"\bhow to\b.*\bcheat\b",
        r"\bself[-\s]?harm\b",
    ]
    return any(re.search(pat, text, re.IGNORECASE) for pat in harmful_patterns)

def is_out_of_scope(context: str) -> bool:
    if not context or "no relevant context found" in context.lower():
        return True
    # Add a few signals like no keywords or very general context
    if len(context.split()) < 10:
        return True
    return False

def generate_response(question: str, ground_truth=None):
    if not question or not isinstance(question, str) or len(question.strip()) < 3:
        return {
            "response_short": "Invalid input.",
            "response_detailed": "Your question seems too short or unclear. Please rephrase it with more details."
        }

    # Step 1: Filter malicious/unsafe content
    if is_profane(question) or is_sensitive_or_harmful(question):
        return {
            "response_short": "Sorry, that question cannot be answered.",
            "response_detailed": "This assistant cannot respond to questions containing inappropriate or harmful content. Please try again with a different question."
        }

    # Step 2: Get context
    context = search_context(question)
    print("Context found:", context)

    # Step 3: If context is missing or not related to insurance
    if is_out_of_scope(context):
        suggestion_prompt = f"The user asked: '{question}'. Suggest a rephrased version of this question that would be relevant to insurance topics like policies, claims, coverage, premium, etc."
        suggestion = remove_think_tags(run_ollama(suggestion_prompt))
        return {
            "response_short": "I can only assist with insurance-related questions.",
            "response_detailed": f"This query appears unrelated to insurance. Try rephrasing your question like this:\n\n**{suggestion.strip()}**"
        }

    # Step 4: Prompt creation
    prompt_short = f"Answer concisely:\n\nContext: {context}\n\nQuestion: {question}"
    prompt_detailed = f"Answer in detail:\n\nContext: {context}\n\nQuestion: {question}"

    # Step 5: LLM responses
    response_short_raw = run_ollama(prompt_short)
    response_detailed_raw = run_ollama(prompt_detailed)
    print(response_detailed_raw)
    # If the LLM returns an error or timeout message
    if response_short_raw.startswith("Error") or response_detailed_raw.startswith("Error"):
        return {
            "response_short": "Sorry, I'm having trouble generating a response right now.",
            "response_detailed": f"There was an error while processing your question. Please try again shortly.\n\n{response_detailed_raw}"
        }

    response_short = remove_think_tags(response_short_raw)
    response_detailed = remove_think_tags(response_detailed_raw)

    # Step 6: Post-check LLM output for safety
    if is_profane(response_short + response_detailed) or is_sensitive_or_harmful(response_detailed):
        return {
            "response_short": "Content blocked.",
            "response_detailed": "The assistant generated a response that contains sensitive content and has been filtered. Please try a different question."
        }

    # Step 7: Optional logging
    if context and response_detailed.strip():
        sample = {
            "question": question.strip(),
            "answer": response_detailed.strip(),
            "contexts": [context.strip()],
            "ground_truth": clean_ground_truth(ground_truth)
        }
        # evaluate_and_store(sample)

    return {
        "response_short": response_short,
        "response_detailed": response_detailed
    }


def run_ollama(prompt):
    """Uses OpenRouter to get a response from a hosted LLM model."""
    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        print("Raw completion object:", completion)  # Debug line

        # Defensive check
        message = completion.choices[0].message
        if not message or not hasattr(message, "content") or not message.content:
            return "Error: No content generated by the model."

        return message.content.strip()

    except Exception as e:
        return f"Error during OpenRouter call: {str(e)}"


# def run_ollama(prompt):
#         """Helper function to run Ollama and fetch a response."""
#         try:
#             result = subprocess.run(
#                 ['ollama', 'run', 'deepseek-r1:1.5b', prompt],
#                 capture_output=True,
#                 text=True,
#                 check=True,
#                 encoding='utf-8'
#             )
#             return result.stdout.strip()
#         except subprocess.CalledProcessError as e:
#             return f"Command failed with error: {e.stderr}"
#         except FileNotFoundError:
#             return "Error: 'ollama' command not found."
#         except Exception as e:
#             return f"Error: {str(e)}"