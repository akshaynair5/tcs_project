import os
from flask import request, jsonify
from app.services.pdf_service import process_pdf_and_store

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
        process_pdf_and_store(file_path)

        return jsonify({"message": "File uploaded and stored in Neo4j successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500
