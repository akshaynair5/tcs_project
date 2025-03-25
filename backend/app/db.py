from pymongo import MongoClient
import os

# Use environment variables for security
MONGO_URI = os.getenv("MONGO_URI")
# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
try:
    client.admin.command("ping")  # Check if MongoDB is reachable
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Failed to connect: {e}")
db = client.Cluster0