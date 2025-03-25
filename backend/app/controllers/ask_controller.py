from bson import ObjectId
from flask import jsonify, request
from app.services.deepseek_service import generate_response
from app.models.message_model import MessageModel

class AskController:
    @staticmethod
    def ask_question():
        data = request.get_json()
        chat_id = data.get("chat_id")
        user_id = data.get("user_id")
        question = data.get("question", "")

        if not all([chat_id, user_id, question]):
            return jsonify({"error": "chat_id, user_id, and question are required"}), 400

        # Ensure chat_id is a valid ObjectId
        try:
            chat_id = ObjectId(chat_id)
        except:
            return jsonify({"error": "Invalid chat_id format. Must be a 24-character hex string."}), 400

        # 1️⃣ Store the user's message
        user_message_id = MessageModel.add_message(chat_id, user_id, question, "user")

        # 2️⃣ Send request to AI model
        response_text = generate_response(question)

        # 3️⃣ Store AI's response
        ai_message_id = MessageModel.add_message(chat_id, "ai_assistant", response_text, "assistant")

        # 4️⃣ Return AI's response
        return jsonify({
            "user_message_id": user_message_id,
            "ai_message_id": ai_message_id,
            "answer": response_text
        }), 200
