# app/db/operations.py

from .database import main_topic_collection, list_topics_collection, points_discussion_collection, cost_ai_collection
from bson import ObjectId

import logging


logger = logging.getLogger(__name__)

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
        "topic_name_id": topic_name_id,
        "elaboration": elaboration,
        "learn_objective": "",
        "assessment": "",
        "prompting": "",
        "handout": "",
        "outline": "",
        "script": "",
        "quiz": "",
        "discussion": "",
        "method": "",
        "duration": "",
        "casestudy": "",
        "cost_elaboration": "",
        "cost_prompting": "",
        "cost_handout": "",
        "cost_quiz": "",
        "cost_quiz": "",
        "cost_presentation": ""
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

def get_point_of_discussion(point_id: str):
    return points_discussion_collection.find_one({"_id": ObjectId(point_id)})

def get_points_discussion_by_topic_id(topic_id):
    return list(points_discussion_collection.find({"topic_name_id": ObjectId(topic_id)}))

def update_prompting(point_id: str, prompting: str):
    points_discussion_collection.update_one(
        {"_id": ObjectId(point_id)},
        {"$set": {"prompting": prompting}}
    )

def update_handout(point_id: str, handout: str):
    points_discussion_collection.update_one(
        {"_id": ObjectId(point_id)},
        {"$set": {"handout": handout}}
    )    

def update_misc_points(point_id: str, misc_points: dict):
    logger.info(f"Updating misc points for point of discussion: {point_id}")
    try:
        result = points_discussion_collection.update_one(
            {"_id": ObjectId(point_id)},
            {"$set": {
                "learn_objective": misc_points.get("learn_objective", ""),
                "assessment": misc_points.get("assessment", ""),
                "method": misc_points.get("method", ""),
                "duration": misc_points.get("duration")
            }}
        )
        logger.info(f"Update result: matched {result.matched_count}, modified {result.modified_count}")
        if result.modified_count == 0:
            logger.warning(f"No documents were modified for point of discussion: {point_id}")
    except Exception as e:
        logger.error(f"Error updating misc points for point of discussion {point_id}: {str(e)}")
        raise

def update_quiz(point_id: str, quiz_content: str):
    logger.info(f"Updating quiz for point of discussion: {point_id}")
    try:
        # Log the input parameters
        logger.debug(f"Point ID: {point_id}")
        logger.debug(f"Quiz content length: {len(quiz_content)}")

        # Ensure point_id is a valid ObjectId
        object_id = ObjectId(point_id)

        # Perform the update operation
        result = points_discussion_collection.update_one(
            {"_id": object_id},
            {"$set": {"quiz": quiz_content}}
        )

        # Log the result of the update operation
        logger.info(f"Update result: matched {result.matched_count}, modified {result.modified_count}")

        if result.matched_count == 0:
            logger.warning(f"No document found for point of discussion: {point_id}")
        elif result.modified_count == 0:
            logger.warning(f"Document found but not modified for point of discussion: {point_id}")
        else:
            logger.info(f"Successfully updated quiz for point of discussion: {point_id}")

        # Verify the update
        updated_doc = points_discussion_collection.find_one({"_id": object_id})
        if updated_doc:
            logger.debug(f"Updated document: {updated_doc}")
        else:
            logger.warning(f"Could not retrieve updated document for point of discussion: {point_id}")

    except Exception as e:
        logger.error(f"Error updating quiz for point of discussion {point_id}: {str(e)}", exc_info=True)
        raise

def get_points_discussion_ids_by_topic_id(topic_id):
    points = list(points_discussion_collection.find(
        {"topic_name_id": ObjectId(topic_id)},
        {"_id": 1, "point_of_discussion": 1}
    ))
    return [{"id": str(point["_id"]), "point": point["point_of_discussion"]} for point in points]    