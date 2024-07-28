# fastapi app/routes/openai_routes.py
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from app.services.openai_service import create_listof_topic, save_topic_to_database

class TopicRequest(BaseModel):
    topic: str

router = APIRouter()

def convert_objectid_to_str(obj):
    if isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj


@router.post("/list-of-topics/")
async def generate_list_of_topics(request: TopicRequest):
    try:
        result = create_listof_topic(request.topic)
        return convert_objectid_to_str(result)
    except Exception as e:
        logging.error(f"Error in generate_list_of_topics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-topics-to-database/")
async def save_topics_to_database():
    try:
        result = save_topic_to_database()
        return {"message": "Topics saved to database successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
