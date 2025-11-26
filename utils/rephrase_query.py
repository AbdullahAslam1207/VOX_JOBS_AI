from groq import Groq
import os

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def rephrase_question_jobs(prompt, query):
    """
    Rephrase function specifically for job search queries.
    Uses English language model understanding for job-related queries.
    """
    response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.3
        )
    print("Jobs rephrase response:", response)
    
    chat_response = response.choices[0].message.content.strip()
    
    # Return the direct rephrased query without markers
    return chat_response