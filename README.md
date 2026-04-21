# VOX_JOBS_AI

AI-powered jobs assistant built with FastAPI, Retrieval-Augmented Generation (RAG), and voice workflows.

The app can:
- fetch jobs from multiple sources,
- build a local ChromaDB vector store,
- answer job search queries with job cards,
- support real-time voice chat over WebSocket,
- run a voice-based mock interview flow.

## Project Highlights

- Backend: FastAPI (`application.py`)
- Retrieval: LangChain + ChromaDB + sentence-transformers embeddings
- LLM: OpenAI chat completions (`gpt-4.1-mini` in current code)
- Voice STT: faster-whisper
- Voice TTS: Groq TTS (Orpheus model)
- Data sources:
  - Mustaqbil API fetcher
  - Jobz.pk scraper

## Folder Structure

```text
VOX_JOBS_AI/
├─ application.py                # Main FastAPI app + endpoints + websocket handlers
├─ requirements.txt              # Python dependencies
├─ modal_llm_simple.py           # Optional Modal deployment helper
├─ test_modal_api.py             # Optional Modal endpoint test
├─ Routes/
│  ├─ fetch_mustaqbil_jobs.py    # Mustaqbil fetcher
│  ├─ fetch_jobz_jobs.py         # Jobz scraper
│  ├─ get_jobs_data.py           # Aggregate external jobs API into JSON
│  └─ vector_store.py            # Build ChromaDB from job JSON
├─ Security/
│  └─ security.py                # API key verification dependency
├─ utils/
│  ├─ chat_function.py           # RAG + LLM response generation
│  ├─ load_model.py              # Load Chroma retriever
│  ├─ voice_stt.py               # faster-whisper wrapper
│  ├─ voice_tts.py               # Groq TTS wrapper
│  ├─ mock_interview_llm.py      # Mock interview LLM flow
│  ├─ session_manager.py
│  └─ ...
├─ Scraped_Data/                 # JSON job datasets
└─ vector_store/all_jobs_db/     # Persistent ChromaDB files
```

## Prerequisites

- Python 3.10+ (3.11 recommended)
- Git
- Windows PowerShell (or any shell)
- API keys for services you plan to use:
  - OpenAI (required for chat + mock interview)
  - Groq (required for TTS in voice features)

## Setup Guide

### 1. Clone and enter project

```powershell
git clone <your-repo-url>
cd VOX_JOBS_AI
```

### 2. Create virtual environment

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create `.env`

Create a `.env` file in project root:

```env
# Security for protected fetch endpoints
API_KEY=your_internal_api_key
API_KEY_NAME=x-api-key

# OpenAI for text chat and mock interview
OPENAI_API_KEY=your_openai_key

# Groq for voice text-to-speech
GROQ_API_KEY=your_groq_key

# Mustaqbil fetcher base URL
API_URL=https://example.com/path/to/mustaqbil/api
```

Notes:
- `API_KEY` and `API_KEY_NAME` are used by `/fetch_jobs_mustaqbil` and `/fetch_jobs_jobz`.
- `OPENAI_API_KEY` is required by chat and mock interview modules.
- `GROQ_API_KEY` is required for voice responses (TTS).

## Run the App

```powershell
uvicorn application:application --reload --port 8000
```

Open:
- Swagger docs: `http://localhost:8000/docs`
- Voice chat test page: `http://localhost:8000/voice_chat_test`
- Mock interview test page: `http://localhost:8000/mock_interview_test`

## Recommended First Run Flow

### Option A: Use existing local data
If `Scraped_Data/all_jobs_data.json` and `vector_store/all_jobs_db` already exist, you can run chat directly.

### Option B: Refresh data + rebuild vector store

1. Fetch source jobs (protected endpoints):
```http
GET /fetch_jobs_mustaqbil
GET /fetch_jobs_jobz
```
Provide header named by `API_KEY_NAME` with value `API_KEY`.

2. Build combined dataset + vector DB:
```http
GET /create_vector_store
```
This triggers:
- dataset refresh into `Scraped_Data/all_jobs_data.json`
- vector embedding + Chroma persistence into `vector_store/all_jobs_db`

## Main API Endpoints

### HTTP
- `GET /` : health/welcome message
- `POST /dummy_apply_jobs` and `POST /apply/run` : dummy apply background task
- `GET /fetch_jobs_mustaqbil` : fetch Mustaqbil jobs (API-key protected)
- `GET /fetch_jobs_jobz` : scrape Jobz jobs (API-key protected)
- `GET /create_vector_store` : refresh JSON + rebuild ChromaDB
- `POST /chat_response_jobs` : text chat response with job cards
- `GET /voice_chat_test` : in-browser voice chat UI
- `GET /mock_interview_test` : in-browser mock interview UI

### WebSocket
- `WS /ws/voice_chat` : real-time voice assistant (PCM streaming, STT, RAG response, TTS)
- `WS /ws/mock_interview_voice` : real-time mock interview voice session

## Voice Features Notes

- STT uses `faster-whisper` on CPU by default.
- TTS uses Groq and requires `GROQ_API_KEY`.
- First transcription/model load can be slower due to model initialization.

## Troubleshooting

- `401 Unauthorized` on fetch endpoints:
  - Check `API_KEY` and `API_KEY_NAME` in `.env`
  - Ensure request header name/value are correct

- Vector store load fails:
  - Run `GET /create_vector_store`
  - Confirm `Scraped_Data/all_jobs_data.json` exists and is valid JSON

- Voice response missing audio:
  - Confirm `GROQ_API_KEY` is set
  - Check server logs for TTS errors

- OpenAI errors:
  - Confirm `OPENAI_API_KEY` is valid and has model access

## Optional: Modal Deployment

The repository includes:
- `modal_llm_simple.py`
- `QUICK_MODAL_GUIDE.md`
- `test_modal_api.py`

Use these if you want to host an LLM endpoint on Modal instead of local/provider-direct patterns.

## Development Notes

- CORS is currently wide open (`allow_origins=["*"]`) in `application.py`.
- Before production deployment, restrict CORS and rotate API keys.
- Consider splitting `application.py` into routers/modules for easier maintenance.
