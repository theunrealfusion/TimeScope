"""Lightweight job manager using SQLite-backed state.

No Redis required. Uses in-process workers with asyncio.
Can be replaced with Celery/Redis later if needed.
"""
import asyncio
import uuid
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    completed_steps: int = 0
    total_steps: int = 0
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobManager:
    """In-process async job manager."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    async def submit(
        self, name: str, func: Callable, *args, **kwargs
    ) -> str:
        """Submit a job for async execution."""
        job = Job(name=name)
        self._jobs[job.id] = job

        task = asyncio.create_task(
            self._run_job(job.id, func, *args, **kwargs)
        )
        self._tasks[job.id] = task

        logger.info(f"Job {job.id} ({name}) submitted.")
        return job.id

    async def _run_job(self, job_id: str, func, *args, **kwargs):
        job = self._jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()

        try:
            result = await func(*args, job=job, **kwargs)
            job.result = result
            job.status = JobStatus.COMPLETED
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED
            logger.error(f"Job {job_id} failed: {e}")
        finally:
            job.completed_at = datetime.utcnow()

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    async def cancel(self, job_id: str) -> bool:
        if job_id in self._tasks:
            self._tasks[job_id].cancel()
            return True
        return False
