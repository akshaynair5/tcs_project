import fitz  # PyMuPDF for text extraction
from neo4j import GraphDatabase
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import pickle
from dotenv import load_dotenv
from app.services.deepseek_service import add_documents_to_graph
import pytesseract  # OCR
from PIL import Image
import io
from transformers import AutoProcessor, AutoModelForImageTextToText

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

processor = AutoProcessor.from_pretrained("ds4sd/SmolDocling-256M-preview")
model = AutoModelForImageTextToText.from_pretrained("ds4sd/SmolDocling-256M-preview")


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Sentence Transformer Model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
dimension = 384  # Embedding size



def extract_text_from_pdf(pdf_path):
    """Extracts text and tabular data from a PDF using PyMuPDF, Tesseract OCR, and SmolDocling."""
    text = ""
    
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            # Extract text normally
            text += page.get_text("text") + "\n"
            
            # Extract images for OCR (if scanned document)
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                
                # Apply OCR to extract text from image
                ocr_text = pytesseract.image_to_string(image)
                text += f"\n[OCR Extracted from Image {img_index} on Page {page_num}]:\n{ocr_text}\n"
                
                # Use SmolDocling to process the image (for tabular data)
                inputs = processor(image, return_tensors="pt")
                outputs = model.generate(**inputs)
                table_data = processor.batch_decode(outputs, skip_special_tokens=True)[0]
                
                text += f"\n[SmolDocling Extracted Table from Image {img_index}]:\n{table_data}\n"
    
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

    print("Document stored in Neo4j.")

def process_pdf_and_store(pdf_path):
    """Extracts text from a PDF and stores it in Neo4j via add_documents_to_graph."""
    print('Processing PDF:', pdf_path)
    text = extract_text_from_pdf(pdf_path)

    # Clean and validate text
    cleaned_text = text.strip()
    if not cleaned_text or len(cleaned_text) < 20:
        print("Skipped: extracted text is empty or too short.")
        return

    # Check if embedding is valid before continuing
    embedding = embedding_model.encode([cleaned_text])[0]
    if np.isnan(embedding).any():
        print("Skipped: embedding contains NaNs.")
        return

    # Text and embedding look good — proceed
    add_documents_to_graph(cleaned_text)
    print("Document stored in Neo4j.")

