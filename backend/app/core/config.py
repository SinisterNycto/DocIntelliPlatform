from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
    DATABASE_NAME: str = "docintelli"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANK_ENABLED: bool = False
    RERANK_MODEL: str = "BAAI/bge-reranker-base"
    RETRIEVAL_CANDIDATES: int = 20
    MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "docintelli")
    CLERK_ISSUER_URL: str = os.getenv("CLERK_ISSUER_URL", "")
    CLERK_WEBHOOK_SECRET: str = os.getenv("CLERK_WEBHOOK_SECRET", "")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    class Config:
        env_file = ".env"

settings = Settings()
