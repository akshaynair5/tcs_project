# 🛡️ PolicyPal – An Insurance ChatBot

**PolicyPal** is an AI-powered insurance chatbot that enables users to interact with complex policy documents using natural language. Designed to handle unstructured data like PDFs and scanned images, it provides fast, reliable answers with contextual accuracy by leveraging a Neo4j knowledge graph and a Retrieval-Augmented Generation (RAG) pipeline powered by LLMs.

---

## 🚀 Features

- 🔐 **JWT-Based Authentication** – Secure user registration & login.
- 📄 **Admin-Only PDF Upload** – Upload insurance PDFs/images, extract text/tables.
- 🧠 **Neo4j Knowledge Graph** – Structured semantic storage of document data.
- 💬 **Persistent Chat** – Store and retrieve full user chat history using MongoDB.
- 🤖 **LLM Integration (Gemini)** – Generate human-like, context-aware responses.
- 📊 **Automated Evaluation** – Faithfulness scoring with Gemini and BERTScore.

---

## 🧩 Architecture Overview

1. **Admins** upload insurance documents (PDF/image).
2. Text and tables are extracted via **Tesseract OCR** and **Camelot**.
3. Extracted data is chunked, keyword-tagged, embedded, and stored in **Neo4j**.
4. Users ask questions, which are rewritten and enriched with relevant context.
5. The **LLM** generates a short and detailed response.
6. Conversations are stored in **MongoDB**, and responses are evaluated for quality.

---

## 🔧 Tech Stack

| Technology         | Purpose                                      |
|--------------------|----------------------------------------------|
| Flask              | Backend APIs                                 |
| MongoDB            | Store users, chats, and messages             |
| Neo4j              | Semantic storage of document content         |
| Gemini / DeepSeek  | Large language model for Q&A                 |
| JWT                | Authentication and authorization             |
| Tesseract OCR      | Image-based text extraction                  |
| Camelot            | Table parsing from PDFs                      |
| KeyBERT + spaCy    | Keyword extraction for graph construction    |

---

## 📂 Knowledge Graph Structure

- **Document Nodes** – Chunks of parsed text from uploads.
- **InsuranceType Nodes** – Keywords/topics like "claim", "premium".
- **Table Nodes** – Parsed tabular data from documents.
- **BELONGS_TO / RELATED_TO** relationships enable semantic traversal.

---

## 🔄 Retrieval-Augmented Generation Flow

1. ✍️ **User asks a question**
2. ✨ **Question rewritten using chat history**
3. 🧠 **Context retrieved from Neo4j** using embedding similarity and fuzzy matching
4. 🪄 **Prompt built and passed to LLM**
5. 📜 **LLM returns brief + detailed answers**
6. 🗃️ **Answers stored in MongoDB and evaluated automatically**

---

## 📈 Evaluation Metrics

- **Faithfulness** – LLM checks whether the answer is accurate to the retrieved context.
- **BERTScore** – Measures semantic similarity to the user's original query.

All results are logged to a CSV file for performance tracking and model improvement.

---

## 🔧 Setup Instructions

> ⚠️ _This is a server-side application and may require specific libraries like `Neo4j`, `MongoDB`, `Flask`, and OCR/table extraction tools._

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/policypal.git
cd policypal
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file with your secrets:

```env
MONGO_URI=...
JWT_SECRET=...
NEO4J_URI=...
LLM_API_KEY=...
```

### 4. Run the application

```bash
python app.py
```

---

## 📌 Future Enhancements

* ⭐ Allow users to rate answers and give feedback.
* 🤖 Fine-tune responses based on user feedback using trainable LLMs.
* 📈 Improve table parsing reliability with better heuristics or ML models.

---

## 🙏 Acknowledgements

This project was developed as part of a TCS internship by **Akshay Nair** and **Akshay Reddy**, under the guidance of **Vasantha Priya Sachithanandan**.
