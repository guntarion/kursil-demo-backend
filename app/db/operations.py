# app/db/operations.py

from .database import main_topic_collection, list_topics_collection, points_discussion_collection
from bson import ObjectId

def get_all_main_topics():
    return list(main_topic_collection.find({}, {"main_topic": 1, "cost": 1}))

def get_main_topic_by_id(main_topic_id):
    return main_topic_collection.find_one({"_id": ObjectId(main_topic_id)})

def get_list_topics_by_main_topic_id(main_topic_id):
    return list(list_topics_collection.find({"main_topic_id": main_topic_id}))

def get_topic_by_name(topic_name):
    return list_topics_collection.find_one({"topic_name": topic_name})

def add_elaborated_point(point_of_discussion, elaboration, topic_name_id):
    print("add_elaborated_point", point_of_discussion, topic_name_id)
    return points_discussion_collection.insert_one({
        "point_of_discussion": point_of_discussion,
        "elaboration": elaboration,
        "topic_name_id": topic_name_id,
        "prompting": "",
        "handout": "",
        "outline": "",
        "script": "",
        "quiz": "",
        "discussion": "",
        "method": "",
        "duration": "",
        "casestudy": ""
    })

def get_elaborated_points_by_topic_id(topic_name_id):
    return list(points_discussion_collection.find({"topic_name_id": topic_name_id}))

def get_topic_by_id(topic_id):
    return list_topics_collection.find_one({"_id": ObjectId(topic_id)})

def get_elaborated_points_by_topic_id(topic_id):
    return list(points_discussion_collection.find({"topic_name_id": ObjectId(topic_id)}))

def update_prompting_content(topic_id, prompting_summary):
    points_discussion_collection.update_many(
        {"topic_name_id": ObjectId(topic_id)},
        {"$set": {"prompting": prompting_summary}}
    )

def update_content(topic_id, point_of_discussion, content):
    points_discussion_collection.update_one(
        {
            "topic_name_id": ObjectId(topic_id),
            "point_of_discussion": point_of_discussion
        },
        {"$set": {"handout": content}}
    )

def update_prompting_and_content(topic_id, results):
    for result in results:
        points_discussion_collection.update_one(
            {
                "topic_name_id": ObjectId(topic_id),
                "point_of_discussion": result['point_of_discussion']
            },
            {
                "$set": {
                    "prompting": result['prompting'],
                    "handout": result['content']
                }
            }
        )

def get_point_of_discussion(point_id: str):
    return points_discussion_collection.find_one({"_id": ObjectId(point_id)})

def update_prompting(point_id: str, prompting: str):
    points_discussion_collection.update_one(
        {"_id": ObjectId(point_id)},
        {"$set": {"prompting": prompting}}
    )