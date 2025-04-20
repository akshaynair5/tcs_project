import re
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from bson import ObjectId
from app.models.message_model import MessageModel
from neo4j import GraphDatabase
import spacy
from keybert import KeyBERT
from sklearn.metrics.pairwise import cosine_similarity
from ragas import SingleTurnSample
from ragas.evaluation import evaluate
from ragas.metrics import answer_relevancy, faithfulness, context_precision
import uuid
import hashlib
import math
from rapidfuzz import fuzz
from better_profanity import profanity
from google import genai
import logging

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

    # Named Entities
    keywords.update(ent.text.lower() for ent in doc.ents if ent.label_ in {"ORG", "PRODUCT", "PERSON", "NORP", "FAC", "GPE", "LOC"})

    # Nouns and Proper Nouns
    keywords.update(token.text.lower() for token in doc if token.pos_ in {"NOUN", "PROPN"} and token.is_alpha)

    # BERT Keywords
    bert_keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words='english')
    keywords.update(kw[0].lower() for kw in bert_keywords[:top_n])

    return list(keywords)

def lemmatize(keyword):
    doc = nlp(keyword.lower())
    return " ".join([token.lemma_ for token in doc if not token.is_punct and not token.is_space])

def generate_deterministic_uuid(text):
    """Generate UUID based on the SHA-1 hash of the chunk."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hashlib.sha1(text.encode()).hexdigest()))

def find_similar_keywords(keywords, threshold=0.7):
    """Finds similar keywords based on cosine similarity after lemmatizing."""
    lemmatized_keywords = [lemmatize(k) for k in keywords]
    vectors = embedding_model.encode(lemmatized_keywords)
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
                    doc_id = generate_deterministic_uuid(chunk)

                    extracted_keywords = extract_keywords(chunk)
                    if not extracted_keywords:
                        continue

                    similar_keywords = find_similar_keywords(extracted_keywords)

                    # Deduplicate keywords with lemmatization
                    lemmatized_map = {keyword: lemmatize(keyword) for keyword in extracted_keywords}
                    unique_lemmas = set(lemmatized_map.values())

                    for keyword in extracted_keywords:
                        original_keyword = keyword
                        lemmatized_keyword = lemmatized_map[keyword]
                        add_insurance_type_if_new(lemmatized_keyword)

                        # Create document and link to insurance type
                        session.run("""
                            MERGE (d:Document {id: $id})
                            ON CREATE SET d.text = $text,
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
                            "type": lemmatized_keyword
                        })

                        # Connect related insurance types (bi-directional)
                        for related_keyword in similar_keywords.get(original_keyword, []):
                            related_lemma = lemmatized_map.get(related_keyword, lemmatize(related_keyword))
                            if lemmatized_keyword != related_lemma:
                                session.run("""
                                    MATCH (t1:InsuranceType {name: $kw1}),
                                          (t2:InsuranceType {name: $kw2})
                                    MERGE (t1)-[:RELATED_TO]->(t2)
                                    MERGE (t2)-[:RELATED_TO]->(t1)
                                """, {
                                    "kw1": lemmatized_keyword,
                                    "kw2": related_lemma
                                })

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

def normalize_score(score, min_val=0, max_val=1):
    """Clamp and normalize a score between min and max."""
    return max(min(score, max_val), min_val)

def format_table_block(table):
    """Format structured table into a human-readable string block."""
    formatted = format_structured_table(table["headers"], table["rows"])
    return f"[Table: {table['title']} (Page {table['page']})]\n{formatted}"

def search_context(question, max_tokens=700, similarity_threshold=0.5):
    try:
        question_embedding = embedding_model.encode([question])[0].tolist()

        with driver.session() as session:
            result = session.run("""
                MATCH (d:Document)
                RETURN d.text AS text, d.embedding AS embedding, d.page AS page, d.chunk_index AS chunk_index
            """)
            chunks, embeddings = [], []
            for record in result:
                embedding = record["embedding"]
                if isinstance(embedding, list) and not any(np.isnan(embedding)):
                    chunks.append({
                        "text": record["text"],
                        "embedding": embedding,
                        "page": record.get("page", 0),
                        "chunk_index": record.get("chunk_index", 0)
                    })
                    embeddings.append(embedding)

        tables = fetch_structured_tables()
        table_embeddings = []
        for table in tables:
            try:
                table_embeddings.append(embedding_model.encode([table["text"]])[0].tolist())
            except Exception as e:
                logging.warning(f"Embedding error for table on page {table.get('page')}: {e}")
                continue

        text_scores = []
        if embeddings:
            text_similarities = cosine_similarity([question_embedding], embeddings)[0]
            for i, chunk in enumerate(chunks):
                sim_score = normalize_score(text_similarities[i])
                if sim_score >= similarity_threshold:
                    fuzz_score = fuzz.partial_ratio(question.lower(), chunk["text"].lower()) / 100
                    final_score = round(0.7 * sim_score + 0.3 * fuzz_score, 4)
                    text_scores.append((chunk["text"], final_score))

        table_scores = []
        if table_embeddings:
            table_similarities = cosine_similarity([question_embedding], table_embeddings)[0]
            for i, table in enumerate(tables):
                sim_score = normalize_score(table_similarities[i])
                if sim_score >= similarity_threshold:
                    fuzz_score = fuzz.partial_ratio(question.lower(), table["text"].lower()) / 100
                    header_score = fuzz.partial_ratio(question.lower(), " ".join(table["headers"]).lower()) / 100
                    final_score = round(0.6 * sim_score + 0.3 * fuzz_score + 0.1 * (header_score / 100), 4)
                    table_scores.append((table, final_score))

        all_scores = text_scores + [(format_table_block(t), s) for t, s in table_scores]
        all_scores.sort(key=lambda x: x[1], reverse=True)

        context = []
        token_count = 0
        seen_texts = set()

        for item, score in all_scores:
            if isinstance(item, str):
                if item in seen_texts:
                    continue
                word_count = len(item.split())
                if token_count + word_count > max_tokens:
                    break
                context.append(item)
                seen_texts.add(item)
                token_count += word_count

        return "\n\n".join(context) if context else "No relevant information found."

    except Exception as e:
        logging.exception("Error occurred during context search.")
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

def generate_response(question: str, chat_id=None, ground_truth=None):
    def default_response(short_msg, detailed_msg):
        return {
            "response_short": short_msg,
            "response_detailed": detailed_msg
        }

    if not question or not isinstance(question, str) or len(question.strip()) < 3:
        return default_response("Invalid input.", "Please provide a clearer and more detailed question.")

    # Step 1: Collect minimal, relevant chat history
    history_snippets = []
    if chat_id:
        try:
            messages = MessageModel.collection.find({"chatId": ObjectId(chat_id)}).sort("timestamp", -1).limit(6)
            for msg in reversed(list(messages)):
                role = msg.get("role", "User").capitalize()
                content = msg.get("content", "")
                message_text = content.get("response_short") if (role.lower() == "assistant" and isinstance(content, dict)) else str(content)
                if message_text.strip():
                    history_snippets.append(f"{role}: {message_text.strip()}")
        except Exception as e:
            print(f"[History Fetch Error] {e}")

    short_history = "\n".join(history_snippets[-3:])  # Only last 3 entries for brevity

    # Step 2: Rewrite question using minimal history
    rewrite_prompt = f"""You are an assistant helping users with insurance-related queries.

    Given the minimal chat history and the user's question, rewrite it to be clear and specific.

    Chat:
    {short_history}

    User Question: {question}

    REWRITTEN QUESTION:"""

    rewritten_question = run_ollama(rewrite_prompt).strip()

    # Step 3: Search context using rewritten question
    context = search_context(rewritten_question)
    print("Context found:", context)

    # Step 4: Build intelligent prompt (with moderation)
    def build_prompt(mode: str, q: str):
        tone = "briefly" if mode == "short" else "in detail"
        return f"""You are a helpful and professional assistant specializing in insurance.

    Answer the user's question {tone} using the context and chat history provided.

    ⚠️ If the question is inappropriate, offensive, unrelated to insurance, or asks for content that is harmful, illegal, or unethical — politely decline to answer.

    Chat:
    {short_history}

    Context: {context}

    User Question: {q}
    """

    # Step 5: Generate both answers
    response_short = remove_think_tags(run_ollama(build_prompt("short", rewritten_question)))
    if not response_short or response_short.lower().startswith("error"):
        return default_response("Temporarily unavailable.", "There was a processing error. Please try again shortly.")

    response_detailed = remove_think_tags(run_ollama(build_prompt("detailed", rewritten_question)))

    # Step 6: Save for evaluation
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
    """Robust LLM API caller using Google Gemini model."""
    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )

        if not hasattr(response, "text") or not response.text:
            return "Error: No content generated by the model."

        return response.text.strip()

    except Exception as e:
        print(f"[LLM Error] {str(e)}")
        return f"Error during Gemini call: {str(e)}"


# def run_ollama(prompt):
#     """Robust LLM API caller using OpenRouter."""
#     try:
#         completion = client.chat.completions.create(
#             model="deepseek/deepseek-r1-zero:free",
#             messages=[{"role": "user", "content": prompt}],
#         )
#         print("Raw completion object:", completion)

#         if not hasattr(completion, "choices") or not completion.choices:
#             return "Error: No choices returned from model."

#         message = completion.choices[0].message
#         if not message or not hasattr(message, "content") or not message.content:
#             return "Error: No content generated by the model."

#         return message.content.strip()

#     except Exception as e:
#         print(f"[LLM Error] {str(e)}")
#         return f"Error during OpenRouter call: {str(e)}"


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