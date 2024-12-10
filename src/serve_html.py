from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os

router = APIRouter()

# Get the directory where the HTML files are stored
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@router.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main index.html file"""
    with open(os.path.join(BASE_DIR, "static/index.html")) as f:
        return HTMLResponse(content=f.read())