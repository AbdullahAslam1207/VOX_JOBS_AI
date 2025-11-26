from groq import Groq
from utils.jobs_prompts import digital_assistant_jobs_prompt
from utils.normalize_history import build_chat_prompt
import os

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
    
    # Get complete response using Groq (no streaming)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": conv_prompt},
            {"role": "user", "content": query}
        ],
        stream=False,
    )
    
    complete_response = response.choices[0].message.content
    print('Jobs response completed')
    
    # Return the complete response
    return {"response": complete_response, "status": 200}
