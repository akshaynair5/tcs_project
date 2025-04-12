from bson import ObjectId
from app.db import db
from datetime import datetime

class MessageModel:
    collection = db.messages

    @staticmethod
    def add_message(chat_id, user_id, content, role):
        message = {
            "chatId": ObjectId(chat_id),
            "userId": user_id if role == "assistant" else ObjectId(user_id),
            "content": content,
            "role": role,  # "user" or "assistant"
            "timestamp": datetime.now()
        }
        return str(MessageModel.collection.insert_one(message).inserted_id)

    @staticmethod
    def get_messages_by_chat(chat_id):
        return list(MessageModel.collection.find({"chatId": ObjectId(chat_id)}))

    @staticmethod
    def delete_messages_by_chat(chat_id):
        return MessageModel.collection.delete_many({"chatId": ObjectId(chat_id)})
    
    @staticmethod
    def delete_message_by_id(message_id):
        return MessageModel.collection.delete_one({"_id": ObjectId(message_id)})
