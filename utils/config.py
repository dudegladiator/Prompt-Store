from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import Optional
import os

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    MONGODB_URI: Optional[str] = os.getenv("MONGODB_URI")
    REDIS_URI: Optional[str] = os.getenv("REDIS_URI")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    MISTRAL_API_KEY: Optional[str] = os.getenv("MISTRAL_API_KEY")
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    
    
    class Config:
        env_file = ".env"

settings = Settings()

# Create database clients using the updated settings
database_client = AsyncIOMotorClient(settings.MONGODB_URI)
database = database_client.cognix

pymongo_client = MongoClient(settings.MONGODB_URI)
pymongo_db = pymongo_client.cognix

def get_async_database():
    return database

def get_sync_database():
    return pymongo_db