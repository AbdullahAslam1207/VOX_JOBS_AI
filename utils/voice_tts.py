"""
Voice TTS (Text-to-Speech) utility using Groq
Handles text-to-speech conversion for voice responses
"""

import os
from groq import Groq
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceTTS:
    """
    Text-to-Speech handler using Groq's Orpheus TTS model
    Supports high-quality English audio generation with vocal directions
    """
    
    def __init__(self, model="canopylabs/orpheus-v1-english", voice="troy", response_format="wav"):
        """
        Initialize the Groq TTS client
        
        Args:
            model: TTS model to use (default: orpheus-v1-english)
            voice: Voice to use (options: troy, etc.)
            response_format: Audio format (wav, mp3, etc.)
        """
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=api_key)
        self.model = model
        self.voice = voice
        self.response_format = response_format
        
        logger.info(f"Groq TTS initialized with model: {model}, voice: {voice}")
    
    def text_to_speech(self, text, output_path=None):
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file. If None, returns audio bytes
            
        Returns:
            bytes: Audio data if output_path is None
            str: Path to saved file if output_path is provided
        """
        try:
            if not text or text.strip() == "":
                logger.warning("Empty text provided to TTS")
                return None
            
            logger.info(f"Generating TTS for text: {text[:50]}...")
            
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format=self.response_format
            )
            
            # If output path is provided, save to file
            if output_path:
                response.write_to_file(output_path)
                logger.info(f"TTS audio saved to: {output_path}")
                return output_path
            else:
                # Return audio bytes directly
                # Note: response object may have read() method or be iterable
                audio_bytes = response.read() if hasattr(response, 'read') else response.content
                logger.info(f"TTS audio generated: {len(audio_bytes)} bytes")
                return audio_bytes
                
        except Exception as e:
            logger.error(f"Error generating TTS: {str(e)}")
            raise Exception(f"TTS generation failed: {str(e)}")
    
    def text_to_speech_stream(self, text):
        """
        Convert text to speech and return as stream/bytes
        Suitable for WebSocket streaming
        
        Args:
            text: Text to convert to speech
            
        Returns:
            bytes: Audio data
        """
        return self.text_to_speech(text, output_path=None)


# Singleton instance for reuse across requests
_tts_instance = None

def get_tts_instance():
    """
    Get or create singleton TTS instance
    
    Returns:
        VoiceTTS: Shared TTS instance
    """
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = VoiceTTS()
        logger.info("TTS instance created")
    return _tts_instance
