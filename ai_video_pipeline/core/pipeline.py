"""End-to-end AI Video Generation Pipeline coordinator for MCP jobs."""

from pathlib import Path
from typing import List, Optional

from ai_video_pipeline.core.director import ExternalDirectorBridge
from ai_video_pipeline.media.compositor import VideoCompositor
from ai_video_pipeline.media.renderer import SceneRenderer
from ai_video_pipeline.media.text_splash import TextSplashGenerator
from ai_video_pipeline.media.tts import TextToSpeechService
from ai_video_pipeline.parsers.omega import ParserOmega
from ai_video_pipeline.parsers.theta import ParserTheta
from ai_video_pipeline.quality.validator import QualityValidator
from ai_video_pipeline.schemas.models import (
    FinalVideoResult,
    JobStatusRecord,
    RenderedSceneAsset,
    ValidationResult,
)


class VideoGenerationPipeline:
    """Coordinates local deterministic pipeline execution on external AI-generated job files."""

    def __init__(
        self,
        director_bridge: Optional[ExternalDirectorBridge] = None,
        parser_omega: Optional[ParserOmega] = None,
        parser_theta: Optional[ParserTheta] = None,
        tts_service: Optional[TextToSpeechService] = None,
        text_splash: Optional[TextSplashGenerator] = None,
        renderer: Optional[SceneRenderer] = None,
        compositor: Optional[VideoCompositor] = None,
        validator: Optional[QualityValidator] = None,
    ) -> None:
        pass

    def execute_job(self, job_dir: Path) -> FinalVideoResult:
        """Run complete generation pipeline for a validated job directory."""
        pass

    def retry_scene(self, job_dir: Path, scene_id: str) -> RenderedSceneAsset:
        """Re-render and re-compose a specific scene after external AI repair."""
        pass

    def get_status(self, job_dir: Path) -> JobStatusRecord:
        """Read current pipeline status from job_dir/status.json."""
        pass
