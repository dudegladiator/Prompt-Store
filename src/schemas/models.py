from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from enum import Enum

class PromptCategory(str, Enum):
    CREATIVE = "Creative"        # Stories, poetry, art, music, creative writing
    PROFESSIONAL = "Professional"    # Business, career, workplace, professional development
    TECHNICAL = "Technical"       # Programming, data, engineering, scientific
    EDUCATIONAL = "Educational"     # Academic, learning, teaching, study materials
    LIFESTYLE = "Lifestyle"       # Health, wellness, personal development, daily life
    CONTENT = "Content"         # Marketing, social media, blogs, articles
    ANALYTICAL = "Analytical"      # Problem-solving, logic, analysis, strategy
    COMMUNICATION = "Communication"   # Interpersonal, writing, speaking, messaging
    ENTERTAINMENT = "Entertainment"   # Games, fun, leisure, recreational
    UTILITY = "Utility"         # Tools, automation, practical tasks, day-to-day helps

class Prompt(BaseModel):
    prompt_id: str
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    search_description: str = Field(..., min_length=10)
    category: PromptCategory
    original_prompt: str = Field(..., min_length=10)
    like_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tags: List[str] = Field(default_factory=list)
    author_id: Optional[str] = None
    is_public: bool = True

class CreatePromptRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    category: PromptCategory
    prompt: str = Field(..., min_length=10)
    tags: List[str] = []
    author_id: str = Field(..., min_length=3)
    is_public: Optional[bool] = False

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
    
db1 = "prompts_unmodified"
db2 = "prompts_discover"
db2_vector = "nm2"