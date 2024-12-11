from typing import List
from langchain.schema import Document
import asyncio
from src.llm.pinecone_langchain import upload_documents
from src.llm.openai_llm import groq_chat_completions
from utils.config import get_async_database

db = get_async_database()

# First, let's create a good system prompt for generating search-friendly prompt descriptions
SYSTEM_PROMPT = """
<system_prompt>
YOU ARE AN EXPERT AI PROMPT ENGINEER SPECIALIZING IN CREATING NATURAL, SEARCH-FRIENDLY DESCRIPTIONS FOR AI PROMPTS. YOUR PRIMARY OBJECTIVE IS TO CONVERT COMPLEX AI PROMPTS INTO CLEAR, ACCESSIBLE DESCRIPTIONS THAT CAN BE USED AS INPUT FOR VECTOR SEARCH SYSTEMS, ENABLING USERS TO DISCOVER THE MOST RELEVANT PROMPTS THROUGH NATURAL LANGUAGE QUERIES.

###GUIDELINES###

1. **FOCUS ON THE USE CASE:** Clearly articulate the primary purpose of the prompt and the specific problem it solves.
2. **SIMPLIFY THE LANGUAGE:** Use simple, non-technical language that is easy to understand for users with varying levels of expertise.
3. **INCLUDE SCENARIOS:** Provide relatable examples or scenarios where this prompt would be particularly useful.
4. **HIGHLIGHT CAPABILITIES:** Emphasize the key capabilities and outcomes enabled by the prompt, ensuring the description captures its full potential.
5. **USE RELEVANT KEYWORDS:** Naturally integrate keywords that users might search for, enhancing discoverability.
6. **AVOID JARGON:** Refrain from using technical jargon unless it is critical for understanding the prompt's functionality.
7. **BE USER-CENTRIC:** Maintain a conversational tone that resonates with the user, focusing on their needs and questions.

###PROCESS###

1. **UNDERSTAND THE PROMPT:**
   - Analyze the given AI prompt to identify its key features, functionality, and intended use.
   - Extract the core purpose and outcomes of the prompt.

2. **DESCRIBE THE USE CASE:**
   - Frame the description around the real-world applications of the prompt.
   - Highlight how it addresses user challenges or enhances their tasks.

3. **CRAFT NATURAL LANGUAGE DESCRIPTIONS:**
   - Write clear and engaging descriptions that provide users with a concise understanding of the prompt.
   - Focus on making the description searchable and relevant to a broad audience.

4. **OPTIMIZE FOR SEARCH:**
   - Incorporate user-friendly terms and phrases aligned with potential search queries.
   - Ensure the description is structured to rank highly in vector search systems.

5. **FINALIZE WITH USER INSIGHT:**
   - Ensure the description reflects the most user-relevant aspects of the prompt.
   - Verify that the description is free of ambiguity and technical complexity.

###WHAT NOT TO DO###

- **DO NOT USE OVERLY TECHNICAL LANGUAGE** that alienates users unfamiliar with AI concepts.
- **DO NOT CREATE GENERIC DESCRIPTIONS** that fail to highlight the unique aspects of the prompt.
- **DO NOT OMIT POTENTIAL USE CASES OR SCENARIOS**, as these are essential for user understanding.
- **DO NOT OVERLOAD WITH KEYWORDS** at the expense of natural readability.
- **DO NOT IGNORE USER PERSPECTIVE**, always prioritize making descriptions relatable and practical.

RESPOND WITH JUST THE DESCRIPTION - DO NOT INCLUDE ANY META-COMMENTARY, EXPLANATIONS, OR ADDITIONAL SECTIONS.
</system_prompt>

"""

async def fetch_prompts_from_mongodb(skip: int = 0, limit: int = 100) -> List[dict]:
    """
    Fetch prompts from MongoDB with pagination
    """
    try:
        cursor = db.prompts.find({}).skip(skip).limit(limit)
        prompts = await cursor.to_list(length=limit)
        return prompts
    except Exception as e:
        return []

async def generate_searchable_description(prompt_data: dict) -> str:
    """
    Generate a search-friendly description for the prompt using Groq
    """
    try:
        # Prepare input for the LLM
        input_text = f"""
Prompt Name - {prompt_data['name']}
Prompt Description - {prompt_data['description']}
Original Prompt - {prompt_data['prompts'].get('prompt1', '')}

CONVERT COMPLEX AI PROMPTS INTO CLEAR, ACCESSIBLE DESCRIPTIONS THAT CAN BE USED AS INPUT FOR VECTOR SEARCH SYSTEMS, ENABLING USERS TO DISCOVER THE MOST RELEVANT PROMPTS THROUGH NATURAL LANGUAGE QUERIES.
"""
        
        # Generate new description
        search_friendly_description = await groq_chat_completions(
            input=input_text,
            system_prompt=SYSTEM_PROMPT
        )

        return search_friendly_description.strip()
    except Exception as e:
        return None

async def upload_prompt_to_vector_db(batch_size: int = 1):
    """
    Main function to process prompts and upload to Pinecone
    """
    try:
        skip = 0
        total_processed = 0
        total_uploaded = 0
        
        while True:
            # Fetch batch of prompts from MongoDB
            prompts = await fetch_prompts_from_mongodb(skip=skip, limit=batch_size)
            if not prompts:
                break
                
            documents = []
            uuids = []
            
            # Process each prompt in the batch
            for prompt in prompts:
                try:
                    # Generate search-friendly description
                    # search_description = await generate_searchable_description(prompt)
                    # if not search_description:
                    #     continue
                    
                    # Create document for vector store
                    document = Document(
                        page_content=prompt.get("prompts", {}).get("prompt1", ""),
                        metadata={
                            "prompt_id": prompt["prompt_id"],
                            "name": prompt["name"],
                            "original_description": prompt["description"],
                            "uploaded_at": prompt["uploaded_at"].isoformat()
                        }
                    )
                    
                    documents.append(document)
                    uuids.append(prompt["prompt_id"])
                    
                except Exception as e:
                    continue
            
            # Upload batch to Pinecone
            if documents:
                # Using a fixed tenant_id for the prompt search engine
                tenant_id = "harsh90731"
                result = upload_documents(tenant_id, documents, uuids)
                
                if result:
                    total_uploaded += len(documents)
                
            total_processed += len(prompts)
            skip += batch_size
            
            
            # Optional: Add a small delay to prevent overloading
            await asyncio.sleep(1)
        
        return {
            "total_processed": total_processed,
            "total_uploaded": total_uploaded
        }
        
    except Exception as e:
        raise

# Example usage:
async def main():
    result = await upload_prompt_to_vector_db()
    print(f"Processing complete: {result}")

if __name__ == "__main__":
    asyncio.run(main())