"""Text-To-Speech (TTS) narration engine with timestamp synchronization via Kokoro Docker."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_video_pipeline.schemas.models import VideoCategory, WordTimestamp


class TextToSpeechService:
    """TTS Service responsible for voice generation and word-level alignment using local Kokoro Docker."""

    DEFAULT_VOICE = "af_heart"
    SUPPORTED_VOICES = [
        "af_heart",
        "af_bella",
        "af_nicole",
        "af_sarah",
        "af_sky",
        "am_adam",
        "am_michael",
        "bf_emma",
        "bf_isabella",
        "bm_george",
        "bm_lewis",
    ]

    def __init__(
        self,
        sandbox_dir: Optional[Path] = None,
        default_language: str = "en",
        cache_dir: Optional[Path] = None,
    ) -> None:
        self.sandbox_dir = sandbox_dir or (
            Path(__file__).resolve().parent.parent.parent / "video_docker_sandbox"
        )
        self.workspace_dir = self.sandbox_dir / "workspace"
        self.compose_file = self.sandbox_dir / "compose.yaml"
        self.default_language = default_language
        self.cache_dir = cache_dir or (self.workspace_dir / ".cache" / "tts")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def select_voice_profile(self, category: VideoCategory, language: str = "en") -> str:
        """Select an optimal voice profile suited to the content category and language."""
        if category == VideoCategory.KIDS_ANIMATED_STORY:
            return "af_bella"
        elif category == VideoCategory.CS_MATH_EDUCATIONAL:
            return "af_heart"
        else:
            return "am_adam"

    def calculate_speech_duration(self, text: str, words_per_minute: int = 145) -> float:
        """Estimate narration duration from raw text for preliminary storyboard timing."""
        words = len(text.split())
        return max(1.0, (words / words_per_minute) * 60.0)

    def _get_cache_key(self, text: str, voice_id: str, language: str) -> str:
        h = hashlib.sha256()
        h.update(text.strip().encode("utf-8"))
        h.update(voice_id.encode("utf-8"))
        h.update(language.encode("utf-8"))
        return h.hexdigest()[:16]

    def measure_wav_duration(self, wav_path: Path) -> float:
        """Measure actual audio duration accurately using stdlib wave."""
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)

    def estimate_word_timestamps(
        self,
        text: str,
        total_duration: float,
        start_offset: float = 0.0,
    ) -> List[WordTimestamp]:
        """
        Derive precise word-level timestamps proportionally across speech duration.
        """
        # Clean and split into individual words
        words = [w.strip() for w in re.split(r"\s+", text) if w.strip()]
        if not words:
            return []

        # Weight duration by character length to model realistic syllable timing
        lengths = [max(1, len(re.sub(r"[^\w]", "", w))) for w in words]
        total_chars = sum(lengths)

        timestamps: List[WordTimestamp] = []
        curr = start_offset
        for word, char_len in zip(words, lengths):
            word_dur = (char_len / total_chars) * total_duration
            timestamps.append(
                WordTimestamp(
                    word=word,
                    start_time=round(curr, 3),
                    end_time=round(curr + word_dur, 3),
                )
            )
            curr += word_dur

        return timestamps

    def generate_narration(
        self,
        script_text: str,
        voice_id: str,
        language: str,
        output_file: Path,
        scene_duration_limit: Optional[float] = None,
    ) -> Tuple[Path, List[WordTimestamp], Dict[str, Any]]:
        """
        Synthesize voiceover audio using local Kokoro Docker and return timestamps and metadata.
        Caches outputs by text hash to avoid redundant inference.
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(output_file.parent, 0o777)
        except OSError:
            pass

        cache_key = self._get_cache_key(script_text, voice_id, language)
        cached_wav = self.cache_dir / f"{cache_key}.wav"
        cached_meta = self.cache_dir / f"{cache_key}.json"

        if cached_wav.exists() and cached_meta.exists():
            shutil.copy2(cached_wav, output_file)
            meta = json.loads(cached_meta.read_text(encoding="utf-8"))
            timestamps = [
                WordTimestamp(
                    word=w["word"],
                    start_time=w["start_time"],
                    end_time=w["end_time"],
                )
                for w in meta.get("word_timestamps", [])
            ]
            actual_duration = meta.get("duration", self.measure_wav_duration(output_file))
            if scene_duration_limit and actual_duration > scene_duration_limit:
                raise ValueError(
                    f"Narration duration ({actual_duration:.2f}s) exceeds scene duration limit ({scene_duration_limit:.2f}s)"
                )
            return output_file, timestamps, meta

        # Run Kokoro synthesis via Docker container
        try:
            rel_output = output_file.resolve().relative_to(self.workspace_dir.resolve())
            container_out = f"/workspace/{rel_output}"
        except ValueError:
            # If outside workspace, write to cache first
            container_out = f"/workspace/.cache/tts/{cache_key}.wav"

        # Python script executed inside Kokoro Docker container
        py_script = f"""
import sys
from kokoro import KPipeline
import soundfile as sf
import numpy as np

text = {json.dumps(script_text)}
voice = {json.dumps(voice_id)}
pipeline = KPipeline(lang_code='a')
generator = pipeline(text, voice=voice, speed=1.0)
chunks = []
for gs, ps, audio in generator:
    if audio is not None and len(audio) > 0:
        chunks.append(audio)

if not chunks:
    sys.exit(1)

full = np.concatenate(chunks)
sf.write({json.dumps(container_out)}, full, 24000)
print('OK')
"""

        cmd = [
            "docker", "compose", "-f", str(self.compose_file),
            "run", "--rm",
            "tts",
            "python", "-c", py_script,
        ]

        res = subprocess.run(
            cmd,
            cwd=str(self.sandbox_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )

        if res.returncode != 0:
            raise RuntimeError(f"Kokoro TTS generation failed (code {res.returncode}): {res.stderr}")

        # If generated to cache, copy to output_file
        if not output_file.exists():
            gen_path = self.workspace_dir / ".cache" / "tts" / f"{cache_key}.wav"
            if gen_path.exists():
                shutil.copy2(gen_path, output_file)
            else:
                raise FileNotFoundError(f"Generated audio file not found at {output_file}")

        # Save to cache
        shutil.copy2(output_file, cached_wav)

        actual_duration = self.measure_wav_duration(output_file)
        timestamps = self.estimate_word_timestamps(script_text, actual_duration)

        meta = {
            "text": script_text,
            "voice_id": voice_id,
            "language": language,
            "duration": actual_duration,
            "sample_rate": 24000,
            "word_timestamps": [
                {"word": t.word, "start_time": t.start_time, "end_time": t.end_time}
                for t in timestamps
            ],
        }
        cached_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        # Duration mismatch check
        if scene_duration_limit and actual_duration > scene_duration_limit:
            raise ValueError(
                f"Narration duration ({actual_duration:.2f}s) exceeds scene duration limit ({scene_duration_limit:.2f}s)"
            )

        return output_file, timestamps, meta

    def adjust_pacing(
        self,
        audio_path: Path,
        target_duration: float,
        output_file: Path,
    ) -> Path:
        """Slightly time-stretch audio using ffmpeg atempo filter to match duration if needed."""
        actual_dur = self.measure_wav_duration(audio_path)
        tempo_factor = actual_dur / target_duration

        # Guard against unnatural pitch/speed distortion
        if tempo_factor < 0.85 or tempo_factor > 1.15:
            raise ValueError(
                f"Pacing adjustment factor ({tempo_factor:.2f}) is too extreme; regenerate scene timing instead."
            )

        rel_in = audio_path.resolve().relative_to(self.workspace_dir.resolve())
        rel_out = output_file.resolve().relative_to(self.workspace_dir.resolve())

        cmd = [
            "docker", "compose", "-f", str(self.compose_file),
            "run", "--rm",
            "ffmpeg",
            "-y",
            "-i", f"/workspace/{rel_in}",
            "-filter:a", f"atempo={tempo_factor:.4f}",
            f"/workspace/{rel_out}",
        ]
        res = subprocess.run(cmd, cwd=str(self.sandbox_dir), capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg pacing adjustment failed: {res.stderr}")

        return output_file
