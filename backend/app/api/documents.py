from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from typing import List
from app.core.database import db
from app.core.models import DocumentModel
from app.tasks.ingestion import process_website_task, process_pdf_task
from bson import ObjectId
from app.api.auth import get_current_user
import os
import shutil

router = APIRouter()

async def verify_project_ownership(project_id: str, user_id: str):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    project = await db.projects.find_one({"_id": ObjectId(project_id), "user_id": user_id})
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    return project

@router.get("/project/{project_id}", response_model=List[DocumentModel])
async def list_documents(project_id: str, user_id: str = Depends(get_current_user)):
    await verify_project_ownership(project_id, user_id)
        
    documents = []
    cursor = db.documents.find({"project_id": project_id}).sort("created_at", -1)
    async for doc in cursor:
        documents.append(DocumentModel(**doc))
    return documents

@router.post("/url")
async def ingest_url(payload: dict, user_id: str = Depends(get_current_user)):
    project_id = payload.get("project_id")
    url = payload.get("url")
    
    if not project_id or not url:
        raise HTTPException(status_code=400, detail="project_id and url are required")
        
    await verify_project_ownership(project_id, user_id)

    new_doc = DocumentModel(project_id=project_id, filename=url, url=url, status="pending")
    result = await db.documents.insert_one(new_doc.dict(by_alias=True, exclude_none=True))
    doc_id = str(result.inserted_id)
    
    process_website_task.delay(doc_id, project_id, url)
    
    return {"message": "URL ingestion started", "document_id": doc_id}

@router.post("/upload")
async def upload_pdf(project_id: str, file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    await verify_project_ownership(project_id, user_id)
        
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    new_doc = DocumentModel(project_id=project_id, filename=file.filename, status="pending")
    result = await db.documents.insert_one(new_doc.dict(by_alias=True, exclude_none=True))
    doc_id = str(result.inserted_id)
    
    upload_dir = "/tmp/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{doc_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    process_pdf_task.delay(doc_id, project_id, file_path, file.filename)
    
    return {"message": "PDF ingestion started", "document_id": doc_id}

@router.delete("/{document_id}")
async def delete_document(document_id: str, user_id: str = Depends(get_current_user)):
    if not ObjectId.is_valid(document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID")
        
    doc = await db.documents.find_one({"_id": ObjectId(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    await verify_project_ownership(doc["project_id"], user_id)
        
    result = await db.documents.delete_one({"_id": ObjectId(document_id)})
    
    return {"message": "Document deleted successfully"}
