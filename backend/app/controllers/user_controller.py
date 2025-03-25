from flask import jsonify, request
from ..models.user_model import UserModel

class UserController:
    @staticmethod
    def register():
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if UserModel.get_user_by_email(email):
            return jsonify({"error": "User already exists"}), 400

        user_id = UserModel.create_user(email, password)
        token = UserModel.generate_jwt(user_id)
        
        return jsonify({"message": "User created successfully", "token": token, "user_id": user_id}), 201

    @staticmethod
    def login():
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        user = UserModel.get_user_by_email(email)
        if not user or not UserModel.verify_password(password, user["password"]):
            return jsonify({"error": "Invalid email or password"}), 401

        token = UserModel.generate_jwt(user["_id"])

        # Convert MongoDB ObjectId to string and remove password
        user_data = {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "createdAt": user.get("createdAt")  # Optional, include if available
        }

        return jsonify({"message": "Login successful", "token": token, "user": user_data}), 200

    @staticmethod
    def get_user(user_id):
        user = UserModel.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "user_id": str(user["_id"]),
            "email": user["email"],
            "createdAt": user["createdAt"]
        }), 200

    @staticmethod
    def delete_user(user_id):
        result = UserModel.delete_user(user_id)
        if result.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": "User deleted successfully"}), 200

    @staticmethod
    def get_user_chats_with_messages(user_id):
        response, status_code = UserModel.get_user_chats_with_messages(user_id)  # Unpack the response tuple

        # Ensure we are handling a proper JSON response
        if status_code != 200:
            return response, status_code  # Return the error response as is

        user_chats = response.get_json()  # Extract JSON data from Response object
        print("User Chats:", user_chats)

        if not user_chats.get("chats", []):
            return jsonify({"message": "No chats found for the user"}), 200

        try:
            # Ensure no unnecessary `.to_dict()` calls
            return jsonify({"chats": user_chats["chats"]}), 200
        except (AttributeError, TypeError) as e:
            print("Error:", str(e))  # Debugging
            return jsonify({"error": "Unexpected data format"}), 500

    
    @staticmethod
    def verify_login():
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401

        token = auth_header.split(" ")[1]
        decoded = UserModel.verify_jwt(token)

        if not decoded:
            return jsonify({"error": "Invalid or expired token"}), 401

        user = UserModel.get_user_by_id(decoded["user_id"])
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "user_id": str(user["_id"]),
            "email": user["email"],
            "createdAt": user["createdAt"]
        }), 200

