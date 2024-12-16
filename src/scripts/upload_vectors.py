from typing import List
from langchain.schema import Document
import asyncio
import logging
from openai import OpenAI
from src.llm.pinecone_langchain import upload_documents
from utils.config import get_async_database
from utils.config import settings
import json
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import datetime
from enum import Enum
from utils.api_key_rotate import APIKeyManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db = get_async_database()

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

# First, let's create a good system prompt for generating search-friendly prompt descriptions get the response in json format with important fields such as category, tags, and searchable_description
SYSTEM_PROMPT = """<system_prompt>
YOU ARE AN ADVANCED AI METADATA GENERATION SPECIALIST, EXPERT IN CREATING HIGHLY SEARCHABLE AND PRECISE METADATA FOR PROMPT REPOSITORIES. YOUR ROLE IS TO ANALYZE RAW PROMPT DATA (INCLUDING NAME, DESCRIPTION, AND CONTENT) AND TRANSFORM IT INTO OPTIMIZED METADATA THAT MAXIMIZES SEARCHABILITY AND DISCOVERY IN A VECTOR SEARCH ENGINE.

YOUR PRIMARY OBJECTIVE IS TO ENHANCE THE FINDABILITY OF PROMPTS BY GENERATING METADATA THAT FOCUSES ON THE CORE INTENTS AND CAPABILITIES, INDEPENDENT OF HOW THE PROMPT IS STRUCTURED OR USED.

YOU MUST GENERATE:
1. **Category**: A single, most relevant domain or theme.
2. **Tags**: A set of targeted, diverse, and meaningful keywords.
3. **Searchable Description**: A semantically rich, detailed summary that captures the core intent, use cases, and capabilities, and anticipates varied user search queries, irrespective of the specific instructions or structure of the original prompt.

YOUR OUTPUT SHOULD:
- ACCURATELY REFLECT THE ESSENCE AND INTENDED APPLICATION OF THE PROMPT.
- EMPHASIZE THE CAPABILITIES AND PROBLEMS IT ADDRESSES, NOT THE INTERFACE.
- INCLUDE DOMAIN-SPECIFIC TERMINOLOGY, SYNONYMS, AND RELATED CONCEPTS.
- BE DESIGNED FOR SEMANTIC SEARCH, MATCHING USER INTENTS REGARDLESS OF SPECIFIC PHRASING.

---

### TASK REQUIREMENTS

1. **PROMPT ANALYSIS**:
   - ANALYZE THE GIVEN INPUT PROMPT DETAILS (NAME, DESCRIPTION, AND CONTENT).
   - DETERMINE THE CORE INTENT OF THE PROMPT - WHAT CAN IT DO? WHAT PROBLEM DOES IT SOLVE? WHAT IS IT CAPABLE OF GENERATING?
   - FOCUS ON THE CAPABILITIES OFFERED RATHER THAN THE INSTRUCTIONS OR USAGE STEPS.
   - IDENTIFY KEYWORDS, CONCEPTS, AND SPECIALIZED TERMINOLOGY RELATED TO THE CORE CAPABILITY.

2. **CATEGORY SELECTION**:
   - SELECT THE MOST APPROPRIATE CATEGORY FROM THE LIST BELOW:
     - **Creative**: For artistic, storytelling, and imaginative tasks.
     - **Professional**: For business, career, and workplace needs.
     - **Technical**: For programming, engineering, and technical solutions.
     - **Educational**: For learning, teaching, and academic purposes.
     - **Lifestyle**: For personal development, health, and daily living.
     - **Content**: For marketing, social media, and content creation.
     - **Analytical**: For problem-solving and strategic thinking.
     - **Communication**: For interpersonal and professional communication.
     - **Entertainment**: For games, leisure, and recreational activities.
     - **Utility**: For practical tools and automation tasks.

   - IF THE PROMPT SPANS MULTIPLE THEMES, SELECT THE MOST DOMINANT OR BROADEST CATEGORY RELATED TO THE PROMPT'S CAPABILITIES.

3. **TAG GENERATION**:
   - CREATE 5-10 RELEVANT TAGS THAT:
     - REPRESENT THE CORE FUNCTION AND CAPABILITIES OF THE PROMPT.
     - FOCUS ON SEARCHABLE KEYWORDS THAT USERS WOULD TYPICALLY USE, REGARDLESS OF PROMPT SPECIFICS.
     - INCLUDE DOMAIN-SPECIFIC AND GENERAL KEYWORDS, RELATED SYNONYMS.
     - COVER VARIOUS POTENTIAL SEARCH INTENTS, INCLUDING CONCEPTS, PROBLEM AREAS, SKILLS OR USE CASES.

4. **SEARCHABLE DESCRIPTION CREATION**:
   - SYNTHESIZE ALL INFORMATION INTO A SEMANTICALLY RICH, SEO-OPTIMIZED SUMMARY THAT FOCUSES ON:
     - **Core Capabilities**:  What the prompt is fundamentally capable of, regardless of instructions.
     - **Use Cases and Applications**: Focus on the real-world situations where the prompt is most useful.
     - **Problem Solved**:  What problems the prompt helps users overcome.
     - **Potential User Intents**:  Cover the reasons someone might search for this prompt.
     - **Relevant Terminology**: Include both general terms and domain-specific language.
     - **Related Concepts**: Mention what related concepts or prompts a user might be looking for.
   - ENSURE THE DESCRIPTION:
     - ANTICIPATES USER QUERIES FOCUSED ON 'WHAT' THE PROMPT DOES, NOT 'HOW' IT WORKS.
     - EMPHASIZES THE PROMPT'S VALUE AND POTENTIAL APPLICATIONS.
     - INCLUDES GENERAL AND SPECIFIC TERMS TO ENSURE BROAD COVERAGE FOR SEMANTIC SEARCH.
     - IS CLEAR, CONCISE, AND USES ACTION VERBS TO DESCRIBE CORE FUNCTIONALITY.
   - AVOID:
     - Prompt usage instructions
     - Command explanations
     - Technical prompt details

### OUTPUT FORMAT

RETURN THE METADATA IN THE FOLLOWING JSON FORMAT:
{
  "category": "STRING",
  "tags": ["STRING", "STRING", ...],
  "searchable_description": "STRING"
}

### EXAMPLES

#### INPUT EXAMPLE:
Prompt Name: AI-Powered Code Debugger
Prompt Description: A tool for debugging and optimizing Python code using AI assistance.
Prompt: You are a programming assistant specialized in identifying and resolving bugs in Python code. Provide suggestions for optimization and best practices.

#### OUTPUT EXAMPLE:
{
  "category": "Technical",
  "tags": ["python debugging", "AI code analysis", "code optimization", "debugging tools", "Python best practices", "programming error detection", "code refactoring", "software development"],
  "searchable_description": "An AI-driven tool for advanced Python code analysis, bug detection, and optimization. This prompt is designed for tasks such as debugging, refactoring, and enhancing the performance of Python software projects. It offers solutions for finding and fixing errors and applying best coding practices, improving code maintainability and efficiency in Python development environments."
}

#### INPUT EXAMPLE 2:
Prompt Name: Personalized Topology Tutor
Prompt Description: A learning assistant designed to teach advanced Topology using interactive methods.
Prompt: You are 'Cognix,' a personalized learning assistant specializing in Topology. Your focus is on the study of spatial properties under continuous transformations, including Point-Set and Algebraic Topology.

#### OUTPUT EXAMPLE 2:
{
  "category": "Educational",
  "tags": ["topology", "mathematical tutoring", "point-set topology", "algebraic topology", "mathematics education", "geometric math concepts", "advanced math study", "spatial analysis"],
  "searchable_description": "An educational prompt focused on the study of Topology and advanced mathematical spatial concepts, including Point-Set and Algebraic Topology. Ideal for students and learners who want to master spatial properties and transformations. Use this prompt for exploring geometric concepts, mathematical proofs and applications of Topology."
}
"""

async def fetch_prompts_from_mongodb(skip: int = 0, limit: int = 100) -> List[dict]:
    """
    Fetch prompts from MongoDB with pagination
    """
    try:
        cursor = db.prompts_unmodified.find({}).skip(skip).limit(limit)
        prompts = await cursor.to_list(length=limit)
        return prompts
    except Exception as e:
        logging.error(f"Error fetching prompts from MongoDB: {e}")
        return []

async def generate_searchable_description(prompt_data: dict, api_key_manager: APIKeyManager) -> Optional[dict]:
    """
    Generate a search-friendly description for the prompt using Groq with API key rotation
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            prompt_name = prompt_data["name"]
            prompt_description = prompt_data["description"]
            prompt_text = prompt_data["prompts"].get("prompt1", "")
            
            input_text = f"""
            Prompt Name: {prompt_name}
            Prompt Description: {prompt_description}
            Prompt: {prompt_text}
            
            Please generate a JSON object with the category, tags, and searchable description
            """
            
            # Get available API key
            current_api_key = api_key_manager.get_next_available_key()
            
            client = OpenAI(
                api_key=current_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            
            response = client.chat.completions.create(
                model="gemini-2.0-flash-exp",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": input_text}
                ],
                response_format={"type": "json_object"}
            )
            
            # Mark the key as used
            api_key_manager.use_key(current_api_key)
            
            if response.choices and response.choices[0].message.content:
                try:
                    parse = json.loads(response.choices[0].message.content)
                    logging.info(f"Successfully generated searchable description for: {prompt_name}")
                    return {
                        "name": prompt_data["name"],
                        "description": prompt_data["description"],
                        "category": parse.get("category"),
                        "tags": parse.get("tags", []),
                        "search_description": parse.get("searchable_description"),
                        "original_prompt": prompt_data["prompts"].get("prompt1", "")
                    }
                except json.JSONDecodeError as e:
                    logging.error(f"JSONDecodeError for prompt {prompt_data.get('name', 'N/A')}: {e}")
                    retry_count += 1
                    
        except Exception as e:
            logging.error(f"Error generating searchable description: {e} for prompt {prompt_data.get('name', 'N/A')}")
            if "rate_limit" in str(e).lower():
                logging.info(f"Rate limit reached for key {current_api_key}. Switching to next key.")
                retry_count += 1
                await asyncio.sleep(2)  # Small delay before retry
            else:
                retry_count += 1
    
    return None

async def upload_prompt_to_vector_db(batch_size: int = 1):
    """
    Main function to process prompts and upload to Pinecone and insert into mongodb
    """
    api_keys = [
        settings.GEMINI_API_KEY1,
        settings.GEMINI_API_KEY2,
        settings.GEMINI_API_KEY3,
        settings.GEMINI_API_KEY4,
        settings.GEMINI_API_KEY5
    ]
    api_key_manager = APIKeyManager(api_keys)
    try:
        skip = 0
        total_processed = 0
        total_uploaded = 0
        total_inserted = 0
        
        while True:
            # Fetch batch of prompts from MongoDB
            prompts = await fetch_prompts_from_mongodb(skip=skip, limit=batch_size)
            if not prompts:
                logging.info("No more prompts found in MongoDB. Exiting...")
                break
            
            documents = []
            uuids = []
            
            # Process each prompt in the batch
            for prompt in prompts:
                try:
                    # Generate search-friendly description
                    search_description = await generate_searchable_description(prompt, api_key_manager)
                    if not search_description:
                        logging.warning(f"Skipping prompt {prompt.get('name', 'N/A')} due to missing or invalid searchable description.")
                        continue
                        
                    # Insert prompt document in prompts_discover collection
                    prompt_data_for_insert = {
                        "prompt_id": prompt["prompt_id"],
                        "name": prompt["name"],
                        "description": prompt["description"],
                        "search_description": search_description["search_description"],
                        "category": search_description["category"],
                        "tags": search_description["tags"],
                        "created_at": datetime.datetime.now(datetime.UTC),
                        "updated_at": datetime.datetime.now(datetime.UTC),
                        "like_count":0,
                        "original_prompt": search_description["original_prompt"],
                        "is_public": True,
                        "author_id": "harsh90731"
                    }
                    
                    # Insert the document in the prompts_discover collection
                    insert_result = await db.prompts_discover.insert_one(prompt_data_for_insert)
                    
                    if insert_result.inserted_id:
                        total_inserted += 1
                        logging.info(f"Successfully inserted new prompt {prompt.get("prompt_id", "NA")} in prompts_discover")
                    else:
                         logging.warning(f"Failed to insert prompt {prompt.get("prompt_id", "NA")} in prompts_discover")
                         
                    # Create document for vector store
                    document = Document(
                        page_content=search_description["search_description"],
                        metadata={
                            "prompt_id": prompt["prompt_id"],
                            "name": prompt["name"],
                            "description": prompt["description"],
                            "category": search_description["category"],
                            "tags": search_description["tags"],
                            "created_at": datetime.datetime.now(datetime.UTC),
                            "prompt": search_description["original_prompt"],
                            "author_id": "harsh90731"
                        }
                    )
                    
                    documents.append(document)
                    uuids.append(prompt["prompt_id"])
                    
                except Exception as e:
                    logging.error(f"Error processing prompt {prompt.get('name', 'N/A')}: {e}")
                    continue
            
            # Upload batch to Pinecone
            if documents:
                try:
                # Using a fixed tenant_id for the prompt search engine
                   tenant_id = "harsh90731"
                   result = upload_documents(tenant_id, documents, uuids)
                    
                   if result:
                      total_uploaded += len(documents)
                      logging.info(f"Successfully uploaded {len(documents)} prompts to vector store.")
                   else:
                        logging.warning("Pinecone upload failed for the batch.")
                except Exception as e:
                    logging.error(f"Error uploading batch to Pinecone: {e}")
            else:
                logging.info("No document to upload to Pinecone")
                
            total_processed += len(prompts)
            skip += batch_size
            
            
            # Optional: Add a small delay to prevent overloading
            await asyncio.sleep(1)
        
        return {
            "total_processed": total_processed,
            "total_uploaded": total_uploaded,
            "total_inserted": total_inserted,
        }
        
    except Exception as e:
         logging.error(f"Error in main processing loop: {e}")
         raise

# Example usage:
async def main():
    result = await upload_prompt_to_vector_db(batch_size=10) # set batch_size
    print(f"Processing complete: {result}")

if __name__ == "__main__":
    asyncio.run(main())