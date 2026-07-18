from fastapi import APIRouter, HTTPException
from typing import List
from app.core.database import db
from app.core.models import ChatMessageModel
from app.rag.pipeline import rag_pipeline
from bson import ObjectId

router = APIRouter()

@router.get("/project/{project_id}", response_model=List[ChatMessageModel])
async def get_chat_history(project_id: str):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
        
    messages = []
    cursor = db.messages.find({"project_id": project_id}).sort("created_at", 1)
    async for msg in cursor:
        messages.append(ChatMessageModel(**msg))
    return messages

@router.post("/")
async def send_message(payload: dict):
    project_id = payload.get("project_id")
    content = payload.get("content")
    
    if not project_id or not content:
        raise HTTPException(status_code=400, detail="project_id and content are required")
        
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")

    # 1. Save user message to DB
    user_msg = ChatMessageModel(project_id=project_id, role="user", content=content)
    await db.messages.insert_one(user_msg.dict(by_alias=True, exclude_none=True))
    
    # 2. Get answer from RAG Pipeline
    result = await rag_pipeline.answer_question(project_id, content)
    
    # 3. Save assistant message to DB
    assistant_msg = ChatMessageModel(
        project_id=project_id, 
        role="assistant", 
        content=result["answer"],
        sources=[{"name": src} for src in result["sources"]]
    )
    result_insert = await db.messages.insert_one(assistant_msg.dict(by_alias=True, exclude_none=True))
    assistant_msg.id = result_insert.inserted_id
    
    return assistant_msg
