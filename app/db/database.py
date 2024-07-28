# fastapi app/db/database.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database("kursil")

main_topic_collection = db.get_collection("main_topic")
list_topics_collection = db.get_collection("list_topics")
