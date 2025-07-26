import asyncio
import json
import logging
import numpy as np
import webrtcvad
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer, Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
import librosa
import soundfile as sf
from pathlib import Path
import io
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Socially - Real-time Audio Analysis")

# Global variables for models
asr_model = None
asr_tokenizer = None
emotion_model = None
emotion_feature_extractor = None
vad = None

# Audio configuration
SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30  # 30ms frames for VAD
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

class AudioBuffer:
    def __init__(self):
        self.buffer = []
        self.is_speaking = False
        self.silence_frames = 0
        self.speech_frames = 0
        self.min_speech_frames = 10  # Minimum frames to consider as speech
        self.max_silence_frames = 20  # Max silence frames before ending speech

    def add_frame(self, frame_data, is_speech):
        self.buffer.extend(frame_data)
        
        if is_speech:
            self.speech_frames += 1
            self.silence_frames = 0
            if not self.is_speaking and self.speech_frames >= self.min_speech_frames:
                self.is_speaking = True
                logger.info("Speech started")
        else:
            self.silence_frames += 1
            if self.is_speaking and self.silence_frames >= self.max_silence_frames:
                self.is_speaking = False
                logger.info("Speech ended")
                return True  # Signal to process the buffer
        
        return False

    def get_audio_data(self):
        if len(self.buffer) > 0:
            audio_data = np.array(self.buffer, dtype=np.float32)
            self.clear()
            return audio_data
        return None

    def clear(self):
        self.buffer = []
        self.speech_frames = 0
        self.silence_frames = 0

def load_models():
    """Load all required models"""
    global asr_model, asr_tokenizer, emotion_model, emotion_feature_extractor, vad
    
    try:
        logger.info("Loading ASR model...")
        asr_tokenizer = Wav2Vec2Tokenizer.from_pretrained("facebook/wav2vec2-base-960h")
        asr_model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
        
        logger.info("Loading emotion recognition model...")
        # Use a pre-trained emotion model from Hugging Face
        emotion_model = Wav2Vec2ForSequenceClassification.from_pretrained("ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")
        emotion_feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")
        
        logger.info("Initializing VAD...")
        vad = webrtcvad.Vad(2)  # Aggressiveness level 2 (0-3)
        
        logger.info("All models loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        raise

def transcribe_audio(audio_data):
    """Transcribe audio using Wav2Vec2"""
    try:
        # Ensure audio is the right format
        if len(audio_data) < SAMPLE_RATE * 0.5:  # Less than 0.5 seconds
            return ""
        
        # Tokenize and predict
        input_values = asr_tokenizer(audio_data, sampling_rate=SAMPLE_RATE, return_tensors="pt", padding=True).input_values
        
        with torch.no_grad():
            logits = asr_model(input_values).logits
        
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = asr_tokenizer.batch_decode(predicted_ids)[0]
        
        return transcription.strip()
        
    except Exception as e:
        logger.error(f"Error in transcription: {e}")
        return ""

def analyze_emotion(audio_data):
    """Analyze emotion from audio"""
    try:
        if len(audio_data) < SAMPLE_RATE * 0.5:  # Less than 0.5 seconds
            return "neutral"
        
        # Extract features
        inputs = emotion_feature_extractor(audio_data, sampling_rate=SAMPLE_RATE, return_tensors="pt", padding=True)
        
        with torch.no_grad():
            logits = emotion_model(**inputs).logits
        
        predicted_class_id = logits.argmax().item()
        
        # Map to emotion labels (these are typical emotion categories)
        emotion_labels = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
        
        if predicted_class_id < len(emotion_labels):
            return emotion_labels[predicted_class_id]
        else:
            return "neutral"
            
    except Exception as e:
        logger.error(f"Error in emotion analysis: {e}")
        return "neutral"

def process_audio_chunk(chunk_data):
    """Process a chunk of audio data with VAD"""
    try:
        # Convert bytes to numpy array
        audio_np = np.frombuffer(chunk_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Resample to 16kHz if needed
        if len(audio_np) > 0:
            # For VAD, we need 16-bit PCM data
            pcm_data = (audio_np * 32768).astype(np.int16).tobytes()
            
            # Check if this frame contains speech
            is_speech = vad.is_speech(pcm_data[:FRAME_SIZE*2], SAMPLE_RATE)  # VAD expects bytes
            
            return audio_np, is_speech
        
        return None, False
        
    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")
        return None, False

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    load_models()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    audio_buffer = AudioBuffer()
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            
            # Process the audio chunk
            audio_chunk, is_speech = process_audio_chunk(data)
            
            if audio_chunk is not None:
                # Add to buffer and check if we should process
                should_process = audio_buffer.add_frame(audio_chunk, is_speech)
                
                if should_process:
                    # Get accumulated audio data
                    audio_data = audio_buffer.get_audio_data()
                    
                    if audio_data is not None and len(audio_data) > 0:
                        logger.info(f"Processing audio segment of length: {len(audio_data)}")
                        
                        # Run transcription and emotion analysis
                        transcription = transcribe_audio(audio_data)
                        emotion = analyze_emotion(audio_data)
                        
                        # Send results back to client
                        result = {
                            "transcription": transcription,
                            "emotion": emotion,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                        
                        await websocket.send_text(json.dumps(result))
                        logger.info(f"Sent result: {result}")
                        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass

# Serve static files (frontend)
if os.path.exists("fe/dist"):
    app.mount("/static", StaticFiles(directory="fe/dist"), name="static")
    
    @app.get("/")
    async def read_index():
        return FileResponse("fe/dist/index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "models_loaded": asr_model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
