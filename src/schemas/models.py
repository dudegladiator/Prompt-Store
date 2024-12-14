from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class PromptCategory(str, Enum):
    GENERAL = "general"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    BUSINESS = "business"
    ACADEMIC = "academic"

class Prompt(BaseModel):
    prompt_id: str
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    category: PromptCategory
    prompt: str = Field(..., min_length=10)
    like_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    author_id: Optional[str] = None
    is_public: bool = True

class CreatePromptRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    category: PromptCategory
    prompt: str = Field(..., min_length=10)
    tags: List[str] = []
    author_id: Optional[str] = None
    is_public: bool = False

class UpdatePromptRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    category: Optional[PromptCategory] = None
    prompt: Optional[str] = Field(None, min_length=10)
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

class CustomizationRequest(BaseModel):
    prompt_id: str
    customization_message: str = Field(..., min_length=10, max_length=1000)

class CustomizationResponse(BaseModel):
    prompt_id: str
    original_prompt: str
    customization_message: str
    customized_prompt: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaginatedPromptResponse(BaseModel):
    items: List[Prompt]
    total_pages: int
    current_page: int
    total_items: int
    has_next: bool
    has_previous: bool