from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Documentation Intelligence Platform API",
    description="API for ingesting docs, managing projects, and RAG chat.",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:5173", # Frontend dev server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import projects, documents, chat, webhooks

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Documentation Intelligence Platform API"}
