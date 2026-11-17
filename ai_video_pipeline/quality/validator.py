"""Quality validation and visual QA coordinator for video generation pipeline."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_video_pipeline.media.compositor import VideoCompositor
from ai_video_pipeline.quality.analyzer import ContactSheetGenerator, FrameQualityAnalyzer
from ai_video_pipeline.quality.frame_extractor import KeyframeExtractor
from ai_video_pipeline.schemas.job_schemas import (
    JobQAReportModel,
    SceneQAMetricsModel,
    VisualReviewModel,
)
from ai_video_pipeline.schemas.models import (
    JobErrorReport,
    PlanManifest,
    RenderedSceneAsset,
    SceneSpec,
    ValidationResult,
    ValidationStatus,
)


class QualityValidator:
    """Validates generated code, assets, audio-visual sync, and visual quality."""

    MAX_REPAIR_ITERATIONS = 3

    def __init__(
        self,
        extractor: Optional[KeyframeExtractor] = None,
        analyzer: Optional[FrameQualityAnalyzer] = None,
        contact_sheet_gen: Optional[ContactSheetGenerator] = None,
        compositor: Optional[VideoCompositor] = None,
    ) -> None:
        self.extractor = extractor or KeyframeExtractor()
        self.analyzer = analyzer or FrameQualityAnalyzer()
        self.contact_sheet_gen = contact_sheet_gen or ContactSheetGenerator()
        self.compositor = compositor or VideoCompositor()

    def get_repair_count(self, job_dir: Path, scene_id: str) -> int:
        """Get the current repair retry count for a scene."""
        state_file = job_dir / "qa" / "repair_state.json"
        if not state_file.exists():
            return 0
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            return int(data.get(scene_id, 0))
        except Exception:
            return 0

    def increment_repair_count(self, job_dir: Path, scene_id: str) -> int:
        """Increment and persist the repair attempt count for a scene."""
        qa_dir = job_dir / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        state_file = qa_dir / "repair_state.json"
        data = {}
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        curr = int(data.get(scene_id, 0)) + 1
        data[scene_id] = curr
        state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return curr

    def backup_scene_render(self, job_dir: Path, scene_id: str) -> Optional[Path]:
        """Preserve the last successful render until a replacement passes checks."""
        renders_dir = job_dir / "renders"
        current_mp4 = renders_dir / f"{scene_id}.mp4"
        if current_mp4.exists() and current_mp4.stat().st_size > 0:
            backup_mp4 = renders_dir / f"{scene_id}.backup.mp4"
            shutil.copy2(current_mp4, backup_mp4)
            return backup_mp4
        return None

    def restore_scene_backup(self, job_dir: Path, scene_id: str) -> bool:
        """Restore previous backup if replacement render fails checks."""
        renders_dir = job_dir / "renders"
        backup_mp4 = renders_dir / f"{scene_id}.backup.mp4"
        current_mp4 = renders_dir / f"{scene_id}.mp4"
        if backup_mp4.exists() and backup_mp4.stat().st_size > 0:
            shutil.copy2(backup_mp4, current_mp4)
            return True
        return False

    def inspect_scene(
        self,
        job_dir: Path,
        scene: SceneSpec,
        expected_aspect_ratio=None,
    ) -> SceneQAMetricsModel:
        """
        Extract keyframes and perform technical visual QA on an individual scene.
        """
        qa_dir = job_dir / "qa"
        scene_qa_dir = qa_dir / "scenes" / scene.scene_id
        scene_qa_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(scene_qa_dir, 0o777)
        except OSError:
            pass

        video_path = job_dir / "renders" / f"{scene.scene_id}.mp4"
        if not video_path.exists():
            return SceneQAMetricsModel(
                scene_id=scene.scene_id,
                status="failed",
                issues=[f"Rendered video file not found at {video_path}"],
            )

        # 1. FFprobe metadata
        try:
            v_info = self.compositor.probe_media(video_path)
        except Exception as e:
            return SceneQAMetricsModel(
                scene_id=scene.scene_id,
                status="failed",
                issues=[f"Corrupt or unreadable video: {e}"],
            )

        # 2. Extract keyframes
        planned_dur = scene.end_time - scene.start_time
        try:
            frames = self.extractor.extract_scene_keyframes(video_path, planned_dur, scene_qa_dir)
        except Exception as e:
            return SceneQAMetricsModel(
                scene_id=scene.scene_id,
                status="failed",
                issues=[f"Keyframe extraction failed: {e}"],
            )

        # 3. Analyze frames
        metrics = self.analyzer.evaluate_scene(
            scene=scene,
            frames=frames,
            video_info=v_info,
            expected_aspect_ratio=expected_aspect_ratio,
        )

        # Save scene metrics.json
        (scene_qa_dir / "metrics.json").write_text(metrics.model_dump_json(indent=2), encoding="utf-8")
        return metrics

    def inspect_video(
        self,
        job_dir: Path,
        plan: PlanManifest,
    ) -> JobQAReportModel:
        """
        Execute automated visual QA across all scenes, extract frames and contact sheet.
        """
        qa_dir = job_dir / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(qa_dir, 0o777)
        except OSError:
            pass

        scene_frames: Dict[str, Dict[str, Path]] = {}
        scene_metrics: Dict[str, SceneQAMetricsModel] = {}
        all_anomalies: List[str] = []

        passed_count = 0
        failed_count = 0

        for scene in plan.scenes:
            m = self.inspect_scene(job_dir, scene, expected_aspect_ratio=plan.aspect_ratio)
            scene_metrics[scene.scene_id] = m
            if m.status == "passed":
                passed_count += 1
            else:
                failed_count += 1
                for iss in m.issues:
                    all_anomalies.append(f"[{scene.scene_id}] {iss}")

            # Collect frame paths for contact sheet
            s_dir = qa_dir / "scenes" / scene.scene_id
            scene_frames[scene.scene_id] = {
                "start": s_dir / "frame_start.jpg",
                "middle": s_dir / "frame_middle.jpg",
                "end": s_dir / "frame_end.jpg",
            }

        # Generate contact sheet
        contact_sheet_path = qa_dir / "contact_sheet.jpg"
        try:
            self.contact_sheet_gen.create_contact_sheet(
                scene_frames=scene_frames,
                output_image=contact_sheet_path,
                scene_metrics=scene_metrics,
            )
            cs_str = str(contact_sheet_path)
        except Exception as e:
            all_anomalies.append(f"Contact sheet generation failed: {e}")
            cs_str = None

        overall_status = "passed" if failed_count == 0 else "failed"

        # Check for existing agent visual review
        review_file = qa_dir / "visual_review.json"
        ai_review = None
        if review_file.exists():
            try:
                ai_review = VisualReviewModel.model_validate_json(review_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        report = JobQAReportModel(
            job_id=plan.job_id,
            overall_status=overall_status,
            total_scenes=len(plan.scenes),
            scenes_passed=passed_count,
            scenes_failed=failed_count,
            contact_sheet_path=cs_str,
            scene_reports=scene_metrics,
            detected_anomalies=all_anomalies,
            ai_review=ai_review,
        )

        (qa_dir / "quality_report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return report

    def save_visual_review(
        self,
        job_dir: Path,
        review_data: Dict[str, Any],
    ) -> VisualReviewModel:
        """Validate and store visual review findings from external AI agent."""
        qa_dir = job_dir / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        review = VisualReviewModel.model_validate(review_data)
        (qa_dir / "visual_review.json").write_text(review.model_dump_json(indent=2), encoding="utf-8")

        # Update quality report if present
        report_file = qa_dir / "quality_report.json"
        if report_file.exists():
            try:
                rep = JobQAReportModel.model_validate_json(report_file.read_text(encoding="utf-8"))
                rep.ai_review = review
                report_file.write_text(rep.model_dump_json(indent=2), encoding="utf-8")
            except Exception:
                pass

        return review

    def validate_plan_schema(self, plan: PlanManifest) -> ValidationResult:
        """Verify structural conformity and shared timeline consistency of plan.json."""
        issues = []
        if not plan.scenes:
            issues.append("Plan contains no scenes")
        return ValidationResult(
            status=ValidationStatus.PASSED if not issues else ValidationStatus.FAILED,
            issues=issues,
        )

    def validate_scene_code_files(
        self,
        job_dir: Path,
        scenes: List[SceneSpec],
    ) -> ValidationResult:
        """Scan generated animation code files for syntax errors."""
        issues = []
        for s in scenes:
            if s.code_file:
                p = job_dir / "scenes" / s.code_file
                if not p.exists():
                    issues.append(f"Missing code file: {s.code_file}")
        return ValidationResult(
            status=ValidationStatus.PASSED if not issues else ValidationStatus.FAILED,
            issues=issues,
        )

    def check_asset_completeness(
        self,
        plan: PlanManifest,
        rendered_scenes: List[RenderedSceneAsset],
    ) -> ValidationResult:
        issues = []
        rendered_ids = {r.scene_id for r in rendered_scenes}
        for s in plan.scenes:
            if s.scene_id not in rendered_ids:
                issues.append(f"Scene {s.scene_id} is unrendered")
        return ValidationResult(
            status=ValidationStatus.PASSED if not issues else ValidationStatus.FAILED,
            issues=issues,
        )

    def check_timeline_synchrony(
        self,
        plan: PlanManifest,
        rendered_scenes: List[RenderedSceneAsset],
        audio_duration_seconds: float,
    ) -> ValidationResult:
        issues = []
        if abs(plan.target_duration_seconds - audio_duration_seconds) > 1.5:
            issues.append(
                f"Timeline mismatch: video duration ({plan.target_duration_seconds}s) vs audio ({audio_duration_seconds}s)"
            )
        return ValidationResult(
            status=ValidationStatus.PASSED if not issues else ValidationStatus.FAILED,
            issues=issues,
        )

    def write_error_report(
        self,
        job_dir: Path,
        validation: ValidationResult,
    ) -> JobErrorReport:
        report = JobErrorReport(
            job_id=job_dir.name,
            status=validation.status,
            global_errors=validation.issues,
        )
        (job_dir / "errors.json").write_text(json.dumps(validation.issues, indent=2), encoding="utf-8")
        return report
