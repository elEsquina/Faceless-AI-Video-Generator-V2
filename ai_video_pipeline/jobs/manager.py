"""
ai_video_pipeline/jobs/manager.py

Job state management and workspace utilities.
No external dependencies beyond stdlib + pathlib.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Optional
from uuid import uuid4

_JOB_ID_RE = re.compile(r"^[a-f0-9]{8}$")


def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON atomically: write to .tmp then os.replace()."""
    tmp_path = path.with_suffix(".tmp")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


def _read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class JobManager:
    """Manages job workspace creation, state transitions, and error tracking."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        if workspace_root is None:
            default_ws = (
                Path(__file__).resolve().parent.parent.parent
                / "video_docker_sandbox"
                / "workspace"
            )
            self.JOBS_ROOT = default_ws / "jobs"
        else:
            p = Path(workspace_root)
            self.JOBS_ROOT = p if p.name == "jobs" else p / "jobs"

        self.LOCK_FILE: Path = self.JOBS_ROOT / ".active_job"
        self.JOBS_ROOT.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Job creation
    # ------------------------------------------------------------------

    def create_job(self, request_data: dict) -> str:
        """
        Create a new job workspace.

        - Validates no active job (LOCK_FILE exists → raise RuntimeError).
        - Generates job_id = str(uuid4())[:8] (8-char hex slug).
        - Creates directory structure under jobs/<job_id>/.
        - Writes request.json and status.json atomically.
        - Writes LOCK_FILE containing job_id.
        - Returns job_id.
        """
        if self.LOCK_FILE.exists():
            active = self.LOCK_FILE.read_text(encoding="utf-8").strip()
            raise RuntimeError(
                f"Cannot create job: active job '{active}' is still running. "
                "Release the lock first."
            )

        job_id = str(uuid4()).replace("-", "")[:8]

        job_dir = self.JOBS_ROOT / job_id
        for sub in ("scenes", "renders", "logs", "output"):
            p = job_dir / sub
            p.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(p, 0o777)
            except OSError:
                pass

        _atomic_write(job_dir / "request.json", request_data)
        _atomic_write(
            job_dir / "status.json",
            {
                "job_id": job_id,
                "state": "created",
                "progress_pct": 0,
                "current_stage": None,
                "output_path": None,
                "errors": [],
            },
        )

        self.LOCK_FILE.write_text(job_id, encoding="utf-8")

        return job_id

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def get_job_dir(self, job_id: str) -> Path:
        """
        Return validated job directory path.

        Raises ValueError if job_id does not match ^[a-f0-9]{8}$ (path traversal guard).
        """
        if not _JOB_ID_RE.match(job_id):
            raise ValueError(
                f"Invalid job_id '{job_id}': must match ^[a-f0-9]{{8}}$."
            )
        return self.JOBS_ROOT / job_id

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def transition_state(self, job_id: str, new_state: str, **kwargs) -> None:
        """
        Atomically update status.json fields.

        kwargs can include: progress_pct, current_stage, output_path, errors.
        """
        job_dir = self.get_job_dir(job_id)
        status_path = job_dir / "status.json"

        if status_path.exists():
            status = _read_json(status_path)
        else:
            status = {
                "job_id": job_id,
                "state": new_state,
                "progress_pct": 0,
                "current_stage": None,
                "output_path": None,
                "errors": [],
            }

        status["state"] = new_state
        for key in ("progress_pct", "current_stage", "output_path", "errors"):
            if key in kwargs:
                status[key] = kwargs[key]

        _atomic_write(status_path, status)

    def append_error(
        self,
        job_id: str,
        scene_id: Optional[str],
        engine: str,
        stage: str,
        msg: str,
        log_file: Optional[str] = None,
    ) -> None:
        """Append a SceneErrorModel entry to errors.json atomically."""
        job_dir = self.get_job_dir(job_id)
        errors_path = job_dir / "errors.json"

        if errors_path.exists():
            report = _read_json(errors_path)
        else:
            report = {"job_id": job_id, "scene_errors": [], "global_errors": []}

        entry = {
            "scene_id": scene_id,
            "engine": engine,
            "stage": stage,
            "message": msg,
            "log_file": log_file,
        }

        if scene_id is not None:
            report.setdefault("scene_errors", []).append(entry)
        else:
            report.setdefault("global_errors", []).append(entry)

        _atomic_write(errors_path, report)

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def read_status(self, job_id: str) -> dict:
        """Read and return status.json as dict."""
        return _read_json(self.get_job_dir(job_id) / "status.json")

    def read_errors(self, job_id: str) -> dict:
        """Read and return errors.json as dict (or empty report if no file)."""
        errors_path = self.get_job_dir(job_id) / "errors.json"
        if not errors_path.exists():
            return {"job_id": job_id, "scene_errors": [], "global_errors": []}
        return _read_json(errors_path)

    # ------------------------------------------------------------------
    # Lock management
    # ------------------------------------------------------------------

    def release_lock(self, job_id: str) -> None:
        """Remove LOCK_FILE if it contains this job_id."""
        if self.LOCK_FILE.exists():
            active = self.LOCK_FILE.read_text(encoding="utf-8").strip()
            if active == job_id:
                self.LOCK_FILE.unlink()

    def get_active_job(self) -> Optional[str]:
        """Return job_id from LOCK_FILE or None."""
        if self.LOCK_FILE.exists():
            return self.LOCK_FILE.read_text(encoding="utf-8").strip() or None
        return None


class JobLock:
    """Context manager that holds the job lock for the duration of a block."""

    def __init__(self, manager: JobManager, job_id: str) -> None:
        self._manager = manager
        self._job_id = job_id

    def __enter__(self) -> "JobLock":
        # Write lock (create_job already writes it; this supports external callers)
        self._manager.LOCK_FILE.write_text(self._job_id, encoding="utf-8")
        return self

    def __exit__(self, *args) -> None:
        self._manager.release_lock(self._job_id)
