# fastapi app/routes/openai_routes.py
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from app.services.openai_service import create_listof_topic, translate_points, elaborate_discussionpoint, parsing_test, elaborate_discussionpoint, generate_prompting_for_content_creation, generate_content, generate_prompting_and_content
from app.db.operations import get_all_main_topics, get_main_topic_by_id, get_list_topics_by_main_topic_id, get_elaborated_points_by_topic_id, get_topic_by_id, update_prompting_content, update_content, update_prompting_and_content

import logging

logger = logging.getLogger(__name__)

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


@router.get("/main-topics/")
async def get_main_topics():
    try:
        main_topics = get_all_main_topics()
        return convert_objectid_to_str(main_topics)
    except Exception as e:
        logging.error(f"Error in get_main_topics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/main-topics/{main_topic_id}")
async def get_main_topic_details(main_topic_id: str):
    try:
        main_topic = get_main_topic_by_id(main_topic_id)
        if not main_topic:
            raise HTTPException(status_code=404, detail="Main topic not found")
        list_topics = get_list_topics_by_main_topic_id(main_topic_id)
        return convert_objectid_to_str({"main_topic": main_topic, "list_topics": list_topics})
    except Exception as e:
        logging.error(f"Error in get_main_topic_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
class TranslationRequest(BaseModel):
    points: List[str]

@router.post("/translate-points")
async def translate_points_of_discussion(request: TranslationRequest):
    try:
        translated_points = translate_points(request.points)
        return {"translated_points": translated_points}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

class ElaborationRequest(BaseModel):
    topic: str
    objective: str
    points_of_discussion: List[str]

@router.post("/elaborate-points")
async def elaborate_points_of_discussion(request: ElaborationRequest):
    try:
        elaborated_points = elaborate_discussionpoint(request.topic, request.objective, request.points_of_discussion)
        return {"elaborated_points": elaborated_points}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))   

@router.get("/parsing-test")
async def test_parsing():
    logger.debug("Received request for parsing test")
    try:
        elaborated_points = parsing_test()
        # logger.debug(f"Parsing test result: {elaborated_points}")
        return {"elaborated_points": elaborated_points}
    except Exception as e:
        logger.error(f"Error in parsing test: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class ElaborationRequest(BaseModel):
    topic: str
    objective: str
    points_of_discussion: List[str]

@router.post("/elaborate-points")
async def elaborate_points_of_discussion(request: ElaborationRequest):
    logger.debug("Received request for elaboration")
    try:
        elaborated_points = elaborate_discussionpoint(request.topic, request.objective, request.points_of_discussion)
        # logger.debug(f"Elaboration result: {elaborated_points}")
        return {"elaborated_points": elaborated_points}
    except Exception as e:
        logger.error(f"Error in elaboration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
class PromptingRequest(BaseModel):
    topic_id: str

@router.post("/generate-prompting")
async def generate_prompting(request: PromptingRequest):
    logger.debug("Received request for prompting generation")
    try:
        topic = get_topic_by_id(request.topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        elaborated_points = get_elaborated_points_by_topic_id(request.topic_id)
        if not elaborated_points:
            raise HTTPException(status_code=404, detail="Elaborated points not found for the given topic")
        
        prompting_summaries = generate_prompting_for_content_creation(elaborated_points)
        update_prompting_content(request.topic_id, prompting_summaries)
        
        return {"prompting_summaries": prompting_summaries}
    except Exception as e:
        logger.error(f"Error in prompting generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class ContentGenerationRequest(BaseModel):
    topic_id: str

@router.post("/generate-content")
async def generate_content_route(request: ContentGenerationRequest):
    logger.debug("Received request for content generation")
    try:
        topic = get_topic_by_id(request.topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        elaborated_points = get_elaborated_points_by_topic_id(request.topic_id)
        if not elaborated_points:
            raise HTTPException(status_code=404, detail="Elaborated points not found for the given topic")
        
        generated_contents = []
        for point in elaborated_points:
            if point.get('prompting'):
                content = generate_content(point['prompting'])
                update_content(request.topic_id, point['point_of_discussion'], content)
                generated_contents.append({
                    "point_of_discussion": point['point_of_discussion'],
                    "content": content
                })
        
        return {"generated_contents": generated_contents}
    except Exception as e:
        logger.error(f"Error in content generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class ContentGenerationRequest(BaseModel):
    topic_id: str


@router.post("/generate-prompting-and-content")
async def generate_prompting_and_content_route(request: ContentGenerationRequest, background_tasks: BackgroundTasks):
    logger.debug("Received request for prompting and content generation")
    try:
        topic = get_topic_by_id(request.topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        elaborated_points = get_elaborated_points_by_topic_id(request.topic_id)
        if not elaborated_points:
            raise HTTPException(status_code=404, detail="Elaborated points not found for the given topic")
        
        # Start the generation process in the background
        background_tasks.add_task(process_prompting_and_content, request.topic_id, elaborated_points, topic['topic_name'])
        
        return {"message": "Prompting and content generation started in the background"}
    except Exception as e:
        logger.error(f"Error in prompting and content generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_prompting_and_content(topic_id: str, elaborated_points: List[Dict[str, str]], topic_name: str):
    try:
        results = await generate_prompting_and_content(elaborated_points, topic_name)
        update_prompting_and_content(topic_id, results)
        logger.info(f"Completed prompting and content generation for topic: {topic_name}")
    except Exception as e:
        logger.error(f"Error in background prompting and content generation: {str(e)}", exc_info=True)