"""Automated unit and integration tests for Milestone 2: Audio & Video Postproduction."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from ai_video_pipeline.jobs.manager import JobManager
from ai_video_pipeline.mcp.tools import PipelineMCPTools
from ai_video_pipeline.media.compositor import VideoCompositor
from ai_video_pipeline.media.text_splash import TextSplashGenerator, _format_ass_time
from ai_video_pipeline.media.tts import TextToSpeechService
from ai_video_pipeline.parsers.theta import ParserTheta
from ai_video_pipeline.schemas.job_schemas import (
    AudioCueModel,
    AudioPlanModel,
    CaptionStyleModel,
    NarrationSegmentModel,
)
from ai_video_pipeline.schemas.models import (
    AnimationEngine,
    AspectRatio,
    PlanManifest,
    SceneSpec,
    SharedTimeline,
    VideoCategory,
    WordTimestamp,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


# ---------------------------------------------------------------------------
# 1. Audio Plan Schema & Validation Tests
# ---------------------------------------------------------------------------

def test_audio_plan_model_validation():
    # Valid audio plan
    plan = AudioPlanModel(
        job_id="a1b2c3d4",
        voice_id="af_heart",
        language="en",
        bgm_track="bgm.mp3",
        bgm_volume=0.25,
        narration_segments=[
            NarrationSegmentModel(
                scene_id="scene_001",
                text="Hello world",
                start_time=0.0,
                end_time=5.0,
            )
        ],
        sfx_cues=[
            AudioCueModel(
                cue_id="sfx_001",
                source_file="ding.wav",
                start_time=1.5,
                volume_level=0.8,
            )
        ],
    )
    assert plan.job_id == "a1b2c3d4"
    assert len(plan.narration_segments) == 1
    assert plan.sfx_cues[0].start_time == 1.5

    # Invalid volume
    with pytest.raises(Exception):
        AudioPlanModel(job_id="a1b2c3d4", bgm_volume=1.5)  # > 1.0


def test_parser_theta_missing_assets_rejection(temp_workspace: Path):
    theta = ParserTheta(workspace_root=temp_workspace)
    job_dir = temp_workspace / "jobs" / "a1b2c3d4"
    job_dir.mkdir(parents=True, exist_ok=True)

    # Missing BGM should be rejected
    with pytest.raises(FileNotFoundError, match="not found"):
        theta.resolve_audio_asset(job_dir, "nonexistent_music.mp3")

    # Path traversal should be rejected
    with pytest.raises(ValueError, match="Path traversal"):
        theta.resolve_audio_asset(job_dir, "../../etc/passwd")


def test_parser_theta_audio_plan_validation(temp_workspace: Path):
    theta = ParserTheta(workspace_root=temp_workspace)
    job_dir = temp_workspace / "jobs" / "a1b2c3d4"
    job_dir.mkdir(parents=True, exist_ok=True)

    plan_manifest = PlanManifest(
        job_id="a1b2c3d4",
        title="Test",
        category=VideoCategory.CS_MATH_EDUCATIONAL,
        aspect_ratio=AspectRatio.LANDSCAPE_16_9,
        target_duration_seconds=10.0,
        shared_timeline=SharedTimeline(total_duration_seconds=10.0),
        scenes=[
            SceneSpec(
                scene_id="scene_001",
                index=0,
                engine=AnimationEngine.MANIM,
                start_time=0.0,
                end_time=5.0,
                narration_text="Scene 1",
                visual_description="Visual 1",
            ),
            SceneSpec(
                scene_id="scene_002",
                index=1,
                engine=AnimationEngine.MANIM,
                start_time=5.0,
                end_time=10.0,
                narration_text="Scene 2",
                visual_description="Visual 2",
            ),
        ],
    )

    # Narration duration exceeding scene duration must produce validation issue
    invalid_audio_plan = AudioPlanModel(
        job_id="a1b2c3d4",
        narration_segments=[
            NarrationSegmentModel(
                scene_id="scene_001",
                text="Too long speech",
                start_time=0.0,
                end_time=8.0,  # Scene is only 5.0s
            )
        ],
    )
    is_valid, issues = theta.validate_audio_plan(job_dir, plan_manifest, invalid_audio_plan)
    assert is_valid is False
    assert any("exceeds scene duration" in issue for issue in issues)


# ---------------------------------------------------------------------------
# 2. TTS Narration & Cache Reuse Tests
# ---------------------------------------------------------------------------

def test_tts_cache_reuse(tmp_path: Path):
    tts = TextToSpeechService(sandbox_dir=tmp_path, cache_dir=tmp_path / "cache")
    output_wav = tmp_path / "scene_001_narration.wav"

    # Pre-populate cache
    cache_key = tts._get_cache_key("Cached text", "af_heart", "en")
    cached_wav = tts.cache_dir / f"{cache_key}.wav"
    cached_meta = tts.cache_dir / f"{cache_key}.json"

    # Write dummy wav in cache
    import wave
    with wave.open(str(cached_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(b"\x00" * 48000)  # 1.0 second of silence

    meta = {
        "text": "Cached text",
        "voice_id": "af_heart",
        "language": "en",
        "duration": 1.0,
        "word_timestamps": [
            {"word": "Cached", "start_time": 0.0, "end_time": 0.5},
            {"word": "text", "start_time": 0.5, "end_time": 1.0},
        ],
    }
    cached_meta.write_text(json.dumps(meta), encoding="utf-8")

    # Generate narration should hit cache directly without invoking Docker
    res_wav, timestamps, out_meta = tts.generate_narration(
        script_text="Cached text",
        voice_id="af_heart",
        language="en",
        output_file=output_wav,
    )

    assert res_wav.exists()
    assert len(timestamps) == 2
    assert timestamps[0].word == "Cached"
    assert out_meta["duration"] == 1.0


def test_tts_duration_mismatch_detection(tmp_path: Path):
    tts = TextToSpeechService(sandbox_dir=tmp_path, cache_dir=tmp_path / "cache")
    output_wav = tmp_path / "overflow.wav"

    cache_key = tts._get_cache_key("Long text", "af_heart", "en")
    cached_wav = tts.cache_dir / f"{cache_key}.wav"
    cached_meta = tts.cache_dir / f"{cache_key}.json"

    import wave
    with wave.open(str(cached_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(b"\x00" * 240000)  # 5.0 seconds

    cached_meta.write_text(
        json.dumps({"text": "Long text", "duration": 5.0, "word_timestamps": []}),
        encoding="utf-8",
    )

    # Target scene duration limit is 3.0s -> should raise ValueError
    with pytest.raises(ValueError, match="exceeds scene duration limit"):
        tts.generate_narration(
            script_text="Long text",
            voice_id="af_heart",
            language="en",
            output_file=output_wav,
            scene_duration_limit=3.0,
        )


# ---------------------------------------------------------------------------
# 3. Text Splash & ASS Subtitles Generation Tests
# ---------------------------------------------------------------------------

def test_ass_time_formatting():
    assert _format_ass_time(0.0) == "0:00:00.00"
    assert _format_ass_time(65.45) == "0:01:05.45"
    assert _format_ass_time(3661.02) == "1:01:01.02"


def test_ass_subtitle_generation(tmp_path: Path):
    splash = TextSplashGenerator()
    out_ass = tmp_path / "captions.ass"

    word_timestamps = [
        WordTimestamp(word="Gradient", start_time=0.0, end_time=0.6),
        WordTimestamp(word="descent", start_time=0.6, end_time=1.2),
        WordTimestamp(word="converges", start_time=1.2, end_time=2.0),
        WordTimestamp(word="quickly.", start_time=2.0, end_time=2.8),
    ]

    style = CaptionStyleModel(font_name="Arial", font_size=28, primary_color="&H00FFFFFF")
    splash.generate_ass_subtitles(
        word_timestamps=word_timestamps,
        output_file=out_ass,
        aspect_ratio=AspectRatio.LANDSCAPE_16_9,
        style_config=style,
        words_per_phrase=4,
    )

    assert out_ass.exists()
    content = out_ass.read_text(encoding="utf-8")
    assert "[Script Info]" in content
    assert "PlayResX: 854" in content
    assert "PlayResY: 480" in content
    assert "Dialogue:" in content
    assert "Gradient" in content
    assert "\\c" in content  # Contains highlighting tag


def test_vertical_aspect_ratio_safe_margins(tmp_path: Path):
    splash = TextSplashGenerator()
    out_ass = tmp_path / "vertical.ass"

    word_timestamps = [WordTimestamp(word="Mobile", start_time=0.0, end_time=1.0)]
    splash.generate_ass_subtitles(
        word_timestamps=word_timestamps,
        output_file=out_ass,
        aspect_ratio=AspectRatio.PORTRAIT_9_16,
    )

    content = out_ass.read_text(encoding="utf-8")
    assert "PlayResX: 480" in content
    assert "PlayResY: 854" in content
    assert "120" in content  # Higher margin for mobile vertical safe zone


# ---------------------------------------------------------------------------
# 4. FFmpeg Compositor & Mixing Command Construction
# ---------------------------------------------------------------------------

def test_ffmpeg_command_construction():
    compositor = VideoCompositor()
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock(returncode=0, stdout="OK", stderr="")
        mock_run.return_value = mock_proc

        args = ["-version"]
        compositor._run_ffmpeg(args)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert isinstance(cmd, list)
        assert cmd[0] == "docker"
        assert cmd[1] == "compose"
        assert "ffmpeg" in cmd
        assert mock_run.call_args[1].get("shell") is not True


# ---------------------------------------------------------------------------
# 5. Failed Postproduction Recovery (retry_postproduction)
# ---------------------------------------------------------------------------

def test_retry_postproduction_without_rerendering(temp_workspace: Path):
    tools = PipelineMCPTools(workspace_root=temp_workspace)
    res = tools.create_job(
        video_type="cs_math",
        topic_or_prompt="Test Postproduction Recovery",
        target_duration_seconds=5.0,
    )
    job_id = res["job_id"]
    job_dir = Path(res["job_dir"])

    # Setup scenes and mock existing rendered video
    (job_dir / "scenes").mkdir(parents=True, exist_ok=True)
    (job_dir / "scenes" / "scene_001.py").write_text("class S:\n    pass\n")

    storyboard = {
        "job_id": job_id,
        "title": "Postproduction Test",
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
                "narration_text": "Intro",
                "visual_description": "Intro",
                "code_file": "scene_001.py",
            }
        ],
    }
    (job_dir / "storyboard.json").write_text(json.dumps(storyboard), encoding="utf-8")

    # Mock existing scene render in renders/
    renders_dir = job_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    scene_mp4 = renders_dir / "scene_001.mp4"
    scene_mp4.write_bytes(b"dummy_mp4_bytes")

    # Mock postproduction stages to simulate successful recovery
    with patch.object(TextToSpeechService, "generate_narration") as mock_tts, \
         patch.object(VideoCompositor, "assemble_narration_track") as mock_narr_track, \
         patch.object(VideoCompositor, "mix_audio_tracks") as mock_mix, \
         patch.object(VideoCompositor, "concatenate_video_scenes") as mock_cat, \
         patch.object(VideoCompositor, "assemble_final_video") as mock_asm, \
         patch.object(VideoCompositor, "probe_media") as mock_probe:

        mock_tts.return_value = (
            job_dir / "audio" / "scene_001_narration.wav",
            [WordTimestamp(word="Intro", start_time=0.0, end_time=1.0)],
            {"duration": 1.0},
        )
        final_mp4 = job_dir / "output" / "final.mp4"
        final_mp4.parent.mkdir(parents=True, exist_ok=True)
        final_mp4.touch()

        mock_narr_track.return_value = job_dir / "audio" / "narration_full.wav"
        mock_mix.return_value = job_dir / "audio" / "mixed_audio.wav"
        mock_cat.return_value = job_dir / "renders" / "concatenated_visual.mp4"
        mock_asm.return_value = final_mp4
        mock_probe.return_value = {
            "format": {"duration": "5.0"},
            "streams": [
                {"codec_type": "video", "codec_name": "h264"},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
        }

        # Calling retry_postproduction should run postproduction without touching scene rendering
        retry_res = tools.retry_postproduction(job_id)
        assert retry_res["status"] == "completed"
        assert retry_res["duration"] == 5.0

        status = tools.get_job_status(job_id)
        assert status["state"] == "completed"
        assert status["progress_pct"] == 100
