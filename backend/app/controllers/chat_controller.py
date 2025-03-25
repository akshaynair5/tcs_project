from flask import jsonify, request
from app.models.chat_model import ChatModel

class ChatController:
    @staticmethod
    def create_chat():
        data = request.get_json()
        user_id = data.get("user_id")
        title = data.get("title")

        if not user_id or not title:
            return jsonify({"error": "User ID and title are required"}), 400

        chat_id = ChatModel.create_chat(user_id, title)
        return jsonify({"message": "Chat created successfully", "chat_id": chat_id}), 201

    @staticmethod
    def get_chats(user_id):
        chats = ChatModel.get_chats_by_user(user_id)
        if not chats:
            return jsonify({"message": "No chats found"}), 200

        chat_list = [{"chat_id": str(chat["_id"]), "title": chat["title"], "createdAt": chat["createdAt"]} for chat in chats]
        return jsonify(chat_list), 200

    @staticmethod
    def delete_chat(chat_id):
        result = ChatModel.delete_chat(chat_id)
        if result.deleted_count == 0:
            return jsonify({"error": "Chat not found"}), 404

        return jsonify({"message": "Chat deleted successfully"}), 200
