"""IngestExecutor — wire observer output through LaneScheduler.

Ingest executor: dispatches observer output to LaneScheduler.

Flow:
1. StreamingDemuxer extracts audio.wav / video.mp4 / frames to mkdtemp
2. inventory_probe scans channels available
3. For each viable channel, resolve_provider via ProviderSelection
4. Submit LaneTask to LaneScheduler with channel-specific priority
5. Scheduler runs lanes in parallel; lane internals respect priority
6. rag.writer pipes resulting EvidenceClaim through embedder + Milvus + Postgres
"""
from __future__ import annotations

from urusai.agent.state import ChannelDispatch
from urusai.domain.inventory import InventoryReport
from urusai.ingest.scheduler import LaneScheduler


async def run_ingest(
    source: str,
    ingest_id: str,
    inventory: InventoryReport,
    dispatched_channels: list[ChannelDispatch],
) -> dict:
    """Drive a single ingest from stream demux through channel execution to RAG write."""
    # TODO: implement
    # 1) async with stream_video(source, ingest_id) as demuxer
    # 2) scheduler = LaneScheduler()
    # 3) for dispatch in dispatched_channels: build provider + LaneTask, submit
    # 4) await scheduler.run_all()
    # 5) return evidence_counts + skipped_channels
    scheduler = LaneScheduler()
    await scheduler.run_all()
    return {"evidence_counts": {}, "skipped_channels": {}}
