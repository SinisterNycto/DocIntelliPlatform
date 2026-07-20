import os
import logging
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        self.index_name = settings.PINECONE_INDEX_NAME
        
        # Pinecone vector store relies on the PINECONE_API_KEY env variable
        if settings.PINECONE_API_KEY:
            os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY

    def get_store(self, project_id: str) -> PineconeVectorStore:
        if not settings.PINECONE_API_KEY:
            logger.error("PINECONE_API_KEY is not set.")
            return None
            
        return PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=project_id
        )

    def add_texts(self, project_id: str, texts: list[str], metadatas: list[dict] = None):
        store = self.get_store(project_id)
        if store:
            store.add_texts(texts, metadatas=metadatas)
        else:
            logger.error("Failed to add texts: Pinecone store could not be initialized.")

    def delete_namespace(self, project_id: str):
        store = self.get_store(project_id)
        if store:
            try:
                store.delete(delete_all=True, namespace=project_id)
                logger.info(f"Deleted Pinecone namespace: {project_id}")
            except Exception as e:
                logger.error(f"Error deleting namespace {project_id}: {e}")
        else:
            logger.error("Failed to delete namespace: Pinecone store could not be initialized.")

vector_store_manager = VectorStoreManager()
