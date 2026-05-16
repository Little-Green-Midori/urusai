"""Evidence claim writer — synchronise Postgres + Milvus.

Writes embedded claims into Postgres and Milvus.

For each EvidenceClaim insert:
1. INSERT into evidence_claims (Postgres, source-of-truth for structured fields)
2. Embed claim_text via GeminiEmbedder -> text_dense
3. claim_text auto-generates text_sparse via Milvus BM25 function
4. If channel has visual association: embed keyframe/clip -> visual_dense
5. Insert vector row into urusai_v_<ingest_id> Milvus collection
"""
from __future__ import annotations

from urusai.domain.evidence import EvidenceClaim


async def write_claim(claim: EvidenceClaim, ingest_id: str) -> None:
    """Insert single evidence claim into Postgres + Milvus collection."""
    # TODO: implement
    # 1) pg session: INSERT evidence_claims (idempotent by claim id)
    # 2) embedder.embed(claim.claim_text, "text") -> text_dense
    # 3) if claim.channel in {"ocr", "vlm", "scene"}: embedder.embed(keyframe, "image") -> visual_dense
    # 4) milvus_client.insert(collection=f"urusai_v_{ingest_id}", data=[{...}])
    pass
