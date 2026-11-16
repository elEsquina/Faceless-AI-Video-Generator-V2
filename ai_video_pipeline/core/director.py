"""External Director Bridge: File-based plan loader and coordinator (no internal LLM APIs)."""

from pathlib import Path
from typing import List, Optional

from ai_video_pipeline.schemas.models import (
    JobRequest,
    PlanManifest,
    SceneSpec,
    SharedTimeline,
)


class ExternalDirectorBridge:
    """Consumes and coordinates external AI-generated plans without internal LLM APIs."""

    def __init__(self, jobs_root: Optional[Path] = None) -> None:
        pass

    def load_job_request(self, job_dir: Path) -> JobRequest:
        """Read and deserialize request.json from the job directory."""
        pass

    def load_plan_manifest(self, job_dir: Path) -> PlanManifest:
        """Read and deserialize external AI-authored plan.json from the job directory."""
        pass

    def resolve_scene_code_path(self, job_dir: Path, scene: SceneSpec) -> Path:
        """Locate external AI-generated animation script for a given scene."""
        pass

    def extract_shared_timeline(self, plan: PlanManifest) -> SharedTimeline:
        """Extract and verify the unified timeline across all modalities."""
        pass
