from openai import OpenAI
import os

# Initialize OpenAI client for rephrasing.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def rephrase_question_jobs(prompt, query):
    """
    Rephrase function specifically for job search queries.
    Uses English language model understanding for job-related queries.
    """
    response = client.chat.completions.create(
            model="gpt-4.1-mini",
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