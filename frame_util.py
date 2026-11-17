#!/usr/bin/env python3
"""Frame Utility (frame_util.py).

Decomposes output videos for all pipeline jobs into individual image frames,
and archives all jobs with their extracted frames into a root ZIP file.

Usage:
    python3 frame_util.py                     # Decompose all jobs and create jobs_with_frames.zip
    python3 frame_util.py --job <job_id>      # Decompose a specific job
    python3 frame_util.py --zip-only          # Archive existing jobs without re-decomposing
    python3 frame_util.py --format png        # Extract frames as PNG instead of JPG
    python3 frame_util.py --fps 5             # Subsample extraction at 5 frames/sec
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_SANDBOX_DIR = PROJECT_ROOT / "video_docker_sandbox"
DEFAULT_JOBS_DIR = DEFAULT_SANDBOX_DIR / "workspace" / "jobs"
DEFAULT_COMPOSE_FILE = DEFAULT_SANDBOX_DIR / "compose.yaml"
DEFAULT_ZIP_NAME = "jobs_with_frames.zip"


class FrameDecomposer:
    """Decomposes job output videos into frames and packages job archives."""

    def __init__(
        self,
        jobs_dir: Optional[Path] = None,
        sandbox_dir: Optional[Path] = None,
        compose_file: Optional[Path] = None,
    ) -> None:
        self.jobs_dir = Path(jobs_dir or DEFAULT_JOBS_DIR)
        self.sandbox_dir = Path(sandbox_dir or DEFAULT_SANDBOX_DIR)
        self.compose_file = Path(compose_file or DEFAULT_COMPOSE_FILE)
        self.workspace_dir = self.sandbox_dir / "workspace"

    def _run_docker_ffmpeg(self, args: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """Run FFmpeg via Docker Compose container."""
        cmd = [
            "docker", "compose", "-f", str(self.compose_file),
            "run", "--rm", "ffmpeg",
        ] + args
        return subprocess.run(
            cmd,
            cwd=str(self.sandbox_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def locate_output_video(self, job_dir: Path) -> Optional[Path]:
        """Locate the primary output video file for a job."""
        final_mp4 = job_dir / "output" / "final.mp4"
        if final_mp4.exists() and final_mp4.stat().st_size > 0:
            return final_mp4

        # Check for any other mp4 in output/
        out_dir = job_dir / "output"
        if out_dir.exists():
            mp4s = sorted(out_dir.glob("*.mp4"))
            if mp4s:
                return mp4s[0]

        # Fallback to scenes in renders/
        renders_dir = job_dir / "renders"
        if renders_dir.exists():
            mp4s = sorted(renders_dir.glob("*.mp4"))
            if mp4s:
                return mp4s[0]

        return None

    def decompose_video(
        self,
        video_path: Path,
        output_dir: Path,
        img_format: str = "jpg",
        fps: Optional[float] = None,
        quality: int = 2,
    ) -> Dict[str, Any]:
        """Decompose a single video into frames using containerized FFmpeg."""
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(output_dir, 0o777)
        except OSError:
            pass

        # Clean existing frames in output directory
        for f in output_dir.glob(f"frame_*.{img_format}"):
            try:
                f.unlink()
            except OSError:
                pass

        try:
            rel_vid = video_path.resolve().relative_to(self.workspace_dir.resolve())
            rel_out = output_dir.resolve().relative_to(self.workspace_dir.resolve())
        except ValueError:
            raise ValueError(f"Path must be within workspace directory: {video_path}")

        pattern = f"/workspace/{rel_out}/frame_%04d.{img_format}"
        cmd_args = ["-y", "-i", f"/workspace/{rel_vid}"]

        if fps is not None and fps > 0:
            cmd_args.extend(["-vf", f"fps={fps}"])

        if img_format.lower() in ("jpg", "jpeg"):
            cmd_args.extend(["-q:v", str(quality)])

        cmd_args.append(pattern)

        start_t = time.time()
        res = self._run_docker_ffmpeg(cmd_args, timeout=300)
        dur_s = time.time() - start_t

        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg frame decomposition failed: {res.stderr}")

        # Ensure permissions
        extracted_frames = sorted(output_dir.glob(f"frame_*.{img_format}"))
        for frame in extracted_frames:
            try:
                os.chmod(frame, 0o666)
            except OSError:
                pass

        total_bytes = sum(f.stat().st_size for f in extracted_frames)

        return {
            "success": True,
            "frame_count": len(extracted_frames),
            "output_dir": str(output_dir),
            "format": img_format,
            "total_bytes": total_bytes,
            "elapsed_seconds": round(dur_s, 2),
        }

    def decompose_job(
        self,
        job_dir: Path,
        img_format: str = "jpg",
        fps: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Decompose the output video of a specific job directory."""
        video_file = self.locate_output_video(job_dir)
        if not video_file:
            return {
                "job_id": job_dir.name,
                "success": False,
                "error": "No output video found",
                "frame_count": 0,
            }

        frames_dir = job_dir / "frames"
        res = self.decompose_video(
            video_path=video_file,
            output_dir=frames_dir,
            img_format=img_format,
            fps=fps,
        )
        res["job_id"] = job_dir.name
        res["video_file"] = str(video_file)
        return res

    def decompose_all_jobs(
        self,
        img_format: str = "jpg",
        fps: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Decompose videos across all job directories."""
        results = []
        if not self.jobs_dir.exists():
            print(f"Jobs directory does not exist: {self.jobs_dir}")
            return results

        job_dirs = sorted([
            p for p in self.jobs_dir.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        ])

        print(f"Scanning {len(job_dirs)} job directories in: {self.jobs_dir}")
        for job_dir in job_dirs:
            video_file = self.locate_output_video(job_dir)
            if not video_file:
                continue

            print(f"-> Decomposing Job [{job_dir.name}] ({video_file.name})...", end=" ", flush=True)
            try:
                res = self.decompose_job(job_dir, img_format=img_format, fps=fps)
                print(f"DONE ({res['frame_count']} frames in {res.get('elapsed_seconds', 0)}s)")
                results.append(res)
            except Exception as e:
                print(f"FAILED ({e})")
                results.append({
                    "job_id": job_dir.name,
                    "success": False,
                    "error": str(e),
                    "frame_count": 0,
                })

        return results

    def create_jobs_zip(
        self,
        output_zip: Path,
        include_all_jobs: bool = True,
    ) -> Path:
        """Package jobs and their frames into a ZIP archive."""
        output_zip = output_zip.resolve()
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        if output_zip.exists():
            output_zip.unlink()

        print(f"\nCreating ZIP archive: {output_zip}...")
        start_t = time.time()

        job_dirs = sorted([
            p for p in self.jobs_dir.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        ])

        file_count = 0
        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for job_dir in job_dirs:
                # If include_all_jobs is False, skip jobs without output video or frames
                has_frames = (job_dir / "frames").exists() and any((job_dir / "frames").iterdir())
                has_video = self.locate_output_video(job_dir) is not None
                if not include_all_jobs and not (has_frames or has_video):
                    continue

                for root, _, files in os.walk(job_dir):
                    root_path = Path(root)
                    for file in files:
                        file_path = root_path / file
                        # Arcname relative to jobs directory: e.g. "jobs/<job_id>/frames/frame_0001.jpg"
                        rel_path = file_path.relative_to(self.jobs_dir.parent)
                        zf.write(file_path, arcname=str(rel_path))
                        file_count += 1

        elapsed = round(time.time() - start_t, 2)
        size_mb = output_zip.stat().st_size / (1024 * 1024)
        print(f"Archive created: {output_zip.name} ({file_count} files, {size_mb:.2f} MB in {elapsed}s)")
        return output_zip


def main() -> None:
    parser = argparse.ArgumentParser(description="Decompose job videos into frames and zip jobs.")
    parser.add_argument("--job", type=str, help="Specific job ID to decompose")
    parser.add_argument("--format", type=str, default="jpg", choices=["jpg", "png"], help="Frame image format")
    parser.add_argument("--fps", type=float, default=None, help="Optional frame rate for extraction")
    parser.add_argument("--quality", type=int, default=2, help="JPEG quality (2=best, 31=worst)")
    parser.add_argument("--zip-only", action="store_true", help="Skip decomposition and create ZIP only")
    parser.add_argument("--no-zip", action="store_true", help="Skip creating ZIP archive")
    parser.add_argument("--output-zip", type=str, default=str(PROJECT_ROOT / DEFAULT_ZIP_NAME), help="Output ZIP path")
    parser.add_argument("--jobs-dir", type=str, default=str(DEFAULT_JOBS_DIR), help="Path to jobs workspace")

    args = parser.parse_args()
    decomposer = FrameDecomposer(jobs_dir=Path(args.jobs_dir))

    if not args.zip_only:
        if args.job:
            job_path = decomposer.jobs_dir / args.job
            if not job_path.exists():
                print(f"Error: Job {args.job} not found at {job_path}")
                sys.exit(1)
            print(f"Decomposing single job: {args.job}")
            res = decomposer.decompose_job(job_path, img_format=args.format, fps=args.fps)
            print(f"Result: {res}")
        else:
            print("=" * 70)
            print("DECOMPOSING OUTPUT VIDEOS INTO FRAMES")
            print("=" * 70)
            results = decomposer.decompose_all_jobs(img_format=args.format, fps=args.fps)
            total_frames = sum(r.get("frame_count", 0) for r in results if r.get("success"))
            print(f"\nDecomposed {len(results)} job videos into {total_frames} total frames.")

    if not args.no_zip:
        zip_path = Path(args.output_zip)
        decomposer.create_jobs_zip(output_zip=zip_path, include_all_jobs=True)
        print(f"\nFinal ZIP ready at: {zip_path.resolve()}")


if __name__ == "__main__":
    main()
