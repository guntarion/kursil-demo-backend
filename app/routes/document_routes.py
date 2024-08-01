from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from ..services.document_service import get_all_handouts_by_main_topic_id, generate_word_document

router = APIRouter()

class MainTopicRequest(BaseModel):
    main_topic_id: str

@router.post("/generate-handouts-document")
async def generate_handouts_document(request: MainTopicRequest):
    try:
        handouts = await get_all_handouts_by_main_topic_id(request.main_topic_id)
        if not handouts:
            raise HTTPException(status_code=404, detail="No handouts found for the given main topic")
        
        document_path = await generate_word_document(handouts)
        return {"message": "Document generated successfully", "document_path": document_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))