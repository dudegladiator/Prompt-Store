from uuid import uuid4
from datetime import datetime
import json
import pandas as pd
from typing import List, Dict, Any
import asyncio
from utils.config import get_async_database

db = get_async_database()

async def upload_prompts(prompts_data: List[Dict[str, Any]]):
    """
    Upload prompts to the database with specified formatting and validations
    
    Args:
        prompts_data: List of dictionaries containing prompt information
    
    Returns:
        tuple: (success_count, failed_count, error_list)
    """
    success_count = 0
    failed_count = 0
    error_list = []
    
    current_timestamp = datetime.utcnow()
    
    async def process_prompt(prompt_item: Dict[str, Any]):
        try:
            # Extract base information
            name = prompt_item.get('name')
            description = prompt_item.get('description')
            prompts_dict = prompt_item.get('prompts', {})
            
            # Validate required fields
            if not all([name, description, prompts_dict]):
                raise ValueError(f"Missing required fields for prompt: {name}")
            
            # Clean and validate prompts
            cleaned_prompts = {}
            current_key = 1
            
            # Sort prompts by their original number to maintain order
            sorted_prompts = sorted(
                prompts_dict.items(),
                key=lambda x: int(x[0].replace('prompt', ''))
            )
            
            for orig_key, value in sorted_prompts:
                # Skip if value is NaN or None
                if pd.isna(value) or value is None:
                    continue
                    
                # Replace TracyOS with Cognix
                cleaned_value = str(value).replace('TracyOS', 'Cognix')
                
                # Add to cleaned prompts with reorganized keys
                cleaned_prompts[f"prompt{current_key}"] = cleaned_value
                current_key += 1
            
            # If no valid prompts after cleaning, skip this item
            if not cleaned_prompts:
                raise ValueError(f"No valid prompts found for: {name}")
            
            # Prepare document for insertion
            document = {
                "prompt_id": str(uuid4()),
                "name": name,
                "description": description,
                "prompts": cleaned_prompts,
                "uploaded_at": current_timestamp,
                "like_count": 0
            }
            
            # Insert into database
            await db.prompts_unmodified.insert_one(document)
            
            return True, None
            
        except Exception as e:
            return False, f"Error processing prompt '{name}': {str(e)}"
    
    # Process all prompts concurrently
    tasks = [process_prompt(prompt) for prompt in prompts_data]
    results = await asyncio.gather(*tasks)
    
    # Count successes and failures
    for success, error in results:
        if success:
            success_count += 1
        else:
            failed_count += 1
            error_list.append(error)
    
    return success_count, failed_count, error_list

# Function to load and process the JSON file
async def load_and_upload_prompts(file_path: str):
    """
    Load prompts from JSON file and upload to database
    
    Args:
        file_path: Path to the JSON file containing prompts
    """
    try:
        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as file:
            prompts_data = json.load(file)
        
        # Upload prompts
        success_count, failed_count, errors = await upload_prompts(prompts_data)
        
        # Print results
        print(f"Upload Complete:")
        print(f"Successfully uploaded: {success_count}")
        print(f"Failed uploads: {failed_count}")
        
        if errors:
            print("\nErrors encountered:")
            for error in errors:
                print(f"- {error}")
                
    except Exception as e:
        print(f"Error loading file: {str(e)}")


async def main():
    await load_and_upload_prompts('/teamspace/studios/this_studio/fun/Prompt-Search-Engine/prompts.json')

if __name__ == "__main__":
    asyncio.run(main())



















# import pandas as pd
# import json

# # Load the CSV file into a DataFrame
# df = pd.read_csv('/teamspace/studios/this_studio/fun/Prompt-Search-Engine/Prompts.csv')  # Replace with your CSV file path

# # Prepare JSON structure
# json_data = []
# for index, row in df.iterrows():
#     json_data.append({
#         "name": row['Name'],  # Replace 'Name' with the actual column name in your CSV
#         "description": row['Description'],  # Replace 'Description' with the actual column name
#         "prompts": {f"prompt{i-1}": value for i, (col, value) in enumerate(row.items()) if col not in ['Name', 'Description']}
#     })

# # Convert to JSON format
# json_output = json.dumps(json_data, indent=4)

# # Save to a JSON file or print
# with open('prompts.json', 'w') as f:
#     f.write(json_output)