from flask import jsonify, request
from bson import ObjectId
from datetime import datetime
from app.models.message_model import MessageModel

class MessageController:
    @staticmethod
    def add_message():
        data = request.get_json()
        chat_id = data.get("chat_id")
        user_id = data.get("user_id")
        content = data.get("content")
        role = data.get("role")  # "user" or "assistant"

        if not all([chat_id, user_id, content, role]):
            return jsonify({"error": "chat_id, user_id, content, and role are required"}), 400

        message_id = MessageModel.add_message(chat_id, user_id, content, role)
        return jsonify({"message": "Message added successfully", "message_id": message_id}), 201

    @staticmethod
    def get_messages(chat_id):
        messages = MessageModel.get_messages_by_chat(chat_id)
        if not messages:
            return jsonify({"message": "No messages found"}), 200

        message_list = [
            {
                "message_id": str(msg["_id"]),
                "content": msg["content"],
                "role": msg["role"],
                "timestamp": msg["timestamp"]
            }
            for msg in messages
        ]
        return jsonify(message_list), 200

    @staticmethod
    def delete_messages(chat_id):
        result = MessageModel.delete_messages_by_chat(chat_id)
        if result.deleted_count == 0:
            return jsonify({"error": "No messages found"}), 404

        return jsonify({"message": "Messages deleted successfully"}), 200
    
    @staticmethod
    def delete_message(message_id):
        result = MessageModel.delete_message_by_id(message_id)
        if result.deleted_count == 0:
            return jsonify({"error": "Message not found"}), 404

        return jsonify({"message": "Message deleted successfully"}), 200
        

