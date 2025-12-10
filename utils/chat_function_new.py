import requests
from utils.jobs_prompts import digital_assistant_jobs_prompt
from utils.normalize_history import build_chat_prompt
import os
import re
import json

# Modal API endpoint
MODAL_API_URL = "https://am0055461--vox-jobs-llm-chat-completions.modal.run"


def parse_response_with_cards(complete_response):
    """
    Parse the AI response to extract message and job cards.
    
    Args:
        complete_response: String containing message and __CARDS__ with JSON array
        
    Returns:
        dict: {
            "message": str (text before __CARDS__),
            "jobs": list (parsed JSON array after __CARDS__)
        }
    """
    try:
        # Split response by __CARDS__
        if "__CARDS__" in complete_response:
            parts = complete_response.split("__CARDS__", 1)
            message = parts[0].strip()
            
            # Extract and parse the JSON array
            json_part = parts[1].strip()
            # Remove any markdown code blocks if present
            json_part = json_part.replace("```json", "").replace("```", "").strip()
            
            # Fix double curly braces (LLM sometimes escapes braces)
            json_part = json_part.replace("{{", "{").replace("}}", "}")
            
            # Parse JSON
            jobs = json.loads(json_part)
            
            return {
                "message": message,
                "jobs": jobs
            }
        else:
            # If no __CARDS__ found, return entire response as message
            return {
                "message": complete_response.strip(),
                "jobs": []
            }
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"JSON part was: {json_part}")
        return {
            "message": complete_response,
            "jobs": []
        }
    except Exception as e:
        print(f"Error parsing response: {e}")
        return {
            "message": complete_response,
            "jobs": []
        }

def chat_jobs(chat_history, retriever, query):
    """
    Chat function for Jobs chatbot using the jobs_store vector store.
    Provides job search responses based on retrieved job listings.
    Does NOT use streaming - returns complete response.
    
    Args:
        chat_history: Previous conversation history
        retriever: ChromaDB retriever for jobs_store
        query: User's current query
    
    Returns:
        dict: Complete response with text and job cards
    """
    
    
    # Retrieve relevant documents from the vector store
    docs = retriever.invoke(query)
    
    print(f"Total retrieved docs for Jobs: {len(docs)}")
    
    # Build context from retrieved documents
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # Build chat history prompt
    chat_history_text = build_chat_prompt(chat_history)
    
    # Replace placeholders in the prompt
    conv_prompt = (
        digital_assistant_jobs_prompt
        .replace("{chat_history}", chat_history_text)
        .replace("{context}", context)
        .replace("{question}", query)
    )
    
    # Get complete response using Modal-hosted LLM
    payload = {
        "model": "llama",
        "messages": [
            {"role": "system", "content": conv_prompt},
            {"role": "user", "content": query}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    print("Sending request to Modal LLM...")
    
    try:
        response = requests.post(MODAL_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        response_data = response.json()
        complete_response = response_data['choices'][0]['message']['content']
        complete_response = parse_response_with_cards(complete_response)
        complete_response["message"] = re.sub(r'TEXT_MESSAGE', '', complete_response["message"], flags=re.IGNORECASE).strip()
        print('Jobs response completed')
        
    except requests.exceptions.Timeout:
        raise Exception("Modal API request timed out after 120 seconds")
    except Exception as e:
        raise Exception(f"Modal API error: {str(e)}")
    
    # Return the complete response
    return {"response": complete_response, "status": 200}