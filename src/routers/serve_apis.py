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
    CustomizationResponse,
    CreatePromptRequest,
    UpdatePromptRequest,
    PaginatedPromptResponse
)
from src.llm.pinecone_langchain import retrieve_documents
from utils.app_logger import setup_logger
from src.llm.openai_llm import google_chat_completions
from src.llm.system_prompts import system_prompt_for_customization
from utils.rate_limiter import rate_limit
from utils.redis_cache import cached

router = APIRouter(prefix="/api/v1")
db = get_async_database()
logger = setup_logger("src/routers/serve_apis.py")
router = APIRouter(prefix="/api")
db = get_async_database()
logger = setup_logger("src/routers/serve_apis.py")

@router.get("/prompts/search", response_model=PaginatedPromptResponse)
# @rate_limit(max_requests=5, window_seconds=60)
# @cached(expire=300)  # Cache for 5 minutes
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
        
        # Add public/private filter
        filters["is_public"] = True
        
        if query:
            document_retrieved = retrieve_documents(
                tenant_id="harsh90731",
                query=query,
                filters=filters,
                top_k=page_size * page
            )
            
            prompt_ids = [doc.metadata["prompt_id"] 
                         for i, doc in enumerate(document_retrieved)
                         if i >= skip and i < skip + page_size]
            
            sort_pipeline = [{"$sort": {sort_by: 1 if sort_order == "asc" else -1}}]
            if document_retrieved:
                prompts = await db.prompts.find(
                    {"prompt_id": {"$in": prompt_ids}}
                ).sort(sort_pipeline).to_list(length=None)
            else:
                prompts = []
            
            total_items = len(document_retrieved)
            
        else:
            pipeline = []
            if filters:
                pipeline.append({"$match": filters})
                
            # Add sorting
            pipeline.append(
                {"$sort": {sort_by: 1 if sort_order == "asc" else -1}}
            )
            
            count_pipeline = pipeline + [{"$count": "total"}]
            count_result = await db.prompts.aggregate(count_pipeline).to_list(length=1)
            total_items = count_result[0]["total"] if count_result else 0
            
            pipeline.extend([
                {"$skip": skip},
                {"$limit": page_size}
            ])
            
            prompts = await db.prompts.aggregate(pipeline).to_list(length=None)

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
        
@router.post("/prompts", response_model=Prompt)
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
        
@router.put("/prompts/{prompt_id}", response_model=Prompt)
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
# @rate_limit(max_requests=5, window_seconds=60)
# @cached(expire=600)  # Cache for 10 minutes
async def get_categories(
    request: Request
):
    """
    Get all available categories from prompts collection
    """
    try:
        # Get distinct categories from published prompts only
        categories = await db.prompts.distinct("category")
        
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

@router.post("/prompts/customize", response_model=CustomizationResponse)
@rate_limit(max_requests=5, window_seconds=60)
async def customize_prompt(request: CustomizationRequest):
    """
    Customize a prompt with user's specific requirements
    """
    try:
        # Find the prompt
        prompt = await db.prompts.find_one(
            {"prompt_id": request.prompt_id, "is_public": True}
        )
        
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail="Prompt not found"
            )

        # Combine original prompt with customization request
        message = (
            f"Original Prompt: {prompt['prompt']}\n"
            f"Customization Request: {request.customization_message}"
        )
        
        # Get customized response from LLM
        customized_prompt = await google_chat_completions(
            input=message,
            system_prompt=system_prompt_for_customization
        )
        
        return {
            "original_prompt": prompt['prompt'],
            "customized_prompt": customized_prompt,
            "prompt_id": request.prompt_id,
            "customization_message": request.customization_message,
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