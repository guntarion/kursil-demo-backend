# app/db/operations.py

from .database import main_topic_collection, list_topics_collection
from bson import ObjectId

def get_all_main_topics():
    return list(main_topic_collection.find({}, {"main_topic": 1, "cost": 1}))

def get_main_topic_by_id(main_topic_id):
    return main_topic_collection.find_one({"_id": ObjectId(main_topic_id)})

def get_list_topics_by_main_topic_id(main_topic_id):
    return list(list_topics_collection.find({"main_topic_id": main_topic_id}))