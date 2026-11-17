"""Text Splash: Animated caption generation, styling, and narration synchronization."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_video_pipeline.schemas.job_schemas import CaptionStyleModel
from ai_video_pipeline.schemas.models import (
    AspectRatio,
    CaptionCue,
    CaptionStyle,
    VideoCategory,
    WordTimestamp,
)


def _format_ass_time(seconds: float) -> str:
    """Format floating seconds into ASS timestamp H:MM:SS.cc"""
    if seconds < 0:
        seconds = 0.0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


class TextSplashGenerator:
    """Generates animated subtitles, dynamic title splashes, and keyword callouts."""

    def __init__(self) -> None:
        pass

    def get_style_preset(self, category: VideoCategory) -> CaptionStyle:
        """Resolve caption styling presets matched to the video category."""
        if category == VideoCategory.KIDS_ANIMATED_STORY:
            return CaptionStyle(
                font_name="Arial Rounded MT Bold",
                font_size=32,
                primary_color="&H00FFFFFF",
                highlight_color="&H0000D7FF",  # Bright warm gold
                animation_preset="pop_bounce",
            )
        elif category == VideoCategory.CS_MATH_EDUCATIONAL:
            return CaptionStyle(
                font_name="Arial",
                font_size=28,
                primary_color="&H00FFFFFF",
                highlight_color="&H0000FFFF",  # Electric yellow
                animation_preset="karaoke_highlight",
            )
        else:
            return CaptionStyle(
                font_name="Arial",
                font_size=26,
                primary_color="&H00FFFFFF",
                highlight_color="&H0050FA7B",  # Vibrant green
                animation_preset="fade_glow",
            )

    def build_caption_cues(
        self,
        timestamps: List[WordTimestamp],
        style: Optional[CaptionStyle] = None,
        words_per_group: int = 4,
    ) -> List[CaptionCue]:
        """Group word timestamps into readable, animated subtitle cues."""
        if not timestamps:
            return []

        cues: List[CaptionCue] = []
        for i in range(0, len(timestamps), words_per_group):
            group = timestamps[i : i + words_per_group]
            text = " ".join(w.word for w in group)
            start_t = group[0].start_time
            end_t = group[-1].end_time
            cues.append(
                CaptionCue(
                    text=text,
                    start_time=start_t,
                    end_time=end_t,
                    style=style,
                )
            )
        return cues

    def synchronize_with_narration(
        self,
        cues: List[CaptionCue],
        audio_offset_seconds: float,
    ) -> List[CaptionCue]:
        """Align caption display intervals precisely with audio narration offset."""
        shifted = []
        for cue in cues:
            shifted.append(
                CaptionCue(
                    text=cue.text,
                    start_time=round(cue.start_time + audio_offset_seconds, 3),
                    end_time=round(cue.end_time + audio_offset_seconds, 3),
                    style=cue.style,
                )
            )
        return shifted

    def generate_ass_subtitles(
        self,
        word_timestamps: List[WordTimestamp],
        output_file: Path,
        aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE_16_9,
        style_config: Optional[CaptionStyleModel] = None,
        words_per_phrase: int = 4,
    ) -> Path:
        """
        Generate ASS subtitle file with dynamic active-word highlighting.
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Resolution based on aspect ratio
        if aspect_ratio == AspectRatio.PORTRAIT_9_16:
            res_x, res_y = 480, 854
            margin_v = 120  # Safe zone away from mobile controls
            font_size = 26
        else:
            res_x, res_y = 854, 480
            margin_v = 35
            font_size = 28

        cfg = style_config or CaptionStyleModel()
        font_name = cfg.font_name or "Arial"
        pri_color = cfg.primary_color or "&H00FFFFFF"
        hl_color = cfg.highlight_color or "&H0000FFFF"

        ass_header = f"""[Script Info]
Title: Faceless Video Animated Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{pri_color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        # Group word timestamps into phrases of words_per_phrase
        for i in range(0, len(word_timestamps), words_per_phrase):
            phrase_words = word_timestamps[i : i + words_per_phrase]
            # For each word in the phrase, create a dialog line where that word is highlighted
            for active_idx, target_word in enumerate(phrase_words):
                w_start = _format_ass_time(target_word.start_time)
                w_end = _format_ass_time(target_word.end_time)

                # Assemble highlighted line
                parts = []
                for idx, w in enumerate(phrase_words):
                    if idx == active_idx:
                        # Highlight active word with glow & color
                        parts.append(f"{{\\c{hl_color}\\b1}}{w.word}{{\\c{pri_color}\\b0}}")
                    else:
                        parts.append(w.word)

                dialogue_text = " ".join(parts)
                events.append(f"Dialogue: 0,{w_start},{w_end},Default,,0,0,0,,{dialogue_text}")

        full_content = ass_header + "\n".join(events) + "\n"
        output_file.write_text(full_content, encoding="utf-8")
        return output_file

    def export_subtitle_track(
        self,
        cues: List[CaptionCue],
        output_path: Path,
        format_type: str = "ass",
    ) -> Path:
        """Export timed captions to subtitle file (ASS or SRT)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if format_type.lower() == "srt":
            lines = []
            for idx, c in enumerate(cues, 1):
                s_h = int(c.start_time // 3600)
                s_m = int((c.start_time % 3600) // 60)
                s_s = int(c.start_time % 60)
                s_ms = int(round((c.start_time - int(c.start_time)) * 1000))

                e_h = int(c.end_time // 3600)
                e_m = int((c.end_time % 3600) // 60)
                e_s = int(c.end_time % 60)
                e_ms = int(round((c.end_time - int(c.end_time)) * 1000))

                lines.append(f"{idx}")
                lines.append(f"{s_h:02d}:{s_m:02d}:{s_s:02d},{s_ms:03d} --> {e_h:02d}:{e_m:02d}:{e_s:02d},{e_ms:03d}")
                lines.append(c.text)
                lines.append("")
            output_path.write_text("\n".join(lines), encoding="utf-8")
        else:
            # Simple ASS
            header = """[Script Info]
ScriptType: v4.00+
PlayResX: 854
PlayResY: 480

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,28,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,20,20,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            dialogues = [
                f"Dialogue: 0,{_format_ass_time(c.start_time)},{_format_ass_time(c.end_time)},Default,,0,0,0,,{c.text}"
                for c in cues
            ]
            output_path.write_text(header + "\n".join(dialogues) + "\n", encoding="utf-8")

        return output_path
