"""Keyframe extraction module for Visual Quality Assurance via FFmpeg."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class KeyframeExtractor:
    """Extracts keyframes from rendered video scenes for visual inspection and analysis."""

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

    def extract_frame(
        self,
        video_path: Path,
        timestamp: float,
        output_image: Path,
    ) -> Path:
        """
        Extract a single video frame at timestamp (seconds) using containerized FFmpeg.
        """
        output_image.parent.mkdir(parents=True, exist_ok=True)
        if output_image.exists():
            try:
                output_image.unlink()
            except OSError:
                pass
        try:
            os.chmod(output_image.parent, 0o777)
        except OSError:
            pass

        rel_vid = video_path.resolve().relative_to(self.workspace_dir.resolve())
        rel_out = output_image.resolve().relative_to(self.workspace_dir.resolve())

        cmd = [
            "docker", "compose", "-f", str(self.compose_file),
            "run", "--rm",
            "ffmpeg",
            "-y",
            "-ss", f"{timestamp:.3f}",
            "-i", f"/workspace/{rel_vid}",
            "-vframes", "1",
            "-q:v", "2",
            "-update", "1",
            f"/workspace/{rel_out}",
        ]

        res = subprocess.run(cmd, cwd=str(self.sandbox_dir), capture_output=True, text=True, timeout=60)
        if res.returncode != 0:
            raise RuntimeError(f"Frame extraction failed at {timestamp:.2f}s: {res.stderr}")

        if not output_image.exists() or output_image.stat().st_size == 0:
            raise FileNotFoundError(f"Extracted frame not found or empty at {output_image}")

        try:
            os.chmod(output_image, 0o666)
        except OSError:
            pass

        return output_image

    def extract_scene_keyframes(
        self,
        video_path: Path,
        scene_duration: float,
        output_dir: Path,
        additional_timestamps: Optional[List[float]] = None,
    ) -> Dict[str, Path]:
        """
        Extract representative keyframes for a scene:
        - frame_start.jpg
        - frame_middle.jpg
        - frame_end.jpg
        - any additional anomaly timestamps requested
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(output_dir, 0o777)
        except OSError:
            pass

        # Determine safe timestamps within scene duration
        dur = max(0.5, scene_duration)
        t_start = min(0.5, dur * 0.1)
        t_mid = dur * 0.5
        t_end = max(t_start + 0.1, dur - 0.5)

        frames: Dict[str, Path] = {}

        # 1. Start frame
        start_img = output_dir / "frame_start.jpg"
        self.extract_frame(video_path, t_start, start_img)
        frames["start"] = start_img

        # 2. Middle frame
        mid_img = output_dir / "frame_middle.jpg"
        self.extract_frame(video_path, t_mid, mid_img)
        frames["middle"] = mid_img

        # 3. End frame
        end_img = output_dir / "frame_end.jpg"
        self.extract_frame(video_path, t_end, end_img)
        frames["end"] = end_img

        # 4. Optional extra anomaly timestamps
        if additional_timestamps:
            for idx, t in enumerate(additional_timestamps, 1):
                safe_t = max(0.0, min(dur - 0.1, t))
                extra_img = output_dir / f"frame_anomaly_{idx:02d}.jpg"
                self.extract_frame(video_path, safe_t, extra_img)
                frames[f"anomaly_{idx:02d}"] = extra_img

        return frames
