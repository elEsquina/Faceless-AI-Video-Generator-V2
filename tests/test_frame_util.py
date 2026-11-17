"""Unit tests for frame_util.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from frame_util import FrameDecomposer


@pytest.fixture
def temp_jobs_env(tmp_path: Path):
    ws = tmp_path / "workspace"
    jobs = ws / "jobs"
    jobs.mkdir(parents=True)
    return tmp_path, ws, jobs


def test_locate_output_video(temp_jobs_env):
    tmp_path, ws, jobs = temp_jobs_env
    decomposer = FrameDecomposer(jobs_dir=jobs, sandbox_dir=tmp_path)

    job_a = jobs / "job_a"
    (job_a / "output").mkdir(parents=True)
    final_mp4 = job_a / "output" / "final.mp4"
    final_mp4.write_bytes(b"mock video data")

    assert decomposer.locate_output_video(job_a) == final_mp4

    # Test fallback to renders/
    job_b = jobs / "job_b"
    (job_b / "renders").mkdir(parents=True)
    scene_mp4 = job_b / "renders" / "scene_001.mp4"
    scene_mp4.write_bytes(b"mock scene data")

    assert decomposer.locate_output_video(job_b) == scene_mp4

    # Test missing video
    job_c = jobs / "job_c"
    job_c.mkdir()
    assert decomposer.locate_output_video(job_c) is None


def test_decompose_video_command_construction(temp_jobs_env):
    tmp_path, ws, jobs = temp_jobs_env
    decomposer = FrameDecomposer(jobs_dir=jobs, sandbox_dir=tmp_path)

    job_dir = jobs / "job_test"
    out_dir = job_dir / "output"
    out_dir.mkdir(parents=True)
    vid = out_dir / "final.mp4"
    vid.write_bytes(b"mock")
    frames_dir = job_dir / "frames"

    def fake_ffmpeg_run(*args, **kwargs):
        (frames_dir / "frame_0001.jpg").write_bytes(b"img")
        return MagicMock(returncode=0)

    with patch.object(decomposer, "_run_docker_ffmpeg", side_effect=fake_ffmpeg_run) as mock_ffmpeg:
        res = decomposer.decompose_video(video_path=vid, output_dir=frames_dir, img_format="jpg", fps=10.0)
        assert res["success"] is True
        assert res["frame_count"] == 1

        cmd = mock_ffmpeg.call_args[0][0]
        assert "-i" in cmd
        assert "-vf" in cmd
        assert "fps=10.0" in cmd
        assert "-q:v" in cmd


def test_create_jobs_zip(temp_jobs_env):
    tmp_path, ws, jobs = temp_jobs_env
    decomposer = FrameDecomposer(jobs_dir=jobs, sandbox_dir=tmp_path)

    job_dir = jobs / "job_zip"
    job_dir.mkdir(parents=True)
    (job_dir / "request.json").write_text('{"id": "zip"}')
    (job_dir / "frames").mkdir()
    (job_dir / "frames" / "frame_0001.jpg").write_bytes(b"frame data")

    zip_file = tmp_path / "test_out.zip"
    decomposer.create_jobs_zip(output_zip=zip_file)
    assert zip_file.exists()
    assert zip_file.stat().st_size > 0
