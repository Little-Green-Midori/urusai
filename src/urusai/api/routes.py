"""API routes —— Phase 1 ingest / query endpoints。

POST /ingest: file_path 或 url → inventory probe → channel dispatch → IngestState
POST /query : ingest_id + query → agent loop → final answer + evidence trace
"""
from __future__ import annotations

import subprocess
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from urusai.agent.graph import run_query
from urusai.agent.trace import serialize_trace
from urusai.api.schemas import (
    EvidenceItem,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from urusai.channels.asr import ASRChannel
from urusai.channels.inventory_probe import run_inventory_probe
from urusai.channels.scene import SceneChannel
from urusai.channels.subtitle import SubtitleChannel
from urusai.store.ingest_store import IngestState, get_default_store


router = APIRouter()

VIDEO_EXTS = (".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v")


def _download_video(url: str) -> str:
    out_dir = tempfile.mkdtemp(prefix="urusai_video_")
    out_template = str(Path(out_dir) / "%(id)s.%(ext)s")
    cmd = [
        "yt-dlp", "-f", "best[ext=mp4]/best",
        "--no-warnings", "-o", out_template, url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=400, detail=f"yt-dlp invocation failed: {exc}"
        ) from exc
    if result.returncode != 0:
        raise HTTPException(
            status_code=400,
            detail=f"yt-dlp download failed: {result.stderr[:300]}",
        )
    for path in Path(out_dir).iterdir():
        if path.suffix.lower() in VIDEO_EXTS:
            return str(path)
    raise HTTPException(status_code=400, detail="yt-dlp produced no video file")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(req: IngestRequest) -> IngestResponse:
    if not req.file_path and not req.url:
        raise HTTPException(status_code=400, detail="file_path or url required")

    source_path = req.file_path or _download_video(req.url or "")
    if not Path(source_path).exists():
        raise HTTPException(status_code=400, detail=f"file not found: {source_path}")

    ingest_id = uuid.uuid4().hex[:12]
    video_id = req.video_id or ingest_id
    inv_report = run_inventory_probe(source_path, video_id, url=req.url)

    state = IngestState(ingest_id=ingest_id, inventory=inv_report)
    inv = inv_report.inventory
    dispatched = inv_report.dispatched_channels

    if "SubtitleChannel" in dispatched and req.url and inv.has_manual_subs:
        sub = SubtitleChannel()
        claims = await sub.extract_from_url(req.url, inv.subs_lang or "und")
        state.absorb(claims)
    elif "ASRChannel" in dispatched:
        asr = ASRChannel()
        try:
            claims = await asr.extract(source_path)
            state.absorb(claims)
        finally:
            asr.unload()

    if "SceneChannel" in dispatched:
        scene = SceneChannel()
        claims = await scene.extract(source_path)
        state.absorb(claims)

    get_default_store().put(state)

    return IngestResponse(
        ingest_id=ingest_id,
        inventory=inv_report,
        notebooks=state.notebook_summary(),
    )


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(req: QueryRequest) -> QueryResponse:
    state = get_default_store().get(req.ingest_id)
    if state is None:
        raise HTTPException(
            status_code=404, detail=f"ingest_id not found: {req.ingest_id}"
        )

    agent_state = run_query(req.query, state)

    cited: list[EvidenceItem] = []
    for i in agent_state.cited_indices:
        if not (0 <= i < len(agent_state.retrieved_evidence)):
            continue
        c = agent_state.retrieved_evidence[i]
        cited.append(
            EvidenceItem(
                index=i,
                channel=c.channel,
                start_sec=c.time_range.start,
                end_sec=c.time_range.end,
                text=c.claim_text,
                source_tool=c.source_tool,
            )
        )

    trace = serialize_trace(
        agent_state.retrieved_evidence,
        agent_state.cited_indices or None,
    )
    status = "answered" if agent_state.final_answer else "abstain"

    return QueryResponse(
        status=status,
        answer=agent_state.final_answer,
        cited_evidence=cited,
        abstain_kind=agent_state.abstain_kind,
        abstain_reason=agent_state.abstain_reason,
        trace=trace,
    )
