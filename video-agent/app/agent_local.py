"""
Video Analyzer Agent using LiteLLM directly - Local Development Version
Analyzes videos and answers questions based on video content.
"""

import logging
import os
import ssl
import warnings
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Optional, Dict, Any

# Disable SSL verification for corporate networks with self-signed certificates
ssl._create_default_https_context = ssl._create_unverified_context
os.environ.setdefault("PYTHONHTTPSVERIFY", "0")
os.environ.setdefault("CURL_CA_BUNDLE", "")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")

import litellm
litellm.ssl_verify = False

warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from the agent."""
    status: Literal["input_required", "completed", "error"]
    message: str


class VideoAnalyzerAgent:
    """
    Video Analyzer Agent using LiteLLM directly.
    Analyzes video content and answers questions grounded in the video.
    """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        """Initialize the Video Analyzer Agent."""
        self.model_name = 'sap/anthropic--claude-4.5-sonnet'
        self.system_prompt = self._get_system_prompt()
        self.video_context: Optional[Dict[str, Any]] = None

    def set_video_context(self, video_data: Dict[str, Any]) -> None:
        """Set the video context for the agent."""
        self.video_context = video_data
        logger.info(f"Video context set: {video_data['metadata']['filename']}")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Video Analyzer agent."""
        return """You are a Video Analyzer Agent, an expert at understanding and teaching video content.

## Your Capabilities:

1. **Video Analysis**: You can analyze videos by examining:
   - Visual frames extracted at key moments
   - Complete audio transcription with timestamps
   - Video metadata (duration, resolution, etc.)

2. **Teaching & Explanation**: You excel at:
   - Summarizing video content clearly and concisely
   - Explaining concepts presented in the video
   - Breaking down complex topics into understandable parts
   - Providing step-by-step explanations
   - Answering questions about specific moments in the video

3. **Grounded Responses**: You MUST:
   - Base ALL answers strictly on the video content provided
   - Reference specific timestamps when discussing audio content
   - Refer to specific frames when discussing visual content
   - Never make up information not present in the video
   - Clearly state if a question cannot be answered from the video content

## Response Guidelines:

- Be clear, accurate, and educational
- Use timestamps to reference specific moments (e.g., "At 2:35...")
- Describe visual elements when relevant
- Quote or paraphrase the transcription when discussing spoken content
- If asked about something not in the video, politely explain that you can only discuss the video content
- Structure longer explanations with headings and bullet points
- Be patient and thorough when teaching concepts

## Important Constraints:

❌ DO NOT invent information not present in the video
❌ DO NOT discuss topics outside the video content
❌ DO NOT make assumptions about content not shown or said
✅ DO reference specific evidence from frames or transcription
✅ DO admit when information is not available in the video
✅ DO provide timestamps and frame references"""

    def _build_context_prompt(self, query: str) -> str:
        """Build a prompt with video context."""
        if not self.video_context:
            return f"No video has been processed yet. Please upload and process a video first.\n\nUser query: {query}"

        metadata = self.video_context['metadata']
        transcription = self.video_context['transcription']
        frames = self.video_context['frames']

        context_parts = [
            "# VIDEO CONTEXT",
            "",
            "## Video Metadata:",
            f"- Filename: {metadata['filename']}",
            f"- Duration: {metadata['duration_seconds']} seconds",
            f"- Resolution: {metadata['width']}x{metadata['height']}",
            f"- FPS: {metadata['fps']}",
            f"- Size: {metadata['size_mb']} MB",
            "",
            "## Audio Transcription:",
            f"Language: {transcription['language']}",
            "",
            "Full Transcript:",
            transcription['text'],
            "",
            "Timestamped Segments:",
        ]

        for seg in transcription['segments'][:50]:
            context_parts.append(
                f"[{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text']}"
            )

        context_parts.extend([
            "",
            f"## Visual Frames: ({len(frames)} frames extracted)",
            "Frame timestamps:",
        ])

        for frame in frames:
            context_parts.append(
                f"- Frame at {frame['timestamp']}s (frame #{frame['frame_number']})"
            )

        context_parts.extend([
            "",
            "---",
            "",
            "## User Question:",
            query,
            "",
            "Please answer based ONLY on the video content above. Reference specific timestamps and frames when relevant."
        ])

        return "\n".join(context_parts)

    async def stream(
        self, query: str, context_id: str
    ) -> AsyncGenerator[dict, None]:
        """Stream responses from the agent."""
        if not self.video_context:
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": "⚠️ No video has been processed yet. Please upload and process a video first before asking questions.",
            }
            return

        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "🎬 Analyzing video content to answer your question...",
        }

        try:
            context_prompt = self._build_context_prompt(query)

            response = await litellm.acompletion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context_prompt},
                ],
            )

            answer = response.choices[0].message.content

            # Log token usage
            if hasattr(response, 'usage') and response.usage:
                logger.info(
                    f"Token Usage - Input: {response.usage.prompt_tokens}, "
                    f"Output: {response.usage.completion_tokens}, "
                    f"Total: {response.usage.total_tokens}"
                )

            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": answer,
            }

        except Exception as e:
            logger.exception("Error processing video query")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": f"❌ Error processing request: {str(e)}",
            }

    def invoke(self, query: str, context_id: str) -> AgentResponse:
        """Synchronous invocation of the agent."""
        import asyncio

        async def _run():
            if not self.video_context:
                return AgentResponse(status="error", message="No video has been processed yet.")

            context_prompt = self._build_context_prompt(query)
            response = await litellm.acompletion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context_prompt},
                ],
            )
            return response.choices[0].message.content

        try:
            result = asyncio.run(_run())
            if isinstance(result, AgentResponse):
                return result
            return AgentResponse(status="completed", message=result)
        except Exception as e:
            return AgentResponse(status="error", message=f"Error: {str(e)}")