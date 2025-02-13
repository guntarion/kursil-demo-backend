# app/routes/document_routes.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from bson import ObjectId
from ..services.document_service import get_all_handouts_by_main_topic_id, generate_handout_word_document, get_all_kursil_by_main_topic_id, generate_kursil_word_document, get_powerpoint_data_by_main_topic_id, generate_powerpoint_document
from ..db.operations import update_main_topic_document, get_main_topic_by_id

import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class MainTopicRequest(BaseModel):
    main_topic_id: str

@router.post("/generate-kursil-document")
async def generate_kursil_document(request: MainTopicRequest):
    try:
        main_topic, kursil_data = await get_all_kursil_by_main_topic_id(request.main_topic_id)
        if not main_topic:
            raise HTTPException(status_code=404, detail="Main topic not found")
        
        if not kursil_data:
            return {"message": "No kursil data found for the given main topic, but proceeding with document generation"}
        
        document_url = await generate_kursil_word_document(main_topic, kursil_data)
        
        # Update the main_topic_collection with the new document URL
        updated = await update_main_topic_document(request.main_topic_id, {"latest_kursil_document": document_url})
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update main topic with new document URL")
        
        return {"message": "Kursil document generated and uploaded successfully", "document_url": document_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-handout-document")
async def generate_handouts_document(request: MainTopicRequest):
    try:
        main_topic, handouts = await get_all_handouts_by_main_topic_id(request.main_topic_id)
        if not main_topic or not handouts:
            raise HTTPException(status_code=404, detail="No handouts found for the given main topic")
        
        document_url = await generate_handout_word_document(main_topic, handouts)
        
        # Update the main_topic_collection with the new document URL
        updated = await update_main_topic_document(request.main_topic_id, {"latest_handout_document": document_url})
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update main topic with new document URL")
        
        return {"message": "Handouts document generated and uploaded successfully", "document_url": document_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-powerpoint-document")
async def generate_powerpoint_document_route(request: MainTopicRequest):
    try:
        main_topic, powerpoint_data = await get_powerpoint_data_by_main_topic_id(request.main_topic_id)
        if not main_topic or not powerpoint_data:
            raise HTTPException(status_code=404, detail="No data found for the given main topic")
        
        document_url = await generate_powerpoint_document(main_topic, powerpoint_data)
        
        # Update the main_topic_collection with the new document URL
        updated = await update_main_topic_document(request.main_topic_id, {"latest_powerpoint_document": document_url})
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update main topic with new document URL")
        
        return {"message": "PowerPoint document generated and uploaded successfully", "document_url": document_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download-document/{main_topic_id}/{document_type}")
async def download_document(main_topic_id: str, document_type: str):
    main_topic = await get_main_topic_by_id(main_topic_id)
    if not main_topic:
        raise HTTPException(status_code=404, detail="Main topic not found")
    
    if document_type == "kursil":
        document_url = main_topic.get("latest_kursil_document")
    elif document_type == "handout":
        document_url = main_topic.get("latest_handout_document")
    elif document_type == "presentation": 
        document_url = main_topic.get("latest_powerpoint_document")
    else:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    if not document_url:
        raise HTTPException(status_code=404, detail=f"No {document_type} document found for this main topic")
    
    return RedirectResponse(document_url)