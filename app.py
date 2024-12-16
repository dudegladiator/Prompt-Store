from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import redis
from utils.config import settings

app = FastAPI(
    title="Prompt Store",
    description="vff",
    version="1.0.0"
)
redis_client_main = redis.Redis.from_url(
            settings.REDIS_URI,
            decode_responses=True  # This automatically decodes responses
        )

# Mount static files first
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.routers import serve_html, serve_apis
# Include routers
app.include_router(serve_html.router)
app.include_router(serve_apis.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
