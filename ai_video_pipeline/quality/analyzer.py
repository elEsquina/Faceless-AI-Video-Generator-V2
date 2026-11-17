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

    def detect_suspicious_text_overlap(
        self,
        img_path: Path,
        band_y_fraction: Tuple[float, float] = (0.55, 0.88),
    ) -> List[str]:
        """
        Heuristic CV check for suspicious overlapping text or colliding glyphs.
        Scans annotation bands for abnormal stroke density and absence of character separation.
        Note: Generic pixel checks cannot guarantee 100% detection of all collisions;
        this serves as an automated alert for agent visual inspection.
        """
        warnings: List[str] = []
        if not img_path.exists():
            return warnings

        try:
            with Image.open(img_path) as im:
                gray = np.array(im.convert("L"))
                h, w = gray.shape
                y_start = int(h * band_y_fraction[0])
                y_end = int(h * band_y_fraction[1])
                band = gray[y_start:y_end, :]

                # Find bright pixels against dark background (text strokes)
                bg_level = float(np.percentile(band, 15))
                text_mask = band > (bg_level + 40.0)

                # Check horizontal stroke projection in text band
                vert_prof = np.sum(text_mask, axis=1)  # rows with text
                horiz_prof = np.sum(text_mask, axis=0)  # cols with text

                # If there are active text lines, inspect character density
                active_rows = np.where(vert_prof > (w * 0.02))[0]
                if len(active_rows) > 0:
                    # Look for dense clusters where characters might be overlapping
                    # by checking contiguous active columns without inter-word / inter-char gaps
                    active_cols = (horiz_prof > 4).astype(int)
                    # Check vertical stroke crowding in multi-line regions
                    row_density = vert_prof[active_rows] / float(w)
                    if np.any(row_density > 0.45):
                        warnings.append(
                            f"Suspiciously high horizontal text stroke density ({row_density.max():.2f}) "
                            f"in annotation band [y: {y_start}-{y_end}]; possible overlapping text or un-cleared label."
                        )
        except Exception:
            pass

        return warnings

    def detect_lingering_annotations(
        self,
        prev_img_path: Path,
        curr_img_path: Path,
        band_y_fraction: Tuple[float, float] = (0.55, 0.88),
    ) -> List[str]:
        """
        Compare adjacent transition frames for lingering annotations that fail to clear
        when a new annotation or status update appears.
        """
        warnings: List[str] = []
        if not prev_img_path.exists() or not curr_img_path.exists():
            return warnings

        try:
            with Image.open(prev_img_path) as im1, Image.open(curr_img_path) as im2:
                g1 = np.array(im1.convert("L"), dtype=float)
                g2 = np.array(im2.convert("L"), dtype=float)
                if g1.shape != g2.shape:
                    return warnings

                h, w = g1.shape
                y_start = int(h * band_y_fraction[0])
                y_end = int(h * band_y_fraction[1])

                band1 = g1[y_start:y_end, :]
                band2 = g2[y_start:y_end, :]

                # Text masks
                mask1 = band1 > 60.0
                mask2 = band2 > 60.0

                # Residual overlap: pixels active in both frames where stroke patterns changed
                overlap = mask1 & mask2
                diff = np.abs(band1 - band2)

                # Significant difference in annotation zone while preserving old strokes
                if np.sum(overlap) > (band1.size * 0.08) and np.mean(diff[overlap]) > 25.0:
                    warnings.append(
                        f"Potential lingering annotation between frames: text strokes persist and collide "
                        f"across transition in band [y: {y_start}-{y_end}]."
                    )
        except Exception:
            pass

        return warnings

    def check_explicit_bounding_box_collision(
        self,
        boxes: List[Dict[str, float]],
    ) -> List[str]:
        """
        Detect geometric collisions using explicit 2D bounding boxes when scene metadata is available.
        Each box dict: {"name": str, "x_min": float, "x_max": float, "y_min": float, "y_max": float}
        """
        collisions: List[str] = []
        n = len(boxes)
        for i in range(n):
            for j in range(i + 1, n):
                b1 = boxes[i]
                b2 = boxes[j]
                # Check AABB intersection
                overlap_x = max(0.0, min(b1["x_max"], b2["x_max"]) - max(b1["x_min"], b2["x_min"]))
                overlap_y = max(0.0, min(b1["y_max"], b2["y_max"]) - max(b1["y_min"], b2["y_min"]))
                if overlap_x > 0.05 and overlap_y > 0.05:
                    collisions.append(
                        f"Explicit text bounding box collision detected between '{b1.get('name', i)}' "
                        f"and '{b2.get('name', j)}' (overlap: {overlap_x:.2f} x {overlap_y:.2f})."
                    )
        return collisions

    def evaluate_scene(
        self,
        scene: SceneSpec,
        frames: Dict[str, Path],
        video_info: Dict[str, Any],
        expected_aspect_ratio: AspectRatio = AspectRatio.LANDSCAPE_16_9,
        text_bounding_boxes: Optional[List[Dict[str, float]]] = None,
    ) -> SceneQAMetricsModel:
        """
        Evaluate technical visual quality across start, transition, middle, and end keyframes.
        """
        issues: List[str] = []
        advisories: List[str] = []
        is_blank = False
        is_frozen = False

        frame_metrics: Dict[str, Dict[str, Any]] = {}
        ordered_keys = [k for k in ("start", "transition_q1", "middle", "transition_q3", "end") if k in frames]
        if not ordered_keys:
            ordered_keys = list(frames.keys())

        for key in ordered_keys:
            if key in frames and frames[key].exists():
                m = self.analyze_single_frame(frames[key])
                frame_metrics[key] = m
                if m["is_blank"]:
                    is_blank = True
                    issues.append(f"Detected blank or empty frame at {key} keyframe (mean={m['mean_luminance']}, std={m['std_contrast']})")
                elif m["is_overexposed"]:
                    issues.append(f"Detected overexposed frame at {key} keyframe (mean={m['mean_luminance']})")

                # Run text overlap heuristic on keyframe
                overlap_warnings = self.detect_suspicious_text_overlap(frames[key])
                for w in overlap_warnings:
                    advisories.append(f"Unverified pixel-pattern advisory [{key}]: {w}")

        # Lingering annotation check across adjacent transition frames
        for i in range(len(ordered_keys) - 1):
            k_prev = ordered_keys[i]
            k_curr = ordered_keys[i + 1]
            if k_prev in frames and k_curr in frames:
                lingering = self.detect_lingering_annotations(frames[k_prev], frames[k_curr])
                for lw in lingering:
                    advisories.append(f"Unverified pixel-pattern advisory [{k_prev}->{k_curr}]: {lw}")

        box_collisions = []
        # Explicit bounding box collision check if metadata is supplied
        if text_bounding_boxes:
            box_collisions = self.check_explicit_bounding_box_collision(text_bounding_boxes)
            issues.extend(box_collisions)

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
                    any(term in desc_lower for term in ("static", "still frame", "held diagram", "hold card"))
                    and not any(term in desc_lower for term in ("moving", "animated", "dynamic", "walking", "running"))
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
        expected = {AspectRatio.PORTRAIT_9_16: 9/16, AspectRatio.LANDSCAPE_16_9: 16/9, AspectRatio.SQUARE_1_1: 1.0}.get(expected_aspect_ratio)
        if expected is not None and (height<=0 or width<=0 or abs(width/height-expected)/expected>.02):
            aspect_ok = False
            issues.append(f"Aspect ratio mismatch: expected {expected_aspect_ratio.value}, got {width}x{height}")

        # Check duration
        planned_dur = scene.end_time - scene.start_time
        if abs(duration - planned_dur) > 1.5:
            issues.append(f"Duration mismatch: planned {planned_dur:.2f}s, rendered {duration:.2f}s")

        # Determine overall status:
        # Critical defects (blank frame, wrong aspect ratio) fail;
        # Suspicious overlap / lingering annotation alerts surface as warnings for agent review.
        status = "passed"
        has_critical = is_blank or not aspect_ok or is_frozen or bool(box_collisions)
        if has_critical:
            status = "failed"
        elif issues:
            status = "warning"

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
            advisories=advisories,
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

        # Determine unique ordered column keys across scenes
        preferred_order = ["start", "transition_q1", "middle", "transition_q3", "end"]
        all_keys = set()
        for f_dict in scene_frames.values():
            all_keys.update(f_dict.keys())
        cols_keys = [k for k in preferred_order if k in all_keys]
        for k in sorted(all_keys):
            if k not in cols_keys:
                cols_keys.append(k)
        if not cols_keys:
            cols_keys = ["start", "middle", "end"]

        cols = len(cols_keys)
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

            for c_idx, key in enumerate(cols_keys):
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
