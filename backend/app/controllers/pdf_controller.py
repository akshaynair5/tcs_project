import os
from flask import request, jsonify
from app.services.pdf_service import extract_text_from_pdf, store_text_in_neo4j

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def upload_pdf():
    """Handles PDF upload, extracts text, and stores it in Neo4j."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(file_path)
        if not extracted_text.strip():
            return jsonify({"error": "Extracted text is empty"}), 400

        # Store extracted text in Neo4j
        store_text_in_neo4j(extracted_text)

        return jsonify({"message": "File uploaded and stored in Neo4j successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500


# import os
# import numpy as np
# from flask import request, jsonify
# from app.services.pdf_service import extract_text_from_pdf, store_text_embedding

# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# def upload_pdf():
#     if "file" not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400

#     file = request.files["file"]
#     if file.filename == "":
#         return jsonify({"error": "No selected file"}), 400

#     file_path = os.path.join(UPLOAD_FOLDER, file.filename)
#     file.save(file_path)

#     # Extract text and store in the vector database
#     extracted_text = extract_text_from_pdf(file_path)
#     store_text_embedding(extracted_text)

#     return jsonify({"message": "File uploaded and stored successfully"}), 200
