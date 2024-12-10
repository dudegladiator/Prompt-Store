from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.serve_html import router as serve_html
from src.serve_apis import router as serve_apis

app = FastAPI(
    title="Prompt Search Engine",
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
app.include_router(serve_html)
app.include_router(serve_apis)

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

# Optional: Add startup and shutdown events if needed
@app.on_event("startup")
async def startup_event():
    """
    Initialize any necessary resources on startup
    """
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources on shutdown
    """
    pass

