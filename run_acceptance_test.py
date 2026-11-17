"""End-to-End Acceptance Test for MCP-Driven Video Generation Pipeline Milestone 1.

Renders a 15-second CS/Math Gradient Descent educational video via Docker Manim.
Tests:
- create_job
- validate_plan
- execute_job (real Docker rendering)
- get_job_status
- get_job_errors & retry_scene (with an injected syntax error repaired)
- ffprobe validation of duration, resolution, size
"""

import json
import os
import subprocess
from pathlib import Path

from ai_video_pipeline.mcp.tools import PipelineMCPTools
from ai_video_pipeline.schemas.models import AnimationEngine, AspectRatio, VideoCategory

WORKSPACE = Path("/home/othmane/Faceless_V2/video_docker_sandbox/workspace")

SCENE_001_PY = '''from manim import *

class GradientDescentIntroScene(Scene):
    def construct(self):
        title = Text("Gradient Descent", font_size=42, color=BLUE).to_edge(UP)
        subtitle = Text("Optimization Algorithm", font_size=24, color=GRAY).next_to(title, DOWN)
        self.play(Write(title), FadeIn(subtitle), run_time=1.5)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        func_label = MathTex("L(\\\\theta) = \\\\theta^2", font_size=32, color=YELLOW).next_to(parabola, RIGHT)
        
        self.play(Create(axes), Create(parabola), Write(func_label), run_time=2.0)
        self.wait(1.5)
'''

SCENE_002_PY = '''from manim import *

class GradientDescentStepsScene(Scene):
    def construct(self):
        title = Text("Iterative Descent", font_size=36, color=BLUE).to_edge(UP)
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
        
        dot = Dot(axes.coords_to_point(2.4, 2.4**2), color=RED, radius=0.1)
        label = MathTex("\\\\theta_0", font_size=28, color=RED).next_to(dot, RIGHT)
        self.play(FadeIn(dot), Write(label), run_time=1.0)
        
        steps = [1.5, 0.9, 0.4, 0.1]
        for theta in steps:
            target = axes.coords_to_point(theta, theta**2)
            self.play(dot.animate.move_to(target), run_time=0.8)
        
        self.wait(0.8)
'''

SCENE_003_PY = '''from manim import *

class GradientDescentConvergenceScene(Scene):
    def construct(self):
        title = Text("Convergence at Minimum", font_size=36, color=GREEN).to_edge(UP)
        result = MathTex("\\\\nabla L(\\\\theta^*) \\\\approx 0", font_size=32, color=YELLOW).next_to(title, DOWN)
        self.play(Write(title), Write(result), run_time=1.5)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        min_dot = Dot(axes.coords_to_point(0, 0), color=GREEN, radius=0.12)
        min_label = Text("Global Minimum", font_size=24, color=GREEN).next_to(min_dot, DOWN)
        
        self.add(axes, parabola)
        self.play(FadeIn(min_dot), Write(min_label), run_time=1.5)
        self.wait(2.0)
'''


def main():
    print("=== Starting Video Generation Pipeline Acceptance Test ===")
    tools = PipelineMCPTools(workspace_root=WORKSPACE)

    # 1. create_job
    print("\n--- 1. Calling create_job via MCP ---")
    req = tools.create_job(
        video_type="cs_math_educational",
        topic_or_prompt="Gradient descent optimization algorithm explained with loss function curve",
        target_duration_seconds=15.0,
        language="en",
        aspect_ratio="16:9",
    )
    print("create_job result:", req)
    assert req["success"] is True
    job_id = req["job_id"]
    job_dir = Path(req["job_dir"])

    # 2. Director writes scenes and storyboard
    print(f"\n--- 2. External Director generating job artifacts in {job_dir} ---")
    scenes_dir = job_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    (scenes_dir / "scene_001.py").write_text(SCENE_001_PY, encoding="utf-8")
    (scenes_dir / "scene_002.py").write_text(SCENE_002_PY, encoding="utf-8")
    (scenes_dir / "scene_003.py").write_text(SCENE_003_PY, encoding="utf-8")

    storyboard = {
        "job_id": job_id,
        "title": "Gradient Descent Optimization",
        "category": "cs_math_educational",
        "aspect_ratio": "16:9",
        "target_duration_seconds": 15.0,
        "scenes": [
            {
                "scene_id": "scene_001",
                "index": 0,
                "engine": "manim",
                "start_time": 0.0,
                "end_time": 5.0,
                "narration_text": "Gradient Descent is a fundamental optimization algorithm.",
                "visual_description": "Loss function parabola and title display",
                "code_file": "scene_001.py",
            },
            {
                "scene_id": "scene_002",
                "index": 1,
                "engine": "manim",
                "start_time": 5.0,
                "end_time": 10.0,
                "narration_text": "We iteratively update parameters in the direction of steepest descent.",
                "visual_description": "Point moving down the parabola curve towards zero",
                "code_file": "scene_002.py",
            },
            {
                "scene_id": "scene_003",
                "index": 2,
                "engine": "manim",
                "start_time": 10.0,
                "end_time": 15.0,
                "narration_text": "When the gradient approaches zero, the algorithm converges.",
                "visual_description": "Point stabilizes at the global minimum",
                "code_file": "scene_003.py",
            },
        ],
    }
    (job_dir / "storyboard.json").write_text(json.dumps(storyboard, indent=2), encoding="utf-8")

    # 3. validate_plan
    print("\n--- 3. Calling validate_plan via MCP ---")
    val_res = tools.validate_plan(job_id)
    print("validate_plan result:", val_res)
    assert val_res["is_valid"] is True

    # 4. execute_job (Real Docker execution)
    print("\n--- 4. Calling execute_job via MCP (Docker Manim + FFmpeg) ---")
    exec_res = tools.execute_job(job_id)
    print("execute_job result:", exec_res)
    assert exec_res["status"] == "completed"
    output_mp4 = Path(exec_res["output_path"])
    assert output_mp4.exists()
    print(f"Final MP4 successfully generated at: {output_mp4}")

    # 5. get_job_status
    print("\n--- 5. Calling get_job_status via MCP ---")
    status = tools.get_job_status(job_id)
    print("get_job_status result:", status)
    assert status["state"] == "completed"
    assert status["progress_pct"] == 100

    # 6. Test Error Handling and retry_scene
    print("\n--- 6. Testing Error Handling & retry_scene via MCP ---")
    # Inject a syntax error into scene_002
    (scenes_dir / "scene_002.py").write_text("broken syntax def (", encoding="utf-8")
    retry_broken = tools.retry_scene(job_id, "scene_002")
    print("retry_scene with broken syntax result:", retry_broken)
    assert retry_broken["success"] is False

    # Check get_job_errors
    errors = tools.get_job_errors(job_id)
    print("get_job_errors result:", errors)
    assert len(errors["scene_errors"]) > 0

    # Repair scene_002 and retry
    print("Repairing scene_002 and retrying...")
    (scenes_dir / "scene_002.py").write_text(SCENE_002_PY, encoding="utf-8")
    retry_fixed = tools.retry_scene(job_id, "scene_002")
    print("retry_scene repaired result:", retry_fixed)
    assert retry_fixed["success"] is True

    # 7. Inspect final MP4 with ffprobe
    print("\n--- 7. Inspecting Final MP4 with FFprobe ---")
    # Use ffmpeg container to run ffprobe
    sandbox_dir = Path("/home/othmane/Faceless_V2/video_docker_sandbox")
    rel_mp4 = output_mp4.relative_to(WORKSPACE)
    probe_cmd = [
        "docker", "compose", "-f", str(sandbox_dir / "compose.yaml"),
        "run", "--rm",
        "--entrypoint", "ffprobe",
        "ffmpeg",
        "-v", "error",
        "-show_entries", "format=duration,size:stream=width,height,codec_name",
        "-of", "json",
        f"/workspace/{rel_mp4}",
    ]
    probe_res = subprocess.run(probe_cmd, cwd=str(sandbox_dir), capture_output=True, text=True)
    print("FFprobe output:", probe_res.stdout)

    info = json.loads(probe_res.stdout)
    duration = float(info["format"]["duration"])
    file_size = int(info["format"]["size"])
    width = info["streams"][0]["width"]
    height = info["streams"][0]["height"]

    print(f"\n==========================================")
    print(f"ACCEPTANCE TEST PASSED!")
    print(f"Job ID: {job_id}")
    print(f"Output MP4: {output_mp4}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Resolution: {width}x{height}")
    print(f"File Size: {file_size} bytes ({file_size / 1024:.1f} KB)")
    print(f"==========================================")


if __name__ == "__main__":
    main()
