"""Specialized generation skill references and documentation locators."""

from pathlib import Path
from typing import Dict, List, Optional

from ai_video_pipeline.schemas.models import AnimationEngine, VideoCategory


class SkillDocumentLocator:
    """Manages paths and metadata for specialized generation skill guides."""

    def __init__(self, skills_dir: Optional[Path] = None) -> None:
        pass

    def get_skill_path(self, category: VideoCategory) -> Path:
        """Return the filesystem path to the markdown skill guide for a category."""
        pass

    def read_skill_content(self, category: VideoCategory) -> str:
        """Read markdown instructions intended for the external AI director."""
        pass

    def get_recommended_engines(self, category: VideoCategory) -> List[AnimationEngine]:
        """Return default recommended animation technologies for a content category."""
        pass
