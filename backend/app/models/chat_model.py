from bson import ObjectId
from app.db import db
from datetime import datetime

class ChatModel:
    collection = db.chats

    @staticmethod
    def create_chat(user_id, title):
        chat = {
            "userId": ObjectId(user_id),
            "title": title,
            "createdAt": datetime.now()
        }
        return str(ChatModel.collection.insert_one(chat).inserted_id)

    @staticmethod
    def get_chats_by_user(user_id):
        return list(ChatModel.collection.find({"userId": ObjectId(user_id)}))

    @staticmethod
    def delete_chat(chat_id):
        return ChatModel.collection.delete_one({"_id": ObjectId(chat_id)})
