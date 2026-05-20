# Video Analyzer Agent

An intelligent A2A (Agent-to-Agent) video analysis agent that processes videos, extracts frames, transcribes audio, and answers questions based strictly on video content.

## Features

- 🎬 **Video Processing**: Handles videos up to 2GB
- 🖼️ **Frame Extraction**: Captures key frames from videos
- 🎤 **Audio Transcription**: Uses Whisper AI for accurate transcription
- 🤖 **AI-Powered Analysis**: PydanticAI with Claude 4.5 Sonnet via SAP Gen AI Hub
- 📊 **Grounded Responses**: Answers based only on video content
- 🔄 **A2A Protocol**: Full Agent-to-Agent protocol support
- 📈 **Telemetry**: Built-in AI Core token tracking

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  Video Analyzer  │────▶│  SAP Gen AI Hub │
│  (Upload & Chat)│     │  Agent (A2A)     │     │  (Claude 4.5)   │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │ Video Processing │
                        │ - Frame Extract  │
                        │ - Whisper AI     │
                        └──────────────────┘
```

## Prerequisites

- Python 3.13+
- FFmpeg
- SAP AI Core credentials
- Docker (for containerized deployment)

## Installation

### Local Development

1. **Install system dependencies**:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg libsm6 libxext6 libxrender-dev libgomp1 libglib2.0-0
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your SAP AI Core credentials
```

4. **Run the agent**:
```bash
python app/main.py --port 5000
```

### Docker Deployment

```bash
docker build -t video-analyzer-agent \
  --build-arg ARTIFACTORY_USER=your-user \
  --build-arg ARTIFACTORY_TOKEN=your-token .

docker run -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/videos:/app/videos \
  video-analyzer-agent
```

## API Endpoints

### Upload Video
```bash
POST /upload-video
Content-Type: multipart/form-data

# Response
{
  "status": "success",
  "metadata": {
    "filename": "video.mp4",
    "duration_seconds": 120.5,
    "width": 1920,
    "height": 1080,
    "size_mb": 45.2
  },
  "frames_extracted": 20,
  "transcription_language": "en"
}
```

### Health Check
```bash
GET /health

# Response
{
  "status": "healthy",
  "agent": "Video Analyzer Agent",
  "video_loaded": true
}
```

### A2A Agent Card
```bash
GET /.well-known/agent.json
```

## Usage

1. **Upload a video** (up to 2GB)
2. **Wait for processing** (frame extraction + transcription)
3. **Ask questions** about the video content
4. **Get grounded answers** based only on what's in the video

## Example Questions

- "Summarize this video"
- "What are the main concepts explained?"
- "What happens at timestamp 2:30?"
- "Teach me the key topics from this video"
- "List the important points covered"

## Configuration

### Environment Variables

```bash
# SAP AI Core
AICORE_CLIENT_ID=your-client-id
AICORE_CLIENT_SECRET=your-client-secret
AICORE_AUTH_URL=https://your-auth-url
AICORE_BASE_URL=https://your-ai-core-url
AICORE_RESOURCE_GROUP=default

# Server
HOST=0.0.0.0
PORT=5000

# Video Processing
VIDEO_STORAGE_PATH=/app/videos
MAX_VIDEO_SIZE_GB=2
```

## Application Foundation Deployment

Deploy to SAP Application Foundation using the provided `app.yaml`:

```bash
# Deploy using AppFND CLI or CI/CD pipeline
# The app.yaml configures:
# - 4GB memory limit for video processing
# - 10GB persistent volume for video storage
# - Claude 4.5 Sonnet model
# - JWT authentication
```

## Project Structure

```
video-agent/
├── app/
│   ├── main.py              # A2A server + FastAPI endpoints
│   ├── agent.py             # PydanticAI video analyzer agent
│   ├── agent_executor.py    # A2A protocol executor
│   └── video_processor.py   # Video processing utilities
├── app.yaml                 # Application Foundation config
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## Technologies

- **PydanticAI**: Modern AI agent framework
- **LiteLLM**: LLM gateway for SAP Gen AI Hub
- **A2A SDK**: Agent-to-Agent protocol
- **OpenCV**: Frame extraction
- **Whisper AI**: Audio transcription
- **MoviePy**: Video processing
- **FastAPI**: REST API endpoints
- **Application Foundation SDK**: Telemetry & AI Core integration

## Limitations

- Maximum video size: 2GB
- Supported formats: MP4, AVI, MOV, MKV, WEBM
- Agent responses are grounded only to video content
- Processing time depends on video length and size

## License

Copyright © SAP SE