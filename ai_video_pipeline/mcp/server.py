"""Local Python MCP Server definition exposing video generation tools."""

from typing import Any, Callable, Dict, Optional

from ai_video_pipeline.mcp.tools import PipelineMCPTools


class LocalPipelineMCPServer:
    """Local Model Context Protocol (MCP) server managing tool registration and dispatch."""

    def __init__(self, tools: Optional[PipelineMCPTools] = None) -> None:
        pass

    def register_tool(self, name: str, handler: Callable[..., Any], description: str) -> None:
        """Register a pipeline tool with the MCP server."""
        pass

    def setup_tool_routes(self) -> None:
        """Register the 6 core pipeline tools: create_job, validate_plan, execute_job, etc."""
        pass

    def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch incoming MCP JSON-RPC tool requests to local file operations."""
        pass

    def start_stdio_server(self) -> None:
        """Interface definition for launching stdio MCP transport (not executed in scaffold)."""
        pass
