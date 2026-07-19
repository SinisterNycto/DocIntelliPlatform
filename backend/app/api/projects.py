from fastapi import APIRouter, HTTPException
from typing import List
from app.core.database import db
from app.core.models import ProjectModel
from bson import ObjectId

router = APIRouter()

@router.get("/", response_model=List[ProjectModel])
async def list_projects():
    projects = []
    cursor = db.projects.find().sort("created_at", -1)
    async for document in cursor:
        projects.append(ProjectModel(**document))
    return projects

@router.post("/", response_model=ProjectModel)
async def create_project(project: dict):
    if "name" not in project or not project["name"]:
        raise HTTPException(status_code=400, detail="Project name is required")
        
    new_project = ProjectModel(name=project["name"], description=project.get("description", ""))
    result = await db.projects.insert_one(new_project.dict(by_alias=True, exclude_none=True))
    new_project.id = result.inserted_id
    
    return new_project

@router.get("/{project_id}", response_model=ProjectModel)
async def get_project(project_id: str):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
        
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return ProjectModel(**project)

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
        
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Delete the project document
    await db.projects.delete_one({"_id": ObjectId(project_id)})
    
    # Delete all associated documents
    await db.documents.delete_many({"project_id": project_id})
    
    # Delete the vector namespace
    from app.vectorstore.pinecone_store import vector_store_manager
    vector_store_manager.delete_namespace(project_id)
    
    return {"status": "success", "message": "Project deleted successfully"}
