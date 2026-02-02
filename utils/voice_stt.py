"""
Voice STT (Speech-to-Text) utility using faster-whisper
Handles streaming audio chunks and transcription
"""

import io
import numpy as np
from faster_whisper import WhisperModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceSTT:
    """
    Speech-to-Text handler using faster-whisper
    Supports streaming audio chunks for real-time transcription
    """
    
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Initialize the Whisper model
        
        Args:
            model_size: Model size (tiny, base, small, medium, large-v2)
            device: Device to run on (cpu, cuda)
            compute_type: Compute type (int8, float16, float32)
        """
        logger.info(f"Loading Whisper model: {model_size} on {device}")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Whisper model loaded successfully")
    
    def transcribe_audio(self, audio_data, language="en"):
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Audio data as bytes (WAV, MP3, etc.)
            language: Language code (en, es, fr, etc.)
            
        Returns:
            str: Transcribed text
        """
        try:
            # Convert bytes to numpy array
            # Assuming 16kHz, 16-bit PCM audio
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_array,
                language=language,
                beam_size=5,
                vad_filter=True,  # Voice Activity Detection
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Collect all segments
            transcription = " ".join([segment.text for segment in segments])
            
            logger.info(f"Transcription completed: {transcription[:100]}...")
            return transcription.strip()
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def transcribe_audio_file(self, audio_path, language="en"):
        """
        Transcribe audio from file path
        
        Args:
            audio_path: Path to audio file
            language: Language code
            
        Returns:
            str: Transcribed text
        """
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                vad_filter=True
            )
            
            transcription = " ".join([segment.text for segment in segments])
            return transcription.strip()
            
        except Exception as e:
            logger.error(f"File transcription error: {str(e)}")
            raise Exception(f"Failed to transcribe file: {str(e)}")


# Global instance (lazy loaded)
_stt_instance = None


def get_stt_instance():
    """Get or create the global STT instance"""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = VoiceSTT(model_size="base", device="cpu", compute_type="int8")
    return _stt_instance
