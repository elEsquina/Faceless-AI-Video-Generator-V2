"""Frame quality analysis and contact sheet generation using Pillow and NumPy."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageStat

from ai_video_pipeline.schemas.job_schemas import SceneQAMetricsModel
from ai_video_pipeline.schemas.models import AspectRatio, SceneSpec


class FrameQualityAnalyzer:
    """Analyzes visual characteristics of extracted keyframes and detects defects."""

    def analyze_single_frame(self, image_path: Path) -> Dict[str, float | bool]:
        """
        Compute basic luminance, standard deviation, and brightness metrics of an image.
        """
        with Image.open(image_path) as img:
            # Convert to RGB then Grayscale for brightness calculations
            rgb = img.convert("RGB")
            gray = rgb.convert("L")
            stat = ImageStat.Stat(gray)
            mean_lum = stat.mean[0]
            std_lum = stat.stddev[0]

            # Detect black/blank or completely solid frames
            is_black = mean_lum < 6.0 and std_lum < 4.0
            is_solid = std_lum < 1.5  # Solid single color without any text/shapes
            is_blank = is_black or is_solid

            # Detect severe overexposure
            is_overexposed = mean_lum > 248.0 and std_lum < 10.0

        return {
            "mean_luminance": round(mean_lum, 2),
            "std_contrast": round(std_lum, 2),
            "is_blank": is_blank,
            "is_overexposed": is_overexposed,
        }

    def compute_frame_difference(self, img1_path: Path, img2_path: Path) -> float:
        """
        Calculate Mean Absolute Error (MAE) between two frames to measure visual movement.
        """
        with Image.open(img1_path) as im1, Image.open(img2_path) as im2:
            arr1 = np.array(im1.convert("L"), dtype=float)
            arr2 = np.array(im2.convert("L"), dtype=float)
            if arr1.shape != arr2.shape:
                return 100.0
            return float(np.mean(np.abs(arr1 - arr2)))

    def evaluate_scene(
        self,
        scene: SceneSpec,
        frames: Dict[str, Path],
        video_info: Dict[str, Any],
        expected_aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE_16_9,
    ) -> SceneQAMetricsModel:
        """
        Evaluate technical visual quality across start, middle, and end scene keyframes.
        """
        issues: List[str] = []
        is_blank = False
        is_frozen = False

        frame_metrics: Dict[str, Dict[str, Any]] = {}
        for key in ("start", "middle", "end"):
            if key in frames and frames[key].exists():
                m = self.analyze_single_frame(frames[key])
                frame_metrics[key] = m
                if m["is_blank"]:
                    is_blank = True
                    issues.append(f"Detected blank or empty frame at {key} keyframe (mean={m['mean_luminance']}, std={m['std_contrast']})")
                elif m["is_overexposed"]:
                    issues.append(f"Detected overexposed frame at {key} keyframe (mean={m['mean_luminance']})")

        # Compute average scene luminance and contrast across available frames
        if frame_metrics:
            mean_lum = float(np.mean([m["mean_luminance"] for m in frame_metrics.values()]))
            contrast_std = float(np.mean([m["std_contrast"] for m in frame_metrics.values()]))
        else:
            mean_lum, contrast_std = 0.0, 0.0

        # Check for frozen / static animation
        if "start" in frames and "middle" in frames and "end" in frames:
            diff_sm = self.compute_frame_difference(frames["start"], frames["middle"])
            diff_me = self.compute_frame_difference(frames["middle"], frames["end"])

            # If pixel difference across keyframes is near zero throughout scene
            if diff_sm < 0.05 and diff_me < 0.05:
                # Legitimate static scene check:
                # In CS/Math, static diagrams or title cards with high contrast and readable text
                # are legitimate, not frozen defects.
                desc_lower = (scene.visual_description or "").lower()
                is_legitimate_static = (
                    any(term in desc_lower for term in ("title", "card", "formula", "display", "diagram", "slide", "minimum", "curve"))
                    and contrast_std > 8.0
                    and not is_blank
                )
                if not is_legitimate_static:
                    is_frozen = True
                    issues.append(
                        f"Scene appears unexpectedly frozen/static across time (diff_start_mid={diff_sm:.2f}, diff_mid_end={diff_me:.2f})"
                    )

        # Video geometry & format check
        streams = video_info.get("streams", [])
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        duration = float(video_info.get("format", {}).get("duration", 0.0))

        aspect_ok = True
        if expected_aspect_ratio == AspectRatio.PORTRAIT_9_16:
            if width > height:
                aspect_ok = False
                issues.append(f"Aspect ratio mismatch: expected 9:16 portrait, got {width}x{height}")
        elif expected_aspect_ratio == AspectRatio.LANDSCAPE_16_9:
            if height > width:
                aspect_ok = False
                issues.append(f"Aspect ratio mismatch: expected 16:9 landscape, got {width}x{height}")

        # Check duration
        planned_dur = scene.end_time - scene.start_time
        if abs(duration - planned_dur) > 1.5:
            issues.append(f"Duration mismatch: planned {planned_dur:.2f}s, rendered {duration:.2f}s")

        # Determine overall status
        status = "passed"
        if is_blank or not aspect_ok:
            status = "failed"
        elif is_frozen or issues:
            status = "warning" if len(issues) == 1 and not is_frozen else "failed"

        evidence = {k: str(v) for k, v in frames.items()}

        return SceneQAMetricsModel(
            scene_id=scene.scene_id,
            duration=round(duration, 2),
            width=width,
            height=height,
            is_blank=is_blank,
            is_frozen=is_frozen,
            mean_luminance=round(mean_lum, 2),
            contrast_std=round(contrast_std, 2),
            aspect_ratio_ok=aspect_ok,
            status=status,
            issues=issues,
            evidence_frames=evidence,
        )


class ContactSheetGenerator:
    """Generates tiled contact sheets for visual inspection across scenes."""

    def create_contact_sheet(
        self,
        scene_frames: Dict[str, Dict[str, Path]],  # scene_id -> {"start": path, "middle": path, "end": path}
        output_image: Path,
        scene_metrics: Optional[Dict[str, SceneQAMetricsModel]] = None,
        thumb_width: int = 320,
        thumb_height: int = 180,
    ) -> Path:
        """
        Tile extracted keyframes into a structured contact sheet image with scene labels.
        """
        output_image.parent.mkdir(parents=True, exist_ok=True)
        if output_image.exists():
            try:
                output_image.unlink()
            except OSError:
                pass

        scenes = list(scene_frames.keys())
        if not scenes:
            raise ValueError("No scene frames provided for contact sheet")

        cols = 3  # Start, Middle, End
        rows = len(scenes)

        padding = 16
        header_height = 40
        row_height = thumb_height + 36

        sheet_width = padding * 2 + cols * thumb_width + (cols - 1) * padding
        sheet_height = padding * 2 + header_height + rows * row_height

        # Create dark canvas
        sheet = Image.new("RGB", (sheet_width, sheet_height), color=(18, 20, 24))
        draw = ImageDraw.Draw(sheet)

        # Title header
        draw.text((padding, padding), "Faceless AI Video — Visual QA Contact Sheet", fill=(240, 240, 245))

        y_offset = padding + header_height

        for r_idx, scene_id in enumerate(scenes):
            f_dict = scene_frames[scene_id]
            metrics = scene_metrics.get(scene_id) if scene_metrics else None
            status_text = f"[{metrics.status.upper()}]" if metrics else ""

            # Row label
            status_color = (80, 220, 100) if metrics and metrics.status == "passed" else (240, 70, 70)
            draw.text((padding, y_offset), f"Scene: {scene_id}  {status_text}", fill=status_color)

            for c_idx, key in enumerate(("start", "middle", "end")):
                x_pos = padding + c_idx * (thumb_width + padding)
                y_pos = y_offset + 20

                if key in f_dict and f_dict[key].exists():
                    try:
                        with Image.open(f_dict[key]) as frame_img:
                            thumb = frame_img.convert("RGB").resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                            sheet.paste(thumb, (x_pos, y_pos))
                            # Frame border
                            draw.rectangle(
                                [x_pos, y_pos, x_pos + thumb_width, y_pos + thumb_height],
                                outline=(60, 65, 75),
                                width=1,
                            )
                            # Timestamp tag
                            draw.text((x_pos + 4, y_pos + thumb_height - 18), f"{key.upper()}", fill=(255, 255, 0))
                    except Exception:
                        draw.rectangle(
                            [x_pos, y_pos, x_pos + thumb_width, y_pos + thumb_height],
                            fill=(40, 20, 20),
                            outline=(200, 50, 50),
                        )
                        draw.text((x_pos + 10, y_pos + 50), f"Frame Error ({key})", fill=(255, 100, 100))
                else:
                    draw.rectangle(
                        [x_pos, y_pos, x_pos + thumb_width, y_pos + thumb_height],
                        fill=(30, 30, 35),
                        outline=(50, 50, 60),
                    )
                    draw.text((x_pos + 10, y_pos + 50), f"No Frame ({key})", fill=(150, 150, 150))

            y_offset += row_height

        sheet.save(str(output_image), quality=92)
        try:
            os.chmod(output_image, 0o666)
        except OSError:
            pass
        return output_image
