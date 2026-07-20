import os
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from app.tasks.celery_app import celery_app
from app.rag.pipeline import rag_pipeline
from app.core.config import settings
from bson import ObjectId
import logging
import pymongo

logger = logging.getLogger(__name__)

# Initialize a synchronous client for Celery workers
mongo_client = pymongo.MongoClient(settings.MONGODB_URI)
sync_db = mongo_client[settings.DATABASE_NAME]

def update_doc_status(doc_id: str, status: str, error_msg: str = None):
    update_data = {"status": status}
    if error_msg:
        update_data["error_message"] = error_msg
    sync_db.documents.update_one({"_id": ObjectId(doc_id)}, {"$set": update_data})

@celery_app.task
def process_website_task(doc_id: str, project_id: str, url: str):
    """Scrapes a URL via Jina Reader, extracts markdown text, and chunks it into Pinecone."""
    logger.info(f"Starting web ingestion for {url}")
    
    try:
        update_doc_status(doc_id, "processing")
        
        # Use Jina.ai Reader API to correctly render JavaScript and extract markdown
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=30)
        response.raise_for_status()
        
        text = response.text
        
        if len(text) < 50:
            raise ValueError("Extracted text is too short. Might be an invalid page.")

        # Chunk and Add to Vector Database
        num_chunks = rag_pipeline.process_document(project_id, text, source=url)
        
        logger.info(f"Successfully processed {url} into {num_chunks} chunks.")
        update_doc_status(doc_id, "completed")
        
    except Exception as e:
        logger.error(f"Failed to process website {url}: {e}")
        update_doc_status(doc_id, "failed", str(e))

@celery_app.task
def process_pdf_task(doc_id: str, project_id: str, file_path: str, filename: str):
    """Extracts text from a saved PDF file and chunks it into FAISS."""
    logger.info(f"Starting PDF ingestion for {filename}")
    
    try:
        update_doc_status(doc_id, "processing")
        
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text() + "\n\n"
        
        if len(text.strip()) < 50:
            raise ValueError("Could not extract meaningful text from PDF.")

        # Chunk and Add to FAISS
        num_chunks = rag_pipeline.process_document(project_id, text, source=filename)
        
        logger.info(f"Successfully processed PDF {filename} into {num_chunks} chunks.")
        update_doc_status(doc_id, "completed")
        
    except Exception as e:
        logger.error(f"Failed to process PDF {filename}: {e}")
        update_doc_status(doc_id, "failed", str(e))
    finally:
        # Cleanup temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
