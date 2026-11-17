"""External Director Bridge: File-based plan loader and coordinator (no internal LLM APIs)."""

import json
from pathlib import Path
from typing import List, Optional

from ai_video_pipeline.schemas.job_schemas import (
    JobRequestModel,
    StoryboardModel,
)
from ai_video_pipeline.schemas.models import (
    AnimationEngine,
    AspectRatio,
    JobRequest,
    PlanManifest,
    SceneSpec,
    SharedTimeline,
    TimelineInterval,
    VideoCategory,
)


class ExternalDirectorBridge:
    """Consumes and coordinates external AI-generated plans without internal LLM APIs."""

    def __init__(self, jobs_root: Optional[Path] = None) -> None:
        self.jobs_root = jobs_root or (Path(__file__).resolve().parent.parent.parent / "video_docker_sandbox" / "workspace" / "jobs")

    def load_job_request(self, job_dir: Path) -> JobRequest:
        """Read and deserialize request.json from the job directory."""
        req_path = job_dir / "request.json"
        if not req_path.exists():
            raise FileNotFoundError(f"request.json not found in {job_dir}")
        data = json.loads(req_path.read_text(encoding="utf-8"))
        validated = JobRequestModel.model_validate(data)
        return JobRequest(
            video_type=validated.video_type,
            topic_or_prompt=validated.topic_or_prompt,
            target_duration_seconds=validated.target_duration_seconds,
            language=validated.language,
            aspect_ratio=validated.aspect_ratio,
        )

    def load_plan_manifest(self, job_dir: Path) -> PlanManifest:
        """Read and deserialize external AI-authored storyboard.json from the job directory."""
        plan_path = job_dir / "storyboard.json"
        if not plan_path.exists():
            # Fallback to plan.json if storyboard.json not present
            plan_path = job_dir / "plan.json"
        if not plan_path.exists():
            raise FileNotFoundError(f"Neither storyboard.json nor plan.json found in {job_dir}")

        data = json.loads(plan_path.read_text(encoding="utf-8"))
        validated = StoryboardModel.model_validate(data)
        
        scenes = [
            SceneSpec(
                scene_id=s.scene_id,
                index=s.index,
                engine=s.engine,
                start_time=s.start_time,
                end_time=s.end_time,
                narration_text=s.narration_text,
                visual_description=s.visual_description,
                code_file=s.code_file,
                inline_code=s.inline_code,
            )
            for s in validated.scenes
        ]

        intervals = [
            TimelineInterval(
                track_name=s.scene_id,
                start_time=s.start_time,
                end_time=s.end_time,
            )
            for s in scenes
        ]
        shared_timeline = SharedTimeline(
            total_duration_seconds=validated.target_duration_seconds,
            visual_intervals=intervals,
        )

        return PlanManifest(
            job_id=validated.job_id,
            title=validated.title,
            category=validated.category,
            aspect_ratio=validated.aspect_ratio,
            target_duration_seconds=validated.target_duration_seconds,
            shared_timeline=shared_timeline,
            scenes=scenes,
        )

    def resolve_scene_code_path(self, job_dir: Path, scene: SceneSpec) -> Path:
        """Locate external AI-generated animation script for a given scene."""
        if not scene.code_file:
            raise ValueError(f"Scene {scene.scene_id} has no code_file specified")
        
        code_path = job_dir / "scenes" / scene.code_file
        if not code_path.exists():
            # Check if code_file was specified with scenes/ prefix
            alt_path = job_dir / scene.code_file
            if alt_path.exists():
                return alt_path
            raise FileNotFoundError(f"Code file for scene {scene.scene_id} not found at {code_path}")
        return code_path

    def extract_shared_timeline(self, plan: PlanManifest) -> SharedTimeline:
        """Extract and verify the unified timeline across all modalities."""
        intervals = [
            TimelineInterval(
                track_name=s.scene_id,
                start_time=s.start_time,
                end_time=s.end_time,
            )
            for s in plan.scenes
        ]
        return SharedTimeline(
            total_duration_seconds=plan.target_duration_seconds,
            visual_intervals=intervals,
        )
