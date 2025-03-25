from flask import Blueprint
from app.controllers.chat_controller import ChatController

chat_routes = Blueprint("chat_routes", __name__)

chat_routes.route("/chat", methods=["POST"])(ChatController.create_chat)
chat_routes.route("/chats/<user_id>", methods=["GET"])(ChatController.get_chats)
chat_routes.route("/chat/<chat_id>", methods=["DELETE"])(ChatController.delete_chat)
