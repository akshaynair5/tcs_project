from flask import Blueprint
from app.controllers.ask_controller import AskController

ask_routes = Blueprint("ask_routes", __name__)

ask_routes.route("/ask", methods=["POST"])(AskController.ask_question)
