from flask import Flask, request, jsonify
from app.services.deepseek_service import generate_response

app = Flask(__name__)

@app.route('/api/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    print(request.json)
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    answer = generate_response(question)
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True)
