from flask import Blueprint
from app.controllers.user_controller import UserController

user_routes = Blueprint("user_routes", __name__)

user_routes.route("/register", methods=["POST"])(UserController.register)
user_routes.route("/login", methods=["POST"])(UserController.login)
user_routes.route("/user/<user_id>", methods=["GET"])(UserController.get_user)
user_routes.route("/user/<user_id>", methods=["DELETE"])(UserController.delete_user)
user_routes.route("/user/<user_id>/chats", methods=["GET"])(UserController.get_user_chats_with_messages)
user_routes.route("/verify-login", methods=["POST"])(UserController.verify_login)