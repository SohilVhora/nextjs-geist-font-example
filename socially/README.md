# Socially - Real-time Audio Transcription & Emotion Analysis

A proof-of-concept web application that captures audio from a user's microphone, streams it to a backend server, and performs real-time transcription and emotion analysis using machine learning models.

## Features

- **Real-time Audio Capture**: Captures audio from user's microphone using Web Audio API
- **Voice Activity Detection**: Uses WebRTC VAD to detect when user is speaking
- **Speech Recognition**: Transcribes audio using Facebook's Wav2Vec2 model
- **Emotion Analysis**: Analyzes speaker's emotion using pre-trained Wav2Vec2 classification model
- **WebSocket Communication**: Real-time bidirectional communication between frontend and backend
- **Modern UI**: Clean, responsive interface built with React and TypeScript
- **Containerized**: Single Docker image for easy deployment

## Technology Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- Modern CSS with Google Fonts
- WebSocket client for real-time communication
- MediaRecorder API for audio capture

### Backend
- FastAPI with Python 3.10
- WebSocket server for real-time communication
- Transformers library for ML models
- WebRTC VAD for voice activity detection
- Librosa for audio processing

### Models
- **ASR**: `facebook/wav2vec2-base-960h` for speech recognition
- **Emotion**: `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition` for emotion classification

## Quick Start

### Using Docker (Recommended)

1. **Clone and build the application:**
   ```bash
   git clone <repository-url>
   cd socially
   docker build -t socially-app .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 socially-app
   ```

3. **Access the application:**
   Open your browser and navigate to `http://localhost:8000`

### Development Setup

#### Backend Setup
```bash
cd socially/backend
pip install -r requirements.txt
python main.py
```

#### Frontend Setup
```bash
cd socially/frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000` and will connect to the backend at `http://localhost:8000`.

## Usage Instructions

1. **Grant Microphone Permission**: Click "Start Recording" and allow microphone access when prompted
2. **Speak Clearly**: The system uses voice activity detection to automatically process speech segments
3. **View Results**: Transcription and emotion analysis will appear in real-time below the controls
4. **Stop Recording**: Click "Stop Recording" when finished

## API Endpoints

- `GET /health` - Health check endpoint
- `WebSocket /ws` - Real-time audio streaming and processing

## Architecture

```
┌─────────────────┐    WebSocket     ┌──────────────────┐
│   React Frontend│ ◄──────────────► │  FastAPI Backend │
│                 │                  │                  │
│ • Audio Capture │                  │ • VAD Processing │
│ • WebSocket     │                  │ • ASR (Wav2Vec2) │
│ • UI Display    │                  │ • Emotion Model  │
└─────────────────┘                  └──────────────────┘
```

## Audio Processing Pipeline

1. **Audio Capture**: MediaRecorder captures audio in 250ms chunks
2. **Voice Activity Detection**: WebRTC VAD detects speech segments
3. **Buffering**: Audio is buffered until end of speech is detected
4. **Transcription**: Wav2Vec2 model transcribes the audio segment
5. **Emotion Analysis**: Classification model analyzes emotional content
6. **Results**: JSON response sent back via WebSocket

## Supported Emotions

- Happy
- Sad
- Angry
- Neutral
- Fear
- Surprise
- Disgust

## Browser Compatibility

- Chrome 66+
- Firefox 60+
- Safari 14+
- Edge 79+

**Note**: Requires HTTPS in production for microphone access.

## Performance Considerations

- Models are loaded once at startup
- Audio processing is done in real-time
- WebSocket connection handles multiple concurrent users
- Docker image includes all dependencies for offline operation

## Troubleshooting

### Common Issues

1. **Microphone Access Denied**
   - Ensure you're using HTTPS (required for microphone access)
   - Check browser permissions for microphone access

2. **WebSocket Connection Failed**
   - Verify the backend is running on port 8000
   - Check firewall settings

3. **No Transcription Results**
   - Speak clearly and loudly enough for VAD to detect
   - Ensure audio input is working in your browser

4. **Docker Build Issues**
   - Ensure you have sufficient disk space (image is ~3GB)
   - Check Docker daemon is running

### Logs

View application logs:
```bash
docker logs <container-id>
```

## Development

### Project Structure
```
socially/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── requirements.txt     # Python dependencies
│   └── models/             # Model files directory
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # Main React component
│   │   ├── components/     # React components
│   │   └── App.css         # Styles
│   ├── package.json        # Node dependencies
│   └── vite.config.ts      # Vite configuration
├── Dockerfile              # Multi-stage Docker build
└── .github/workflows/      # CI/CD pipeline
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker build
5. Submit a pull request

## License

This project is a proof-of-concept for educational purposes.

## Acknowledgments

- Facebook AI for Wav2Vec2 models
- Hugging Face for model hosting and transformers library
- WebRTC project for voice activity detection
