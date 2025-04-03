from bson import ObjectId
from flask import jsonify, request
from app.services.deepseek_service import generate_response
from app.models.message_model import MessageModel

import logging
from flask import request, jsonify
from bson import ObjectId

class AskController:
    @staticmethod
    def ask_question():
        """Handles a user's question by storing it, generating a response, and returning it."""

        try:
            data = request.get_json()
            chat_id = data.get("chat_id")
            user_id = data.get("user_id")
            question = str(data.get("question", "")).strip()

            if not all([chat_id, user_id, question]):
                logging.warning("Missing required fields: chat_id, user_id, or question.")
                return jsonify({"error": "chat_id, user_id, and question are required"}), 400

            try:
                chat_id = ObjectId(chat_id)
            except:
                logging.warning(f"Invalid chat_id format: {chat_id}")
                return jsonify({"error": "Invalid chat_id format. Must be a 24-character hex string."}), 400

            user_message_id = MessageModel.add_message(chat_id, user_id, question, "user")

            try:
                response_text = generate_response(question)
            except Exception as e:
                logging.error(f"AI Model Error: {str(e)}")
                return jsonify({"error": "AI response generation failed. Please try again later."}), 500

            ai_message_id = MessageModel.add_message(chat_id, "ai_assistant", response_text, "assistant")

            return jsonify({
                "user_message_id": user_message_id,
                "ai_message_id": ai_message_id,
                "answer": response_text
            }), 200

        except Exception as e:
            logging.error(f"Unexpected Error: {str(e)}")
            return jsonify({"error": "Internal server error."}), 500
