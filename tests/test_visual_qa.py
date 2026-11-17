"""Automated unit and integration tests for Milestone 3: Visual QA and Agent-Driven Repair."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image, ImageDraw

from ai_video_pipeline.jobs.manager import JobManager
from ai_video_pipeline.mcp.tools import PipelineMCPTools
from ai_video_pipeline.quality.analyzer import ContactSheetGenerator, FrameQualityAnalyzer
from ai_video_pipeline.quality.frame_extractor import KeyframeExtractor
from ai_video_pipeline.quality.validator import QualityValidator
from ai_video_pipeline.schemas.job_schemas import (
    JobQAReportModel,
    SceneQAMetricsModel,
    VisualReviewModel,
)
from ai_video_pipeline.schemas.models import (
    AnimationEngine,
    AspectRatio,
    PlanManifest,
    SceneSpec,
    SharedTimeline,
    VideoCategory,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


# ---------------------------------------------------------------------------
# 1. Blank and Overexposed Frame Detection Tests
# ---------------------------------------------------------------------------

def test_blank_and_black_frame_detection(tmp_path: Path):
    analyzer = FrameQualityAnalyzer()

    # Completely black frame
    black_img = tmp_path / "black.jpg"
    Image.new("RGB", (320, 180), color=(0, 0, 0)).save(black_img)
    res_black = analyzer.analyze_single_frame(black_img)
    assert res_black["is_blank"] is True
    assert res_black["mean_luminance"] < 1.0

    # Solid blue frame (no shapes or contrast)
    solid_img = tmp_path / "solid.jpg"
    Image.new("RGB", (320, 180), color=(0, 0, 150)).save(solid_img)
    res_solid = analyzer.analyze_single_frame(solid_img)
    assert res_solid["is_blank"] is True

    # High-contrast normal frame
    normal_img = tmp_path / "normal.jpg"
    im = Image.new("RGB", (320, 180), color=(20, 20, 20))
    draw = ImageDraw.Draw(im)
    draw.text((50, 50), "L(theta) = theta^2", fill=(255, 255, 0))
    im.save(normal_img)
    res_normal = analyzer.analyze_single_frame(normal_img)
    assert res_normal["is_blank"] is False


def test_overexposed_frame_detection(tmp_path: Path):
    analyzer = FrameQualityAnalyzer()
    overexposed = tmp_path / "whiteout.jpg"
    Image.new("RGB", (320, 180), color=(255, 255, 255)).save(overexposed)
    res = analyzer.analyze_single_frame(overexposed)
    assert res["is_overexposed"] is True


# ---------------------------------------------------------------------------
# 2. Frozen Scene vs Legitimate Static Scene Detection
# ---------------------------------------------------------------------------

def test_frozen_scene_detection(tmp_path: Path):
    analyzer = FrameQualityAnalyzer()
    scene_spec = SceneSpec(
        scene_id="scene_001",
        index=0,
        engine=AnimationEngine.MANIM,
        start_time=0.0,
        end_time=5.0,
        narration_text="Descent movement",
        visual_description="Point moving down the parabola curve dynamically",
    )

    # Identical frames across start, middle, end
    frame = tmp_path / "identical.jpg"
    im = Image.new("RGB", (320, 180), color=(30, 30, 30))
    draw = ImageDraw.Draw(im)
    draw.ellipse([50, 50, 80, 80], fill=(255, 0, 0))
    im.save(frame)

    frames = {"start": frame, "middle": frame, "end": frame}
    video_info = {
        "format": {"duration": "5.0"},
        "streams": [{"codec_type": "video", "width": 854, "height": 480}],
    }

    metrics = analyzer.evaluate_scene(scene_spec, frames, video_info, AspectRatio.LANDSCAPE_16_9)
    assert metrics.is_frozen is True
    assert metrics.status != "passed"
    assert any("frozen" in iss for iss in metrics.issues)


def test_legitimate_static_scene_handling(tmp_path: Path):
    analyzer = FrameQualityAnalyzer()
    # Scene description explicitly indicates a static formula card
    scene_spec = SceneSpec(
        scene_id="scene_001",
        index=0,
        engine=AnimationEngine.MANIM,
        start_time=0.0,
        end_time=5.0,
        narration_text="Proof display",
        visual_description="Static formula card displaying the mathematical definition",
    )

    frame = tmp_path / "formula_card.jpg"
    im = Image.new("RGB", (320, 180), color=(15, 20, 30))
    draw = ImageDraw.Draw(im)
    draw.text((40, 40), "nabla L(theta*) approx 0", fill=(255, 255, 255))
    im.save(frame)

    frames = {"start": frame, "middle": frame, "end": frame}
    video_info = {
        "format": {"duration": "5.0"},
        "streams": [{"codec_type": "video", "width": 854, "height": 480}],
    }

    metrics = analyzer.evaluate_scene(scene_spec, frames, video_info, AspectRatio.LANDSCAPE_16_9)
    # Must NOT be marked as failed/frozen defect
    assert metrics.is_frozen is False
    assert metrics.is_blank is False


# ---------------------------------------------------------------------------
# 3. Aspect Ratio and Resolution Mismatch Detection
# ---------------------------------------------------------------------------

def test_aspect_ratio_mismatch_detection(tmp_path: Path):
    analyzer = FrameQualityAnalyzer()
    scene_spec = SceneSpec(
        scene_id="scene_001",
        index=0,
        engine=AnimationEngine.MANIM,
        start_time=0.0,
        end_time=5.0,
        narration_text="",
        visual_description="Mobile vertical video",
    )

    frame = tmp_path / "frame.jpg"
    Image.new("RGB", (320, 180), color=(50, 50, 50)).save(frame)
    frames = {"start": frame, "middle": frame, "end": frame}

    # Expected portrait 9:16, but video stream is 854x480 landscape
    video_info = {
        "format": {"duration": "5.0"},
        "streams": [{"codec_type": "video", "width": 854, "height": 480}],
    }

    metrics = analyzer.evaluate_scene(scene_spec, frames, video_info, expected_aspect_ratio=AspectRatio.PORTRAIT_9_16)
    assert metrics.aspect_ratio_ok is False
    assert metrics.status == "failed"
    assert any("Aspect ratio mismatch" in iss for iss in metrics.issues)


# ---------------------------------------------------------------------------
# 4. Contact Sheet Generation Tests
# ---------------------------------------------------------------------------

def test_contact_sheet_generation(tmp_path: Path):
    gen = ContactSheetGenerator()
    f1 = tmp_path / "f1.jpg"
    Image.new("RGB", (320, 180), color=(50, 100, 150)).save(f1)

    scene_frames = {
        "scene_001": {"start": f1, "middle": f1, "end": f1},
        "scene_002": {"start": f1, "middle": f1, "end": f1},
    }

    out_sheet = tmp_path / "contact_sheet.jpg"
    res_path = gen.create_contact_sheet(scene_frames, out_sheet)

    assert res_path.exists()
    assert res_path.stat().st_size > 0
    with Image.open(res_path) as im:
        assert im.width > 900
        assert im.height > 300


# ---------------------------------------------------------------------------
# 5. Visual Review Submission & Validation Tests
# ---------------------------------------------------------------------------

def test_visual_review_validation_and_storage(temp_workspace: Path):
    tools = PipelineMCPTools(workspace_root=temp_workspace)
    create_res = tools.create_job(
        video_type="cs_math",
        topic_or_prompt="Test Review Submission",
        target_duration_seconds=10.0,
    )
    job_id = create_res["job_id"]

    # Valid visual review
    valid_review = {
        "overall_status": "needs_repair",
        "reviewer": "codex_antigravity",
        "issues": [
            {
                "scene_id": "scene_001",
                "severity": "high",
                "issue_type": "equation_overflow",
                "description": "The math formula is cut off at the edge of the frame.",
                "suggested_fix": "Add scale(0.8) to the formula object.",
            }
        ],
        "scenes_to_repair": ["scene_001"],
        "notes": "Scene 1 equation text touches upper border.",
    }

    sub_res = tools.submit_visual_review(job_id, valid_review)
    assert sub_res["success"] is True
    assert sub_res["overall_status"] == "needs_repair"
    assert "scene_001" in sub_res["scenes_to_repair"]

    # Invalid visual review (missing overall_status)
    invalid_review = {"reviewer": "tester"}
    inv_res = tools.submit_visual_review(job_id, invalid_review)
    assert inv_res["success"] is False
    assert "Invalid visual review" in inv_res["error"]


# ---------------------------------------------------------------------------
# 6. Maximum Retry Limit and Render Preservation Tests
# ---------------------------------------------------------------------------

def test_max_repair_iterations_and_render_preservation(temp_workspace: Path):
    tools = PipelineMCPTools(workspace_root=temp_workspace)
    create_res = tools.create_job(
        video_type="cs_math",
        topic_or_prompt="Test Max Retry",
        target_duration_seconds=5.0,
    )
    job_id = create_res["job_id"]
    job_dir = Path(create_res["job_dir"])

    (job_dir / "scenes").mkdir(parents=True, exist_ok=True)
    (job_dir / "scenes" / "scene_001.py").write_text("class S:\n    pass\n")

    sb = {
        "job_id": job_id,
        "title": "Max Retry Test",
        "category": "cs_math",
        "aspect_ratio": "16:9",
        "target_duration_seconds": 5.0,
        "scenes": [
            {
                "scene_id": "scene_001",
                "index": 0,
                "engine": "manim",
                "start_time": 0.0,
                "end_time": 5.0,
                "narration_text": "T",
                "visual_description": "V",
                "code_file": "scene_001.py",
            }
        ],
    }
    (job_dir / "storyboard.json").write_text(json.dumps(sb))

    # Existing good render
    renders_dir = job_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    good_render = renders_dir / "scene_001.mp4"
    good_render.write_bytes(b"good_render_data")

    # Manually simulate 3 repair attempts reached
    qa_dir = job_dir / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    (qa_dir / "repair_state.json").write_text(json.dumps({"scene_001": 3}))

    # 4th retry must be rejected
    res = tools.retry_scene(job_id, "scene_001")
    assert res["success"] is False
    assert "Maximum automatic repair iterations" in res["error"]

    # Verify original good render was preserved
    assert good_render.exists()
    assert good_render.read_bytes() == b"good_render_data"
