"""Local MCP Tool implementations for external AI coding agents (Codex / Antigravity)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_video_pipeline.core.director import ExternalDirectorBridge
from ai_video_pipeline.jobs.manager import JobManager
from ai_video_pipeline.media.compositor import VideoCompositor
from ai_video_pipeline.media.text_splash import TextSplashGenerator
from ai_video_pipeline.media.tts import TextToSpeechService
from ai_video_pipeline.parsers.omega import ParserOmega
from ai_video_pipeline.parsers.theta import ParserTheta
from ai_video_pipeline.schemas.job_schemas import (
    AudioPlanModel,
    JobErrorReportModel,
    JobRequestModel,
    JobStatusModel,
    SceneErrorModel,
    StoryboardModel,
    ValidationResultModel,
)
from ai_video_pipeline.schemas.models import (
    AnimationEngine,
    JobState,
    PlanManifest,
    WordTimestamp,
)


class PipelineMCPTools:
    """Defines tool interfaces exposed via Model Context Protocol (MCP) to external AI agents."""

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        job_manager: Optional[JobManager] = None,
        parser_omega: Optional[ParserOmega] = None,
        director_bridge: Optional[ExternalDirectorBridge] = None,
        parser_theta: Optional[ParserTheta] = None,
        tts_service: Optional[TextToSpeechService] = None,
        text_splash: Optional[TextSplashGenerator] = None,
        compositor: Optional[VideoCompositor] = None,
    ) -> None:
        self.workspace_root = workspace_root
        self.job_manager = job_manager or JobManager(workspace_root=self.workspace_root)
        self.parser_omega = parser_omega or ParserOmega()
        self.director_bridge = director_bridge or ExternalDirectorBridge()
        self.parser_theta = parser_theta or ParserTheta(workspace_root=self.job_manager.JOBS_ROOT.parent)
        self.tts_service = tts_service or TextToSpeechService()
        self.text_splash = text_splash or TextSplashGenerator()
        self.compositor = compositor or VideoCompositor()

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
            # Create Milestone 2 subdirectories
            for sub in ("audio", "captions"):
                (job_dir / sub).mkdir(parents=True, exist_ok=True)
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
        """Validate the AI-authored storyboard.json, scene code files, and audio_plan.json."""
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

        # Validate audio_plan if present
        audio_file = job_dir / "audio_plan.json"
        if audio_file.exists():
            try:
                plan_manifest = self.director_bridge.load_plan_manifest(job_dir)
                audio_plan = self.parser_theta.load_audio_plan(job_dir)
                audio_ok, audio_errs = self.parser_theta.validate_audio_plan(job_dir, plan_manifest, audio_plan)
                if not audio_ok:
                    issues.extend(audio_errs)
            except Exception as e:
                issues.append(f"Audio plan validation exception: {e}")

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

    def _execute_postproduction(
        self,
        job_id: str,
        job_dir: Path,
        plan: PlanManifest,
        scene_outputs: List[Path],
    ) -> Dict[str, Any]:
        """
        Execute Parser Theta, Kokoro TTS, Text Splash captions, and FFmpeg audio/video composition.
        """
        # Load audio plan
        audio_plan = self.parser_theta.load_audio_plan(job_dir)
        audio_dir = job_dir / "audio"
        captions_dir = job_dir / "captions"
        audio_dir.mkdir(parents=True, exist_ok=True)
        captions_dir.mkdir(parents=True, exist_ok=True)

        # -------------------------------------------------------------
        # Stage 1: Narration Generation (Kokoro TTS)
        # -------------------------------------------------------------
        self.job_manager.transition_state(
            job_id,
            "narration_generation",
            progress_pct=50,
            current_stage="synthesizing_narration",
        )

        # Match narration segments by scene
        narr_by_scene = {n.scene_id: n for n in audio_plan.narration_segments}
        scene_narrations: List[Tuple[Path, float]] = []
        all_word_timestamps: List[WordTimestamp] = []

        voice_id = audio_plan.voice_id or self.tts_service.select_voice_profile(plan.category)
        language = audio_plan.language or "en"

        for scene in plan.scenes:
            scene_dur = scene.end_time - scene.start_time
            # Determine script text
            if scene.scene_id in narr_by_scene:
                script_text = narr_by_scene[scene.scene_id].text
                scene_voice = narr_by_scene[scene.scene_id].voice_id or voice_id
            else:
                script_text = scene.narration_text or ""
                scene_voice = voice_id

            if not script_text.strip():
                # Generate a short silent padding wav if no narration
                silent_wav = audio_dir / f"{scene.scene_id}_silent.wav"
                cmd = [
                    "docker", "compose", "-f", str(self.compositor.compose_file),
                    "run", "--rm", "ffmpeg", "-y",
                    "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", f"{scene_dur:.4f}",
                    f"/workspace/{silent_wav.resolve().relative_to(self.compositor.workspace_dir.resolve())}",
                ]
                subprocess.run(cmd, cwd=str(self.compositor.sandbox_dir), capture_output=True)
                scene_narrations.append((silent_wav, scene_dur))
                continue

            scene_wav = audio_dir / f"{scene.scene_id}_narration.wav"
            try:
                _, timestamps, meta = self.tts_service.generate_narration(
                    script_text=script_text,
                    voice_id=scene_voice,
                    language=language,
                    output_file=scene_wav,
                    scene_duration_limit=scene_dur + 0.1,  # allow slight epsilon
                )
            except Exception as e:
                err_msg = f"Narration generation failed for scene {scene.scene_id}: {e}"
                self.job_manager.append_error(
                    job_id, scene.scene_id, "kokoro_tts", "narration_generation", err_msg
                )
                self.job_manager.transition_state(job_id, "failed", errors=[err_msg])
                self.job_manager.release_lock(job_id)
                return {"status": "failed", "job_id": job_id, "error": err_msg}

            scene_narrations.append((scene_wav, scene_dur))

            # Shift word timestamps by scene start_time on global timeline
            for wt in timestamps:
                all_word_timestamps.append(
                    WordTimestamp(
                        word=wt.word,
                        start_time=round(wt.start_time + scene.start_time, 3),
                        end_time=round(wt.end_time + scene.start_time, 3),
                    )
                )

        # Assemble full continuous narration track
        narration_full = audio_dir / "narration_full.wav"
        try:
            self.compositor.assemble_narration_track(scene_narrations, narration_full)
        except Exception as e:
            err_msg = f"Narration track assembly failed: {e}"
            self.job_manager.append_error(job_id, None, "ffmpeg", "narration_assembly", err_msg)
            self.job_manager.transition_state(job_id, "failed", errors=[err_msg])
            self.job_manager.release_lock(job_id)
            return {"status": "failed", "job_id": job_id, "error": err_msg}

        # -------------------------------------------------------------
        # Stage 2: Caption Generation (Text Splash)
        # -------------------------------------------------------------
        self.job_manager.transition_state(
            job_id,
            "caption_generation",
            progress_pct=70,
            current_stage="generating_animated_captions",
        )

        captions_ass = captions_dir / "captions.ass"
        try:
            self.text_splash.generate_ass_subtitles(
                word_timestamps=all_word_timestamps,
                output_file=captions_ass,
                aspect_ratio=plan.aspect_ratio,
                style_config=audio_plan.caption_style,
                words_per_phrase=4,
            )
        except Exception as e:
            err_msg = f"Caption generation failed: {e}"
            self.job_manager.append_error(job_id, None, "text_splash", "caption_generation", err_msg)
            self.job_manager.transition_state(job_id, "failed", errors=[err_msg])
            self.job_manager.release_lock(job_id)
            return {"status": "failed", "job_id": job_id, "error": err_msg}

        # -------------------------------------------------------------
        # Stage 3: Audio Mixing (BGM, SFX, Narration)
        # -------------------------------------------------------------
        self.job_manager.transition_state(
            job_id,
            "audio_mixing",
            progress_pct=82,
            current_stage="mixing_audio_tracks",
        )

        bgm_resolved = None
        if audio_plan.bgm_track:
            try:
                bgm_resolved = self.parser_theta.resolve_audio_asset(job_dir, audio_plan.bgm_track)
            except Exception as e:
                err_msg = f"Could not resolve BGM asset '{audio_plan.bgm_track}': {e}"
                self.job_manager.append_error(job_id, None, "parser_theta", "audio_mixing", err_msg)
                self.job_manager.transition_state(job_id, "failed", errors=[err_msg])
                self.job_manager.release_lock(job_id)
                return {"status": "failed", "job_id": job_id, "error": err_msg}

        sfx_resolved_list = []
        for sfx in audio_plan.sfx_cues:
            if sfx.source_file:
                try:
                    sfx_path = self.parser_theta.resolve_audio_asset(job_dir, sfx.source_file)
                    sfx_resolved_list.append({
                        "source_file": str(sfx_path),
                        "start_time": sfx.start_time,
                        "volume": sfx.volume_level,
                    })
                except Exception as e:
                    err_msg = f"Could not resolve SFX asset '{sfx.source_file}': {e}"
                    self.job_manager.append_error(job_id, None, "parser_theta", "audio_mixing", err_msg)
                    self.job_manager.transition_state(job_id, "failed", errors=[err_msg])
                    self.job_manager.release_lock(job_id)
                    return {"status": "failed", "job_id": job_id, "error": err_msg}

        mixed_audio = audio_dir / "mixed_audio.wav"
        try:
            self.compositor.mix_audio_tracks(
                narration=narration_full,
                total_duration=plan.target_duration_seconds,
                output_file=mixed_audio,
                bgm_path=bgm_resolved,
                bgm_volume=audio_plan.bgm_volume,
                bgm_fade_in=audio_plan.bgm_fade_in,
                bgm_fade_out=audio_plan.bgm_fade_out,
                sfx_cues=sfx_resolved_list,
            )
        except Exception as e:
            err_msg = f"Audio mixing failed: {e}"
            self.job_manager.append_error(job_id, None, "ffmpeg", "audio_mixing", err_msg)
            self.job_manager.transition_state(job_id, "failed", errors=[err_msg])
            self.job_manager.release_lock(job_id)
            return {"status": "failed", "job_id": job_id, "error": err_msg}

        # -------------------------------------------------------------
        # Stage 4: Video Composition & Captions Burning
        # -------------------------------------------------------------
        self.job_manager.transition_state(
            job_id,
            "video_composition",
            progress_pct=90,
            current_stage="assembling_final_video",
        )

        visual_concat = job_dir / "renders" / "concatenated_visual.mp4"
        try:
            self.compositor.concatenate_video_scenes(scene_outputs, visual_concat, job_dir=job_dir)
        except Exception as e:
            err_msg = f"Visual concatenation failed: {e}"
            self.job_manager.append_error(job_id, None, "ffmpeg", "video_composition", err_msg)
            self.job_manager.transition_state(job_id, "failed", errors=[err_msg])
            self.job_manager.release_lock(job_id)
            return {"status": "failed", "job_id": job_id, "error": err_msg}

        final_mp4 = job_dir / "output" / "final.mp4"
        try:
            self.compositor.assemble_final_video(
                video_path=visual_concat,
                audio_track=mixed_audio,
                output_file=final_mp4,
                captions_path=captions_ass if captions_ass.exists() else None,
            )
        except Exception as e:
            err_msg = f"Final assembly failed: {e}"
            self.job_manager.append_error(job_id, None, "ffmpeg", "video_composition", err_msg)
            self.job_manager.transition_state(job_id, "failed", errors=[err_msg])
            self.job_manager.release_lock(job_id)
            return {"status": "failed", "job_id": job_id, "error": err_msg}

        # -------------------------------------------------------------
        # Stage 5: Quality Inspection via FFprobe
        # -------------------------------------------------------------
        try:
            probe_info = self.compositor.probe_media(final_mp4)
            duration = float(probe_info.get("format", {}).get("duration", 0.0))
            streams = probe_info.get("streams", [])
            has_video = any(s.get("codec_type") == "video" for s in streams)
            has_audio = any(s.get("codec_type") == "audio" for s in streams)

            if not has_video or not has_audio or duration <= 0:
                raise ValueError(
                    f"Final MP4 validation failed: has_video={has_video}, has_audio={has_audio}, duration={duration}"
                )
        except Exception as e:
            err_msg = f"Final media verification failed: {e}"
            self.job_manager.append_error(job_id, None, "ffprobe", "quality_validation", err_msg)
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
            "scenes_completed": len(plan.scenes),
            "duration": duration,
            "has_narration": True,
            "has_captions": captions_ass.exists(),
        }

    def execute_job(self, job_id: str) -> Dict[str, Any]:
        """Trigger the deterministic Python rendering, TTS, and composition pipeline."""
        try:
            job_dir = self.job_manager.get_job_dir(job_id)
        except Exception as e:
            return {"status": "failed", "error": str(e)}

        status = self.job_manager.read_status(job_id)
        if status.get("state") not in ("validated", "created"):
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
        renders_dir = job_dir / "renders"

        for idx, scene in enumerate(plan.scenes):
            scene_out = renders_dir / f"{scene.scene_id}.mp4"
            if scene_out.exists() and scene_out.stat().st_size > 0:
                # Reuse existing valid scene render
                scene_outputs.append(scene_out)
                continue

            pct = int(10 + (idx / total_scenes) * 40)
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

        # If audio_plan.json exists, execute full Milestone 2 postproduction
        audio_plan_file = job_dir / "audio_plan.json"
        if audio_plan_file.exists():
            return self._execute_postproduction(job_id, job_dir, plan, scene_outputs)

        # Milestone 1 visual assembly fallback when no audio_plan is present
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

    def retry_postproduction(self, job_id: str) -> Dict[str, Any]:
        """
        Recover from a failed audio, caption, or mixing stage without re-rendering animation scenes.
        """
        try:
            job_dir = self.job_manager.get_job_dir(job_id)
            plan = self.director_bridge.load_plan_manifest(job_dir)
        except Exception as e:
            return {"status": "failed", "error": str(e)}

        renders_dir = job_dir / "renders"
        scene_outputs: List[Path] = []
        for scene in plan.scenes:
            sc_out = renders_dir / f"{scene.scene_id}.mp4"
            if not sc_out.exists() or sc_out.stat().st_size == 0:
                return {
                    "status": "failed",
                    "error": f"Rendered video for scene '{scene.scene_id}' is missing. Run execute_job first.",
                }
            scene_outputs.append(sc_out)

        return self._execute_postproduction(job_id, job_dir, plan, scene_outputs)

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
            audio_plan_file = job_dir / "audio_plan.json"
            if audio_plan_file.exists():
                post_res = self._execute_postproduction(job_id, job_dir, plan, all_outputs)
                return {
                    "success": post_res.get("status") == "completed",
                    "scene_id": scene_id,
                    "output_path": post_res.get("output_path"),
                    "all_scenes_ready": True,
                }
            else:
                try:
                    final_mp4 = self.parser_omega.assemble_final_video(job_dir, all_outputs)
                    self.job_manager.transition_state(
                        job_id,
                        "completed",
                        progress_pct=100,
                        current_stage="done",
                        output_path=str(final_mp4),
                    )
                    return {
                        "success": True,
                        "scene_id": scene_id,
                        "output_path": str(final_mp4),
                        "all_scenes_ready": True,
                    }
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
            "all_scenes_ready": False,
        }
