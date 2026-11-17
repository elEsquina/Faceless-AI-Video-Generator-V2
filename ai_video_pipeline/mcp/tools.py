"""Local MCP Tool implementations for external AI coding agents (Codex / Antigravity)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_video_pipeline.core.director import ExternalDirectorBridge
from ai_video_pipeline.jobs.manager import JobManager
from ai_video_pipeline.parsers.omega import ParserOmega
from ai_video_pipeline.schemas.job_schemas import (
    JobErrorReportModel,
    JobRequestModel,
    JobStatusModel,
    SceneErrorModel,
    StoryboardModel,
    ValidationResultModel,
)
from ai_video_pipeline.schemas.models import AnimationEngine, JobState


class PipelineMCPTools:
    """Defines tool interfaces exposed via Model Context Protocol (MCP) to external AI agents."""

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        job_manager: Optional[JobManager] = None,
        parser_omega: Optional[ParserOmega] = None,
        director_bridge: Optional[ExternalDirectorBridge] = None,
    ) -> None:
        self.workspace_root = workspace_root
        self.job_manager = job_manager or JobManager(workspace_root=self.workspace_root)
        self.parser_omega = parser_omega or ParserOmega()
        self.director_bridge = director_bridge or ExternalDirectorBridge()

    def create_job(
        self,
        video_type: str,
        topic_or_prompt: str,
        target_duration_seconds: float,
        language: str = "en",
        aspect_ratio: str = "16:9",
    ) -> Dict[str, Any]:
        """Create a dedicated job workspace directory and write request.json."""
        try:
            req_model = JobRequestModel.model_validate({
                "video_type": video_type,
                "topic_or_prompt": topic_or_prompt,
                "target_duration_seconds": target_duration_seconds,
                "language": language,
                "aspect_ratio": aspect_ratio,
            })
        except Exception as e:
            return {"error": f"Invalid job request parameters: {e}", "success": False}

        req_dict = {
            "video_type": req_model.video_type.value,
            "topic_or_prompt": req_model.topic_or_prompt,
            "target_duration_seconds": req_model.target_duration_seconds,
            "language": req_model.language,
            "aspect_ratio": req_model.aspect_ratio.value,
        }

        try:
            job_id = self.job_manager.create_job(req_dict)
            job_dir = self.job_manager.get_job_dir(job_id)
            return {
                "success": True,
                "job_id": job_id,
                "job_dir": str(job_dir),
                "status": "created",
                "message": f"Job {job_id} created successfully",
            }
        except Exception as e:
            return {"error": f"Failed to create job: {e}", "success": False}

    def validate_plan(self, job_id: str) -> Dict[str, Any]:
        """Validate the AI-authored storyboard.json, scene code files, and shared timeline consistency."""
        try:
            job_dir = self.job_manager.get_job_dir(job_id)
        except Exception as e:
            return {"is_valid": False, "issues": [str(e)], "scenes_to_regenerate": []}

        issues: List[str] = []
        scenes_to_regen: List[str] = []

        # Check storyboard file
        sb_file = job_dir / "storyboard.json"
        if not sb_file.exists():
            sb_file = job_dir / "plan.json"
        if not sb_file.exists():
            issues.append(f"No storyboard.json or plan.json found in {job_dir}")
            return {"is_valid": False, "issues": issues, "scenes_to_regenerate": []}

        try:
            sb_data = json.loads(sb_file.read_text(encoding="utf-8"))
            sb_model = StoryboardModel.model_validate(sb_data)
        except Exception as e:
            issues.append(f"Storyboard JSON validation failed: {e}")
            return {"is_valid": False, "issues": issues, "scenes_to_regenerate": []}

        # Check scene code files & syntax
        for scene in sb_model.scenes:
            if not scene.code_file and not scene.inline_code:
                issues.append(f"Scene {scene.scene_id} has neither code_file nor inline_code")
                scenes_to_regen.append(scene.scene_id)
                continue

            if scene.code_file:
                code_path = job_dir / "scenes" / scene.code_file
                if not code_path.exists():
                    alt = job_dir / scene.code_file
                    if alt.exists():
                        code_path = alt
                    else:
                        issues.append(f"Code file for {scene.scene_id} not found at {code_path}")
                        scenes_to_regen.append(scene.scene_id)
                        continue

                # Validate syntax via handler
                try:
                    handler = self.parser_omega.get_handler(scene.engine)
                    valid, err = handler.validate_code_file(code_path)
                    if not valid:
                        issues.append(f"Code validation failed for {scene.scene_id}: {err}")
                        scenes_to_regen.append(scene.scene_id)
                except Exception as e:
                    issues.append(f"Validator exception for {scene.scene_id}: {e}")
                    scenes_to_regen.append(scene.scene_id)

        is_valid = len(issues) == 0
        val_result = {
            "is_valid": is_valid,
            "issues": issues,
            "scenes_to_regenerate": scenes_to_regen,
        }

        # Write validation.json atomically
        val_file = job_dir / "validation.json"
        val_file.write_text(json.dumps(val_result, indent=2), encoding="utf-8")

        if is_valid:
            self.job_manager.transition_state(job_id, "validated")
        else:
            self.job_manager.transition_state(job_id, "plan_pending", errors=issues)

        return val_result

    def execute_job(self, job_id: str) -> Dict[str, Any]:
        """Trigger the deterministic Python rendering, TTS, and composition pipeline."""
        try:
            job_dir = self.job_manager.get_job_dir(job_id)
        except Exception as e:
            return {"status": "failed", "error": str(e)}

        status = self.job_manager.read_status(job_id)
        if status.get("state") not in ("validated", "created"):
            # Auto-validate if not yet done
            val = self.validate_plan(job_id)
            if not val.get("is_valid"):
                return {
                    "status": "failed",
                    "error": f"Plan validation failed: {val.get('issues')}",
                }

        # Transition to rendering
        self.job_manager.transition_state(
            job_id, "rendering", progress_pct=5, current_stage="rendering_scenes"
        )

        try:
            plan = self.director_bridge.load_plan_manifest(job_dir)
        except Exception as e:
            self.job_manager.transition_state(job_id, "failed", errors=[str(e)])
            self.job_manager.release_lock(job_id)
            return {"status": "failed", "error": f"Could not load plan manifest: {e}"}

        scene_outputs: List[Path] = []
        total_scenes = len(plan.scenes)

        for idx, scene in enumerate(plan.scenes):
            pct = int(10 + (idx / total_scenes) * 75)
            self.job_manager.transition_state(
                job_id,
                "rendering",
                progress_pct=pct,
                current_stage=f"rendering_{scene.scene_id}",
            )

            res = self.parser_omega.execute_scene(job_dir, scene)
            if not res.get("success"):
                err_msg = res.get("error", "Unknown render error")
                self.job_manager.append_error(
                    job_id,
                    scene_id=scene.scene_id,
                    engine=scene.engine.value,
                    stage="rendering",
                    msg=err_msg,
                    log_file=res.get("log_file"),
                )
                self.job_manager.transition_state(
                    job_id,
                    "failed",
                    errors=[f"Scene {scene.scene_id} failed: {err_msg}"],
                )
                self.job_manager.release_lock(job_id)
                return {
                    "status": "failed",
                    "job_id": job_id,
                    "failed_scene": scene.scene_id,
                    "error": err_msg,
                    "log_file": res.get("log_file"),
                }

            scene_outputs.append(Path(res["output_path"]))

        # Assemble final video
        self.job_manager.transition_state(
            job_id, "rendering", progress_pct=90, current_stage="assembling_output"
        )

        try:
            final_mp4 = self.parser_omega.assemble_final_video(job_dir, scene_outputs)
        except Exception as e:
            err_msg = f"Assembly failed: {e}"
            self.job_manager.append_error(job_id, None, "ffmpeg", "assembly", err_msg)
            self.job_manager.transition_state(job_id, "failed", errors=[err_msg])
            self.job_manager.release_lock(job_id)
            return {"status": "failed", "job_id": job_id, "error": err_msg}

        self.job_manager.transition_state(
            job_id,
            "completed",
            progress_pct=100,
            current_stage="done",
            output_path=str(final_mp4),
        )
        self.job_manager.release_lock(job_id)

        return {
            "status": "completed",
            "job_id": job_id,
            "output_path": str(final_mp4),
            "scenes_completed": total_scenes,
        }

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Query current job lifecycle state, progress percentage, and stage from status.json."""
        try:
            return self.job_manager.read_status(job_id)
        except Exception as e:
            return {"error": f"Failed to read status: {e}"}

    def get_job_errors(self, job_id: str) -> Dict[str, Any]:
        """Retrieve structured error reports from errors.json to guide scene repair."""
        try:
            return self.job_manager.read_errors(job_id)
        except Exception as e:
            return {"error": f"Failed to read errors: {e}"}

    def retry_scene(self, job_id: str, scene_id: str) -> Dict[str, Any]:
        """Re-validate, re-render, and re-composite only a repaired scene."""
        try:
            job_dir = self.job_manager.get_job_dir(job_id)
            plan = self.director_bridge.load_plan_manifest(job_dir)
        except Exception as e:
            return {"success": False, "error": str(e)}

        target_scene = next((s for s in plan.scenes if s.scene_id == scene_id), None)
        if not target_scene:
            return {"success": False, "error": f"Scene {scene_id} not found in plan"}

        # Re-render scene
        res = self.parser_omega.execute_scene(job_dir, target_scene)
        if not res.get("success"):
            err_msg = res.get("error", "Unknown error")
            self.job_manager.append_error(
                job_id,
                scene_id=scene_id,
                engine=target_scene.engine.value,
                stage="retry_scene",
                msg=err_msg,
                log_file=res.get("log_file"),
            )
            return {"success": False, "scene_id": scene_id, "error": err_msg}

        # Check if all scenes now have renders
        renders_dir = job_dir / "renders"
        all_outputs = []
        all_ok = True
        for s in plan.scenes:
            out = renders_dir / f"{s.scene_id}.mp4"
            if not out.exists():
                all_ok = False
                break
            all_outputs.append(out)

        if all_ok:
            try:
                final_mp4 = self.parser_omega.assemble_final_video(job_dir, all_outputs)
                self.job_manager.transition_state(
                    job_id,
                    "completed",
                    progress_pct=100,
                    current_stage="done",
                    output_path=str(final_mp4),
                )
            except Exception as e:
                return {
                    "success": True,
                    "scene_id": scene_id,
                    "error": f"Scene rendered, but assembly failed: {e}",
                }

        return {
            "success": True,
            "scene_id": scene_id,
            "output_path": res.get("output_path"),
            "all_scenes_ready": all_ok,
        }
