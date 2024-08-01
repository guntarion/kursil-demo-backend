# fastapi app/db/database.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
# client = MongoClient(MONGO_URI)
client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database("kursil")

main_topic_collection = db.get_collection("main_topic")
list_topics_collection = db.get_collection("list_topics")
points_discussion_collection = db.get_collection("points_discussion")
cost_ai_collection = db.get_collection("cost_ai")
