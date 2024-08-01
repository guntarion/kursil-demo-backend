# app/db/operations.py
from motor.motor_asyncio import AsyncIOMotorClient
from .database import main_topic_collection, list_topics_collection, points_discussion_collection, cost_ai_collection
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

async def get_all_main_topics():
    cursor = main_topic_collection.find({}, {"main_topic": 1, "cost": 1})
    return await cursor.to_list(length=None)

async def get_main_topic_by_id(main_topic_id):
    return await main_topic_collection.find_one({"_id": ObjectId(main_topic_id)})

async def get_list_topics_by_main_topic_id(main_topic_id):
    cursor = list_topics_collection.find({"main_topic_id": main_topic_id})
    return await cursor.to_list(length=None)

async def get_topic_by_name(topic_name):
    return await list_topics_collection.find_one({"topic_name": topic_name})

async def add_elaborated_point(point_of_discussion, elaboration, topic_name_id):
    logger.info(f"Adding elaborated point: {point_of_discussion}, {topic_name_id}")
    result = await points_discussion_collection.insert_one({
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
        "cost_presentation": ""
    })
    return result.inserted_id

async def get_elaborated_points_by_topic_id(topic_name_id):
    cursor = points_discussion_collection.find({"topic_name_id": topic_name_id})
    return await cursor.to_list(length=None)

async def get_topic_by_id(topic_id):
    return await list_topics_collection.find_one({"_id": ObjectId(topic_id)})

async def update_prompting_content(topic_id, prompting_summary):
    result = await points_discussion_collection.update_many(
        {"topic_name_id": ObjectId(topic_id)},
        {"$set": {"prompting": prompting_summary}}
    )
    return result.modified_count

async def update_content(topic_id, point_of_discussion, content):
    result = await points_discussion_collection.update_one(
        {
            "topic_name_id": ObjectId(topic_id),
            "point_of_discussion": point_of_discussion
        },
        {"$set": {"handout": content}}
    )
    return result.modified_count

async def get_point_of_discussion(point_id: str):
    return await points_discussion_collection.find_one({"_id": ObjectId(point_id)})

async def get_points_discussion_by_topic_id(topic_id):
    cursor = points_discussion_collection.find({"topic_name_id": ObjectId(topic_id)})
    return await cursor.to_list(length=None)

async def update_prompting(point_id: str, prompting: str):
    result = await points_discussion_collection.update_one(
        {"_id": ObjectId(point_id)},
        {"$set": {"prompting": prompting}}
    )
    return result.modified_count

async def update_handout(point_id: str, handout: str):
    result = await points_discussion_collection.update_one(
        {"_id": ObjectId(point_id)},
        {"$set": {"handout": handout}}
    )
    return result.modified_count

async def update_misc_points(point_id: str, misc_points: dict):
    logger.info(f"Updating misc points for point of discussion: {point_id}")
    try:
        result = await points_discussion_collection.update_one(
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
        return result.modified_count
    except Exception as e:
        logger.error(f"Error updating misc points for point of discussion {point_id}: {str(e)}")
        raise

async def update_quiz(point_id: str, quiz_content: str):
    logger.info(f"Updating quiz for point of discussion: {point_id}")
    try:
        logger.debug(f"Point ID: {point_id}")
        logger.debug(f"Quiz content length: {len(quiz_content)}")

        result = await points_discussion_collection.update_one(
            {"_id": ObjectId(point_id)},
            {"$set": {"quiz": quiz_content}}
        )

        logger.info(f"Update result: matched {result.matched_count}, modified {result.modified_count}")

        if result.matched_count == 0:
            logger.warning(f"No document found for point of discussion: {point_id}")
        elif result.modified_count == 0:
            logger.warning(f"Document found but not modified for point of discussion: {point_id}")
        else:
            logger.info(f"Successfully updated quiz for point of discussion: {point_id}")

        return result.modified_count
    except Exception as e:
        logger.error(f"Error updating quiz for point of discussion {point_id}: {str(e)}", exc_info=True)
        raise

async def get_points_discussion_ids_by_topic_id(topic_id):
    cursor = points_discussion_collection.find(
        {"topic_name_id": ObjectId(topic_id)},
        {"_id": 1, "point_of_discussion": 1}
    )
    points = await cursor.to_list(length=None)
    return [{"id": str(point["_id"]), "point": point["point_of_discussion"]} for point in points]

async def get_topic_id_by_point_id(point_id):
    point = await points_discussion_collection.find_one({"_id": ObjectId(point_id)})
    if point and 'topic_name_id' in point:
        return str(point['topic_name_id'])
    return None

async def get_total_cost_by_topic(topic_id: str):
    pipeline = [
        {"$match": {"topic_id": topic_id}},
        {"$group": {"_id": "$topic_id", "total_cost": {"$sum": "$cost"}}}
    ]
    result = await cost_ai_collection.aggregate(pipeline).to_list(length=1)
    return result[0]["total_cost"] if result else 0