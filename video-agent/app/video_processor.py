"""
Video processing utilities for extracting frames, audio, and transcription.
"""

import os
import logging
import base64
from pathlib import Path
from typing import List, Dict, Tuple
import cv2
import whisper
from moviepy.editor import VideoFileClip
from PIL import Image
import io

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process videos to extract frames, audio, and transcription."""

    def __init__(self, video_dir: str = None):
        """
        Initialize the video processor.

        Args:
            video_dir: Directory to store uploaded videos (defaults to VIDEO_STORAGE_PATH env var or ./videos)
        """
        if video_dir is None:
            video_dir = os.environ.get("VIDEO_STORAGE_PATH", os.path.join(os.path.dirname(__file__), "..", "videos"))
        self.video_dir = Path(video_dir)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.whisper_model = None
        
    def _load_whisper_model(self):
        """Lazy load Whisper model for audio transcription."""
        if self.whisper_model is None:
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
        return self.whisper_model

    def save_video(self, video_data: bytes, filename: str) -> Path:
        """
        Save uploaded video to disk.
        
        Args:
            video_data: Video file bytes
            filename: Original filename
            
        Returns:
            Path to saved video file
        """
        video_path = self.video_dir / filename
        with open(video_path, "wb") as f:
            f.write(video_data)
        logger.info(f"Saved video to {video_path}")
        return video_path

    def extract_frames(
        self, 
        video_path: Path, 
        num_frames: int = 20,
        max_dimension: int = 1024
    ) -> List[Dict[str, any]]:
        """
        Extract evenly spaced frames from video.
        
        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            max_dimension: Maximum width/height for frames
            
        Returns:
            List of frame data with timestamps and base64 encoded images
        """
        logger.info(f"Extracting {num_frames} frames from {video_path}")
        frames = []
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            # Calculate frame indices to extract
            if total_frames < num_frames:
                frame_indices = list(range(total_frames))
            else:
                frame_indices = [
                    int(i * total_frames / num_frames) 
                    for i in range(num_frames)
                ]
            
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if ret:
                    # Resize frame if needed
                    height, width = frame.shape[:2]
                    if max(height, width) > max_dimension:
                        scale = max_dimension / max(height, width)
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        frame = cv2.resize(frame, (new_width, new_height))
                    
                    # Convert to RGB and encode as base64
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Convert to base64
                    buffer = io.BytesIO()
                    pil_image.save(buffer, format="JPEG", quality=85)
                    img_base64 = base64.b64encode(buffer.getvalue()).decode()
                    
                    timestamp = idx / fps if fps > 0 else 0
                    
                    frames.append({
                        "frame_number": idx,
                        "timestamp": round(timestamp, 2),
                        "image_base64": img_base64,
                        "width": pil_image.width,
                        "height": pil_image.height
                    })
            
            cap.release()
            logger.info(f"Extracted {len(frames)} frames")
            
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            raise
        
        return frames

    def extract_audio_and_transcribe(self, video_path: Path) -> Dict[str, any]:
        """
        Extract audio from video and transcribe it.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with audio path and transcription
        """
        logger.info(f"Extracting audio from {video_path}")
        
        try:
            # Extract audio using moviepy
            video = VideoFileClip(str(video_path))
            audio_path = video_path.with_suffix('.wav')
            
            if video.audio is not None:
                video.audio.write_audiofile(
                    str(audio_path),
                    codec='pcm_s16le',
                    verbose=False,
                    logger=None
                )
                video.close()
                
                # Transcribe audio using Whisper
                logger.info("Transcribing audio...")
                model = self._load_whisper_model()
                result = model.transcribe(str(audio_path))
                
                transcription = {
                    "text": result["text"],
                    "segments": [
                        {
                            "start": seg["start"],
                            "end": seg["end"],
                            "text": seg["text"]
                        }
                        for seg in result["segments"]
                    ],
                    "language": result.get("language", "unknown")
                }
                
                logger.info(f"Transcription complete: {len(transcription['segments'])} segments")
                return transcription
            else:
                logger.warning("No audio track found in video")
                return {
                    "text": "",
                    "segments": [],
                    "language": "none"
                }
                
        except Exception as e:
            logger.error(f"Error extracting/transcribing audio: {e}")
            raise

    def get_video_metadata(self, video_path: Path) -> Dict[str, any]:
        """
        Get video metadata (duration, resolution, fps, etc.).
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video metadata
        """
        try:
            cap = cv2.VideoCapture(str(video_path))
            
            metadata = {
                "filename": video_path.name,
                "size_mb": round(video_path.stat().st_size / (1024 * 1024), 2),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": round(cap.get(cv2.CAP_PROP_FPS), 2),
                "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "duration_seconds": round(
                    cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                    2
                ) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0
            }
            
            cap.release()
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            raise

    def process_video(
        self, 
        video_path: Path,
        num_frames: int = 20
    ) -> Dict[str, any]:
        """
        Complete video processing pipeline.
        
        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            
        Returns:
            Dictionary with all extracted data
        """
        logger.info(f"Processing video: {video_path}")
        
        # Get metadata
        metadata = self.get_video_metadata(video_path)
        
        # Extract frames
        frames = self.extract_frames(video_path, num_frames)
        
        # Extract and transcribe audio
        transcription = self.extract_audio_and_transcribe(video_path)
        
        result = {
            "metadata": metadata,
            "frames": frames,
            "transcription": transcription,
            "video_path": str(video_path)
        }
        
        logger.info("Video processing complete")
        return result