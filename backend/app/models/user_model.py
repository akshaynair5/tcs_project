import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.db import db
from flask import jsonify

SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Replace with a secure key in production

class UserModel:
    collection = db.users
    chats_collection = db.chats
    messages_collection = db.messages

    @staticmethod
    def hash_password(password):
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password, hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def create_user(email, password):
        hashed_password = UserModel.hash_password(password)
        user = {
            "email": email,
            "password": hashed_password,
            "createdAt": datetime.now()
        }
        return str(UserModel.collection.insert_one(user).inserted_id)

    @staticmethod
    def get_user_by_email(email):
        return UserModel.collection.find_one({"email": email})

    @staticmethod
    def get_user_by_id(user_id):
        return UserModel.collection.find_one({"_id": ObjectId(user_id)})

    @staticmethod
    def delete_user(user_id):
        return UserModel.collection.delete_one({"_id": ObjectId(user_id)})

    @staticmethod
    def generate_jwt(user_id):
        payload = {
            "user_id": str(user_id),
            "exp":  datetime.now(timezone.utc) + timedelta(days=7)  # Token expires in 7 days
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    @staticmethod
    def verify_jwt(token):
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return decoded
        except jwt.ExpiredSignatureError:
            return None  # Token has expired
        except jwt.InvalidTokenError:
            return None  # Invalid token
        
    @staticmethod
    def get_user_chats_with_messages(user_id):
        try:

            # Validate ObjectId before querying
            if not ObjectId.is_valid(user_id):
                return jsonify({"error": "Invalid user ID"}), 400

            # Fetch user chats
            user_chats = list(UserModel.chats_collection.find({"userId": ObjectId(user_id)}))

            for chat in user_chats:
                chat["_id"] = str(chat["_id"])  # Convert ObjectId to string
                chat["userId"] = str(chat["userId"])

                # Fetch messages for the chat
                chat_messages = list(UserModel.messages_collection.find({"chatId": ObjectId(chat["_id"])}))

                # Convert ObjectId fields in messages
                for message in chat_messages:
                    if not isinstance(message, dict):
                        print(f"Unexpected data format in messages: {message}")
                        continue  # Skip invalid entries

                    message["_id"] = str(message["_id"])
                    message["chatId"] = str(message["chatId"])
                    message["userId"] = str(message["userId"])

                # Sort messages by timestamp (ensure no issues with missing timestamps)
                try:
                    chat_messages.sort(key=lambda msg: msg.get("timestamp", 0), reverse=False)
                except Exception as sort_error:
                    print(f"Error sorting messages: {sort_error}")

                chat["messages"] = chat_messages

                # Handle last message safely
                chat["lastMessage"] = chat_messages[0].get("content", "No messages yet") if chat_messages else "No messages yet"
                chat["lastMessageTime"] = chat_messages[0].get("timestamp", "") if chat_messages else ""

            return jsonify({"chats": user_chats}), 200

        except Exception as e:
            import traceback
            print("Error:", traceback.format_exc())  # Full traceback for debugging
            return jsonify({"error": str(e)}), 500


