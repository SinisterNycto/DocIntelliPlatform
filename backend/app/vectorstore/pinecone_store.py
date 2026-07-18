import os
import logging
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2",
            google_api_key=settings.GEMINI_API_KEY  # type: ignore
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

vector_store_manager = VectorStoreManager()
