from flask import Flask
from flask_cors import CORS
from app.routes.pdf_routes import pdf_bp 
from app.routes.user_routes import user_routes
from app.routes.ask_routes import ask_routes
from app.routes.message_routes import message_routes
from app.routes.chat_routes import chat_routes


def create_app():
    app = Flask(__name__)

    CORS(
        app, 
        supports_credentials=True, 
        allow_headers=["Authorization", "Content-Type"], 
        resources={r"/api/*": {"origins": "*"}}
    )

    app.register_blueprint(pdf_bp, url_prefix="/api/pdf")
    app.register_blueprint(user_routes, url_prefix="/api")
    app.register_blueprint(message_routes, url_prefix="/api")
    app.register_blueprint(chat_routes, url_prefix="/api")
    app.register_blueprint(ask_routes, url_prefix="/api")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

