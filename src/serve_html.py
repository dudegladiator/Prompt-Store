from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter()

# Get the directory where the HTML files are stored
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@router.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main index.html file"""
    with open(os.path.join(BASE_DIR, "index.html")) as f:
        return HTMLResponse(content=f.read())

@router.get("/scripts.js")
async def get_scripts():
    """Serve the JavaScript file"""
    return FileResponse(
        os.path.join(BASE_DIR, "scripts.js"),
        media_type="application/javascript"
    )