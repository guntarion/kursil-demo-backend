# app/routes/rag_routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rag_service import ingest_data, query_data

router = APIRouter()


class IngestRequest(BaseModel):
    main_topic_id: str


class QueryRequest(BaseModel):
    main_topic_id: str
    query: str


@router.post("/ingest")
async def ingest_route(request: IngestRequest):
    try:
        result = await ingest_data(request.main_topic_id)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_route(request: QueryRequest):
    try:
        result = await query_data(request.main_topic_id, request.query)
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
