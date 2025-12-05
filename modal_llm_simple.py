"""
Modal deployment for LLM inference using Transformers
This is a simpler alternative that doesn't require vLLM
"""

import modal

# Create a Modal app
app = modal.App("vox-jobs-llm")

# Define the image with required dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.1.0",
        "transformers==4.44.0",  # Updated for Llama 3.1 support
        "accelerate==0.25.0",
        "huggingface_hub",
        "bitsandbytes",
        "fastapi[standard]",
    )
)

# Define GPU configuration
GPU_CONFIG = modal.gpu.A10G()  # A10G is cheaper and works well for 7B-8B models

# Model configuration
MODEL_NAME = "meta-llama/Meta-Llama-3.1-8B-Instruct"
# Alternative models you can use:
# "mistralai/Mistral-7B-Instruct-v0.3"
# "meta-llama/Llama-2-7b-chat-hf"


@app.cls(
    gpu=GPU_CONFIG,
    image=image,
    secrets=[modal.Secret.from_name("huggingface")],  # HuggingFace token for gated models
    container_idle_timeout=300,
    timeout=600,
)
class Model:
    @modal.enter()
    def setup(self):
        """Load the model when container starts"""
        import torch
        import os
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        # Get HuggingFace token from environment
        hf_token = os.environ.get("HUGGING_FACE_TOKEN")
        
        print(f"Loading model: {MODEL_NAME}")
        print(f"Using HF token: {'Yes' if hf_token else 'No'}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            token=hf_token
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_8bit=True,  # Use 8-bit quantization to save memory
            token=hf_token
        )
        
        print("Model loaded successfully!")

    @modal.method()
    def generate(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048):
        """Generate response from messages"""
        import torch
        
        # Format messages using the tokenizer's chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens if max_tokens > 0 else 2048,
                temperature=temperature,
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode
        response = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )
        
        return response


@app.function(image=image)
@modal.web_endpoint(method="POST")
def chat_completions(request: dict):
    """
    OpenAI-compatible chat completions endpoint
    
    Request format:
    {
        "model": "llama",
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    """
    messages = request.get("messages", [])
    temperature = request.get("temperature", 0.7)
    max_tokens = request.get("max_tokens", 2048)
    
    if max_tokens == -1:
        max_tokens = 2048
    
    # Get model instance and generate
    model = Model()
    response_text = model.generate.remote(messages, temperature, max_tokens)
    
    # Return OpenAI-compatible response
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop",
                "index": 0
            }
        ],
        "model": request.get("model", "llama"),
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


@app.local_entrypoint()
def main():
    """Test the deployment"""
    model = Model()
    
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python? Answer in one sentence."}
    ]
    
    print("Testing model generation...")
    response = model.generate.remote(test_messages)
    print(f"\nResponse: {response}")
