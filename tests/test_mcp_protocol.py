"""Integration tests for FastMCP Protocol and STDIO transport.

Verifies true client-server communication using the official MCP Python SDK
(mcp.client.stdio, mcp.client.session) rather than direct Python method calls.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import sys
import pytest

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from mcp.types import CallToolResult, TextContent


def get_server_params(workspace_dir: Path) -> StdioServerParameters:
    """Construct STDIO server parameters pointing to local Python FastMCP server."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
    # Point workspace to the test temp directory if needed, or use default
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "ai_video_pipeline.mcp.server"],
        env=env,
    )


def parse_tool_result(result: CallToolResult) -> dict:
    """Parse JSON payload from an MCP CallToolResult."""
    assert len(result.content) > 0, "MCP result contained no content blocks"
    first = result.content[0]
    assert isinstance(first, TextContent), f"Expected TextContent, got {type(first)}"
    return json.loads(first.text)


def test_mcp_server_initialization_and_tool_discovery(tmp_path: Path):
    """Verify MCP protocol initialization and discovery of all 11 registered tools."""
    async def _run():
        params = get_server_params(tmp_path)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                init_res = await session.initialize()
                assert init_res.serverInfo.name == "ai-video-pipeline"

                tools_list = await session.list_tools()
                tool_names = {t.name for t in tools_list.tools}
                expected_tools = {
                    "create_job",
                    "validate_plan",
                    "execute_job",
                    "get_job_status",
                    "get_job_errors",
                    "retry_scene",
                    "retry_postproduction",
                    "inspect_video",
                    "inspect_scene",
                    "submit_visual_review",
                    "get_quality_report",
                }
                assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"
                assert len(tools_list.tools) == 11

    asyncio.run(_run())


def test_mcp_create_job_over_stdio(tmp_path: Path):
    """Verify invoking create_job over real MCP STDIO transport."""
    async def _run():
        params = get_server_params(tmp_path)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                res = await session.call_tool(
                    "create_job",
                    arguments={
                        "video_type": "cs_math_educational",
                        "topic_or_prompt": "Binary Search Protocol Test",
                        "target_duration_seconds": 30.0,
                        "language": "en",
                        "aspect_ratio": "16:9",
                    },
                )
                data = parse_tool_result(res)
                assert data["success"] is True
                assert "job_id" in data
                job_id = data["job_id"]
                job_dir = Path(data["job_dir"])
                assert job_dir.exists()
                assert (job_dir / "request.json").exists()

                # Clean up test job
                try:
                    lock_file = job_dir.parent / ".active_job"
                    if lock_file.exists():
                        lock_file.unlink()
                    shutil.rmtree(job_dir, ignore_errors=True)
                except Exception:
                    pass

    asyncio.run(_run())


def test_mcp_validate_plan_missing_job(tmp_path: Path):
    """Verify MCP error response when validating non-existent job."""
    async def _run():
        params = get_server_params(tmp_path)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                res = await session.call_tool(
                    "validate_plan",
                    arguments={"job_id": "non_existent_9999"},
                )
                data = parse_tool_result(res)
                assert data["is_valid"] is False
                assert len(data["issues"]) > 0

    asyncio.run(_run())


def test_mcp_get_job_status_and_errors(tmp_path: Path):
    """Verify get_job_status and get_job_errors over MCP STDIO."""
    async def _run():
        params = get_server_params(tmp_path)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # 1. Create a job
                create_res = await session.call_tool(
                    "create_job",
                    arguments={
                        "video_type": "general_explanatory",
                        "topic_or_prompt": "Photosynthesis",
                        "target_duration_seconds": 15.0,
                    },
                )
                cdata = parse_tool_result(create_res)
                assert cdata["success"] is True
                job_id = cdata["job_id"]
                job_dir = Path(cdata["job_dir"])

                try:
                    # 2. Query status
                    status_res = await session.call_tool(
                        "get_job_status",
                        arguments={"job_id": job_id},
                    )
                    sdata = parse_tool_result(status_res)
                    assert sdata["state"] == "created"
                    assert sdata["progress_pct"] == 0

                    # 3. Query errors (empty initially)
                    err_res = await session.call_tool(
                        "get_job_errors",
                        arguments={"job_id": job_id},
                    )
                    edata = parse_tool_result(err_res)
                    assert edata["job_id"] == job_id
                    assert edata["scene_errors"] == []
                    assert edata["global_errors"] == []

                finally:
                    # Cleanup
                    lock_file = job_dir.parent / ".active_job"
                    if lock_file.exists():
                        lock_file.unlink()
                    shutil.rmtree(job_dir, ignore_errors=True)

    asyncio.run(_run())


def test_mcp_single_active_job_conflict(tmp_path: Path):
    """Verify that MCP rejects second job creation while first job is locked."""
    async def _run():
        params = get_server_params(tmp_path)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # Create first job
                res1 = await session.call_tool(
                    "create_job",
                    arguments={
                        "video_type": "kids_animated_story",
                        "topic_or_prompt": "First Active Job",
                        "target_duration_seconds": 10.0,
                    },
                )
                d1 = parse_tool_result(res1)
                assert d1["success"] is True
                job1_id = d1["job_id"]
                job1_dir = Path(d1["job_dir"])

                try:
                    # Attempt second job while job 1 lock is held
                    res2 = await session.call_tool(
                        "create_job",
                        arguments={
                            "video_type": "kids_animated_story",
                            "topic_or_prompt": "Second Conflicting Job",
                            "target_duration_seconds": 10.0,
                        },
                    )
                    d2 = parse_tool_result(res2)
                    assert d2["success"] is False
                    assert "active job" in d2["error"].lower() or "locked" in d2["error"].lower()

                finally:
                    lock_file = job1_dir.parent / ".active_job"
                    if lock_file.exists():
                        lock_file.unlink()
                    shutil.rmtree(job1_dir, ignore_errors=True)

    asyncio.run(_run())


def test_mcp_visual_review_submission_and_report(tmp_path: Path):
    """Verify submit_visual_review and get_quality_report tools over MCP STDIO."""
    async def _run():
        params = get_server_params(tmp_path)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # Create job
                c_res = await session.call_tool(
                    "create_job",
                    arguments={
                        "video_type": "cs_math_educational",
                        "topic_or_prompt": "QA MCP Protocol Test",
                        "target_duration_seconds": 20.0,
                    },
                )
                cdata = parse_tool_result(c_res)
                job_id = cdata["job_id"]
                job_dir = Path(cdata["job_dir"])

                try:
                    # Submit visual review
                    review_payload = {
                        "job_id": job_id,
                        "reviewer": "test_agent",
                        "overall_status": "needs_repair",
                        "issues": [
                            {
                                "scene_id": "scene_001",
                                "severity": "medium",
                                "issue_type": "frozen_frame",
                                "description": "Text element does not move.",
                                "suggested_fix": "Add Write animation.",
                            }
                        ],
                        "scenes_to_repair": ["scene_001"],
                        "notes": "Testing review over MCP.",
                    }
                    rev_res = await session.call_tool(
                        "submit_visual_review",
                        arguments={"job_id": job_id, "review": review_payload},
                    )
                    rdata = parse_tool_result(rev_res)
                    assert rdata["success"] is True
                    assert rdata["job_id"] == job_id
                    assert rdata["overall_status"] == "needs_repair"

                    # Fetch quality report
                    rep_res = await session.call_tool(
                        "get_quality_report",
                        arguments={"job_id": job_id},
                    )
                    rep_data = parse_tool_result(rep_res)
                    assert rep_data["job_id"] == job_id
                    assert rep_data["ai_review"] is not None
                    assert rep_data["ai_review"]["reviewer"] == "test_agent"

                finally:
                    lock_file = job_dir.parent / ".active_job"
                    if lock_file.exists():
                        lock_file.unlink()
                    shutil.rmtree(job_dir, ignore_errors=True)

    asyncio.run(_run())
