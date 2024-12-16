from math import ceil
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Query, Request, Depends, status
from typing import Optional, List
from datetime import datetime
from utils.config import get_async_database
from src.schemas.models import (
    Prompt, 
    PromptCategory, 
    CustomizationRequest, 
    CreatePromptRequest,
    UpdatePromptRequest
)
from src.llm.pinecone_langchain import retrieve_documents
from utils.app_logger import setup_logger
from src.llm.openai_llm import google_chat_completions
from src.llm.system_prompts import system_prompt_for_customization
from utils.rate_limiter import rate_limit
from utils.redis_cache import cached

logger = setup_logger("src/routers/serve_apis.py")
router = APIRouter(prefix="/api")
db = get_async_database()

@router.get("/prompts/search")
@cached(expire=300)  # Cache for 5 minutes
async def search_prompts(
    request: Request,
    query: Optional[str] = None,
    category: Optional[PromptCategory] = None,
    tags: Optional[List[str]] = Query(None),
    sort_by: Optional[str] = Query("created_at", enum=["created_at", "like_count", "name"]),
    sort_order: Optional[str] = Query("desc", enum=["asc", "desc"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(9, ge=1, le=100)
):
    try:
        skip = (page - 1) * page_size
        filters = {}
        
        if category:
            filters["category"] = category
        if tags:
            filters["tags"] = {"$all": tags}
        
        if query and query!="undefined":
            document_retrieved = retrieve_documents(
                tenant_id="harsh90731",
                query=query,
                filters=filters,
                top_k=page_size * page
            )
            
            prompt_ids = [doc.id for doc in document_retrieved]
            
            if document_retrieved:
                prompts = await db.prompts_discover.find(
                    {"prompt_id": {"$in": prompt_ids}}
                ).to_list(length=None)
            else:
                prompts = []
            
            total_items = len(document_retrieved)
            
        else:
            pipeline = [
                {"$match": filters}, # Filtering first to reduce the documents to sort
                {"$sort": {sort_by: 1 if sort_order == "asc" else -1}},
                {"$skip": skip},
                {"$limit": page_size},
                {"$project": {"_id": 0}} # Remove _id at the end
            ]

            prompts = await db.prompts_discover.aggregate(pipeline).to_list(length=None)

            # Count query optimization - use count_documents for simple counting with filters
            total_items = await db.prompts_discover.count_documents(filters)

        # Clean up and prepare response
        for prompt in prompts:
            prompt.pop("_id", None)

        total_pages = ceil(total_items / page_size)
        
        return {
            "items": prompts,
            "total_pages": total_pages,
            "current_page": page,
            "total_items": total_items,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
            
    except Exception as e:
        logger.error(f"Error in search_prompts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while searching prompts"
        )
    
@router.get("/prompts/{prompt_id}")
@cached(expire=300)  # Cache for 5 minutes
async def get_prompt(prompt_id: str):
    try:
        prompt = await db.prompts_discover.find_one({"prompt_id": prompt_id})
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found"
            )
            
        prompt.pop("_id", None)
        return prompt
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch prompt"
        )
        
@router.post("/create_prompt", response_model=Prompt)
@rate_limit(max_requests=5, window_seconds=60)
async def create_prompt(
    prompt: CreatePromptRequest
):
    try:
        new_prompt = prompt.dict()
        new_prompt["prompt_id"] = str(uuid4())
        new_prompt["author_id"] = prompt.author_id
        new_prompt["created_at"] = datetime.utcnow()
        new_prompt["updated_at"] = datetime.utcnow()
        new_prompt["is_public"] = False
        
        result = await db.upload_prompt.insert_one(new_prompt)
        return {
            "prompt_id": new_prompt["prompt_id"],
            "status": "Prompt created successfully",
            "message": "Prompt will be reviewed by our team before publishing"
        }
        
    except Exception as e:
        logger.error(f"Error in create_prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create prompt"
        )
        
@router.put("/update_prompt/{prompt_id}", response_model=Prompt)
async def update_prompt(
    prompt_id: str,
    prompt_update: UpdatePromptRequest
):
    try:
        existing_prompt = await db.prompts.find_one({"prompt_id": prompt_id, "is_public": True})
        if not existing_prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found"
            )
            
        update_data = prompt_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Need to review the code 
        await db.update_prompt.insert_one
        
        return {
            "prompt_id": prompt_id,
            "status": "Prompt updated successfully",
            "message": "Prompt will be reviewed by our team before publishing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prompt"
        )
        
@router.get("/categories")
@cached(expire=3000)
async def get_categories(
    request: Request
):
    """
    Get all available categories from prompts collection
    """
    try:
        # Get distinct categories from published prompts only
        categories = await db.prompts_discover.distinct("category")
        
        # If no categories found, return empty list
        if not categories:
            return []
            
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch categories"
        )

@router.post("/prompts/customize")
@rate_limit(max_requests=5, window_seconds=60)
async def customize_prompt(request: Request, customization: CustomizationRequest):
    """
    Customize a prompt with user's specific requirements
    """
    try:
        # Find the prompt
        prompt = await db.prompts_discover.find_one(
            {"prompt_id": customization.prompt_id, "is_public": True}
        )
        
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail="Prompt not found"
            )

        # Combine original prompt with customization request
        message = (
            f"Original Prompt: {prompt['original_prompt']}\n"
            f"Customization Request: {customization.customization_message}"
        )
        
        # Get customized response from LLM
        customized_prompt = await google_chat_completions(
            input=message,
            system_prompt=system_prompt_for_customization
        )
        logger.info(f"Customized prompt: {customized_prompt}")
        
        return {
            "original_prompt": prompt['original_prompt'],
            "customized_prompt": customized_prompt,
            "prompt_id": customization.prompt_id,
            "customization_message": customization.customization_message,
            "created_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error customizing prompt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to customize prompt"
        )