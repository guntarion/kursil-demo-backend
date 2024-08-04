from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.multimedia_service import topic_text_to_speech
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class TextToSpeechRequest(BaseModel):
    main_topic_id: str
    text: str
    voice_id: str


@router.post("/topic-text-to-speech")
async def generate_speech(request: TextToSpeechRequest):
    logger.info(
        f"Received text-to-speech request for main_topic_id: {request.main_topic_id}")
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(request.main_topic_id):
            logger.warning(f"Invalid main_topic_id: {request.main_topic_id}")
            raise HTTPException(
                status_code=400, detail="Invalid main_topic_id")

        logger.debug(
            f"Calling topic_text_to_speech with parameters: main_topic_id={request.main_topic_id}, text={request.text[:50]}..., voice_id={request.voice_id}")
        result = topic_text_to_speech(
            request.main_topic_id, request.text, request.voice_id)

        if "error" in result:
            logger.error(
                f"Error returned from topic_text_to_speech: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])

        logger.info(f"Successfully generated speech: {result['message']}")
        return result
    except Exception as e:
        logger.exception(f"Unexpected error in generate_speech: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
