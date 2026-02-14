import httpx
import json
import asyncio
import numpy as np
from pathlib import Path
from fastapi import FastAPI, Depends, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from Routes.fetch_mustaqbil_jobs import fetch_jobs
from Routes.fetch_jobz_jobs import fetch_jobz_jobs
from Security.security import verify_api_key
from Routes.get_jobs_data import fetch_and_save_jobs
from Routes.vector_store import create_chroma_db_from_jobs
from utils.load_model import load_jobs_vector_store
from utils.chat_function import chat_jobs
from utils.rephrase_query import rephrase_question_jobs
from utils.jobs_prompts import rephrase_query_prompt_jobs
from utils.normalize_history import clean_and_parse
from utils.voice_stt import get_stt_instance
from utils.voice_tts import get_tts_instance
from utils.session_manager import session_manager
import subprocess
import os
import requests
import sys
import logging



load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

application = FastAPI()

# Enable CORS for all origins (customize as needed)
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@application.get("/")
def home():
    return {"message": "Welcome to VoxJobs AI home route!"}




@application.get("/fetch_jobs_mustaqbil")
async def fetch_jobs_mustaqbil(api_key: str = Depends(verify_api_key)):
    result = await fetch_jobs()
    return result


@application.get("/fetch_jobs_jobz")
async def fetch_jobs_jobz(api_key: str = Depends(verify_api_key)):
    result = await fetch_jobz_jobs()
    return result
    


@application.get("/create_vector_store")
async def create_vector_store():
    #first get data 
    print("Vector store creation started...")
    result = fetch_and_save_jobs()

    #then create vector store
    result = create_chroma_db_from_jobs()
    return result



@application.post("/chat_response_jobs")
async def chat_response_jobs(request: Request):
    """
    Chat endpoint for Jobs chatbot using jobs_store vector store.
    Provides job search responses based on job listings database.
    Does not use streaming - returns complete response.
    """
    print("chat api jobs is hit")
    
    # Step 1: Parse request
    data = await request.json()
    chat_history = data.get("user_query", [])
    query = data.get("query", "")
    
    # Step 2: Rephrase query based on chat history
    if chat_history:
        previous_user_message = chat_history[-1].get("userMessage", "")
        previous_bot_message = chat_history[-1].get("botResponse", "")
    else:
        previous_user_message = ""
        previous_bot_message = ""
    
    # print(f"Received jobs query: {query}")
    # print(f"Previous message: {previous_user_message}")
    
    if previous_bot_message:
        previous_bot_message = clean_and_parse(previous_bot_message)
        # print(f"clean bot message: {previous_bot_message}")
        
        # Create rephrase prompt for jobs using job-specific prompt
        updated_rephrase_query_prompt_jobs = rephrase_query_prompt_jobs.replace("{previous_query}", previous_user_message)
        updated_rephrase_query_prompt_jobs = updated_rephrase_query_prompt_jobs.replace("{previous_bot_response}", previous_bot_message)
        
        # Rephrase the query using job-specific function
        query = rephrase_question_jobs(updated_rephrase_query_prompt_jobs, query)
        print(f"rephrased jobs query: {query}")

    # Step 3: Load vector store
    retriever = load_jobs_vector_store()
    if retriever is None:
        return {
            "response": "",
            "status": 500,
            "error": "Failed to load jobs vector store"
        }

    retriever = retriever.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    print("Jobs ChromaDB retriever loaded successfully")

    try:
        return chat_jobs(chat_history, retriever, query)
    except Exception as e:
        print(f"The error is {str(e)}")
        return {"response": "", "status": 500, "error": str(e)}


@application.websocket("/ws/voice_chat")
async def voice_chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for voice chat with PCM streaming
    Handles streaming PCM16 audio chunks, transcribes using STT, and processes with LLM
    
    Protocol:
    1. Client connects and receives session_id
    2. Client sends PCM16 audio chunks as binary data (real-time streaming)
    3. Client sends {"action": "end"} to trigger transcription
    4. Server responds with transcription and LLM response
    5. Client sends {"action": "clear"} to clear chat history
    """
    await websocket.accept()
    logger.info("Voice chat WebSocket connection established")
    
    # Create session
    session_id = session_manager.create_session()
    await websocket.send_json({"type": "session_created", "session_id": session_id})
    logger.info(f"Session created: {session_id}")
    
    # Audio buffer for accumulating PCM16 chunks
    audio_buffer = bytearray()
    
    try:
        while True:
            # Receive message from client
            message = await websocket.receive()
            
            # Handle binary PCM16 audio data
            if "bytes" in message:
                audio_chunk = message["bytes"]
                audio_buffer.extend(audio_chunk)
                # Don't send acknowledgment for every chunk (too much overhead)
            
            # Handle text commands
            elif "text" in message:
                data = json.loads(message["text"])
                action = data.get("action")
                
                # Process accumulated PCM audio
                if action == "end":
                    if len(audio_buffer) == 0:
                        await websocket.send_json({
                            "type": "error",
                            "message": "No audio data to process"
                        })
                        continue
                    
                    logger.info(f"Processing PCM audio buffer: {len(audio_buffer)} bytes")
                    
                    try:
                        # Step 1: Convert PCM16 to float32 and transcribe
                        await websocket.send_json({"type": "status", "message": "Transcribing audio..."})
                        
                        import numpy as np
                        
                        # Make a copy of the buffer to avoid resize issues
                        audio_data = bytes(audio_buffer)
                        
                        # Convert PCM16 bytes to numpy float32 array
                        pcm_int16 = np.frombuffer(audio_data, dtype=np.int16).copy()
                        pcm_float32 = pcm_int16.astype(np.float32) / 32768.0
                        
                        # Clear buffer immediately after copying
                        audio_buffer.clear()
                        
                        logger.info(f"Converted to numpy array: {len(pcm_float32)} samples")
                        
                        # Transcribe using faster-whisper
                        stt = get_stt_instance()
                        
                        # Transcribe directly from numpy array
                        segments, info = stt.model.transcribe(
                            pcm_float32,
                            language="en",
                            beam_size=5,
                            vad_filter=True,
                            vad_parameters=dict(min_silence_duration_ms=500)
                        )
                        
                        transcription = " ".join([segment.text for segment in segments]).strip()
                        
                        logger.info(f"Transcription: {transcription}")
                        await websocket.send_json({
                            "type": "transcription",
                            "text": transcription
                        })
                        
                        if not transcription or transcription.strip() == "":
                            await websocket.send_json({
                                "type": "error",
                                "message": "Could not transcribe audio. Please try again."
                            })
                            continue
                        
                        # Step 2: Get chat history
                        chat_history = session_manager.get_chat_history(session_id)
                        
                        # Step 3: Rephrase query if there's history
                        query = transcription
                        if chat_history:
                            previous_user_message = chat_history[-1].get("userMessage", "")
                            previous_bot_message = chat_history[-1].get("botResponse", "")
                            
                            if previous_bot_message:
                                previous_bot_message = clean_and_parse(previous_bot_message)
                                
                                updated_rephrase_query_prompt = rephrase_query_prompt_jobs.replace("{previous_query}", previous_user_message)
                                updated_rephrase_query_prompt = updated_rephrase_query_prompt.replace("{previous_bot_response}", previous_bot_message)
                                
                                query = rephrase_question_jobs(updated_rephrase_query_prompt, transcription)
                                logger.info(f"Rephrased query: {query}")
                        
                        # Step 4: Load vector store
                        await websocket.send_json({"type": "status", "message": "Processing your query..."})
                        retriever = load_jobs_vector_store()
                        
                        if retriever is None:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Failed to load jobs vector store"
                            })
                            audio_buffer.clear()
                            continue
                        
                        retriever = retriever.as_retriever(search_type="similarity", search_kwargs={"k": 5})
                        
                        # Step 5: Get response from LLM
                        result = chat_jobs(chat_history, retriever, query)
                        
                        if result.get("status") == 200:
                            response_data = result.get("response", {})
                            bot_message = response_data.get("message", "")
                            jobs = response_data.get("jobs", [])
                            
                            # Display jobs JSON on terminal
                            if jobs:
                                logger.info("=" * 50)
                                logger.info("📋 JOBS CARDS DATA:")
                                logger.info(json.dumps(jobs, indent=2))
                                logger.info("=" * 50)
                            
                            # Add to session history
                            session_manager.add_message(session_id, transcription, bot_message)
                            
                            # Step 6: Generate TTS audio for bot_message (text before __CARDS__)
                            try:
                                await websocket.send_json({"type": "status", "message": "Generating speech..."})
                                
                                tts = get_tts_instance()
                                audio_bytes = tts.text_to_speech_stream(bot_message)
                                
                                if audio_bytes:
                                    logger.info(f"TTS audio generated: {len(audio_bytes)} bytes")
                                    
                                    # Send text response first
                                    await websocket.send_json({
                                        "type": "response",
                                        "transcription": transcription,
                                        "message": bot_message,
                                        "jobs": jobs
                                    })
                                    
                                    # Then send audio
                                    await websocket.send_bytes(audio_bytes)
                                    
                                    logger.info("Response and audio sent successfully")
                                else:
                                    # Send without audio if TTS failed
                                    await websocket.send_json({
                                        "type": "response",
                                        "transcription": transcription,
                                        "message": bot_message,
                                        "jobs": jobs
                                    })
                                    logger.warning("TTS generated no audio, sent text only")
                                    
                            except Exception as tts_error:
                                logger.error(f"TTS error: {str(tts_error)}")
                                # Send text response even if TTS fails
                                await websocket.send_json({
                                    "type": "response",
                                    "transcription": transcription,
                                    "message": bot_message,
                                    "jobs": jobs
                                })
                                logger.info("Response sent without audio due to TTS error")
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": result.get("error", "Failed to get response")
                            })
                        
                    except Exception as e:
                        logger.error(f"Error processing audio: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Error: {str(e)}"
                        })
                        # Clear buffer on error
                        audio_buffer.clear()
                
                # Clear chat history
                elif action == "clear":
                    session_manager.clear_session(session_id)
                    session_id = session_manager.create_session()
                    await websocket.send_json({
                        "type": "session_created",
                        "session_id": session_id,
                        "message": "Chat history cleared"
                    })
                    logger.info(f"Chat history cleared, new session: {session_id}")
                
                # Get chat history
                elif action == "get_history":
                    chat_history = session_manager.get_chat_history(session_id)
                    await websocket.send_json({
                        "type": "history",
                        "chat_history": chat_history
                    })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        session_manager.clear_session(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


@application.get("/voice_chat_test", response_class=HTMLResponse)
async def voice_chat_test():
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>VoxJobs Voice Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: Segoe UI, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .container {
            background: white;
            border-radius: 20px;
            width: 800px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            text-align: center;
        }

        .chat-area {
            flex: 1;
            padding: 20px;
            background: #f5f5f5;
            overflow-y: auto;
        }

        .message { margin-bottom: 15px; }
        .message.user { text-align: right; }
        .message.bot { text-align: left; }

        .message-bubble {
            display: inline-block;
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 70%;
        }

        .message.user .message-bubble {
            background: #667eea;
            color: white;
        }

        .message.bot .message-bubble {
            background: white;
            border: 1px solid #ddd;
        }

        .status-area {
            padding: 10px;
            text-align: center;
            background: #d1ecf1;
        }

        .controls {
            padding: 15px;
            display: flex;
            justify-content: center;
            gap: 10px;
        }

        button {
            padding: 12px 20px;
            border-radius: 25px;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }

        #recordBtn { background: #28a745; color: white; }
        #recordBtn.recording { background: #dc3545; }

        #clearBtn { background: #6c757d; color: white; }

        .connection-status {
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 10px;
        }

        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h2>🎙️ VoxJobs Voice Chat</h2>
        <span id="connectionStatus" class="connection-status disconnected">Disconnected</span>
    </div>

    <div class="chat-area" id="chatArea">
        <div class="message bot">
            <div class="message-bubble">
                Welcome! Click "Start Speaking", talk, then click "Stop Speaking" when done.
            </div>
        </div>
    </div>

    <div class="status-area" id="statusArea">Ready. PCM Streaming Mode.</div>

    <div class="controls">
        <button id="recordBtn">
            <span>🎤</span>
            <span>Start Speaking</span>
        </button>
        <button id="clearBtn">
            <span>🗑</span>
            <span>Clear</span>
        </button>
    </div>
</div>

<script>
console.log("🚀 Script loaded - PCM Streaming Mode");

let ws;
let audioContext;
let processor;
let input;
let stream;
let isRecording = false;

const recordBtn = document.getElementById("recordBtn");
const clearBtn = document.getElementById("clearBtn");
const chatArea = document.getElementById("chatArea");
const statusArea = document.getElementById("statusArea");
const connectionStatus = document.getElementById("connectionStatus");

function updateStatus(msg) {
    statusArea.textContent = msg;
}

function connectWebSocket() {
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${location.host}/ws/voice_chat`;

    console.log("Connecting to", wsUrl);
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("✅ WebSocket connected");
        connectionStatus.textContent = "Connected";
        connectionStatus.className = "connection-status connected";
        updateStatus("Connected. Click Start Speaking.");
    };

    ws.onmessage = (event) => {
        // Handle binary audio data
        if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
            console.log("🔊 Received audio data");
            playAudio(event.data);
            return;
        }
        
        // Handle JSON messages
        const data = JSON.parse(event.data);
        console.log("⬇️", data);

        if (data.type === "transcription") {
            addMessage(data.text, "user");
        }

        if (data.type === "response") {
            addMessage(data.message, "bot");
            
            // Display jobs if available
            if (data.jobs && data.jobs.length > 0) {
                console.log("📋 Jobs:", data.jobs);
                // Optionally display job cards in UI
            }
            
            updateStatus("Ready.");
        }

        if (data.type === "error") {
            updateStatus("Error: " + data.message);
        }
        
        if (data.type === "status") {
            updateStatus(data.message);
        }
    };

    ws.onclose = () => {
        console.log("❌ WebSocket closed");
        connectionStatus.textContent = "Disconnected";
        connectionStatus.className = "connection-status disconnected";
    };
}

recordBtn.onclick = async () => {
    if (!isRecording) {
        // Start recording
        try {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            input = audioContext.createMediaStreamSource(stream);
            
            processor = audioContext.createScriptProcessor(4096, 1, 1);
            
            processor.onaudioprocess = (event) => {
                if (!isRecording) return;
                
                const floatData = event.inputBuffer.getChannelData(0);
                const pcm16 = float32ToPCM16(floatData);
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(pcm16);
                }
            };
            
            input.connect(processor);
            processor.connect(audioContext.destination);
            
            isRecording = true;
            recordBtn.classList.add("recording");
            const btnText = recordBtn.querySelector("span:last-child");
            if (btnText) btnText.textContent = "Stop Speaking";
            updateStatus("🎤 Recording... Click to stop.");
            
        } catch (e) {
            console.error(e);
            updateStatus("Mic error: " + e.message);
        }
    } else {
        // Stop recording
        isRecording = false;
        
        if (processor) processor.disconnect();
        if (input) input.disconnect();
        if (audioContext) audioContext.close();
        if (stream) stream.getTracks().forEach(t => t.stop());
        
        ws.send(JSON.stringify({ action: "end" }));
        
        recordBtn.classList.remove("recording");
        const btnText = recordBtn.querySelector("span:last-child");
        if (btnText) btnText.textContent = "Start Speaking";
        updateStatus("Processing audio...");
    }
};

clearBtn.onclick = () => {
    ws.send(JSON.stringify({ action: "clear" }));
    chatArea.innerHTML = "";
};

function addMessage(text, sender) {
    const div = document.createElement("div");
    div.className = `message ${sender}`;
    div.innerHTML = `<div class="message-bubble">${text}</div>`;
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Play audio received from server
function playAudio(audioData) {
    try {
        // Convert to Blob if it's ArrayBuffer
        const blob = audioData instanceof Blob ? audioData : new Blob([audioData], { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(blob);
        
        const audio = new Audio(audioUrl);
        audio.play().then(() => {
            console.log("🔊 Playing audio");
            updateStatus("🔊 Playing response...");
        }).catch(err => {
            console.error("Audio play error:", err);
            updateStatus("Audio play failed: " + err.message);
        });
        
        // Clean up URL after playing
        audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
            updateStatus("Ready.");
        };
        
    } catch (err) {
        console.error("Error playing audio:", err);
        updateStatus("Audio error: " + err.message);
    }
}

// Float32 to PCM16 converter
function float32ToPCM16(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    
    let offset = 0;
    for (let i = 0; i < float32Array.length; i++, offset += 2) {
        let sample = Math.max(-1, Math.min(1, float32Array[i]));
        view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
    }
    return buffer;
}

connectWebSocket();
</script>
</body>
</html>
"""
    return HTMLResponse(html_content)
