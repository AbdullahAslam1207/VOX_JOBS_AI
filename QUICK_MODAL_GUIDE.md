# Quick Modal Deployment Guide

## The Issue
vLLM doesn't work on Windows, but that's OK! You don't need to install vLLM locally. Modal will handle all dependencies in the cloud.

## Solution: Use the Simple Deployment

I've created **`modal_llm_simple.py`** which uses Transformers instead of vLLM. It's:
- ✅ Easier to deploy
- ✅ Works from Windows
- ✅ Uses A10G GPU (cheaper than A100)
- ✅ Still fast enough for production

## Quick Steps

### 1. Install Modal (only this!)
```powershell
pip install modal
```

### 2. Authenticate
```powershell
modal token new
```

### 3. Set up HuggingFace Token (for Llama models)
Get your token from: https://huggingface.co/settings/tokens

```powershell
modal secret create huggingface HUGGING_FACE_HUB_TOKEN="hf_your_token_here"
```

**Note:** If you want to use Mistral (no token needed), edit `modal_llm_simple.py`:
```python
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.3"
# And remove or comment out the secrets line:
# secrets=[modal.Secret.from_name("huggingface")],
```

### 4. Deploy
```powershell
modal deploy modal_llm_simple.py
```

This will:
- Upload the code to Modal
- Build the container with all dependencies (torch, transformers, etc.)
- Deploy to GPU
- Give you a URL

### 5. Get Your Endpoint
After deployment, you'll see:
```
✓ Created web function chat_completions => https://username--vox-jobs-llm-chat-completions.modal.run
```

**Copy this URL!**

### 6. Test It
```powershell
# PowerShell test
$body = @{
    model = "llama"
    messages = @(
        @{
            role = "user"
            content = "What is Python?"
        }
    )
    temperature = 0.7
    max_tokens = 200
} | ConvertTo-Json

Invoke-RestMethod -Uri "YOUR_MODAL_URL_HERE" -Method Post -Body $body -ContentType "application/json"
```

### 7. Update Your App

Edit `chat_function.py`:

```python
# Change this line at the top:
MODAL_API_URL = "https://your-actual-modal-url.modal.run"

# And update the chat function to use non-streaming:
payload = {
    "model": "llama",
    "messages": [
        {"role": "system", "content": conv_prompt},
        {"role": "user", "content": query}
    ],
    "temperature": 0.7,
    "max_tokens": 2048
}

response = requests.post(MODAL_API_URL, json=payload)
response.raise_for_status()
response_data = response.json()

complete_response = response_data['choices'][0]['message']['content']
```

## Choose Your Model

In `modal_llm_simple.py`, you can use:

### Option 1: Llama 3.1 (Best quality, needs HF token)
```python
MODEL_NAME = "meta-llama/Meta-Llama-3.1-8B-Instruct"
secrets=[modal.Secret.from_name("huggingface")]  # Keep this
```

### Option 2: Mistral (Good quality, no token needed)
```python
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.3"
# Remove or comment: secrets=[modal.Secret.from_name("huggingface")]
```

### Option 3: Llama 2 (Older but works, needs HF token)
```python
MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"
secrets=[modal.Secret.from_name("huggingface")]  # Keep this
```

## GPU Options

Current setting: **A10G** (good balance of cost/performance)

You can change in the file:
```python
GPU_CONFIG = modal.gpu.A10G()  # Current - ~$1/hour
# or
GPU_CONFIG = modal.gpu.A100(memory=40)  # Faster but expensive - ~$3/hour
# or  
GPU_CONFIG = modal.gpu.T4()  # Cheapest - ~$0.60/hour (slower)
```

## Troubleshooting

### "No module named modal"
```powershell
pip install modal
```

### "Authentication required"
```powershell
modal token new
```

### "Model gated" or "Access denied"
1. Go to https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct
2. Click "Agree and access repository"
3. Get your token from https://huggingface.co/settings/tokens
4. Run: `modal secret create huggingface HUGGING_FACE_HUB_TOKEN="your_token"`

### "Out of memory"
Change to a smaller model or upgrade GPU:
```python
GPU_CONFIG = modal.gpu.A100(memory=40)
```

## Cost Estimates

Modal charges:
- **A10G**: ~$1.10/hour (only when running)
- **Container idle**: Free for 5 minutes, then scales to zero
- **Cold start**: First request takes ~30s to load model

**Tip:** With the 5-minute idle timeout, if you get requests every few minutes, the container stays warm and responses are instant!

## View Logs
```powershell
modal app logs vox-jobs-llm
```

## Stop Deployment
```powershell
modal app stop vox-jobs-llm
```

## Important Notes

1. **First request is slow** (~30-60 seconds) - Modal needs to load the model
2. **Subsequent requests are fast** (~1-3 seconds) if within idle timeout
3. **Auto-scales to zero** when idle - you only pay for actual usage
4. **No Windows installation needed** - everything runs in Modal's cloud

You're now ready to deploy! Just run:
```powershell
modal deploy modal_llm_simple.py
```
