# app/db/operations.py
from motor.motor_asyncio import AsyncIOMotorClient
from .database import main_topic_collection, list_topics_collection, points_discussion_collection, cost_ai_collection
from bson import ObjectId
import logging

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter with a striking emoji
formatter = logging.Formatter('⚡ %(asctime)s - %(levelname)s - %(message)s')

# Add the formatter to the handler
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)


async def get_all_main_topics():
    cursor = main_topic_collection.find({}, {
        "main_topic": 1, 
        "cost": 1, 
        "link_image_icon": 1  
    })
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

def convert_object_id(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_object_id(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_object_id(v) for v in obj]
    return obj

async def get_topic_by_id(topic_id: str):
    topic = await list_topics_collection.find_one({"_id": ObjectId(topic_id)})
    if topic:
        return convert_object_id(topic)
    return None

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
    result = [{"id": str(point["_id"]), "point": point["point_of_discussion"]} for point in points]

    # Log the result with a striking emoji
    logger.debug("⚡ Retrieved points discussion IDs: %s", result)

    return result

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

async def update_translated_handout(point_id: str, translated_handout: str):
    logger.info(f"Updating translated handout for point of discussion: {point_id}")
    try:
        result = await points_discussion_collection.update_one(
            {"_id": ObjectId(point_id)},
            {"$set": {"handout_id": translated_handout}}
        )

        logger.info(f"Update result: matched {result.matched_count}, modified {result.modified_count}")

        if result.matched_count == 0:
            logger.warning(f"No document found for point of discussion: {point_id}")
        elif result.modified_count == 0:
            logger.warning(f"Document found but not modified for point of discussion: {point_id}")
        else:
            logger.info(f"Successfully updated translated handout for point of discussion: {point_id}")

        return result.modified_count
    except Exception as e:
        logger.error(f"Error updating translated handout for point of discussion {point_id}: {str(e)}", exc_info=True)
        raise

async def update_main_topic_document(main_topic_id: str, update_data: dict):
    try:
        result = await main_topic_collection.update_one(
            {"_id": ObjectId(main_topic_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating main topic document: {str(e)}")
        return False

async def get_main_topic_by_id(main_topic_id: str):
    try:
        return await main_topic_collection.find_one({"_id": ObjectId(main_topic_id)})
    except Exception as e:
        logger.error(f"Error getting main topic by ID: {str(e)}")
        return None    
    

async def update_topic_analogy(topic_id: str, analogy: str):
    result = await list_topics_collection.update_one(
        {"_id": ObjectId(topic_id)},
        {"$set": {"topic_analogy": analogy}}
    )
    return result.modified_count > 0


async def get_all_elaboration_by_main_topic_id(main_topic_id: str):
    # Get the main topic document
    main_topic = await main_topic_collection.find_one({"_id": ObjectId(main_topic_id)})
    if not main_topic:
        logger.warning(f"Main topic not found for ID: {main_topic_id}")
        return None, []

    all_elaborations = []
    debug_info = {
        "main_topic_id": main_topic_id,
        "list_topics": [],
        "elaboration_entries": []
    }

    # Query list_topics_collection
    list_topics_query = {"main_topic_id": main_topic_id}
    logger.info(f"Querying list_topics_collection with: {list_topics_query}")

    list_topics_cursor = list_topics_collection.find(list_topics_query)
    list_topics_docs = await list_topics_cursor.to_list(length=None)

    logger.info(f"Found {len(list_topics_docs)} list topics for main topic {main_topic_id}")

    for list_topic in list_topics_docs:
        topic_id = list_topic["_id"]
        debug_info["list_topics"].append({
            "topic_id": str(topic_id),
            "topic_name": list_topic["topic_name"]
        })

        # Query points_discussion_collection using ObjectId for topic_name_id
        points_discussion_cursor = points_discussion_collection.find({"topic_name_id": topic_id})
        points_discussion_docs = await points_discussion_cursor.to_list(length=None)

        logger.info(f"Found {len(points_discussion_docs)} points of discussion for topic {list_topic['topic_name']}")

        for point in points_discussion_docs:
            if point.get('elaboration'):
                elaboration_entry = {
                    'topic_name': list_topic['topic_name'],
                    'point_of_discussion': point['point_of_discussion'],
                    'elaboration': point['elaboration']
                }
                all_elaborations.append(elaboration_entry)
                debug_info["elaboration_entries"].append({
                    "topic_id": str(topic_id),
                    "point_id": str(point['_id']),
                    "point_of_discussion": point['point_of_discussion']
                })

    if not all_elaborations:
        logger.warning(f"No elaboration entries found for main topic {main_topic_id}")

    return main_topic['main_topic'], all_elaborations, debug_info

async def get_all_points_of_discussion_by_main_topic_id(main_topic_id: str):
    cursor = list_topics_collection.find({"main_topic_id": main_topic_id})
    topics = await cursor.to_list(length=None)
    
    all_points = []
    for topic in topics:
        if 'point_of_discussion' in topic:
            all_points.extend(topic['point_of_discussion'])
    
    return all_points