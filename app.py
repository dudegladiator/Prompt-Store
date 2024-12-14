from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.routers import serve_html, serve_apis

app = FastAPI(
    title="Prompt Store",
    description="API for generating and managing AI prompts",
    version="1.0.0"
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

# Include routers
app.include_router(serve_html.router)
app.include_router(serve_apis.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
