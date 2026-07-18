from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client[settings.DATABASE_NAME]

# Collections
projects_collection = db["projects"]
documents_collection = db["documents"]
chat_sessions_collection = db["chat_sessions"]
messages_collection = db["messages"]
study_notes_collection = db["study_notes"]
flashcards_collection = db["flashcards"]

# Ensure indexes
async def init_db():
    await projects_collection.create_index("name")
    await documents_collection.create_index("project_id")
    await chat_sessions_collection.create_index("project_id")
    await messages_collection.create_index("session_id")
    await study_notes_collection.create_index("project_id")
    await flashcards_collection.create_index("project_id")
