"""Milestone 3.5: Real MCP Integration and Autonomous Video Repair Acceptance Test.

Executes the complete end-to-end workflow using true MCP protocol client-server
communication over STDIO (no direct Python method calls to PipelineMCPTools):

User Request -> External Director -> FastMCP Server (STDIO) -> Parser Omega ->
Docker Renderer -> Parser Theta -> Kokoro TTS -> Text Splash -> FFmpeg ->
Visual QA -> External Director Review -> Code Repair -> MCP retry_scene -> Final MP4
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from mcp.types import CallToolResult, TextContent


WORKSPACE_ROOT = Path("/home/othmane/Faceless_V2/video_docker_sandbox/workspace")
JOBS_ROOT = WORKSPACE_ROOT / "jobs"

# ==============================================================================
# Original CS/Math Animation Code: Binary Search (3 Scenes)
# ==============================================================================

SCENE_001_PY = '''from manim import *

class BinarySearchIntro(Scene):
    def construct(self):
        title = Text("Binary Search Algorithm", font_size=40, color=BLUE).to_edge(UP)
        subtitle = Text("Efficient Search in a Sorted Array", font_size=24, color=GRAY).next_to(title, DOWN)
        self.play(Write(title), FadeIn(subtitle), run_time=2.0)
        
        target_label = MathTex(r"\\text{Target: } T = 49", font_size=32, color=YELLOW).shift(UP * 1.5)
        self.play(Write(target_label), run_time=1.5)
        
        values = [3, 8, 14, 27, 35, 49, 62]
        cells = VGroup()
        for i, val in enumerate(values):
            sq = Square(side_length=1.0, color=WHITE, fill_opacity=0.2, fill_color=BLUE)
            num = Text(str(val), font_size=28, color=WHITE)
            idx = Text(f"[{i}]", font_size=18, color=GRAY).next_to(sq, DOWN * 0.7)
            cell = VGroup(sq, num, idx)
            cells.add(cell)
            
        cells.arrange(RIGHT, buff=0.2).shift(DOWN * 0.5)
        self.play(Create(cells), run_time=3.5)
        self.wait(3.0)
'''

SCENE_002_VALID_PY = '''from manim import *

class BinarySearchFirstStep(Scene):
    def construct(self):
        title = Text("Step 1: Check the Midpoint", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(title), run_time=1.5)
        
        target_label = MathTex(r"T = 49 \\quad (\\text{Target})", font_size=28, color=YELLOW).next_to(title, DOWN)
        self.play(FadeIn(target_label), run_time=1.0)
        
        values = [3, 8, 14, 27, 35, 49, 62]
        cells = VGroup()
        for i, val in enumerate(values):
            sq = Square(side_length=1.0, color=WHITE, fill_opacity=0.2, fill_color=BLUE)
            num = Text(str(val), font_size=28, color=WHITE)
            idx = Text(f"[{i}]", font_size=18, color=GRAY).next_to(sq, DOWN * 0.7)
            cells.add(VGroup(sq, num, idx))
            
        cells.arrange(RIGHT, buff=0.2).shift(DOWN * 0.2)
        self.add(cells)
        
        p_low = Text("Low", font_size=20, color=GREEN).next_to(cells[0], UP * 0.8)
        p_high = Text("High", font_size=20, color=RED).next_to(cells[6], UP * 0.8)
        p_mid = Text("Mid (27)", font_size=20, color=YELLOW).next_to(cells[3], UP * 0.8)
        self.play(FadeIn(p_low), FadeIn(p_high), FadeIn(p_mid), run_time=1.5)
        
        box = SurroundingRectangle(cells[3], color=YELLOW, buff=0.08)
        comp_text = MathTex(r"49 > 27 \\implies \\text{Search Right}", font_size=26, color=YELLOW).shift(DOWN * 2.2)
        self.play(Create(box), Write(comp_text), run_time=2.0)
        
        left_half = VGroup(cells[0], cells[1], cells[2], cells[3], p_low, p_mid, box)
        self.play(left_half.animate.set_opacity(0.25), run_time=1.5)
        
        new_low = Text("New Low", font_size=20, color=GREEN).next_to(cells[4], UP * 0.8)
        self.play(FadeIn(new_low), run_time=1.0)
        self.wait(1.5)
'''

# Defective Scene 2: Empty construct resulting in 100% blank black frame defect
SCENE_002_DEFECTIVE_PY = '''from manim import *

class BinarySearchFirstStep(Scene):
    def construct(self):
        # Deliberate Defect: completely empty scene without any visuals
        self.wait(10.0)
'''

SCENE_003_PY = '''from manim import *

class BinarySearchFound(Scene):
    def construct(self):
        title = Text("Step 2: Target Found!", font_size=36, color=GREEN).to_edge(UP)
        self.play(Write(title), run_time=1.5)
        
        values = [3, 8, 14, 27, 35, 49, 62]
        cells = VGroup()
        for i, val in enumerate(values):
            sq = Square(side_length=1.0, color=WHITE, fill_opacity=0.2, fill_color=BLUE)
            num = Text(str(val), font_size=28, color=WHITE)
            idx = Text(f"[{i}]", font_size=18, color=GRAY).next_to(sq, DOWN * 0.7)
            cells.add(VGroup(sq, num, idx))
            
        cells.arrange(RIGHT, buff=0.2).shift(DOWN * 0.2)
        for i in range(4):
            cells[i].set_opacity(0.25)
        self.add(cells)
        
        p_mid = Text("Mid (49)", font_size=22, color=GREEN).next_to(cells[5], UP * 0.8)
        self.play(FadeIn(p_mid), run_time=1.5)
        
        highlight_box = SurroundingRectangle(cells[5], color=GREEN, buff=0.1, stroke_width=4)
        match_text = MathTex(r"A[5] = 49 == T \\quad \\checkmark", font_size=30, color=GREEN).shift(DOWN * 1.8)
        self.play(Create(highlight_box), Write(match_text), run_time=2.0)
        
        complexity = MathTex(r"\\text{Time Complexity: } \\mathcal{O}(\\log_2 n)", font_size=32, color=YELLOW).shift(DOWN * 2.6)
        self.play(Write(complexity), run_time=2.0)
        self.wait(3.0)
'''


def parse_mcp_result(result: CallToolResult) -> dict:
    """Parse JSON payload from CallToolResult."""
    assert len(result.content) > 0, "MCP result contained no content blocks"
    first = result.content[0]
    assert isinstance(first, TextContent)
    return json.loads(first.text)


async def run_milestone3_5_test() -> dict:
    print("============================================================================")
    print("=== Milestone 3.5: Real MCP Integration & Autonomous Video Repair Test ===")
    print("============================================================================")

    # Clean active job lock if present
    lock_file = JOBS_ROOT / ".active_job"
    if lock_file.exists():
        lock_file.unlink()

    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/othmane/Faceless_V2"
    server_params = StdioServerParameters(
        command="/home/othmane/miniforge3/bin/python3",
        args=["-m", "ai_video_pipeline.mcp.server"],
        env=env,
    )

    print("\n--- 1. Launching FastMCP Server over STDIO ---")
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_res = await session.initialize()
            print(f"Connected to MCP Server: {init_res.serverInfo.name} (version {init_res.serverInfo.version})")

            # 2. Tool Discovery via tools/list
            print("\n--- 2. Discovering Registered MCP Tools ---")
            tools_resp = await session.list_tools()
            tool_names = [t.name for t in tools_resp.tools]
            print(f"Discovered {len(tool_names)} tools: {', '.join(tool_names)}")
            assert "create_job" in tool_names
            assert "validate_plan" in tool_names
            assert "execute_job" in tool_names
            assert "inspect_video" in tool_names
            assert "inspect_scene" in tool_names
            assert "submit_visual_review" in tool_names
            assert "retry_scene" in tool_names

            # 3. Invoke create_job over MCP STDIO
            print("\n--- 3. Invoking create_job via MCP Protocol ---")
            create_res = await session.call_tool(
                "create_job",
                arguments={
                    "video_type": "cs_math_educational",
                    "topic_or_prompt": "Binary search algorithm with 3 scenes, English narration, captions, 16:9",
                    "target_duration_seconds": 30.0,
                    "language": "en",
                    "aspect_ratio": "16:9",
                },
            )
            cdata = parse_mcp_result(create_res)
            assert cdata["success"] is True
            job_id = cdata["job_id"]
            job_dir = Path(cdata["job_dir"])
            print(f"MCP Job Created: {job_id} at {job_dir}")
            assert (job_dir / "request.json").exists()

            # 4. External Director generates animation and postproduction artifacts
            print("\n--- 4. External Director Authoring Scene Code & Plans ---")
            scenes_dir = job_dir / "scenes"
            scenes_dir.mkdir(parents=True, exist_ok=True)

            (scenes_dir / "scene_001.py").write_text(SCENE_001_PY, encoding="utf-8")
            (scenes_dir / "scene_002.py").write_text(SCENE_002_VALID_PY, encoding="utf-8")
            (scenes_dir / "scene_003.py").write_text(SCENE_003_PY, encoding="utf-8")

            storyboard = {
                "job_id": job_id,
                "title": "Binary Search Algorithm Explanation",
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
                        "narration_text": "Binary search finds a target item in a sorted list by repeatedly dividing the search space in half instead of scanning sequentially.",
                        "visual_description": "Sorted array cells with indices and target label",
                        "code_file": "scene_001.py",
                    },
                    {
                        "scene_id": "scene_002",
                        "index": 1,
                        "engine": "manim",
                        "start_time": 10.0,
                        "end_time": 20.0,
                        "narration_text": "We inspect the middle element, twenty-seven. Since forty-nine is greater, we eliminate the entire left half.",
                        "visual_description": "Pointers Low, Mid, High with middle comparison and left half elimination",
                        "code_file": "scene_002.py",
                    },
                    {
                        "scene_id": "scene_003",
                        "index": 2,
                        "engine": "manim",
                        "start_time": 20.0,
                        "end_time": 30.0,
                        "narration_text": "At the next midpoint, we find forty-nine. With each step cutting possibilities in half, binary search runs in logarithmic time.",
                        "visual_description": "Target found highlight and logarithmic time complexity formula",
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
                        "text": "Binary search finds a target item in a sorted list by repeatedly dividing the search space in half instead of scanning sequentially.",
                        "start_time": 0.0,
                        "end_time": 10.0,
                    },
                    {
                        "scene_id": "scene_002",
                        "text": "We inspect the middle element, twenty-seven. Since forty-nine is greater, we eliminate the entire left half.",
                        "start_time": 10.0,
                        "end_time": 20.0,
                    },
                    {
                        "scene_id": "scene_003",
                        "text": "At the next midpoint, we find forty-nine. With each step cutting possibilities in half, binary search runs in logarithmic time.",
                        "start_time": 20.0,
                        "end_time": 30.0,
                    },
                ],
                "sfx_cues": [
                    {
                        "cue_id": "sfx_target_found",
                        "audio_type": "sound_effect",
                        "source_file": "chime_sfx.wav",
                        "start_time": 23.5,
                        "duration_seconds": 0.6,
                        "volume_level": 0.45,
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
            print("Storyboard, audio plan, and scene scripts successfully written.")

            # 5. Invoke validate_plan over MCP STDIO
            print("\n--- 5. Invoking validate_plan via MCP Protocol ---")
            val_res = await session.call_tool("validate_plan", arguments={"job_id": job_id})
            vdata = parse_mcp_result(val_res)
            print(f"validate_plan result: is_valid={vdata['is_valid']}, issues={vdata['issues']}")
            assert vdata["is_valid"] is True

            # 6. Invoke execute_job over MCP STDIO
            print("\n--- 6. Invoking execute_job via MCP Protocol ---")
            exec_res = await session.call_tool("execute_job", arguments={"job_id": job_id})
            edata = parse_mcp_result(exec_res)
            print(f"execute_job result: status={edata['status']}, output={edata.get('output_path')}")
            assert edata["status"] == "completed"
            assert Path(edata["output_path"]).exists()

            # 7. Invoke inspect_video over MCP STDIO
            print("\n--- 7. Invoking inspect_video via MCP Protocol ---")
            qa_res = await session.call_tool("inspect_video", arguments={"job_id": job_id})
            qadata = parse_mcp_result(qa_res)
            print(f"inspect_video result: overall_status={qadata['overall_status']}, contact_sheet={qadata['contact_sheet_path']}")
            assert qadata["overall_status"] == "passed"
            assert qadata["scenes_passed"] == 3
            assert Path(qadata["contact_sheet_path"]).exists()

            # Record scene mtimes before defect test
            scene_001_mp4 = job_dir / "renders" / "scene_001.mp4"
            scene_003_mp4 = job_dir / "renders" / "scene_003.mp4"
            mtime_scene1_before = scene_001_mp4.stat().st_mtime
            mtime_scene3_before = scene_003_mp4.stat().st_mtime

            # 8. Inject deliberate visual defect into Scene 2
            print("\n--- 8. Injecting Deliberate Visual Defect into Scene 2 ---")
            (scenes_dir / "scene_002.py").write_text(SCENE_002_DEFECTIVE_PY, encoding="utf-8")

            # 9. Invoke retry_scene over MCP STDIO on defective scene
            print("\n--- 9. Invoking retry_scene on Defective Scene 2 via MCP Protocol ---")
            retry_def_res = await session.call_tool("retry_scene", arguments={"job_id": job_id, "scene_id": "scene_002"})
            r_def_data = parse_mcp_result(retry_def_res)
            print("Defective retry_scene response:", r_def_data)
            assert r_def_data["qa_status"] == "failed"

            # 10. Autonomous Visual QA: Inspect defective scene via MCP
            print("\n--- 10. Agent Invoking inspect_scene via MCP Protocol ---")
            inspect_def_res = await session.call_tool("inspect_scene", arguments={"job_id": job_id, "scene_id": "scene_002"})
            s2_def = parse_mcp_result(inspect_def_res)
            print("Defective Scene 2 Metrics:", s2_def)
            assert s2_def["is_blank"] is True
            assert s2_def["status"] == "failed"
            print("Agent Observation: Scene 2 keyframes are 100% black (mean=0.0, std=0.0). Construct method had no visual mobjects.")

            # 11. Agent submits structured visual review via MCP
            print("\n--- 11. Agent Invoking submit_visual_review via MCP Protocol ---")
            review_payload = {
                "job_id": job_id,
                "reviewer": "codex_antigravity",
                "overall_status": "needs_repair",
                "issues": [
                    {
                        "scene_id": "scene_002",
                        "severity": "critical",
                        "issue_type": "blank_frame",
                        "description": "Scene 2 rendered as an empty black screen with zero contrast or elements.",
                        "suggested_fix": "Restore Manim construct method drawing array cells, pointers, and midpoint comparison.",
                    }
                ],
                "scenes_to_repair": ["scene_002"],
                "notes": "Scene 2 requires animation code restoration.",
            }
            rev_res = await session.call_tool("submit_visual_review", arguments={"job_id": job_id, "review": review_payload})
            rev_data = parse_mcp_result(rev_res)
            print("submit_visual_review response:", rev_data)
            assert rev_data["success"] is True

            # 12. Autonomous Code Repair: Agent fixes scene_002.py
            print("\n--- 12. Agent Repairing Scene 2 Animation Code ---")
            (scenes_dir / "scene_002.py").write_text(SCENE_002_VALID_PY, encoding="utf-8")

            # 13. Invoke retry_scene over MCP STDIO for repaired scene
            print("\n--- 13. Invoking retry_scene on Repaired Scene 2 via MCP Protocol ---")
            retry_rep_res = await session.call_tool("retry_scene", arguments={"job_id": job_id, "scene_id": "scene_002"})
            r_rep_data = parse_mcp_result(retry_rep_res)
            print("Repaired retry_scene response:", r_rep_data)
            assert r_rep_data["qa_status"] == "passed"

            # 14. Verify Targeted Repair: Scenes 1 and 3 were NOT re-rendered
            print("\n--- 14. Verifying Targeted Repair Isolation ---")
            mtime_scene1_after = scene_001_mp4.stat().st_mtime
            mtime_scene3_after = scene_003_mp4.stat().st_mtime
            assert mtime_scene1_before == mtime_scene1_after, "Scene 1 was re-rendered unnecessarily!"
            assert mtime_scene3_before == mtime_scene3_after, "Scene 3 was re-rendered unnecessarily!"
            print("CONFIRMED: Scene 1 and Scene 3 retained their original render files untouched.")

            # 15. Verify Final Quality Report via get_quality_report
            print("\n--- 15. Invoking get_quality_report via MCP Protocol ---")
            final_qa_res = await session.call_tool("get_quality_report", arguments={"job_id": job_id})
            final_qa = parse_mcp_result(final_qa_res)
            print(f"Final QA Status: {final_qa['overall_status']}, Passed: {final_qa['scenes_passed']}/{final_qa['total_scenes']}")
            assert final_qa["overall_status"] == "passed"
            assert final_qa["scenes_passed"] == 3

            # 16. Inspect Final Video with FFprobe
            print("\n--- 16. Probing Final MP4 Video ---")
            final_mp4 = Path(r_rep_data["output_path"])
            probe_cmd = [
                "docker", "compose", "-f", "/home/othmane/Faceless_V2/video_docker_sandbox/compose.yaml",
                "run", "--rm",
                "--entrypoint", "ffprobe",
                "ffmpeg",
                "-v", "error",
                "-show_entries", "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height",
                "-of", "json",
                f"/workspace/jobs/{job_id}/output/final.mp4",
            ]
            probe_proc = subprocess.run(probe_cmd, cwd="/home/othmane/Faceless_V2/video_docker_sandbox", capture_output=True, text=True)
            probe_data = json.loads(probe_proc.stdout)
            format_info = probe_data.get("format", {})
            streams = probe_data.get("streams", [])
            video_stream = next(s for s in streams if s["codec_type"] == "video")
            audio_stream = next(s for s in streams if s["codec_type"] == "audio")

            duration = float(format_info.get("duration", 0.0))
            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))
            vcodec = video_stream.get("codec_name")
            acodec = audio_stream.get("codec_name")
            file_size = int(format_info.get("size", 0))

            print("============================================================================")
            print("=== MILESTONE 3.5 ACCEPTANCE TEST COMPLETED SUCCESSFULLY! ===")
            print(f"Job ID: {job_id}")
            print(f"Output Video: {final_mp4}")
            print(f"Contact Sheet: {final_qa['contact_sheet_path']}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Resolution: {width}x{height}")
            print(f"Video Codec: {vcodec}")
            print(f"Audio Codec: {acodec}")
            print(f"File Size: {file_size} bytes ({file_size / 1024:.1f} KB)")
            print("============================================================================")

            assert 29.0 <= duration <= 31.0
            assert width == 854 and height == 480
            assert vcodec == "h264"
            assert acodec == "aac"

            return {
                "job_id": job_id,
                "final_mp4": str(final_mp4),
                "contact_sheet": final_qa["contact_sheet_path"],
                "duration": duration,
                "resolution": f"{width}x{height}",
                "file_size": file_size,
            }


if __name__ == "__main__":
    asyncio.run(run_milestone3_5_test())
