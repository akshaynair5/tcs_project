from bson import ObjectId
from app.db import db

class EmbeddingModel:
    collection = db.embeddings

    @staticmethod
    def add_embedding(message_id, embedding_vector, metadata=None):
        embedding = {
            "messageId": ObjectId(message_id),
            "embedding": embedding_vector,  # Store as an array
            "metadata": metadata or {}
        }
        return str(EmbeddingModel.collection.insert_one(embedding).inserted_id)

    @staticmethod
    def get_embedding_by_message(message_id):
        return EmbeddingModel.collection.find_one({"messageId": ObjectId(message_id)})

    @staticmethod
    def delete_embedding_by_message(message_id):
        return EmbeddingModel.collection.delete_one({"messageId": ObjectId(message_id)})
