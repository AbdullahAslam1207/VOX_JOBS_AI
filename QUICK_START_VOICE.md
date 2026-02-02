# Quick Start - Voice Chat Installation

## Installation Steps

### 1. Install faster-whisper
```bash
pip install faster-whisper
```

### 2. Verify Installation
```bash
python verify_voice_setup.py
```

### 3. Run the Application
```bash
uvicorn application:application --reload --port 8000
```

### 4. Test Voice Chat
Open your browser and go to:
```
http://localhost:8000/voice_chat_test
```

## What to Expect

### First Run
- Whisper model will download (~150MB for base model)
- This is a one-time download
- Takes 2-5 minutes depending on internet speed

### Using Voice Chat
1. Click "Start Speaking" button
2. Speak your job search query clearly
3. **Stop talking and wait** - it will automatically detect 2 seconds of silence
4. Audio is automatically processed when silence is detected
5. Wait for:
   - ✅ Audio transcription
   - ✅ LLM processing  
   - ✅ Job results
6. Continue the conversation!

## Testing the Setup

Run this in terminal:
```bash
python -c "import faster_whisper; print('✓ faster-whisper installed')"
```

## Troubleshooting

### If faster-whisper fails to install:
```bash
# Try with specific version
pip install faster-whisper==1.1.0

# Or with verbose output
pip install faster-whisper -v
```

### If you get CUDA errors:
```bash
# Install CPU-only version
pip install faster-whisper --no-deps
pip install av
pip install tokenizers
```

### If WebSocket connection fails:
- Check if port 8000 is available
- Try: `uvicorn application:application --reload --port 8001`
- Update URL to: `http://localhost:8001/voice_chat_test`

## Quick Test Commands

```bash
# Check all imports
python verify_voice_setup.py

# Start server
uvicorn application:application --reload --port 8000

# In another terminal, test connection
python -c "import websocket; print('WebSocket library ready')"
```

## URLs

- **Voice Chat UI**: http://localhost:8000/voice_chat_test
- **Regular Chat**: http://localhost:8000/chat_response_jobs
- **WebSocket**: ws://localhost:8000/ws/voice_chat
- **API Docs**: http://localhost:8000/docs

## Next Steps

1. Install dependencies
2. Run verify script
3. Start the server
4. Open voice chat UI
5. Grant microphone permissions
6. Start talking!

For detailed documentation, see:
- `VOICE_CHAT_README.md` - Full documentation
- `VOICE_IMPLEMENTATION_SUMMARY.md` - Technical details
