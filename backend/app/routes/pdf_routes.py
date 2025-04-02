from flask import Blueprint
from app.controllers.pdf_controller import upload_pdf

pdf_bp = Blueprint("pdf", __name__)

pdf_bp.route("/upload", methods=["POST"])(upload_pdf)
