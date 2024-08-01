# fastapi app/routes/openai_routes.py
import json
import asyncio
import random
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import List, Dict
from bson import ObjectId
from app.services.openai_service import create_listof_topic, translate_points, elaborate_discussionpoint, elaborate_discussionpoint,  generate_prompting, generate_handout, generate_misc_points, generate_quiz
from app.db.operations import get_all_main_topics, get_main_topic_by_id, get_list_topics_by_main_topic_id, get_elaborated_points_by_topic_id, get_topic_by_id,  get_point_of_discussion, update_prompting, update_handout, update_misc_points, update_quiz, get_points_discussion_by_topic_id, get_points_discussion_ids_by_topic_id, get_topic_id_by_point_id
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

task_tracker = {}
logger = logging.getLogger(__name__)

def generate_task_id():
    return str(ObjectId())

def update_task_status(task_id: str, status: TaskStatus):
    task_tracker[task_id] = status

def update_task_progress(task_id: str, progress: float, message: str):
    if task_id in task_tracker:
        task_tracker[task_id] = {
            "status": TaskStatus.PENDING,
            "progress": progress,
            "message": message
        }    

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


# @router.get("/task-status/{task_id}")
# async def get_task_status(task_id: str):
#     if task_id not in task_tracker:
#         raise HTTPException(status_code=404, detail="Task not found")
#     return {"status": task_tracker[task_id].value}
def update_task_progress(task_id: str, progress: float, message: str):
    if task_id in task_tracker:
        task_tracker[task_id] = {
            "status": TaskStatus.PENDING,
            "progress": progress,
            "message": message
        }

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in task_tracker:
        raise HTTPException(status_code=404, detail="Task not found")
    task_info = task_tracker[task_id]
    return {
        "status": task_info["status"].value if isinstance(task_info, dict) else task_info.value,
        "progress": task_info.get("progress", 0) if isinstance(task_info, dict) else 0,
        "message": task_info.get("message", "") if isinstance(task_info, dict) else ""
    }

def update_task_status(task_id: str, status: TaskStatus):
    if task_id in task_tracker:
        if isinstance(task_tracker[task_id], dict):
            task_tracker[task_id]["status"] = status
        else:
            task_tracker[task_id] = status
    else:
        task_tracker[task_id] = status

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
        main_topics = await get_all_main_topics()
        return convert_objectid_to_str(main_topics)
    except Exception as e:
        logging.error(f"Error in get_main_topics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/main-topics/{main_topic_id}")
async def get_main_topic_details(main_topic_id: str):
    try:
        main_topic = await get_main_topic_by_id(main_topic_id)
        if not main_topic:
            raise HTTPException(status_code=404, detail="Main topic not found")
        list_topics = await get_list_topics_by_main_topic_id(main_topic_id)
        return convert_objectid_to_str({"main_topic": main_topic, "list_topics": list_topics})
    except Exception as e:
        logging.error(f"Error in get_main_topic_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/points-discussion/{topic_id}")
async def get_points_discussion(topic_id: str):
    try:
        points_discussion = await get_points_discussion_by_topic_id(topic_id)
        if not points_discussion:
            raise HTTPException(status_code=404, detail="No points of discussion found for this topic")
        return convert_objectid_to_str(points_discussion)
    except Exception as e:
        logger.error(f"Error Data Not Found in get_points_discussion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))



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

# Oleh tombol elaborate
@router.post("/elaborate-points")
async def elaborate_points_of_discussion(request: ElaborationRequest):
    logger.debug("Received request for elaboration")
    try:
        elaborated_points = await elaborate_discussionpoint(request.topic, request.objective, request.points_of_discussion)
        # logger.debug(f"Elaboration result: {elaborated_points}")
        return {"elaborated_points": elaborated_points}
    except Exception as e:
        logger.error(f"Error in elaboration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    

class PromptingRequest(BaseModel):
    point_of_discussion_id: str

# Testing with Insomnia
@router.post("/generate-prompting")
async def generate_prompting_route(request: PromptingRequest):
    logger.debug(f"Received request to generate prompting for point of discussion: {request.point_of_discussion_id}")
    try:
        point = get_point_of_discussion(request.point_of_discussion_id)
        if not point:
            raise HTTPException(status_code=404, detail="Point of discussion not found")
        
        # Check if prompting already exists
        if point.get('prompting'):
            logger.info(f"Prompting already exists for point of discussion: {request.point_of_discussion_id}")
            return {"message": "Prompting already exists", "prompting": point['prompting']}
        
        # If prompting doesn't exist, generate a new one
        prompting = generate_prompting(point['elaboration'], point['point_of_discussion'])
        update_prompting(request.point_of_discussion_id, prompting)
        
        return {"message": "Prompting generated and stored successfully", "prompting": prompting}
    except Exception as e:
        logger.error(f"Error in prompting generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/generate-handout")
async def generate_handout_route(request: PromptingRequest):
    logger.debug(f"Received request to generate handout for point of discussion: {request.point_of_discussion_id}")
    try:
        point = get_point_of_discussion(request.point_of_discussion_id)
        if not point:
            raise HTTPException(status_code=404, detail="Point of discussion not found")
        
        # Check if handout already exists
        if point.get('handout'):
            logger.info(f"Handout already exists for point of discussion: {request.point_of_discussion_id}")
            return {"message": "Handout already exists", "handout": point['handout']}
        
        # Check if prompting exists
        if not point.get('prompting'):
            raise HTTPException(status_code=400, detail="Prompting not found. Please generate prompting first.")
        
        # Generate handout
        handout = generate_handout(point['point_of_discussion'], point['prompting'])
        update_handout(request.point_of_discussion_id, handout)
        
        return {"message": "Handout generated and stored successfully", "handout": handout}
    except Exception as e:
        logger.error(f"Error in handout generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))    

@router.post("/generate-misc-points")
async def generate_misc_points_route(request: PromptingRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Received request to generate miscellaneous points for point of discussion: {request.point_of_discussion_id}")
    try:
        point = get_point_of_discussion(request.point_of_discussion_id)
        if not point:
            raise HTTPException(status_code=404, detail="Point of discussion not found")
        
        if not point.get('handout'):
            raise HTTPException(status_code=400, detail="Handout not found. Please generate handout first.")
        
        # Start the generation process in the background
        background_tasks.add_task(process_misc_points, request.point_of_discussion_id, point['point_of_discussion'], point['handout'])
        
        return {"message": "Miscellaneous points generation started in the background"}
    except Exception as e:
        logger.error(f"Error in miscellaneous points generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_misc_points(point_id: str, point_of_discussion: str, handout: str):
    try:
        misc_points = generate_misc_points(point_of_discussion, handout)
        logger.info(f"Generated misc points for point of discussion: {point_id}")
        logger.debug(f"Misc points: {misc_points}")
        update_misc_points(point_id, misc_points)
        logger.info(f"Updated database with misc points for point of discussion: {point_id}")
    except Exception as e:
        logger.error(f"Error in background misc points generation: {str(e)}", exc_info=True)

@router.post("/generate-quiz")
async def generate_quiz_route(request: PromptingRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Received request to generate quiz for point of discussion: {request.point_of_discussion_id}")
    try:
        point = get_point_of_discussion(request.point_of_discussion_id)
        if not point:
            raise HTTPException(status_code=404, detail="Point of discussion not found")
        
        if not point.get('handout'):
            raise HTTPException(status_code=400, detail="Handout not found. Please generate handout first.")
        
        # Start the generation process in the background
        background_tasks.add_task(process_quiz, request.point_of_discussion_id, point['point_of_discussion'], point['handout'])
        
        return {"message": "Quiz generation started in the background"}
    except Exception as e:
        logger.error(f"Error in quiz generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_quiz(point_id: str, point_of_discussion: str, handout: str):
    try:
        quiz_content = generate_quiz(point_of_discussion, handout)
        logger.info(f"Generated quiz for point of discussion: {point_id}")
        logger.debug(f"Quiz content length: {len(quiz_content)}")

        if not quiz_content:
            logger.warning(f"Generated quiz content is empty for point of discussion: {point_id}")
            return

        try:
            update_quiz(point_id, quiz_content)
            logger.info(f"Updated database with quiz for point of discussion: {point_id}")
        except Exception as db_error:
            logger.error(f"Error updating database with quiz for point of discussion {point_id}: {str(db_error)}", exc_info=True)
    except Exception as e:
        logger.error(f"Error in background quiz generation for point of discussion {point_id}: {str(e)}", exc_info=True)

class TopicPromptingRequest(BaseModel):
    topic_id: str

@router.post("/generate-topic-prompting")
async def generate_topic_prompting_route(topic_request: TopicPromptingRequest):
    logger.debug(f"Received request to generate prompting for topic: {topic_request.topic_id}")
    try:
        points = await get_points_discussion_ids_by_topic_id(topic_request.topic_id)
        if not points:
            raise HTTPException(status_code=404, detail="No points of discussion found for this topic")
        
        results = await process_topic_prompting(points)
        
        return {"message": f"Prompting generation completed for {len(points)} points of discussion", "results": results}
    except Exception as e:
        logger.error(f"Error in topic prompting generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_topic_prompting(points):
    results = []
    for point in points:
        point_data = await get_point_of_discussion(point['id'])
        if not point_data:
            logger.warning(f"Point data not found for id: {point['id']}")
            continue
        
        topic_id = await get_topic_id_by_point_id(point['id'])
        if not topic_id:
            logger.warning(f"Topic ID not found for point id: {point['id']}")
            continue
        
        if not point_data.get('prompting'):
            prompting = await generate_prompting(
                point_data['elaboration'],
                point_data['point_of_discussion'],
                topic_id
            )
            if prompting:
                await update_prompting(point['id'], prompting)
                logger.info(f"Generated prompting for point: {point['id']}")
                results.append({"point_id": point['id'], "status": "generated"})
            else:
                logger.warning(f"No prompting generated for point: {point['id']}")
                results.append({"point_id": point['id'], "status": "failed"})
        else:
            logger.info(f"Prompting already exists for point: {point['id']}")
            results.append({"point_id": point['id'], "status": "existing"})
    
    return results


class TopicHandoutRequest(BaseModel):
    topic_id: str

@router.post("/generate-topic-handout")
async def generate_topic_handout_route(request: TopicHandoutRequest):
    logger.debug(f"Received request to generate handout for topic: {request.topic_id}")
    try:
        points = await get_points_discussion_ids_by_topic_id(request.topic_id)
        if not points:
            raise HTTPException(status_code=404, detail="No points of discussion found for this topic")
        
        results = await process_topic_handout(points)
        
        return {"message": f"Handout generation completed for {len(points)} points of discussion", "results": results}
    except Exception as e:
        logger.error(f"Error in topic handout generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_topic_handout(points):
    results = []
    for point in points:
        point_data = await get_point_of_discussion(point['id'])
        if not point_data:
            logger.warning(f"Point data not found for id: {point['id']}")
            results.append({"point_id": point['id'], "status": "failed", "reason": "Point data not found"})
            continue
        
        if not point_data.get('handout'):
            if not point_data.get('prompting'):
                logger.warning(f"Prompting not found for point: {point['id']}. Skipping handout generation.")
                results.append({"point_id": point['id'], "status": "skipped", "reason": "Prompting not found"})
                continue
            
            handout = await generate_handout(point_data['point_of_discussion'], point_data['prompting'], str(point_data['topic_name_id']))
            if handout:
                await update_handout(point['id'], handout)
                logger.info(f"Generated handout for point: {point['id']}")
                results.append({"point_id": point['id'], "status": "generated"})
            else:
                logger.warning(f"Failed to generate handout for point: {point['id']}")
                results.append({"point_id": point['id'], "status": "failed", "reason": "Handout generation failed"})
        else:
            logger.info(f"Handout already exists for point: {point['id']}")
            results.append({"point_id": point['id'], "status": "existing"})
    
    return results




# For Testing
class TopicPromptingRequest(BaseModel):
    topic_id: str

@router.post("/mock-generate-topic-prompting")
async def mock_generate_topic_prompting_route(request: Request, topic_request: TopicPromptingRequest):
    return EventSourceResponse(mock_process_topic_prompting(topic_request.topic_id))

async def mock_process_topic_prompting(topic_id: str):
    total_steps = 5
    for i in range(1, total_steps + 1):
        await asyncio.sleep(random.uniform(0.5, 2))
        progress = (i / total_steps) * 100
        yield {
            "event": "progress",
            "data": json.dumps({"progress": progress, "message": f"Processed step {i} of {total_steps}"})
        }
    await asyncio.sleep(1)
    yield {
        "event": "complete",
        "data": json.dumps("Prompting generation completed")
    }


class TopicMiscRequest(BaseModel):
    topic_id: str

@router.post("/generate-topic-misc")
async def generate_topic_misc_route(request: TopicMiscRequest):
    logger.debug(f"Received request to generate misc points for topic: {request.topic_id}")
    try:
        points = await get_points_discussion_ids_by_topic_id(request.topic_id)
        logger.debug(f"\n\n⚡️ ----------------------------→ Points retrieved: {points}\n\n")
        if not points:
            raise HTTPException(status_code=404, detail="No points of discussion found for this topic")
        
        results = await process_topic_misc(points)
        
        return {"message": f"Misc points generation completed for {len(points)} points of discussion", "results": results}
    except Exception as e:
        logger.error(f"Error in topic misc points generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_topic_misc(points):
    results = []
    for point in points:
        try:
            point_data = await get_point_of_discussion(point['id'])
            if not point_data:
                logger.warning(f"Point data not found for id: {point['id']}")
                results.append({"point_id": point['id'], "status": "failed", "reason": "Point data not found"})
                continue

            if not point_data.get('handout'):
                logger.warning(f"Handout not found for point: {point['id']}. Skipping misc points generation.")
                results.append({"point_id": point['id'], "status": "skipped", "reason": "Handout not found"})
                continue

            misc_points = await generate_misc_points(point_data['point_of_discussion'], point_data['handout'], str(point_data['topic_name_id']))
            if misc_points:
                await update_misc_points(point['id'], misc_points)
                logger.info(f"Generated misc points for point of discussion: {point['id']}")
                results.append({"point_id": point['id'], "status": "generated"})
            else:
                logger.warning(f"Failed to generate misc points for point: {point['id']}")
                results.append({"point_id": point['id'], "status": "failed", "reason": "Misc points generation failed"})
        except Exception as e:
            logger.error(f"Error generating misc points for point {point['id']}: {str(e)}", exc_info=True)
            results.append({"point_id": point['id'], "status": "failed", "reason": str(e)})
    
    return results

class TopicQuizRequest(BaseModel):
    topic_id: str

@router.post("/generate-topic-quiz")
async def generate_topic_quiz_route(request: TopicQuizRequest):
    logger.debug(f"Received request to generate quiz for topic: {request.topic_id}")
    try:
        points = await get_points_discussion_ids_by_topic_id(request.topic_id)
        if not points:
            raise HTTPException(status_code=404, detail="No points of discussion found for this topic")
        
        results = await process_topic_quiz(points)
        
        return {"message": f"Quiz generation completed for {len(points)} points of discussion", "results": results}
    except Exception as e:
        logger.error(f"Error in topic quiz generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_topic_quiz(points):
    results = []
    for point in points:
        try:
            point_data = await get_point_of_discussion(point['id'])
            if not point_data:
                logger.warning(f"Point data not found for id: {point['id']}")
                results.append({"point_id": point['id'], "status": "failed", "reason": "Point data not found"})
                continue

            if not point_data.get('handout'):
                logger.warning(f"Handout not found for point: {point['id']}. Skipping quiz generation.")
                results.append({"point_id": point['id'], "status": "skipped", "reason": "Handout not found"})
                continue

            quiz_content = await generate_quiz(point_data['point_of_discussion'], point_data['handout'], str(point_data['topic_name_id']))
            if quiz_content:
                await update_quiz(point['id'], quiz_content)
                logger.info(f"Generated and stored quiz for point of discussion: {point['id']}")
                results.append({"point_id": point['id'], "status": "generated"})
            else:
                logger.warning(f"Generated quiz content is empty for point of discussion: {point['id']}")
                results.append({"point_id": point['id'], "status": "failed", "reason": "Empty quiz content"})
        except Exception as e:
            logger.error(f"Error generating quiz for point {point['id']}: {str(e)}", exc_info=True)
            results.append({"point_id": point['id'], "status": "failed", "reason": str(e)})
    
    return results
