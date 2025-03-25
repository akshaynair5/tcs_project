from flask import Blueprint
from app.controllers.message_controller import MessageController

message_routes = Blueprint("message_routes", __name__)

message_routes.route("/message", methods=["POST"])(MessageController.add_message)
message_routes.route("/messages/<chat_id>", methods=["GET"])(MessageController.get_messages)
message_routes.route("/messages/<chat_id>", methods=["DELETE"])(MessageController.delete_messages)
