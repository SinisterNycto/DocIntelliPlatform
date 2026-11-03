from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.core.database import db
from app.core.models import ProjectModel
from bson import ObjectId
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[ProjectModel])
async def list_projects(user_id: str = Depends(get_current_user)):
    projects = []
    cursor = db.projects.find({"user_id": user_id}).sort("created_at", -1)
    async for document in cursor:
        projects.append(ProjectModel(**document))
    return projects

@router.post("/", response_model=ProjectModel)
async def create_project(project: dict, user_id: str = Depends(get_current_user)):
    if "name" not in project or not project["name"]:
        raise HTTPException(status_code=400, detail="Project name is required")
        
    new_project = ProjectModel(user_id=user_id, name=project["name"], description=project.get("description", ""))
    result = await db.projects.insert_one(new_project.dict(by_alias=True, exclude_none=True))
    new_project.id = result.inserted_id
    
    return new_project

@router.get("/{project_id}", response_model=ProjectModel)
async def get_project(project_id: str, user_id: str = Depends(get_current_user)):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
        
    project = await db.projects.find_one({"_id": ObjectId(project_id), "user_id": user_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return ProjectModel(**project)

@router.delete("/{project_id}")
async def delete_project(project_id: str, user_id: str = Depends(get_current_user)):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
        
    project = await db.projects.find_one({"_id": ObjectId(project_id), "user_id": user_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    await db.projects.delete_one({"_id": ObjectId(project_id), "user_id": user_id})
    await db.documents.delete_many({"project_id": project_id})
    await db.messages.delete_many({"project_id": project_id})
    
    # Delete the vector namespace
    from app.vectorstore.pinecone_store import vector_store_manager
    vector_store_manager.delete_namespace(project_id)
    
    return {"status": "success", "message": "Project deleted successfully"}
