import asyncio
from fastapi import HTTPException
from openai import OpenAI
from utils.config import settings
from utils.app_logger import setup_logger

logger = setup_logger("src/llm/openai_llm.py")

async def google_chat_completions(
    input: str,
    system_prompt: str = "",
    model: str = "gemini-2.0-flash-exp"
):
    try:
        logger.info("Starting google_chat_completions with model: %s", model)
        client = OpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": input
                }
            ]
        )
        logger.info("google_chat_completions response received")
        return response.choices[0].message.content
    except Exception as e:
        logger.error("Error in google_chat_completions: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def groq_chat_completions(
    input: str,
    system_prompt: str = "",
    model: str = "llama-3.3-70b-versatile"
):
    try:
        logger.info("Starting groq_chat_completions with model: %s", model)
        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": input
                }
            ]
        )
        logger.info("groq_chat_completions response received")
        return response.choices[0].message.content
    except Exception as e:
        logger.error("Error in groq_chat_completions: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))