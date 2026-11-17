"""Pydantic v2 schema models for MCP validation/serialization of job/pipeline data.

These are parallel to the dataclasses in models.py which remain for internal use.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from ai_video_pipeline.schemas.models import (
    AnimationEngine,
    AspectRatio,
    VideoCategory,
)


# ---------------------------------------------------------------------------
# 1. JobRequestModel
# ---------------------------------------------------------------------------

class JobRequestModel(BaseModel):
    """Pydantic version of JobRequest — used for MCP request validation."""

    video_type: VideoCategory
    topic_or_prompt: str
    target_duration_seconds: float = Field(gt=0, le=600)
    language: str = "en"
    aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE_16_9

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            vt = data.get("video_type")
            if isinstance(vt, str):
                vt_map = {
                    "kids": VideoCategory.KIDS_ANIMATED_STORY,
                    "kids_animated_story": VideoCategory.KIDS_ANIMATED_STORY,
                    "explanatory": VideoCategory.GENERAL_EXPLANATORY,
                    "general_explanatory": VideoCategory.GENERAL_EXPLANATORY,
                    "cs_math": VideoCategory.CS_MATH_EDUCATIONAL,
                    "cs_math_educational": VideoCategory.CS_MATH_EDUCATIONAL,
                }
                data["video_type"] = vt_map.get(vt.lower(), vt)
            ar = data.get("aspect_ratio")
            if isinstance(ar, str):
                ar_map = {
                    "16:9": AspectRatio.LANDSCAPE_16_9,
                    "landscape_16_9": AspectRatio.LANDSCAPE_16_9,
                    "9:16": AspectRatio.PORTRAIT_9_16,
                    "portrait_9_16": AspectRatio.PORTRAIT_9_16,
                    "1:1": AspectRatio.SQUARE_1_1,
                    "square_1_1": AspectRatio.SQUARE_1_1,
                }
                data["aspect_ratio"] = ar_map.get(ar.lower(), ar)
        return data


# ---------------------------------------------------------------------------
# 2. SceneSpecModel
# ---------------------------------------------------------------------------

class SceneSpecModel(BaseModel):
    """Pydantic version of SceneSpec — per-scene data with time validation."""

    scene_id: str = Field(pattern=r"^scene_\d{3}$")
    index: int = Field(ge=0)
    engine: AnimationEngine
    start_time: float = Field(ge=0)
    end_time: float = Field(gt=0)
    narration_text: str
    visual_description: str
    code_file: Optional[str] = None
    inline_code: Optional[str] = None

    @model_validator(mode="after")
    def _end_after_start(self) -> "SceneSpecModel":
        if self.end_time <= self.start_time:
            raise ValueError(
                f"end_time ({self.end_time}) must be greater than "
                f"start_time ({self.start_time})"
            )
        return self


# ---------------------------------------------------------------------------
# 3. StoryboardModel
# ---------------------------------------------------------------------------

class StoryboardModel(BaseModel):
    """Pydantic version of PlanManifest (storyboard.json) with scene integrity checks."""

    job_id: str = Field(pattern=r"^([0-9a-f]{8}|[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$")
    title: str
    category: VideoCategory
    aspect_ratio: AspectRatio
    target_duration_seconds: float = Field(gt=0)
    scenes: List[SceneSpecModel] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _normalize_category(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cat = data.get("category")
            if isinstance(cat, str):
                cat_map = {
                    "kids": VideoCategory.KIDS_ANIMATED_STORY,
                    "kids_animated_story": VideoCategory.KIDS_ANIMATED_STORY,
                    "explanatory": VideoCategory.GENERAL_EXPLANATORY,
                    "general_explanatory": VideoCategory.GENERAL_EXPLANATORY,
                    "cs_math": VideoCategory.CS_MATH_EDUCATIONAL,
                    "cs_math_educational": VideoCategory.CS_MATH_EDUCATIONAL,
                }
                data["category"] = cat_map.get(cat.lower(), cat)
            ar = data.get("aspect_ratio")
            if isinstance(ar, str):
                ar_map = {
                    "16:9": AspectRatio.LANDSCAPE_16_9,
                    "landscape_16_9": AspectRatio.LANDSCAPE_16_9,
                    "9:16": AspectRatio.PORTRAIT_9_16,
                    "portrait_9_16": AspectRatio.PORTRAIT_9_16,
                    "1:1": AspectRatio.SQUARE_1_1,
                    "square_1_1": AspectRatio.SQUARE_1_1,
                }
                data["aspect_ratio"] = ar_map.get(ar.lower(), ar)
        return data

    @model_validator(mode="after")
    def _validate_scenes(self) -> "StoryboardModel":
        ids = [s.scene_id for s in self.scenes]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate scene_ids found in storyboard scenes")

        # Check for overlapping time intervals
        sorted_scenes = sorted(self.scenes, key=lambda s: s.start_time)
        for i in range(len(sorted_scenes) - 1):
            current = sorted_scenes[i]
            nxt = sorted_scenes[i + 1]
            if nxt.start_time < current.end_time:
                raise ValueError(
                    f"Overlapping scenes: {current.scene_id} ends at "
                    f"{current.end_time} but {nxt.scene_id} starts at {nxt.start_time}"
                )
        return self


# ---------------------------------------------------------------------------
# 4. Audio & Postproduction Models
# ---------------------------------------------------------------------------

class AudioCueModel(BaseModel):
    """Audio cue specification for SFX or BGM."""

    cue_id: str
    audio_type: str = "sound_effect"
    source_file: Optional[str] = None
    start_time: float = Field(default=0.0, ge=0.0)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    volume_level: float = Field(default=1.0, ge=0.0, le=2.0)
    fade_in: float = Field(default=0.0, ge=0.0)
    fade_out: float = Field(default=0.0, ge=0.0)


class NarrationSegmentModel(BaseModel):
    """Narration segment mapped to a scene."""

    scene_id: str
    text: str
    voice_id: Optional[str] = None
    language: str = "en"
    start_time: float = Field(ge=0.0)
    end_time: float = Field(gt=0.0)


class CaptionStyleModel(BaseModel):
    """Configuration for animated captions."""

    font_name: str = "Arial"
    font_size: int = 24
    primary_color: str = "&H00FFFFFF"
    highlight_color: str = "&H0000FFFF"
    position: str = "bottom"


class AudioPlanModel(BaseModel):
    """Audio configuration for a job (audio_plan.json)."""

    job_id: str
    voice_id: str = "af_heart"
    language: str = "en"
    bgm_track: Optional[str] = None
    bgm_volume: float = Field(default=0.2, ge=0, le=1)
    bgm_fade_in: float = Field(default=1.0, ge=0)
    bgm_fade_out: float = Field(default=2.0, ge=0)
    narration_segments: List[NarrationSegmentModel] = Field(default_factory=list)
    sfx_cues: List[AudioCueModel] = Field(default_factory=list)
    caption_style: CaptionStyleModel = Field(default_factory=CaptionStyleModel)


# ---------------------------------------------------------------------------
# 5. JobStatusModel
# ---------------------------------------------------------------------------

class JobStatusModel(BaseModel):
    """Pydantic version of JobStatusRecord (status.json)."""

    job_id: str
    state: Literal[
        "created",
        "validated",
        "rendering",
        "narration_generation",
        "caption_generation",
        "audio_mixing",
        "video_composition",
        "completed",
        "failed",
    ]
    progress_pct: float = Field(default=0.0, ge=0, le=100)
    current_stage: Optional[str] = None
    output_path: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 6. SceneErrorModel
# ---------------------------------------------------------------------------

class SceneErrorModel(BaseModel):
    """Error details for a single scene."""

    scene_id: str
    engine: str
    stage: str
    error_message: str
    log_file: Optional[str] = None
    retry_eligible: bool = True
    suggested_fix: Optional[str] = None


# ---------------------------------------------------------------------------
# 7. JobErrorReportModel
# ---------------------------------------------------------------------------

class JobErrorReportModel(BaseModel):
    """Consolidated error report (errors.json)."""

    job_id: str
    status: Literal["passed", "warning", "failed"]
    global_errors: List[str] = Field(default_factory=list)
    scene_errors: List[SceneErrorModel] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 8. ValidationResultModel
# ---------------------------------------------------------------------------

class ValidationResultModel(BaseModel):
    """Result of a pipeline validation step."""

    is_valid: bool
    issues: List[str] = Field(default_factory=list)
    scenes_to_regenerate: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def load_storyboard(job_dir: Path) -> StoryboardModel:
    """Read storyboard.json from job_dir and return a validated StoryboardModel."""
    storyboard_path = job_dir / "storyboard.json"
    return StoryboardModel.model_validate_json(storyboard_path.read_text(encoding="utf-8"))


def load_job_request(job_dir: Path) -> JobRequestModel:
    """Read request.json from job_dir and return a validated JobRequestModel."""
    request_path = job_dir / "request.json"
    return JobRequestModel.model_validate_json(request_path.read_text(encoding="utf-8"))


def load_audio_plan(job_dir: Path) -> AudioPlanModel:
    """Read audio_plan.json from job_dir and return a validated AudioPlanModel."""
    audio_path = job_dir / "audio_plan.json"
    if not audio_path.exists():
        return AudioPlanModel(job_id=job_dir.name)
    return AudioPlanModel.model_validate_json(audio_path.read_text(encoding="utf-8"))


def write_status(job_dir: Path, status: JobStatusModel) -> None:
    """Atomically write status.json (write to .tmp then os.replace)."""
    target = job_dir / "status.json"
    payload = status.model_dump_json(indent=2)
    fd, tmp_path = tempfile.mkstemp(dir=job_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def write_error_report(job_dir: Path, report: JobErrorReportModel) -> None:
    """Atomically write errors.json (write to .tmp then os.replace)."""
    target = job_dir / "errors.json"
    payload = report.model_dump_json(indent=2)
    fd, tmp_path = tempfile.mkstemp(dir=job_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
