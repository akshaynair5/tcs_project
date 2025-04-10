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
import re

# Load environment variables
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize models
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
processor = AutoProcessor.from_pretrained("ds4sd/SmolDocling-256M-preview")
model = AutoModelForImageTextToText.from_pretrained("ds4sd/SmolDocling-256M-preview")

# Tesseract setup
tesseract_path = r"C:\Program Files\Tesseract-OCR"
tesseract_exe = os.path.join(tesseract_path, "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = tesseract_exe
os.environ["PATH"] += os.pathsep + tesseract_path

# Neo4j credentials
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Embedding size
dimension = 384

def clean_text(text):
    # Remove unnecessary line breaks, multiple spaces, and OCR noise like 'ﬁ', 'ﬂ'
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"[\ufb01\ufb02]", "", text) 
    return text.strip()

def extract_text_from_pdf(pdf_path):
    """Returns list of per-page text blocks with OCR and SmolDocling enhancements."""
    page_texts = []

    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            combined_text = ""
            try:
                combined_text += page.get_text("text") + "\n"
            except Exception as e:
                print(f"[ERROR] Text extraction failed on page {page_num}: {e}")

            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

                    try:
                        ocr_text = pytesseract.image_to_string(image)
                        combined_text += f"\n[OCR Image {img_index}]:\n{ocr_text}\n"
                    except Exception as ocr_error:
                        print(f"[ERROR] OCR failed: {ocr_error}")

                    try:
                        inputs = processor(image, return_tensors="pt")
                        outputs = model.generate(**inputs)
                        table_data = processor.batch_decode(outputs, skip_special_tokens=True)[0]
                        combined_text += f"\n[SmolDocling Table {img_index}]:\n{table_data}\n"
                    except Exception as smol_error:
                        print(f"[ERROR] SmolDocling failed: {smol_error}")

                except Exception as img_error:
                    print(f"[ERROR] Image extraction failed: {img_error}")

            page_texts.append(clean_text(combined_text))

    return page_texts

def process_pdf_and_store(pdf_path):
    """Extracts text from a PDF and stores it in Neo4j via add_documents_to_graph."""
    print('Processing PDF:', pdf_path)
    try:
        page_texts = extract_text_from_pdf(pdf_path)

        total_text = " ".join(page_texts)
        if not total_text or len(total_text) < 20:
            print("Skipped: extracted text is empty or too short.")
            return

        add_documents_to_graph(page_texts)
        print("✅ Document stored in Neo4j.")

    except Exception as err:
        print(f"[ERROR] Failed to process and store PDF: {err}")

