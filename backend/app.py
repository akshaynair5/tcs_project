from flask import Flask
from flask_cors import CORS
from app.routes.chat_routes import chat_bp
from app.routes.pdf_routes import pdf_bp 

def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(pdf_bp, url_prefix="/api/pdf")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
