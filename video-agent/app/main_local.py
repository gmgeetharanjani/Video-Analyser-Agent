"""
A2A Server for Video Analyzer Agent with video upload endpoint - Local Development Version
"""

import logging
import os
import ssl
from pathlib import Path
from dotenv import load_dotenv

# Load .env file before anything else (handles special characters safely)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=False)

# Disable SSL verification for corporate networks with self-signed certificates
# This is needed for Whisper model downloads and LLM API calls
ssl._create_default_https_context = ssl._create_unverified_context
os.environ.setdefault("PYTHONHTTPSVERIFY", "0")
os.environ.setdefault("CURL_CA_BUNDLE", "")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")

import click
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_local import VideoAnalyzerAgent
from agent_executor import VideoAnalyzerExecutor
from video_processor import VideoProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_env_var(key: str, default: str = "") -> str:
    """Get an environment variable or return a default value."""
    return os.environ.get(key, default)


# Server configuration
HOST = get_env_var("HOST", "0.0.0.0")
PORT = int(get_env_var("PORT", "8080"))

# Global instances
video_processor = VideoProcessor()
video_agent = VideoAnalyzerAgent()


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8080, help="Port to bind to")
def main(host: str = HOST, port: int = PORT):
    """Start the Video Analyzer A2A agent server."""
    logger.info("Starting Video Analyzer A2A server (Local Development Mode)")
    logger.info(f"Using HOST: {host}")
    logger.info(f"Using PORT: {port}")

    # Create FastAPI app for video upload
    app = FastAPI(title="Video Analyzer Agent")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Agent capabilities
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
    )

    # Agent skill definition
    skill = AgentSkill(
        id="video-analyzer-agent",
        name="Video Analyzer Agent",
        description=(
            "An AI agent that analyzes videos by extracting frames, transcribing audio, "
            "and answering questions based strictly on the video content. Capable of "
            "summarizing videos, explaining concepts, and teaching material presented in videos."
        ),
        tags=[
            "video-analysis", "video-processing", "transcription", "teaching",
            "education", "content-analysis", "a2a", "pydantic-ai"
        ],
        examples=[
            "Summarize this video for me",
            "What concepts are explained in this video?",
            "What happens at timestamp 2:30?",
            "Teach me the main topic covered in this video",
            "What is shown in the video frames?",
            "Can you explain the key points from the video?",
        ],
    )

    # Agent card (metadata)
    agent_card = AgentCard(
        name="Video Analyzer Agent",
        description=(
            "An intelligent video analysis agent that processes videos up to 2GB in size. "
            "Extracts visual frames, transcribes audio content, and provides grounded answers "
            "based strictly on the video content. Perfect for learning from video tutorials, "
            "understanding presentations, and getting insights from recorded content."
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=[skill],
    )

    # Task store for managing conversation state
    task_store = InMemoryTaskStore()

    # Request handler with agent executor
    request_handler = DefaultRequestHandler(
        agent_executor=VideoAnalyzerExecutor(video_agent),
        task_store=task_store,
    )

    # Add video upload endpoint BEFORE mounting A2A (mount at "/" catches everything)
    @app.post("/upload-video")
    async def upload_video(file: UploadFile = File(...)):
        """Upload and process a video file."""
        try:
            MAX_SIZE = 2 * 1024 * 1024 * 1024  # 2GB in bytes
            contents = await file.read()
            file_size = len(contents)

            if file_size > MAX_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is 2GB, got {file_size / (1024**3):.2f}GB"
                )

            logger.info(f"Received video upload: {file.filename} ({file_size / (1024**2):.2f}MB)")

            video_path = video_processor.save_video(contents, file.filename)

            logger.info("Processing video...")
            video_data = video_processor.process_video(video_path, num_frames=20)

            video_agent.set_video_context(video_data)

            logger.info("Video processing complete")

            return {
                "status": "success",
                "message": "Video processed successfully",
                "metadata": video_data["metadata"],
                "frames_extracted": len(video_data["frames"]),
                "transcription_language": video_data["transcription"]["language"],
                "transcription_length": len(video_data["transcription"]["text"])
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error processing video")
            raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "agent": "Video Analyzer Agent",
            "video_loaded": video_agent.video_context is not None
        }

    @app.get("/video-status")
    async def video_status():
        """Get current video processing status."""
        if video_agent.video_context:
            return {
                "video_loaded": True,
                "metadata": video_agent.video_context["metadata"]
            }
        return {"video_loaded": False}

    from pydantic import BaseModel as PydanticBaseModel

    class ChatRequest(PydanticBaseModel):
        message: str
        context_id: str = "default"

    @app.post("/chat")
    async def chat(request: ChatRequest):
        """Simple REST chat endpoint - sends a message and returns the agent response."""
        if not video_agent.video_context:
            return {"response": "⚠️ No video has been processed yet. Please upload a video first."}

        final_response = ""
        async for item in video_agent.stream(request.message, request.context_id):
            if item.get("is_task_complete"):
                final_response = item.get("content", "")
                break
            elif not final_response:
                final_response = item.get("content", "")

        return {"response": final_response}

    # Create A2A server application
    a2a_server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    # Mount A2A server LAST (mounting at "/" catches all unmatched routes)
    app.mount("/", a2a_server.build())

    logger.info(f"Starting server at http://{host}:{port}")
    logger.info(f"Upload endpoint: http://{host}:{port}/upload-video")
    logger.info(f"Health check: http://{host}:{port}/health")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()