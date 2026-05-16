"""LaneScheduler — lane-based concurrent channel dispatch.

Each provider declares a lane:
- gpu_heavy: 1 at a time (asyncio.Semaphore(1))
- gpu_medium: budget-aware
- cpu: about cpu_count - 1
- external: 1 per service
- api: per-provider rate limit (TokenRotator)
- io: unlimited
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Awaitable, Callable

from urusai.providers.base import Lane


_DEFAULT_LANE_BUDGETS: dict[Lane, int] = {
    "gpu_heavy": 1,
    "gpu_medium": 1,
    "cpu": max(1, (os.cpu_count() or 4) - 1),
    "external": 1,
    "api": 8,
    "io": 16,
}


@dataclass
class LaneTask:
    """Single channel job submitted to the scheduler."""

    channel: str
    provider_id: str
    lane: Lane
    priority: int
    fn: Callable[[], Awaitable[None]]
    reason: str = ""


class LaneScheduler:
    """Per-lane bounded concurrency with priority queue."""

    def __init__(self, lane_budgets: dict[Lane, int] | None = None):
        budgets = lane_budgets or _DEFAULT_LANE_BUDGETS
        self._budgets = budgets
        self._semaphores: dict[Lane, asyncio.Semaphore] = {
            lane: asyncio.Semaphore(budget) for lane, budget in budgets.items()
        }
        self._queues: dict[Lane, asyncio.PriorityQueue] = {
            lane: asyncio.PriorityQueue() for lane in budgets
        }
        self._worker_tasks: list[asyncio.Task] = []
        self._stopped = False

    async def submit(self, task: LaneTask) -> None:
        """Enqueue task; higher priority runs first within lane."""
        await self._queues[task.lane].put((-task.priority, task))

    async def run_all(self) -> None:
        """Start workers; wait for queues to drain."""
        for lane, budget in self._budgets.items():
            for _ in range(budget):
                self._worker_tasks.append(asyncio.create_task(self._worker(lane)))
        await asyncio.gather(*(q.join() for q in self._queues.values()))
        self._stopped = True
        for t in self._worker_tasks:
            t.cancel()

    async def _worker(self, lane: Lane) -> None:
        queue = self._queues[lane]
        sem = self._semaphores[lane]
        while not self._stopped:
            _prio, task = await queue.get()
            try:
                async with sem:
                    await task.fn()
            finally:
                queue.task_done()
