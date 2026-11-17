"""Milestone 3 Acceptance Test: Automated Visual QA and Agent-Driven Scene Repair.

Executes the complete end-to-end workflow:
1. create_job (30-second CS/Math video on Gradient Descent).
2. Write animation code for 3 Manim scenes, storyboard.json, and audio_plan.json.
3. validate_plan via MCP.
4. execute_job via MCP (Docker Manim + Kokoro TTS + Text Splash captions + FFmpeg compositing).
5. inspect_video via MCP: extracts keyframes, generates contact sheet and technical QA report.
6. Introduce deliberate visual defect in scene 2 (completely blank/black frames).
7. Execute retry_scene: automated QA detects blank defect and flags failure.
8. Submit structured visual review via MCP (submit_visual_review).
9. Repair scene 2 animation code.
10. Execute retry_scene: verifies targeted re-render of only scene 2, leaving scenes 1 & 3 untouched.
11. Rerun inspect_video: confirms all scenes pass QA, updated contact sheet generated.
12. Verify final MP4 with FFprobe for duration (30.0s), resolution (854x480), video (h264), and audio (aac).
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
        self.play(Write(title), Write(formula), run_time=2.0)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        self.play(Create(axes), Create(parabola), run_time=2.0)
        
        dot = Dot(axes.coords_to_point(2.5, 6.25), color=RED, radius=0.12)
        self.play(FadeIn(dot), run_time=1.0)
        
        steps = [1.8, 1.3, 0.9, 0.55, 0.25, 0.08]
        for theta in steps:
            target = axes.coords_to_point(theta, theta**2)
            self.play(dot.animate.move_to(target), run_time=0.7)
        
        self.wait(0.8)
'''

# --- Scene 2 Defective: Completely Blank/Black Animation ---
SCENE_002_DEFECTIVE_PY = '''from manim import *

class GradientDescentSteps(Scene):
    def construct(self):
        # Defect: Nothing added or drawn to screen — completely black blank frames!
        self.wait(10.0)
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
    print("=== Starting Milestone 3 Acceptance Test: Automated Visual QA ===")
    print("==================================================================")
    tools = PipelineMCPTools(workspace_root=WORKSPACE)

    # 1. create_job via MCP
    print("\n--- 1. Calling create_job via MCP ---")
    req = tools.create_job(
        video_type="cs_math_educational",
        topic_or_prompt="Gradient descent optimization algorithm with visual QA validation",
        target_duration_seconds=30.0,
        language="en",
        aspect_ratio="16:9",
    )
    assert req["success"] is True
    job_id = req["job_id"]
    job_dir = Path(req["job_dir"])
    print(f"Created Job: {job_id} at {job_dir}")

    # 2. External Director writing generation artifacts
    print("\n--- 2. External Director writing initial animation artifacts ---")
    scenes_dir = job_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    (scenes_dir / "scene_001.py").write_text(SCENE_001_PY, encoding="utf-8")
    (scenes_dir / "scene_002.py").write_text(SCENE_002_PY, encoding="utf-8")
    (scenes_dir / "scene_003.py").write_text(SCENE_003_PY, encoding="utf-8")

    storyboard = {
        "job_id": job_id,
        "title": "Gradient Descent Optimization with Visual QA",
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
                "start_time": 0.0,
                "end_time": 10.0,
            },
            {
                "scene_id": "scene_002",
                "text": "At each step, parameters are updated in the opposite direction of the gradient to descend the loss curve.",
                "start_time": 10.0,
                "end_time": 20.0,
            },
            {
                "scene_id": "scene_003",
                "text": "When the gradient approaches zero, the step sizes shrink and the algorithm converges to the optimal parameter.",
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
    assert val_res["is_valid"] is True
    print("Plan validated successfully.")

    # 4. execute_job via MCP (Full Rendering & Postproduction)
    print("\n--- 4. Calling execute_job via MCP ---")
    exec_res = tools.execute_job(job_id)
    assert exec_res["status"] == "completed"
    print("Initial video rendering & postproduction completed.")

    # 5. inspect_video via MCP
    print("\n--- 5. Calling inspect_video via MCP ---")
    qa_report = tools.inspect_video(job_id)
    print(f"Overall QA Status: {qa_report.get('overall_status')}")
    print(f"Contact Sheet: {qa_report.get('contact_sheet_path')}")
    assert qa_report["overall_status"] == "passed"
    assert qa_report["scenes_passed"] == 3
    assert Path(qa_report["contact_sheet_path"]).exists()

    # Track modification times to verify targeted re-rendering
    scene_001_mp4 = job_dir / "renders" / "scene_001.mp4"
    scene_003_mp4 = job_dir / "renders" / "scene_003.mp4"
    scene_001_mtime_before = scene_001_mp4.stat().st_mtime
    scene_003_mtime_before = scene_003_mp4.stat().st_mtime

    # 6. Deliberately introduce detectable visual defect into scene 2
    print("\n--- 6. Injecting deliberate visual defect into scene 2 (completely blank/black animation) ---")
    (scenes_dir / "scene_002.py").write_text(SCENE_002_DEFECTIVE_PY, encoding="utf-8")

    # Call retry_scene on scene_002
    print("Executing retry_scene on defective scene 2...")
    retry_defective = tools.retry_scene(job_id, "scene_002")
    print(f"Defective scene retry result: {retry_defective}")

    # Inspect scene 2 via inspect_scene MCP tool
    scene_2_qa = tools.inspect_scene(job_id, "scene_002")
    print("Scene 2 QA Inspection findings:", scene_2_qa)
    assert scene_2_qa["is_blank"] is True, "Expected blank frame defect was not detected"
    assert scene_2_qa["status"] == "failed"
    print("CONFIRMED: Automated Visual QA successfully detected blank frame defect!")

    # 7. Agent submits structured visual review via MCP
    print("\n--- 7. External Director submitting structured visual review via MCP ---")
    visual_review_data = {
        "job_id": job_id,
        "reviewer": "codex_antigravity",
        "overall_status": "needs_repair",
        "issues": [
            {
                "scene_id": "scene_002",
                "severity": "critical",
                "issue_type": "blank_frame",
                "description": "Scene 2 rendered as a completely blank black screen with zero contrast or math visualization.",
                "suggested_fix": "Restore the descent trajectory visualization with axes and moving dot.",
            }
        ],
        "scenes_to_repair": ["scene_002"],
        "notes": "Scene 2 animation requires code restoration.",
    }
    review_res = tools.submit_visual_review(job_id, visual_review_data)
    print("submit_visual_review response:", review_res)
    assert review_res["success"] is True

    # 8. External Director repairs scene 2 code
    print("\n--- 8. External Director repairing scene 2 animation code ---")
    (scenes_dir / "scene_002.py").write_text(SCENE_002_PY, encoding="utf-8")

    # 9. Execute targeted retry_scene
    print("\n--- 9. Calling retry_scene on repaired scene 2 ---")
    retry_repaired = tools.retry_scene(job_id, "scene_002")
    print(f"Repaired scene retry result: {retry_repaired}")
    assert retry_repaired["success"] is True
    assert retry_repaired["qa_status"] == "passed"

    # 10. Verify targeted repair: scenes 1 and 3 were NOT re-rendered
    print("\n--- 10. Verifying targeted scene repair isolation ---")
    scene_001_mtime_after = scene_001_mp4.stat().st_mtime
    scene_003_mtime_after = scene_003_mp4.stat().st_mtime
    assert scene_001_mtime_before == scene_001_mtime_after, "Scene 1 was re-rendered unnecessarily!"
    assert scene_003_mtime_before == scene_003_mtime_after, "Scene 3 was re-rendered unnecessarily!"
    print("CONFIRMED: Targeted repair verified! Scenes 1 and 3 were preserved without re-rendering.")

    # 11. Rerun inspect_video & get_quality_report
    print("\n--- 11. Final QA Inspection via get_quality_report ---")
    final_qa = tools.get_quality_report(job_id)
    assert final_qa["overall_status"] == "passed"
    assert final_qa["scenes_passed"] == 3
    print(f"All 3 scenes PASSED visual QA. Contact sheet: {final_qa['contact_sheet_path']}")

    # 12. FFprobe validation of final composed MP4
    print("\n--- 12. Validating Final MP4 with FFprobe ---")
    final_mp4 = job_dir / "output" / "final.mp4"
    assert final_mp4.exists()

    sandbox_dir = Path("/home/othmane/Faceless_V2/video_docker_sandbox")
    rel_mp4 = final_mp4.relative_to(WORKSPACE)
    probe_cmd = [
        "docker", "compose", "-f", str(sandbox_dir / "compose.yaml"),
        "run", "--rm",
        "--entrypoint", "ffprobe",
        "ffmpeg",
        "-v", "error",
        "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height,channels,sample_rate",
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

    assert video_stream is not None and video_stream.get("codec_name") == "h264"
    assert audio_stream is not None and audio_stream.get("codec_name") == "aac"
    assert abs(duration - 30.0) < 0.5, f"Expected 30.0s duration, got {duration}s"

    print("\n==================================================================")
    print("=== MILESTONE 3 ACCEPTANCE TEST PASSED! ===")
    print(f"Job ID: {job_id}")
    print(f"Output MP4: {final_mp4}")
    print(f"Contact Sheet: {final_qa['contact_sheet_path']}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Resolution: {video_stream.get('width')}x{video_stream.get('height')}")
    print(f"Video Codec: {video_stream.get('codec_name')}")
    print(f"Audio Codec: {audio_stream.get('codec_name')} ({audio_stream.get('sample_rate')} Hz)")
    print(f"File Size: {file_size} bytes ({file_size / 1024:.1f} KB)")
    print("==================================================================")


if __name__ == "__main__":
    main()
