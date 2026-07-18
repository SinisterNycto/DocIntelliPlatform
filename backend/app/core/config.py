from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
    DATABASE_NAME: str = "docintelli"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "docintelli")

    class Config:
        env_file = ".env"

settings = Settings()
