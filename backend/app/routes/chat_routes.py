from flask import Blueprint
from app.controllers.chat_controller import ask_question

chat_bp = Blueprint('chat', __name__)

chat_bp.route('/ask', methods=['POST'])(ask_question)
