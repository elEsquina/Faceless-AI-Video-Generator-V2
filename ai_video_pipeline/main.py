"""Main entry point for starting the local MCP server or pipeline runner."""

from pathlib import Path
from typing import Optional

from ai_video_pipeline.core.director import ExternalDirectorBridge
from ai_video_pipeline.core.pipeline import VideoGenerationPipeline
from ai_video_pipeline.mcp.server import LocalPipelineMCPServer
from ai_video_pipeline.mcp.tools import PipelineMCPTools
from ai_video_pipeline.media.compositor import VideoCompositor
from ai_video_pipeline.media.renderer import SceneRenderer
from ai_video_pipeline.media.text_splash import TextSplashGenerator
from ai_video_pipeline.media.tts import TextToSpeechService
from ai_video_pipeline.parsers.omega import ParserOmega
from ai_video_pipeline.parsers.theta import ParserTheta
from ai_video_pipeline.quality.validator import QualityValidator


class PipelineApplication:
    """Application bootstrapper and MCP server coordinator."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = workspace_root

    def bootstrap_pipeline(self) -> VideoGenerationPipeline:
        """Initialize and wire deterministic local pipeline services."""
        return VideoGenerationPipeline()

    def bootstrap_mcp_server(self) -> LocalPipelineMCPServer:
        """Wire MCP tools and initialize the local Python MCP server."""
        tools = PipelineMCPTools(workspace_root=self.workspace_root)
        return LocalPipelineMCPServer(tools=tools)


def main() -> None:
    """CLI and application entrypoint to start MCP STDIO server."""
    app = PipelineApplication()
    server = app.bootstrap_mcp_server()
    server.start_stdio_server()


if __name__ == "__main__":
    main()
