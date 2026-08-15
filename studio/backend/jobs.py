from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4


@dataclass
class Job:
    id: str
    kind: str
    status: str = "queued"
    progress: float = 0
    message: str = "Queued"
    logs: list[str] = field(default_factory=list)
    result: dict[str, Any] | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def log(self, message: str) -> None:
        self.logs.append(message)
        self.message = message

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "logs": self.logs[-250:],
            "result": self.result,
            "createdAt": self.created_at,
        }


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def start(self, kind: str, runner: Callable[[Job], dict[str, Any] | None]) -> Job:
        job = Job(id=uuid4().hex, kind=kind)
        with self._lock:
            self._jobs[job.id] = job

        def run() -> None:
            job.status = "running"
            try:
                job.result = runner(job) or {}
                job.progress = 100
                job.status = "completed"
            except Exception as exc:  # noqa: BLE001 - surfaced to the local UI
                job.log(str(exc))
                job.status = "failed"

        threading.Thread(target=run, daemon=True, name=f"studio-{kind}-{job.id[:8]}").start()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)
