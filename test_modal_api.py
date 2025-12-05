"""
Quick test script for Modal LLM API
"""
import requests
import time

# Modal API endpoint
MODAL_API_URL = "https://am0055461--vox-jobs-llm-chat-completions.modal.run"

def test_modal_api():
    """Test the Modal API with a simple request"""
    
    payload = {
        "model": "llama",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Keep responses brief."},
            {"role": "user", "content": "Say hello in one sentence."}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    print("Sending test request to Modal...")
    print(f"URL: {MODAL_API_URL}")
    
    start_time = time.time()
    
    try:
        response = requests.post(MODAL_API_URL, json=payload)
        
        elapsed_time = time.time() - start_time
        print(f"\n✓ Response received in {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            
            print("\n" + "="*50)
            print("RESPONSE:")
            print("="*50)
            print(content)
            print("="*50)
            
        else:
            print(f"\n✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n✗ Request timed out after 120 seconds")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing Modal LLM API")
    print("="*50 + "\n")
    test_modal_api()
