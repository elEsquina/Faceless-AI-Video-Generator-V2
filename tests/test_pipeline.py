"""Automated unit and integration tests for MCP-driven Video Generation Pipeline."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from ai_video_pipeline.jobs.manager import JobManager, JobLock
from ai_video_pipeline.mcp.tools import PipelineMCPTools
from ai_video_pipeline.parsers.omega import (
    BaseAnimationCodeHandler,
    BlenderScriptHandler,
    DockerEngineRunner,
    ManimScriptHandler,
    ParserOmega,
    RemotionComponentHandler,
)
from ai_video_pipeline.schemas.job_schemas import (
    JobRequestModel,
    SceneSpecModel,
    StoryboardModel,
)
from ai_video_pipeline.schemas.models import (
    AnimationEngine,
    AspectRatio,
    SceneSpec,
    VideoCategory,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


# ---------------------------------------------------------------------------
# 1. Schemas & Validation Tests
# ---------------------------------------------------------------------------

def test_job_request_validation():
    # Valid request
    req = JobRequestModel(
        video_type="cs_math",
        topic_or_prompt="Gradient Descent",
        target_duration_seconds=15.0,
        aspect_ratio="16:9",
    )
    assert req.video_type == VideoCategory.CS_MATH_EDUCATIONAL
    assert req.aspect_ratio == AspectRatio.LANDSCAPE_16_9

    # Invalid duration
    with pytest.raises(Exception):
        JobRequestModel(
            video_type="cs_math",
            topic_or_prompt="Test",
            target_duration_seconds=-5.0,
        )


def test_storyboard_timeline_validation():
    # Overlapping scenes must fail
    with pytest.raises(ValueError, match="Overlapping scenes"):
        StoryboardModel(
            job_id="a1b2c3d4",
            title="Overlapping Scenes Test",
            category="cs_math",
            aspect_ratio="16:9",
            target_duration_seconds=10.0,
            scenes=[
                SceneSpecModel(
                    scene_id="scene_001",
                    index=0,
                    engine=AnimationEngine.MANIM,
                    start_time=0.0,
                    end_time=6.0,
                    narration_text="Scene 1",
                    visual_description="Visual 1",
                    code_file="scene_001.py",
                ),
                SceneSpecModel(
                    scene_id="scene_002",
                    index=1,
                    engine=AnimationEngine.MANIM,
                    start_time=4.0,  # Overlaps with scene_001 (end=6.0)
                    end_time=10.0,
                    narration_text="Scene 2",
                    visual_description="Visual 2",
                    code_file="scene_002.py",
                ),
            ],
        )


def test_storyboard_duplicate_scenes_validation():
    with pytest.raises(ValueError, match="Duplicate scene_ids"):
        StoryboardModel(
            job_id="a1b2c3d4",
            title="Duplicate Test",
            category="cs_math",
            aspect_ratio="16:9",
            target_duration_seconds=10.0,
            scenes=[
                SceneSpecModel(
                    scene_id="scene_001",
                    index=0,
                    engine=AnimationEngine.MANIM,
                    start_time=0.0,
                    end_time=5.0,
                    narration_text="Scene 1",
                    visual_description="Visual 1",
                    code_file="scene_001.py",
                ),
                SceneSpecModel(
                    scene_id="scene_001",  # Duplicate ID
                    index=1,
                    engine=AnimationEngine.MANIM,
                    start_time=5.0,
                    end_time=10.0,
                    narration_text="Scene 2",
                    visual_description="Visual 2",
                    code_file="scene_002.py",
                ),
            ],
        )


# ---------------------------------------------------------------------------
# 2. Path Traversal & Security Tests
# ---------------------------------------------------------------------------

def test_path_traversal_prevention(temp_workspace: Path):
    manager = JobManager(workspace_root=temp_workspace)
    with pytest.raises(ValueError, match="Invalid job_id"):
        manager.get_job_dir("../../etc/passwd")

    with pytest.raises(ValueError, match="Invalid job_id"):
        manager.get_job_dir("../secrets")

    with pytest.raises(ValueError, match="Invalid job_id"):
        manager.get_job_dir("bad/id")


# ---------------------------------------------------------------------------
# 3. Single Active Job Locking Tests
# ---------------------------------------------------------------------------

def test_single_active_job_locking(temp_workspace: Path):
    manager = JobManager(workspace_root=temp_workspace)
    req = {
        "video_type": "cs_math_educational",
        "topic_or_prompt": "Test",
        "target_duration_seconds": 15.0,
    }

    job_id = manager.create_job(req)
    assert manager.get_active_job() == job_id

    # Trying to create second job before releasing lock must fail
    with pytest.raises(RuntimeError, match="active job"):
        manager.create_job(req)

    # Releasing lock enables new job
    manager.release_lock(job_id)
    assert manager.get_active_job() is None

    job_id_2 = manager.create_job(req)
    assert manager.get_active_job() == job_id_2
    manager.release_lock(job_id_2)


# ---------------------------------------------------------------------------
# 4. Code Syntax Validation Tests
# ---------------------------------------------------------------------------

def test_manim_script_syntax_validation(tmp_path: Path):
    handler = ManimScriptHandler()

    valid_script = tmp_path / "valid.py"
    valid_script.write_text(
        "from manim import *\nclass TestScene(Scene):\n    def construct(self):\n        pass\n"
    )
    is_valid, err = handler.validate_code_file(valid_script)
    assert is_valid is True
    assert err is None
    assert handler.find_scene_class(valid_script) == "TestScene"

    # Syntax error
    invalid_script = tmp_path / "invalid.py"
    invalid_script.write_text("from manim import *\nclass Broken(Scene:\n")
    is_valid, err = handler.validate_code_file(invalid_script)
    assert is_valid is False
    assert "Syntax error" in str(err)

    # Missing class
    noclass_script = tmp_path / "noclass.py"
    noclass_script.write_text("x = 42\n")
    is_valid, err = handler.validate_code_file(noclass_script)
    assert is_valid is False
    assert "No scene classes" in str(err)


# ---------------------------------------------------------------------------
# 5. Pipeline State Transitions & Missing Files
# ---------------------------------------------------------------------------

def test_validate_plan_missing_scene_file(temp_workspace: Path):
    tools = PipelineMCPTools(workspace_root=temp_workspace)
    res = tools.create_job(
        video_type="cs_math",
        topic_or_prompt="Test",
        target_duration_seconds=10.0,
    )
    job_id = res["job_id"]
    job_dir = Path(res["job_dir"])

    # Write storyboard referencing nonexistent scene_001.py
    storyboard = {
        "job_id": job_id,
        "title": "Missing File Test",
        "category": "cs_math",
        "aspect_ratio": "16:9",
        "target_duration_seconds": 10.0,
        "scenes": [
            {
                "scene_id": "scene_001",
                "index": 0,
                "engine": "manim",
                "start_time": 0.0,
                "end_time": 10.0,
                "narration_text": "Missing",
                "visual_description": "Missing",
                "code_file": "nonexistent.py",
            }
        ],
    }
    (job_dir / "storyboard.json").write_text(json.dumps(storyboard), encoding="utf-8")

    val = tools.validate_plan(job_id)
    assert val["is_valid"] is False
    assert "scene_001" in val["scenes_to_regenerate"]
    tools.job_manager.release_lock(job_id)


# ---------------------------------------------------------------------------
# 6. Docker Command Construction & Non-Shell Safety
# ---------------------------------------------------------------------------

def test_docker_command_list_construction():
    runner = DockerEngineRunner()
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "OK"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        args = ["run", "--rm", "manim", "--version"]
        runner.run_docker(args)

        mock_run.assert_called_once()
        cmd_called = mock_run.call_args[0][0]
        # Must be list of strings, never a shell string
        assert isinstance(cmd_called, list)
        assert cmd_called[0] == "docker"
        assert cmd_called[1] == "compose"
        assert "--version" in cmd_called
        # Verify shell=True is NOT passed
        kwargs = mock_run.call_args[1]
        assert kwargs.get("shell") is not True


# ---------------------------------------------------------------------------
# 7. Subprocess Failure Handling & Retry Logic
# ---------------------------------------------------------------------------

def test_execute_job_subprocess_failure_and_retry(temp_workspace: Path):
    tools = PipelineMCPTools(workspace_root=temp_workspace)
    res = tools.create_job(
        video_type="cs_math",
        topic_or_prompt="Test Subprocess Failure",
        target_duration_seconds=5.0,
    )
    job_id = res["job_id"]
    job_dir = Path(res["job_dir"])

    # Create scene file
    scene_code = job_dir / "scenes" / "scene_001.py"
    scene_code.write_text(
        "from manim import *\nclass SceneOne(Scene):\n    def construct(self):\n        pass\n"
    )

    storyboard = {
        "job_id": job_id,
        "title": "Subprocess Fail Test",
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
                "visual_description": "Intro visual",
                "code_file": "scene_001.py",
            }
        ],
    }
    (job_dir / "storyboard.json").write_text(json.dumps(storyboard), encoding="utf-8")

    # Mock Docker execution to simulate failure
    with patch.object(DockerEngineRunner, "run_docker") as mock_run:
        failed_proc = MagicMock()
        failed_proc.returncode = 1
        failed_proc.stdout = ""
        failed_proc.stderr = "Traceback (most recent call last): MockError"
        mock_run.return_value = failed_proc

        exec_res = tools.execute_job(job_id)
        assert exec_res["status"] == "failed"
        assert "scene_001" in exec_res["failed_scene"]

        # Status and errors check
        status = tools.get_job_status(job_id)
        assert status["state"] == "failed"

        errs = tools.get_job_errors(job_id)
        assert len(errs["scene_errors"]) == 1
        assert errs["scene_errors"][0]["scene_id"] == "scene_001"

    # Now test retry with successful run
    with patch.object(DockerEngineRunner, "run_docker") as mock_run_retry:
        mock_run_retry.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
        # Simulate creating the rendered file
        rendered_mp4 = job_dir / "renders" / "scene_001.mp4"
        rendered_mp4.touch()

        with patch.object(ParserOmega, "execute_scene") as mock_exec_scene:
            mock_exec_scene.return_value = {
                "scene_id": "scene_001",
                "success": True,
                "output_path": str(rendered_mp4),
                "error": None,
            }
            retry_res = tools.retry_scene(job_id, "scene_001")
            assert retry_res["success"] is True
            assert retry_res["scene_id"] == "scene_001"


def test_remotion_and_blender_command_construction(temp_workspace: Path):
    """Verify that ParserOmega correctly formats arguments for Remotion and Blender engines."""
    omega = ParserOmega(sandbox_dir=temp_workspace)
    job_dir = temp_workspace / "jobs" / "test_engines"
    scenes_dir = job_dir / "scenes"
    renders_dir = job_dir / "renders"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    renders_dir.mkdir(parents=True, exist_ok=True)

    # 1. Remotion Scene
    tsx_file = scenes_dir / "scene_001.tsx"
    tsx_file.write_text("export default function Scene() { return null; }")
    remotion_spec = SceneSpec(
        scene_id="scene_001",
        index=0,
        engine=AnimationEngine.THREE_JS_REMOTION,
        start_time=0.0,
        end_time=5.0,
        narration_text="Narration 1",
        visual_description="Visual 1",
        code_file="scene_001.tsx",
    )

    with patch.object(DockerEngineRunner, "run_docker") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Touch expected output
        (renders_dir / "scene_001.mp4").touch()
        res = omega.execute_scene(job_dir, remotion_spec)
        assert res["success"] is True
        args = mock_run.call_args[0][0]
        assert "remotion" in args
        assert "npx" in args
        assert "--frames=0-149" in args  # 5.0s * 30fps = 150 frames (0 to 149)

    # 2. Blender Scene
    py_file = scenes_dir / "scene_002.py"
    py_file.write_text("import bpy\nprint('hello')")
    blender_spec = SceneSpec(
        scene_id="scene_002",
        index=1,
        engine=AnimationEngine.BLENDER,
        start_time=0.0,
        end_time=10.0,
        narration_text="Narration 2",
        visual_description="Visual 2",
        code_file="scene_002.py",
    )

    with patch.object(DockerEngineRunner, "run_docker") as mock_run_b:
        mock_run_b.return_value = MagicMock(returncode=0)
        (renders_dir / "scene_002.mp4").touch()
        res_b = omega.execute_scene(job_dir, blender_spec)
        assert res_b["success"] is True
        args_b = mock_run_b.call_args[0][0]
        assert "blender" in args_b
        assert "--frames=300" in args_b
        assert "--fps=30" in args_b


def test_video_compositor_h264_encoder_fallback(temp_workspace: Path):
    """Verify that VideoCompositor gracefully falls back to libx264 when NVENC is unavailable."""
    from ai_video_pipeline.media.compositor import VideoCompositor
    compositor = VideoCompositor(sandbox_dir=temp_workspace)

    with patch.object(compositor, "_run_ffmpeg") as mock_run:
        # Simulate NVENC probe failing
        mock_run.return_value = MagicMock(returncode=1)
        encoder = compositor.get_h264_encoder()
        assert encoder == "libx264"
        assert compositor._cached_encoder == "libx264"

        # Subsequent call returns cached value
        assert compositor.get_h264_encoder() == "libx264"

