import camelot
import fitz  # PyMuPDF
import pytesseract
# from paddleocr import PaddleOCR
from PIL import Image
import io
import re
from transformers import AutoProcessor, AutoModelForImageTextToText
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from app.services.deepseek_service import add_documents_to_graph  # existing service

# ========== Setup ========== #

# Load env variables
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tesseract setup
tesseract_path = r"C:\Program Files\Tesseract-OCR"
tesseract_exe = os.path.join(tesseract_path, "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = tesseract_exe
os.environ["PATH"] += os.pathsep + tesseract_path
# ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, structure_version='PP-StructureV2')

# Neo4j setup
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Models
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
processor = AutoProcessor.from_pretrained("ds4sd/SmolDocling-256M-preview")
model = AutoModelForImageTextToText.from_pretrained("ds4sd/SmolDocling-256M-preview")

# ========== Utilities ========== #

def clean_text(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"[\ufb01\ufb02]", "", text)
    return text.strip()

def is_image_file(file_path):
    return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'))

def camelot_tables_to_json(camelot_tables):
    structured = []
    for i, table in enumerate(camelot_tables):
        df = table.df
        if df.shape[0] < 2:
            continue

        headers = df.iloc[0].fillna("").tolist()
        rows = df.iloc[1:].fillna("").values.tolist()
        row_dicts = []

        for row in rows:
            row_dict = {}
            for j, header in enumerate(headers):
                clean_header = header.strip() or f"Column_{j+1}"
                row_dict[clean_header] = row[j].strip() if j < len(row) else ""
            row_dicts.append(row_dict)

        structured.append({
            "table_id": str(uuid.uuid4()),
            "title": f"Table {i + 1}",
            "headers": [h.strip() or f"Column_{j+1}" for j, h in enumerate(headers)],
            "rows": row_dicts
        })

    print(f"[INFO] Extracted {len(structured)} tables from Camelot.")
    return structured

def add_table_to_neo4j(driver, structured_tables, page_number):
    with driver.session() as session:
        for table in structured_tables:
            table_id = table["table_id"]
            title = table["title"]
            headers = table["headers"]
            rows = table["rows"]

            # Create the table node
            session.run("""
                MERGE (t:Table {table_id: $table_id})
                SET t.title = $title, t.page = $page
            """, {
                "table_id": table_id,
                "title": title,
                "page": page_number
            })

            # Create Column nodes and relationships
            for i, col_name in enumerate(headers):
                session.run("""
                    MATCH (t:Table {table_id: $table_id})
                    MERGE (c:Column {name: $name})-[:IN_TABLE]->(t)
                    SET c.index = $index
                """, {
                    "table_id": table_id,
                    "name": col_name,
                    "index": i
                })

            # Insert rows and cells
            for i, row in enumerate(rows):
                row_id = str(uuid.uuid4())

                session.run("""
                    MATCH (t:Table {table_id: $table_id})
                    CREATE (r:Row {row_id: $row_id, index: $index})-[:IN_TABLE]->(t)
                """, {
                    "table_id": table_id,
                    "row_id": row_id,
                    "index": i
                })

                for col_name, cell_value in row.items():
                    session.run("""
                        MATCH (r:Row {row_id: $row_id})
                        MATCH (c:Column {name: $col_name})-[:IN_TABLE]->(:Table {table_id: $table_id})
                        CREATE (cell:Cell {value: $value, column: $col_name})-[:IN_ROW]->(r)
                        CREATE (cell)-[:IN_COLUMN]->(c)
                    """, {
                        "table_id": table_id,
                        "row_id": row_id,
                        "col_name": col_name,
                        "value": cell_value
                    })


# ========== PDF Extraction ========== #

def extract_text_and_tables_from_pdf(pdf_path):
    page_texts = []
    structured_tables = []

    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            combined_text = f"\n--- Page {page_num + 1} ---\n"

            # Extract plain text using layout blocks
            try:
                blocks = page.get_text("blocks")
                blocks.sort(key=lambda b: (round(b[1]), b[0]))
                line_texts = [block[4].strip() for block in blocks if block[4].strip()]
                structured_text = "\n".join(line_texts)
                combined_text += f"[Text Content]:\n{structured_text}\n"
            except Exception as e:
                print(f"[ERROR] Text extraction failed on page {page_num + 1}: {e}")

            # Table extraction using Camelot
            camelot_extracted = False
            try:
                camelot_tables = camelot.read_pdf(
                    pdf_path,
                    pages=str(page_num + 1),
                    flavor='lattice',
                    strip_text='\n'
                )
                if camelot_tables and len(camelot_tables) > 0:
                    table_json = camelot_tables_to_json(camelot_tables)
                    structured_tables.append(table_json)
                    for i, t in enumerate(camelot_tables):
                        combined_text += f"\n[Table {i + 1} - Camelot]:\n{t.df.to_string(index=False)}\n"
                    camelot_extracted = True
                else:
                    raise ValueError("No tables found by Camelot.")
            except Exception as camelot_error:
                print(f"[WARNING] Camelot table extraction failed or returned no tables on page {page_num + 1}: {camelot_error}")

            # Fallback to PaddleOCR table detection if Camelot fails
            # if not camelot_extracted:
            #     try:
            #         pix = page.get_pixmap()
            #         image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            #         result = ocr_engine.ocr(image, cls=True, det=True, rec=True, structure=True)
            #         structured_tables.append(result)
            #         combined_text += f"\n[PaddleOCR Table - Fallback]:\n{json.dumps(result, indent=2)}\n"
            #     except Exception as paddle_error:
            #         print(f"[ERROR] PaddleOCR failed on page {page_num + 1}: {paddle_error}")
            #         structured_tables.append([])

            # OCR text from images in the page
            for img_index, img in enumerate(page.get_images(full=True)):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

                    try:
                        ocr_text = pytesseract.image_to_string(image)
                        if ocr_text.strip():
                            combined_text += f"\n[OCR Image {img_index}]:\n{ocr_text.strip()}\n"
                    except Exception as ocr_error:
                        print(f"[ERROR] OCR failed on page {page_num + 1}: {ocr_error}")

                    try:
                        inputs = processor(image, return_tensors="pt")
                        outputs = model.generate(**inputs)
                        smol_text = processor.batch_decode(outputs, skip_special_tokens=True)[0]
                        if smol_text.strip():
                            combined_text += f"\n[SmolDocling Table {img_index}]:\n{smol_text.strip()}\n"
                    except Exception as smol_error:
                        print(f"[ERROR] SmolDocling failed on page {page_num + 1}: {smol_error}")

                except Exception as img_error:
                    print(f"[ERROR] Image extraction failed on page {page_num + 1}: {img_error}")

            page_texts.append(clean_text(combined_text))

    print('[INFO] Extracted text and tables from PDF.', page_texts)
    print('[INFO] Extracted tables:', structured_tables)
    return page_texts, structured_tables

# ========== Image OCR Extraction ========== #

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        ocr_text = pytesseract.image_to_string(image)
        cleaned_text = clean_text(ocr_text)
        print('[INFO] Extracted text from image.')
        return [f"[Image OCR]:\n{cleaned_text}"]
    except Exception as e:
        print(f"[ERROR] Failed to extract text from image: {e}")
        return []

# ========== Process and Store ========== #

def process_pdf_and_store(file_path):
    print("Processing file:", file_path)
    try:
        if is_image_file(file_path):
            page_texts = extract_text_from_image(file_path)
            structured_tables = []
        else:
            page_texts, structured_tables = extract_text_and_tables_from_pdf(file_path)

        total_text = " ".join(page_texts)
        if not total_text or len(total_text) < 20:
            print("Skipped: extracted text is empty or too short.")
            return

        add_documents_to_graph(page_texts)

        for page_num, table_group in enumerate(structured_tables):
            if table_group:
                add_table_to_neo4j(driver, table_group, page_num + 1)

        print("✅ Document and structured tables stored in Neo4j.")

    except Exception as err:
        print(f"[ERROR] Failed to process and store file: {err}")
