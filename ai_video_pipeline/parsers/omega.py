"""Parser Omega (Ω): Ingests and validates external AI-generated animation source code."""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_video_pipeline.schemas.models import (
    AnimationEngine,
    PlanManifest,
    SceneSpec,
)


class BaseAnimationCodeHandler(ABC):
    """Abstract code handler for engine-specific animation scripts."""

    @abstractmethod
    def validate_code_file(self, code_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate syntax and API safety of the AI-generated code file."""
        pass

    @abstractmethod
    def prepare_execution_context(self, code_path: Path, output_dir: Path) -> dict:
        """Prepare headless execution context and staging for the target engine."""
        pass


class BlenderScriptHandler(BaseAnimationCodeHandler):
    """Blender bpy Python script validator and environment prepper."""

    def validate_code_file(self, code_path: Path) -> Tuple[bool, Optional[str]]:
        if not code_path.exists():
            return False, f"Code file {code_path} does not exist"
        try:
            content = code_path.read_text(encoding="utf-8")
            ast.parse(content, filename=str(code_path))
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error in Blender script {code_path.name}: {e}"
        except Exception as e:
            return False, f"Failed to validate Blender script: {e}"

    def prepare_execution_context(self, code_path: Path, output_dir: Path) -> dict:
        output_dir.mkdir(parents=True, exist_ok=True)
        return {"script": str(code_path), "output_dir": str(output_dir)}


class RemotionComponentHandler(BaseAnimationCodeHandler):
    """Three.js, GSAP, and Remotion TSX component validator and prepper."""

    def validate_code_file(self, code_path: Path) -> Tuple[bool, Optional[str]]:
        if not code_path.exists():
            return False, f"Code file {code_path} does not exist"
        if code_path.suffix not in (".tsx", ".ts", ".jsx", ".js"):
            return False, f"Unsupported Remotion script extension: {code_path.suffix}"
        content = code_path.read_text(encoding="utf-8")
        if not content.strip():
            return False, f"Remotion script {code_path.name} is empty"
        return True, None

    def prepare_execution_context(self, code_path: Path, output_dir: Path) -> dict:
        output_dir.mkdir(parents=True, exist_ok=True)
        return {"entry": str(code_path), "output_dir": str(output_dir)}


class ManimScriptHandler(BaseAnimationCodeHandler):
    """Manim Community Edition Python scene validator and prepper."""

    def validate_code_file(self, code_path: Path) -> Tuple[bool, Optional[str]]:
        if not code_path.exists():
            return False, f"Code file {code_path} does not exist"
        if code_path.suffix != ".py":
            return False, f"Manim script must be a .py file, got {code_path.suffix}"
        try:
            content = code_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(code_path))
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            if not classes:
                return False, f"No scene classes defined in {code_path.name}"
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error in Manim script {code_path.name}: {e}"
        except Exception as e:
            return False, f"Failed to validate Manim script: {e}"

    def find_scene_class(self, code_path: Path) -> str:
        """Find the main Scene class defined in the script."""
        content = code_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(code_path))
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        if not classes:
            raise ValueError(f"No classes found in {code_path}")
        # Prefer classes ending with 'Scene'
        scene_candidates = [c for c in classes if "Scene" in c]
        if scene_candidates:
            return scene_candidates[0]
        return classes[0]

    def prepare_execution_context(self, code_path: Path, output_dir: Path) -> dict:
        output_dir.mkdir(parents=True, exist_ok=True)
        scene_class = self.find_scene_class(code_path)
        return {"script": str(code_path), "scene_class": scene_class, "output_dir": str(output_dir)}


class DockerEngineRunner:
    """Manages Docker Compose container executions for animation engines."""

    def __init__(
        self,
        sandbox_dir: Optional[Path] = None,
        compose_file: Optional[Path] = None,
    ) -> None:
        self.sandbox_dir = sandbox_dir or (
            Path(__file__).resolve().parent.parent.parent / "video_docker_sandbox"
        )
        self.compose_file = compose_file or (self.sandbox_dir / "compose.yaml")
        self.workspace_dir = self.sandbox_dir / "workspace"

    def run_docker(
        self,
        args: List[str],
        log_file: Optional[Path] = None,
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """
        Execute a docker compose command safely via argument lists (no shell=True).
        """
        base_cmd = ["docker", "compose", "-f", str(self.compose_file)]
        full_cmd = base_cmd + args

        res = subprocess.run(
            full_cmd,
            cwd=str(self.sandbox_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"=== Command: {' '.join(full_cmd)} ===\n")
                f.write(f"=== Exit Code: {res.returncode} ===\n")
                if res.stdout:
                    f.write("=== STDOUT ===\n" + res.stdout + "\n")
                if res.stderr:
                    f.write("=== STDERR ===\n" + res.stderr + "\n")

        return res


class ParserOmega:
    """Parser Omega (Ω): Consumes AI-generated animation source code and prepares scene manifests."""

    def __init__(
        self,
        runner: Optional[DockerEngineRunner] = None,
        sandbox_dir: Optional[Path] = None,
    ) -> None:
        self.runner = runner or DockerEngineRunner(sandbox_dir=sandbox_dir)
        self.blender_handler = BlenderScriptHandler()
        self.remotion_handler = RemotionComponentHandler()
        self.manim_handler = ManimScriptHandler()

    def get_handler(self, engine: AnimationEngine) -> BaseAnimationCodeHandler:
        if engine == AnimationEngine.MANIM:
            return self.manim_handler
        elif engine == AnimationEngine.BLENDER:
            return self.blender_handler
        elif engine == AnimationEngine.THREE_JS_REMOTION:
            return self.remotion_handler
        else:
            raise ValueError(f"Unsupported animation engine: {engine}")

    def ingest_scene_animation(self, job_dir: Path, scene: SceneSpec) -> Path:
        """Locate, ingest, and verify AI-generated animation source file for a scene."""
        if not scene.code_file and not scene.inline_code:
            raise ValueError(f"Scene {scene.scene_id} has neither code_file nor inline_code")

        scenes_dir = job_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)

        if scene.code_file:
            code_path = scenes_dir / scene.code_file
            if not code_path.exists():
                alt = job_dir / scene.code_file
                if alt.exists():
                    return alt
                raise FileNotFoundError(f"Code file not found: {code_path}")
            return code_path
        else:
            # Inline code: save to a default filename
            ext = ".py" if scene.engine in (AnimationEngine.MANIM, AnimationEngine.BLENDER) else ".tsx"
            code_path = scenes_dir / f"{scene.scene_id}{ext}"
            code_path.write_text(scene.inline_code or "", encoding="utf-8")
            return code_path

    def validate_scene_code(self, scene: SceneSpec, code_path: Path) -> Tuple[bool, Optional[str]]:
        """Dispatch validation check to the appropriate engine code handler."""
        handler = self.get_handler(scene.engine)
        return handler.validate_code_file(code_path)

    def compile_animation_manifest(self, job_dir: Path, plan: PlanManifest) -> dict:
        """Assemble rendering execution manifests for all scenes in the plan."""
        manifest = {"job_id": plan.job_id, "scenes": []}
        for scene in plan.scenes:
            code_path = self.ingest_scene_animation(job_dir, scene)
            valid, err = self.validate_scene_code(scene, code_path)
            manifest["scenes"].append({
                "scene_id": scene.scene_id,
                "engine": scene.engine.value,
                "code_path": str(code_path),
                "is_valid": valid,
                "error": err,
            })
        return manifest

    def execute_scene(self, job_dir: Path, scene: SceneSpec) -> Dict[str, Any]:
        """
        Execute an animation scene in its dedicated Docker engine container.
        """
        code_path = self.ingest_scene_animation(job_dir, scene)
        valid, err = self.validate_scene_code(scene, code_path)
        if not valid:
            return {
                "scene_id": scene.scene_id,
                "success": False,
                "output_path": None,
                "error": f"Validation failed: {err}",
                "log_file": None,
            }

        log_path = job_dir / "logs" / f"{scene.scene_id}.log"
        renders_dir = job_dir / "renders"
        renders_dir.mkdir(parents=True, exist_ok=True)
        final_scene_output = renders_dir / f"{scene.scene_id}.mp4"

        try:
            # Determine path relative to sandbox workspace
            workspace_dir = self.runner.workspace_dir
            rel_code = code_path.resolve().relative_to(workspace_dir.resolve())
            rel_renders = renders_dir.resolve().relative_to(workspace_dir.resolve())
        except ValueError:
            # If job_dir is outside workspace_dir, copy to workspace/jobs/<job_id>
            job_id = job_dir.name
            target_job_dir = workspace_dir / "jobs" / job_id
            target_scenes = target_job_dir / "scenes"
            target_scenes.mkdir(parents=True, exist_ok=True)
            target_code = target_scenes / code_path.name
            shutil.copy2(code_path, target_code)
            rel_code = target_code.relative_to(workspace_dir)
            target_renders = target_job_dir / "renders"
            target_renders.mkdir(parents=True, exist_ok=True)
            rel_renders = target_renders.relative_to(workspace_dir)

        if scene.engine == AnimationEngine.MANIM:
            scene_class = self.manim_handler.find_scene_class(code_path)
            media_dir_arg = f"/manim/{rel_renders}/manim_out"
            output_filename = f"{scene.scene_id}.mp4"

            args = [
                "run",
                "--rm",
                "manim",
                "-ql",
                "--disable_caching",
                "-o",
                output_filename,
                "--media_dir",
                media_dir_arg,
                str(rel_code),
                scene_class,
            ]

            proc = self.runner.run_docker(args, log_file=log_path)
            if proc.returncode != 0:
                return {
                    "scene_id": scene.scene_id,
                    "success": False,
                    "output_path": None,
                    "error": f"Manim render failed with exit code {proc.returncode}. Check logs.",
                    "log_file": str(log_path),
                }

            # Locate rendered mp4 in media_dir
            # Look inside workspace_dir / rel_renders / manim_out / videos
            manim_media_local = workspace_dir / rel_renders / "manim_out"
            found_mp4s = list(manim_media_local.glob("**/*.mp4"))
            # Filter out partial movie files
            real_mp4s = [p for p in found_mp4s if "partial_movie_files" not in str(p)]
            if not real_mp4s:
                return {
                    "scene_id": scene.scene_id,
                    "success": False,
                    "output_path": None,
                    "error": "Manim completed but no output MP4 found",
                    "log_file": str(log_path),
                }

            # Copy to target final scene output
            shutil.copy2(real_mp4s[0], final_scene_output)
            return {
                "scene_id": scene.scene_id,
                "success": True,
                "output_path": str(final_scene_output),
                "error": None,
                "log_file": str(log_path),
            }

        elif scene.engine == AnimationEngine.BLENDER:
            args = [
                "run",
                "--rm",
                "blender",
                "blender",
                "-b",
                "-t",
                "2",
                "-P",
                f"/workspace/{rel_code}",
            ]
            proc = self.runner.run_docker(args, log_file=log_path)
            if proc.returncode != 0:
                return {
                    "scene_id": scene.scene_id,
                    "success": False,
                    "output_path": None,
                    "error": f"Blender render failed with exit code {proc.returncode}",
                    "log_file": str(log_path),
                }
            return {
                "scene_id": scene.scene_id,
                "success": True,
                "output_path": str(final_scene_output),
                "error": None,
                "log_file": str(log_path),
            }

        elif scene.engine == AnimationEngine.THREE_JS_REMOTION:
            args = ["run", "--rm", "remotion", "npm", "run", "smoke"]
            proc = self.runner.run_docker(args, log_file=log_path)
            if proc.returncode != 0:
                return {
                    "scene_id": scene.scene_id,
                    "success": False,
                    "output_path": None,
                    "error": f"Remotion render failed with exit code {proc.returncode}",
                    "log_file": str(log_path),
                }
            return {
                "scene_id": scene.scene_id,
                "success": True,
                "output_path": str(final_scene_output),
                "error": None,
                "log_file": str(log_path),
            }

        else:
            return {
                "scene_id": scene.scene_id,
                "success": False,
                "output_path": None,
                "error": f"Unsupported animation engine: {scene.engine}",
                "log_file": str(log_path),
            }

    def assemble_final_video(self, job_dir: Path, scene_outputs: List[Path]) -> Path:
        """
        Assemble rendered scene outputs into final.mp4 in the output/ directory.
        """
        out_dir = job_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(out_dir, 0o777)
        except OSError:
            pass
        final_mp4 = out_dir / "final.mp4"

        if not scene_outputs:
            raise ValueError("No scene outputs provided to assemble")

        if len(scene_outputs) == 1:
            shutil.copy2(scene_outputs[0], final_mp4)
            return final_mp4

        # Multiple scenes: concatenate using FFmpeg container
        workspace_dir = self.runner.workspace_dir
        concat_txt = job_dir / "renders" / "concat.txt"
        
        lines = []
        for s in scene_outputs:
            rel = s.resolve().relative_to(workspace_dir.resolve())
            lines.append(f"file '/workspace/{rel}'")
        concat_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            os.chmod(concat_txt, 0o666)
        except OSError:
            pass

        rel_concat = concat_txt.resolve().relative_to(workspace_dir.resolve())
        rel_final = final_mp4.resolve().relative_to(workspace_dir.resolve())

        args = [
            "run",
            "--rm",
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            f"/workspace/{rel_concat}",
            "-c",
            "copy",
            f"/workspace/{rel_final}",
        ]

        log_path = job_dir / "logs" / "ffmpeg_concat.log"
        proc = self.runner.run_docker(args, log_file=log_path)
        if proc.returncode != 0:
            # Fallback re-encode if stream copy fails
            args_reencode = [
                "run",
                "--rm",
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                f"/workspace/{rel_concat}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                f"/workspace/{rel_final}",
            ]
            proc_re = self.runner.run_docker(args_reencode, log_file=log_path)
            if proc_re.returncode != 0:
                raise RuntimeError(f"FFmpeg concat failed: {proc_re.stderr}")

        return final_mp4
