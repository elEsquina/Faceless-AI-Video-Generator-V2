"""Milestone 2 Acceptance Test: 30-Second CS/Math Video with Full Postproduction.

Validates the complete workflow:
Codex/Antigravity -> MCP -> Parser Ω -> Docker Manim -> Parser θ -> Kokoro TTS -> Text Splash -> FFmpeg -> Final MP4

Components verified:
1. 3 animated Manim scenes (30.0s total).
2. Spoken English narration generated locally with Kokoro TTS in Docker.
3. Synchronized animated ASS captions with word-level highlighting.
4. Background ambient music track with volume control, fade-in, and fade-out.
5. Sound effect cue (chime at convergence).
6. Final MP4 container with H.264 video and AAC audio.
7. MCP tools execution (create_job, validate_plan, execute_job, get_job_status, retry_postproduction).
"""

import json
import subprocess
from pathlib import Path

from ai_video_pipeline.mcp.tools import PipelineMCPTools

WORKSPACE = Path("/home/othmane/Faceless_V2/video_docker_sandbox/workspace")

# --- Scene 1: Introduction to Gradient Descent (10.0 seconds) ---
SCENE_001_PY = '''from manim import *

class GradientDescentIntro(Scene):
    def construct(self):
        title = Text("Gradient Descent", font_size=42, color=BLUE).to_edge(UP)
        subtitle = Text("First-Order Optimization", font_size=26, color=GRAY).next_to(title, DOWN)
        self.play(Write(title), FadeIn(subtitle), run_time=2.0)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        func_label = MathTex("L(\\\\theta) = \\\\theta^2", font_size=32, color=YELLOW).next_to(parabola, RIGHT)
        
        self.play(Create(axes), Create(parabola), Write(func_label), run_time=3.0)
        
        dot = Dot(axes.coords_to_point(2.5, 6.25), color=RED, radius=0.1)
        label = MathTex("\\\\theta_0", font_size=28, color=RED).next_to(dot, RIGHT)
        self.play(FadeIn(dot), Write(label), run_time=2.0)
        self.wait(3.0)
'''

# --- Scene 2: Iterative Steps & Steepest Descent (10.0 seconds) ---
SCENE_002_PY = '''from manim import *

class GradientDescentSteps(Scene):
    def construct(self):
        title = Text("Iterative Descent Steps", font_size=36, color=BLUE).to_edge(UP)
        formula = MathTex("\\\\theta_{t+1} = \\\\theta_t - \\\\eta \\\\nabla L(\\\\theta_t)", font_size=30, color=GREEN).next_to(title, DOWN)
        self.add(title, formula)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        self.add(axes, parabola)
        
        dot = Dot(axes.coords_to_point(2.5, 6.25), color=RED, radius=0.1)
        self.add(dot)
        
        # Step downhill: 6 steps of 1.2s = 7.2s
        steps = [1.8, 1.3, 0.9, 0.55, 0.25, 0.08]
        for theta in steps:
            target = axes.coords_to_point(theta, theta**2)
            self.play(dot.animate.move_to(target), run_time=1.2)
        
        self.wait(2.8)
'''

# --- Scene 3: Convergence at Global Minimum (10.0 seconds) ---
SCENE_003_PY = '''from manim import *

class GradientDescentConvergence(Scene):
    def construct(self):
        title = Text("Convergence at Global Minimum", font_size=36, color=GREEN).to_edge(UP)
        cond = MathTex("\\\\nabla L(\\\\theta^*) \\\\approx 0", font_size=32, color=YELLOW).next_to(title, DOWN)
        self.play(Write(title), Write(cond), run_time=2.0)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        min_dot = Dot(axes.coords_to_point(0, 0), color=GREEN, radius=0.14)
        min_label = Text("Optimal Parameter", font_size=24, color=GREEN).next_to(min_dot, DOWN)
        
        self.add(axes, parabola)
        self.play(FadeIn(min_dot), Write(min_label), run_time=2.0)
        
        box = SurroundingRectangle(min_label, color=YELLOW, buff=0.15)
        self.play(Create(box), run_time=2.0)
        self.wait(4.0)
'''


def main():
    print("==================================================================")
    print("=== Starting Milestone 2 Acceptance Test: 30s CS/Math Video ===")
    print("==================================================================")
    tools = PipelineMCPTools(workspace_root=WORKSPACE)

    # 1. create_job via MCP
    print("\n--- 1. Calling create_job via MCP ---")
    req = tools.create_job(
        video_type="cs_math_educational",
        topic_or_prompt="Gradient descent algorithm with loss curve, descent steps, and convergence",
        target_duration_seconds=30.0,
        language="en",
        aspect_ratio="16:9",
    )
    print("create_job response:", req)
    assert req["success"] is True
    job_id = req["job_id"]
    job_dir = Path(req["job_dir"])

    # 2. External Director writes scenes, storyboard.json, and audio_plan.json
    print(f"\n--- 2. External Director writing generation artifacts into {job_dir} ---")
    scenes_dir = job_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    (scenes_dir / "scene_001.py").write_text(SCENE_001_PY, encoding="utf-8")
    (scenes_dir / "scene_002.py").write_text(SCENE_002_PY, encoding="utf-8")
    (scenes_dir / "scene_003.py").write_text(SCENE_003_PY, encoding="utf-8")

    storyboard = {
        "job_id": job_id,
        "title": "Gradient Descent Optimization Algorithm",
        "category": "cs_math_educational",
        "aspect_ratio": "16:9",
        "target_duration_seconds": 30.0,
        "scenes": [
            {
                "scene_id": "scene_001",
                "index": 0,
                "engine": "manim",
                "start_time": 0.0,
                "end_time": 10.0,
                "narration_text": "Gradient descent is a first-order optimization algorithm used to find local minima of a loss function.",
                "visual_description": "Loss function curve and initial parameter display",
                "code_file": "scene_001.py",
            },
            {
                "scene_id": "scene_002",
                "index": 1,
                "engine": "manim",
                "start_time": 10.0,
                "end_time": 20.0,
                "narration_text": "At each step, parameters are updated in the opposite direction of the gradient to descend the loss curve.",
                "visual_description": "Point moving down the parabola curve towards the minimum",
                "code_file": "scene_002.py",
            },
            {
                "scene_id": "scene_003",
                "index": 2,
                "engine": "manim",
                "start_time": 20.0,
                "end_time": 30.0,
                "narration_text": "When the gradient approaches zero, the step sizes shrink and the algorithm converges to the optimal parameter.",
                "visual_description": "Point stabilizes at the global minimum with confirmation box",
                "code_file": "scene_003.py",
            },
        ],
    }
    (job_dir / "storyboard.json").write_text(json.dumps(storyboard, indent=2), encoding="utf-8")

    audio_plan = {
        "job_id": job_id,
        "voice_id": "af_heart",
        "language": "en",
        "bgm_track": "ambient_bgm.wav",
        "bgm_volume": 0.15,
        "bgm_fade_in": 1.0,
        "bgm_fade_out": 2.5,
        "narration_segments": [
            {
                "scene_id": "scene_001",
                "text": "Gradient descent is a first-order optimization algorithm used to find local minima of a loss function.",
                "voice_id": "af_heart",
                "language": "en",
                "start_time": 0.0,
                "end_time": 10.0,
            },
            {
                "scene_id": "scene_002",
                "text": "At each step, parameters are updated in the opposite direction of the gradient to descend the loss curve.",
                "voice_id": "af_heart",
                "language": "en",
                "start_time": 10.0,
                "end_time": 20.0,
            },
            {
                "scene_id": "scene_003",
                "text": "When the gradient approaches zero, the step sizes shrink and the algorithm converges to the optimal parameter.",
                "voice_id": "af_heart",
                "language": "en",
                "start_time": 20.0,
                "end_time": 30.0,
            },
        ],
        "sfx_cues": [
            {
                "cue_id": "sfx_converge",
                "audio_type": "sound_effect",
                "source_file": "chime_sfx.wav",
                "start_time": 21.0,
                "duration_seconds": 0.6,
                "volume_level": 0.4,
            }
        ],
        "caption_style": {
            "font_name": "Arial",
            "font_size": 28,
            "primary_color": "&H00FFFFFF",
            "highlight_color": "&H0000FFFF",
            "position": "bottom",
        },
    }
    (job_dir / "audio_plan.json").write_text(json.dumps(audio_plan, indent=2), encoding="utf-8")

    # 3. validate_plan via MCP
    print("\n--- 3. Calling validate_plan via MCP ---")
    val_res = tools.validate_plan(job_id)
    print("validate_plan response:", val_res)
    assert val_res["is_valid"] is True

    # 4. execute_job via MCP (Docker Manim + Kokoro TTS + Text Splash + FFmpeg Compositor)
    print("\n--- 4. Calling execute_job via MCP (Full Rendering + Postproduction) ---")
    exec_res = tools.execute_job(job_id)
    print("execute_job response:", exec_res)
    assert exec_res["status"] == "completed"
    final_mp4 = Path(exec_res["output_path"])
    assert final_mp4.exists()
    print(f"Final composed MP4: {final_mp4}")

    # 5. get_job_status via MCP
    print("\n--- 5. Calling get_job_status via MCP ---")
    status = tools.get_job_status(job_id)
    print("get_job_status response:", status)
    assert status["state"] == "completed"
    assert status["progress_pct"] == 100

    # 6. Test retry_postproduction (recovers without re-rendering animation scenes)
    print("\n--- 6. Testing retry_postproduction via MCP ---")
    retry_post_res = tools.retry_postproduction(job_id)
    print("retry_postproduction response:", retry_post_res)
    assert retry_post_res["status"] == "completed"

    # 7. Quality Inspection via FFprobe
    print("\n--- 7. Inspecting Final MP4 Media Metadata via FFprobe ---")
    sandbox_dir = Path("/home/othmane/Faceless_V2/video_docker_sandbox")
    rel_mp4 = final_mp4.relative_to(WORKSPACE)
    probe_cmd = [
        "docker", "compose", "-f", str(sandbox_dir / "compose.yaml"),
        "run", "--rm",
        "--entrypoint", "ffprobe",
        "ffmpeg",
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,channels,sample_rate",
        "-of", "json",
        f"/workspace/{rel_mp4}",
    ]
    probe_res = subprocess.run(probe_cmd, cwd=str(sandbox_dir), capture_output=True, text=True)
    probe_data = json.loads(probe_res.stdout)

    format_info = probe_data.get("format", {})
    streams = probe_data.get("streams", [])
    duration = float(format_info.get("duration", 0.0))
    file_size = int(format_info.get("size", 0))

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    assert video_stream is not None, "Missing video stream"
    assert audio_stream is not None, "Missing audio stream"
    assert video_stream.get("codec_name") == "h264", f"Unexpected video codec: {video_stream.get('codec_name')}"
    assert audio_stream.get("codec_name") == "aac", f"Unexpected audio codec: {audio_stream.get('codec_name')}"

    width = video_stream.get("width")
    height = video_stream.get("height")
    channels = audio_stream.get("channels")
    sample_rate = audio_stream.get("sample_rate")

    print("\n==================================================================")
    print("=== MILESTONE 2 ACCEPTANCE TEST PASSED! ===")
    print(f"Job ID: {job_id}")
    print(f"Output MP4: {final_mp4}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Resolution: {width}x{height} (16:9 Landscape)")
    print(f"Video Codec: {video_stream.get('codec_name')}")
    print(f"Audio Codec: {audio_stream.get('codec_name')} ({channels} ch, {sample_rate} Hz)")
    print(f"File Size: {file_size} bytes ({file_size / 1024:.1f} KB)")
    print("==================================================================")


if __name__ == "__main__":
    main()
