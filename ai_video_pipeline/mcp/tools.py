"""Local MCP Tool implementations for external AI coding agents (Codex / Antigravity)."""

from pathlib import Path
from typing import Any, Dict, List, Optional


class PipelineMCPTools:
    """Defines tool interfaces exposed via Model Context Protocol (MCP) to external AI agents."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        pass

    def create_job(
        self,
        video_type: str,
        topic_or_prompt: str,
        target_duration_seconds: float,
        language: str = "en",
        aspect_ratio: str = "16:9",
    ) -> Dict[str, Any]:
        """Create a dedicated job workspace directory and write request.json."""
        pass

    def validate_plan(self, job_id: str) -> Dict[str, Any]:
        """Validate the AI-authored plan.json, scene code files, and shared timeline consistency."""
        pass

    def execute_job(self, job_id: str) -> Dict[str, Any]:
        """Trigger the deterministic Python rendering, TTS, and composition pipeline."""
        pass

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Query current job lifecycle state, progress percentage, and stage from status.json."""
        pass

    def get_job_errors(self, job_id: str) -> Dict[str, Any]:
        """Retrieve structured error reports from errors.json to guide scene repair."""
        pass

    def retry_scene(self, job_id: str, scene_id: str) -> Dict[str, Any]:
        """Re-validate, re-render, and re-composite only a repaired scene."""
        pass
