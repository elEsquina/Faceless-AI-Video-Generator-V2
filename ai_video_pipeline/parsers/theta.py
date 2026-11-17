"""Parser Theta (θ): Consumes AI-generated sound, music, and editing instructions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_video_pipeline.schemas.job_schemas import AudioPlanModel
from ai_video_pipeline.schemas.models import (
    AudioCue,
    AudioType,
    PlanManifest,
    SharedTimeline,
    TimelineInterval,
)


class ParserTheta:
    """Parser Theta (θ): Ingests audio cues and editing directives, binding to the shared timeline."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = workspace_root or (
            Path(__file__).resolve().parent.parent.parent
            / "video_docker_sandbox"
            / "workspace"
        )
        self.assets_dir = self.workspace_root / "assets" / "audio"

    def load_audio_plan(self, job_dir: Path) -> AudioPlanModel:
        """Load and parse audio_plan.json from job directory."""
        audio_file = job_dir / "audio_plan.json"
        if not audio_file.exists():
            return AudioPlanModel(job_id=job_dir.name)
        data = json.loads(audio_file.read_text(encoding="utf-8"))
        return AudioPlanModel.model_validate(data)

    def resolve_audio_asset(self, job_dir: Path, filename: str) -> Path:
        """
        Locate a local audio asset, checking job directory, workspace assets, or absolute path.
        Rejects missing assets and path traversal.
        """
        if not filename:
            raise ValueError("Empty audio filename provided")

        # Guard against directory traversal
        if ".." in filename or filename.startswith("/"):
            # Check if it's an allowed absolute path inside workspace
            resolved = Path(filename).resolve()
            if not str(resolved).startswith(str(self.workspace_root.resolve())):
                raise ValueError(f"Path traversal detected or asset outside workspace: {filename}")
            if not resolved.exists():
                raise FileNotFoundError(f"Audio asset not found: {filename}")
            return resolved

        # Check job_dir / assets / filename
        candidate1 = job_dir / "assets" / filename
        if candidate1.exists():
            return candidate1

        # Check workspace_root / assets / audio / filename
        candidate2 = self.assets_dir / filename
        if candidate2.exists():
            return candidate2

        # Check workspace_root / assets / filename
        candidate3 = self.workspace_root / "assets" / filename
        if candidate3.exists():
            return candidate3

        # Check direct job_dir / filename
        candidate4 = job_dir / filename
        if candidate4.exists():
            return candidate4

        raise FileNotFoundError(
            f"Required audio asset '{filename}' was not found in job or workspace asset directories."
        )

    def validate_audio_plan(
        self,
        job_dir: Path,
        plan: PlanManifest,
        audio_plan: AudioPlanModel,
    ) -> Tuple[bool, List[str]]:
        """
        Validate audio cues against scene durations and check local asset existence.
        """
        issues: List[str] = []
        total_duration = plan.target_duration_seconds

        # Validate BGM track if specified
        if audio_plan.bgm_track:
            try:
                self.resolve_audio_asset(job_dir, audio_plan.bgm_track)
            except Exception as e:
                issues.append(f"Background music error: {e}")

        # Validate SFX cues
        for cue in audio_plan.sfx_cues:
            if cue.start_time < 0:
                issues.append(f"SFX {cue.cue_id} has negative start time: {cue.start_time}")
            if cue.start_time > total_duration:
                issues.append(
                    f"SFX {cue.cue_id} start time ({cue.start_time}s) exceeds video duration ({total_duration}s)"
                )
            if cue.source_file:
                try:
                    self.resolve_audio_asset(job_dir, cue.source_file)
                except Exception as e:
                    issues.append(f"SFX {cue.cue_id} asset error: {e}")

        # Validate narration segment timing against scenes
        scene_map = {s.scene_id: s for s in plan.scenes}
        for seg in audio_plan.narration_segments:
            if seg.scene_id not in scene_map:
                issues.append(f"Narration segment references unknown scene '{seg.scene_id}'")
            else:
                scene = scene_map[seg.scene_id]
                scene_dur = scene.end_time - scene.start_time
                seg_dur = seg.end_time - seg.start_time
                if seg_dur > scene_dur + 0.1:
                    issues.append(
                        f"Narration for scene '{seg.scene_id}' duration ({seg_dur:.2f}s) "
                        f"exceeds scene duration ({scene_dur:.2f}s)"
                    )

        return len(issues) == 0, issues

    def ingest_audio_instructions(self, plan: PlanManifest) -> List[AudioCue]:
        """Extract and normalize all AI-planned sound effects and music cues."""
        cues: List[AudioCue] = []
        # Ingest BGM from plan if present
        for bgm in plan.background_music:
            cues.append(bgm)
        # Ingest scene SFX
        for s in plan.scenes:
            for sfx in s.sound_effects:
                cues.append(sfx)
        return cues

    def map_to_shared_timeline(
        self,
        audio_cues: List[AudioCue],
        timeline: SharedTimeline,
    ) -> SharedTimeline:
        """Position audio events onto the unified video timeline without overlap conflicts."""
        timeline.audio_cues = list(audio_cues)
        return timeline

    def generate_edit_decision_list(
        self,
        plan: PlanManifest,
        audio_plan: Optional[AudioPlanModel] = None,
    ) -> Dict[str, Any]:
        """Translate scene transitions, cuts, and visual effects into an edit decision list (EDL)."""
        edl = {
            "job_id": plan.job_id,
            "total_duration": plan.target_duration_seconds,
            "aspect_ratio": plan.aspect_ratio.value,
            "video_tracks": [],
            "audio_tracks": {
                "narration": [],
                "bgm": None,
                "sfx": [],
            },
        }

        # Video tracks from scenes
        for s in plan.scenes:
            edl["video_tracks"].append({
                "scene_id": s.scene_id,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "duration": s.end_time - s.start_time,
                "engine": s.engine.value,
            })

        if audio_plan:
            if audio_plan.bgm_track:
                edl["audio_tracks"]["bgm"] = {
                    "source_file": audio_plan.bgm_track,
                    "volume": audio_plan.bgm_volume,
                    "fade_in": audio_plan.bgm_fade_in,
                    "fade_out": audio_plan.bgm_fade_out,
                }
            for sfx in audio_plan.sfx_cues:
                edl["audio_tracks"]["sfx"].append({
                    "cue_id": sfx.cue_id,
                    "source_file": sfx.source_file,
                    "start_time": sfx.start_time,
                    "volume": sfx.volume_level,
                })
            for narr in audio_plan.narration_segments:
                edl["audio_tracks"]["narration"].append({
                    "scene_id": narr.scene_id,
                    "text": narr.text,
                    "start_time": narr.start_time,
                    "end_time": narr.end_time,
                    "voice_id": narr.voice_id or audio_plan.voice_id,
                })

        return edl

    def compute_audio_ducking_profile(
        self,
        timeline: SharedTimeline,
        voiceover_intervals: List[TimelineInterval],
    ) -> Dict[str, Any]:
        """Compute volume ducking envelope curves for background music during voiceover."""
        ducking_points = []
        default_volume = 0.4
        ducked_volume = 0.12

        for interval in voiceover_intervals:
            # Duck 0.3s before speech starts, ramp back up 0.5s after
            duck_start = max(0.0, interval.start_time - 0.3)
            duck_end = interval.end_time + 0.5

            ducking_points.append({
                "t_start": duck_start,
                "t_speak_start": interval.start_time,
                "t_speak_end": interval.end_time,
                "t_end": duck_end,
                "ducked_volume": ducked_volume,
                "normal_volume": default_volume,
            })

        return {
            "default_volume": default_volume,
            "ducked_volume": ducked_volume,
            "intervals": ducking_points,
        }
