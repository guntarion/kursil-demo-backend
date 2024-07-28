# app/routes/openai_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.openai_service import create_listof_topic, save_topic_to_database


class TopicRequest(BaseModel):
    topic: str

router = APIRouter()

@router.post("/list-of-topics/")
async def generate_list_of_topics(request: TopicRequest):
    try:
        list_of_topics = create_listof_topic(request.topic)
        return {"list_of_topics": list_of_topics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-topics-to-database/")
async def save_topics_to_database():
    try:
        result = save_topic_to_database()
        return {"message": "Topics saved to database successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
