from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Prompt Generator API",
    description="API for generating and managing AI prompts",
    version="1.0.0"
)

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
app.include_router(serve_api.router)

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

