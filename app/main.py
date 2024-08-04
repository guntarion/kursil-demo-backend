import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.openai_routes import router as openai_router
from app.routes.document_routes import router as document_routes
from app.routes.rag_routes import router as rag_routes

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the openai router
app.include_router(openai_router, prefix="/api", tags=["openai"])
app.include_router(document_routes, prefix="/api", tags=["documents"])
app.include_router(rag_routes, prefix="/rag", tags=["RAG"])

@app.get("/")
async def read_root():
    return {"message": "Server is running okay!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)