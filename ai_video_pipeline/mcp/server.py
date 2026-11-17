"""Local Python MCP Server definition exposing video generation tools via FastMCP."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional

from mcp.server.fastmcp import FastMCP

from ai_video_pipeline.mcp.tools import PipelineMCPTools


def create_pipeline_mcp_server(tools: Optional[PipelineMCPTools] = None) -> FastMCP:
    """Factory creating and configuring the FastMCP server with pipeline tools."""
    tools_instance = tools or PipelineMCPTools()
    server = FastMCP("ai-video-pipeline")

    @server.tool(name="create_job")
    def create_job(
        video_type: str,
        topic_or_prompt: str,
        target_duration_seconds: float,
        language: str = "en",
        aspect_ratio: str = "16:9",
    ) -> Dict[str, Any]:
        """Create a dedicated job workspace directory and write request.json."""
        return tools_instance.create_job(
            video_type=video_type,
            topic_or_prompt=topic_or_prompt,
            target_duration_seconds=target_duration_seconds,
            language=language,
            aspect_ratio=aspect_ratio,
        )

    @server.tool(name="validate_plan")
    def validate_plan(job_id: str) -> Dict[str, Any]:
        """Validate the AI-authored storyboard.json, scene code files, and timeline."""
        return tools_instance.validate_plan(job_id=job_id)

    @server.tool(name="execute_job")
    def execute_job(job_id: str) -> Dict[str, Any]:
        """Trigger deterministic rendering and composition in Docker animation sandbox."""
        return tools_instance.execute_job(job_id=job_id)

    @server.tool(name="get_job_status")
    def get_job_status(job_id: str) -> Dict[str, Any]:
        """Query current job lifecycle state, progress percentage, and stage from status.json."""
        return tools_instance.get_job_status(job_id=job_id)

    @server.tool(name="get_job_errors")
    def get_job_errors(job_id: str) -> Dict[str, Any]:
        """Retrieve structured error reports from errors.json to guide scene repair."""
        return tools_instance.get_job_errors(job_id=job_id)

    @server.tool(name="retry_scene")
    def retry_scene(job_id: str, scene_id: str) -> Dict[str, Any]:
        """Re-validate, re-render, and re-composite only a repaired scene."""
        return tools_instance.retry_scene(job_id=job_id, scene_id=scene_id)

    return server


class LocalPipelineMCPServer:
    """Local Model Context Protocol (MCP) server managing tool registration and dispatch."""

    def __init__(self, tools: Optional[PipelineMCPTools] = None) -> None:
        self.tools = tools or PipelineMCPTools()
        self.fastmcp = create_pipeline_mcp_server(self.tools)
        self._custom_tools: Dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, handler: Callable[..., Any], description: str = "") -> None:
        """Register a pipeline tool with the MCP server."""
        self._custom_tools[name] = handler
        self.fastmcp.tool(name=name, description=description)(handler)

    def setup_tool_routes(self) -> None:
        """Core tools are registered on creation; kept for backward compatibility."""
        pass

    def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch direct method calls to the tools implementation."""
        if hasattr(self.tools, method):
            fn = getattr(self.tools, method)
            return fn(**params)
        elif method in self._custom_tools:
            return self._custom_tools[method](**params)
        else:
            raise ValueError(f"Unknown MCP method: {method}")

    def start_stdio_server(self) -> None:
        """Launch stdio MCP transport for Codex / Antigravity integration."""
        self.fastmcp.run(transport="stdio")
