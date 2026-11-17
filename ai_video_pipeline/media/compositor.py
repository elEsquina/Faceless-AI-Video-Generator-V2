"""Video and audio track composition and final MP4 export via FFmpeg Docker container."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_video_pipeline.schemas.job_schemas import AudioPlanModel
from ai_video_pipeline.schemas.models import (
    AudioCue,
    PlanManifest,
    RenderedSceneAsset,
)


class VideoCompositor:
    """Merges rendered visual scenes, audio tracks, and animated captions into a final MP4."""

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

    def _run_ffmpeg(
        self,
        args: List[str],
        log_file: Optional[Path] = None,
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """Execute command in ffmpeg Docker service via argument list."""
        cmd = [
            "docker", "compose", "-f", str(self.compose_file),
            "run", "--rm",
            "ffmpeg",
        ] + args

        res = subprocess.run(
            cmd,
            cwd=str(self.sandbox_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"=== FFmpeg Command: {' '.join(cmd)} ===\n")
                f.write(f"=== Exit Code: {res.returncode} ===\n")
                if res.stdout:
                    f.write("=== STDOUT ===\n" + res.stdout + "\n")
                if res.stderr:
                    f.write("=== STDERR ===\n" + res.stderr + "\n")

        return res

    def concatenate_video_scenes(
        self,
        scenes: List[Path],
        output_file: Path,
        job_dir: Optional[Path] = None,
    ) -> Path:
        """Concatenate rendered video scene segments into a single continuous video stream."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(output_file.parent, 0o777)
        except OSError:
            pass

        if len(scenes) == 1:
            shutil.copy2(scenes[0], output_file)
            return output_file

        concat_txt = (job_dir or output_file.parent) / "renders" / "video_concat.txt"
        concat_txt.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        for s in scenes:
            rel = s.resolve().relative_to(self.workspace_dir.resolve())
            lines.append(f"file '/workspace/{rel}'")
        concat_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

        rel_concat = concat_txt.resolve().relative_to(self.workspace_dir.resolve())
        rel_out = output_file.resolve().relative_to(self.workspace_dir.resolve())

        args = [
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", f"/workspace/{rel_concat}",
            "-c", "copy",
            f"/workspace/{rel_out}",
        ]

        res = self._run_ffmpeg(args)
        if res.returncode != 0:
            # Re-encode fallback if stream copy fails
            args_reencode = [
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", f"/workspace/{rel_concat}",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                f"/workspace/{rel_out}",
            ]
            res_re = self._run_ffmpeg(args_reencode)
            if res_re.returncode != 0:
                raise RuntimeError(f"FFmpeg scene concatenation failed: {res_re.stderr}")

        return output_file

    def assemble_narration_track(
        self,
        scene_narrations: List[Tuple[Path, float]],  # List of (wav_path, scene_duration)
        output_file: Path,
    ) -> Path:
        """
        Pad and concatenate per-scene narration WAVs so each narration aligns with its scene start time.
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(output_file.parent, 0o777)
        except OSError:
            pass

        if not scene_narrations:
            raise ValueError("No narration segments provided to assemble")

        padded_wavs = []
        for idx, (wav_path, scene_dur) in enumerate(scene_narrations):
            padded_wav = output_file.parent / f"padded_scene_{idx:03d}.wav"
            rel_in = wav_path.resolve().relative_to(self.workspace_dir.resolve())
            rel_out = padded_wav.resolve().relative_to(self.workspace_dir.resolve())

            # Pad with silence to match exact scene duration
            args = [
                "-y",
                "-i", f"/workspace/{rel_in}",
                "-af", f"apad=whole_dur={scene_dur:.4f}",
                "-t", f"{scene_dur:.4f}",
                f"/workspace/{rel_out}",
            ]
            res = self._run_ffmpeg(args)
            if res.returncode != 0:
                raise RuntimeError(f"FFmpeg narration padding failed: {res.stderr}")
            padded_wavs.append(padded_wav)

        if len(padded_wavs) == 1:
            shutil.copy2(padded_wavs[0], output_file)
            return output_file

        # Concatenate padded WAVs
        concat_txt = output_file.parent / "narration_concat.txt"
        lines = [f"file '/workspace/{p.resolve().relative_to(self.workspace_dir.resolve())}'" for p in padded_wavs]
        concat_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
        rel_txt = concat_txt.resolve().relative_to(self.workspace_dir.resolve())
        rel_out = output_file.resolve().relative_to(self.workspace_dir.resolve())

        args = [
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", f"/workspace/{rel_txt}",
            "-c", "copy",
            f"/workspace/{rel_out}",
        ]
        res = self._run_ffmpeg(args)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg narration concat failed: {res.stderr}")

        return output_file

    def mix_audio_tracks(
        self,
        narration: Path,
        total_duration: float,
        output_file: Path,
        bgm_path: Optional[Path] = None,
        bgm_volume: float = 0.2,
        bgm_fade_in: float = 1.0,
        bgm_fade_out: float = 2.0,
        sfx_cues: Optional[List[Dict[str, Any]]] = None,
    ) -> Path:
        """
        Mix and normalize voiceover, background music with fades, and sound effects.
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(output_file.parent, 0o777)
        except OSError:
            pass

        rel_narr = narration.resolve().relative_to(self.workspace_dir.resolve())
        rel_out = output_file.resolve().relative_to(self.workspace_dir.resolve())

        input_args = ["-i", f"/workspace/{rel_narr}"]
        filter_inputs = ["[0:a]"]

        # Background music
        if bgm_path and bgm_path.exists():
            rel_bgm = bgm_path.resolve().relative_to(self.workspace_dir.resolve())
            input_args.extend(["-i", f"/workspace/{rel_bgm}"])
            bgm_idx = len(input_args) // 2 - 1
            fo_start = max(0.0, total_duration - bgm_fade_out)
            bgm_filter = (
                f"[{bgm_idx}:a]aloop=loop=-1:size=2e+09,"
                f"afade=t=in:st=0:d={bgm_fade_in},"
                f"afade=t=out:st={fo_start:.2f}:d={bgm_fade_out},"
                f"volume={bgm_volume:.3f}[bgm]"
            )
            filter_inputs.append("[bgm]")
        else:
            bgm_filter = ""

        # Sound effects
        sfx_filters = []
        if sfx_cues:
            for sfx in sfx_cues:
                sf_path = Path(sfx["source_file"])
                if sf_path.exists():
                    rel_sfx = sf_path.resolve().relative_to(self.workspace_dir.resolve())
                    input_args.extend(["-i", f"/workspace/{rel_sfx}"])
                    sfx_idx = len(input_args) // 2 - 1
                    delay_ms = int(sfx.get("start_time", 0.0) * 1000)
                    vol = sfx.get("volume", 1.0)
                    tag = f"[sfx_{sfx_idx}]"
                    sfx_filters.append(
                        f"[{sfx_idx}:a]adelay={delay_ms}|{delay_ms},volume={vol:.2f}{tag}"
                    )
                    filter_inputs.append(tag)

        # Assemble audio filter graph
        filter_graph_parts = []
        if bgm_filter:
            filter_graph_parts.append(bgm_filter)
        if sfx_filters:
            filter_graph_parts.extend(sfx_filters)

        if len(filter_inputs) > 1:
            all_in = "".join(filter_inputs)
            filter_graph_parts.append(
                f"{all_in}amix=inputs={len(filter_inputs)}:duration=first:dropout_transition=2,"
                f"dynaudnorm=f=150:g=15[aout]"
            )
            map_arg = "[aout]"
        else:
            filter_graph_parts.append("[0:a]dynaudnorm=f=150:g=15[aout]")
            map_arg = "[aout]"

        full_filter_str = ";".join(filter_graph_parts)

        args = (
            ["-y"]
            + input_args
            + ["-filter_complex", full_filter_str, "-map", map_arg, "-t", f"{total_duration:.4f}", f"/workspace/{rel_out}"]
        )

        res = self._run_ffmpeg(args)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio mixing failed: {res.stderr}")

        return output_file

    def burn_captions(
        self,
        video_path: Path,
        captions_path: Path,
        output_file: Path,
    ) -> Path:
        """Overlay animated subtitle text splash track onto video stream using libass."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(output_file.parent, 0o777)
        except OSError:
            pass

        rel_vid = video_path.resolve().relative_to(self.workspace_dir.resolve())
        rel_sub = captions_path.resolve().relative_to(self.workspace_dir.resolve())
        rel_out = output_file.resolve().relative_to(self.workspace_dir.resolve())

        args = [
            "-y",
            "-i", f"/workspace/{rel_vid}",
            "-vf", f"ass=/workspace/{rel_sub}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            f"/workspace/{rel_out}",
        ]

        res = self._run_ffmpeg(args)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg subtitle burning failed: {res.stderr}")

        return output_file

    def assemble_final_video(
        self,
        video_path: Path,
        audio_track: Path,
        output_file: Path,
        captions_path: Optional[Path] = None,
    ) -> Path:
        """
        Compose final H.264 MP4 with AAC audio stream and optional burned subtitles.
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(output_file.parent, 0o777)
        except OSError:
            pass

        rel_vid = video_path.resolve().relative_to(self.workspace_dir.resolve())
        rel_aud = audio_track.resolve().relative_to(self.workspace_dir.resolve())
        rel_out = output_file.resolve().relative_to(self.workspace_dir.resolve())

        cmd_args = [
            "-y",
            "-i", f"/workspace/{rel_vid}",
            "-i", f"/workspace/{rel_aud}",
        ]

        if captions_path and captions_path.exists():
            rel_sub = captions_path.resolve().relative_to(self.workspace_dir.resolve())
            cmd_args.extend(["-vf", f"ass=/workspace/{rel_sub}"])
            cmd_args.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
        else:
            cmd_args.extend(["-c:v", "copy"])

        cmd_args.extend([
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            f"/workspace/{rel_out}",
        ])

        res = self._run_ffmpeg(cmd_args)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg final assembly failed: {res.stderr}")

        return output_file

    def probe_media(self, media_path: Path) -> Dict[str, Any]:
        """Verify video/audio streams, duration, resolution, and codecs via ffprobe."""
        rel_path = media_path.resolve().relative_to(self.workspace_dir.resolve())
        probe_cmd = [
            "docker", "compose", "-f", str(self.compose_file),
            "run", "--rm",
            "--entrypoint", "ffprobe",
            "ffmpeg",
            "-v", "error",
            "-show_entries", "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,channels,sample_rate",
            "-of", "json",
            f"/workspace/{rel_path}",
        ]

        res = subprocess.run(probe_cmd, cwd=str(self.sandbox_dir), capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFprobe inspection failed: {res.stderr}")

        return json.loads(res.stdout)
