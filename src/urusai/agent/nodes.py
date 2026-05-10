"""Agent nodes —— Phase 1 simple two-step。

orchestrator：rule-based dispatch（inventory check + retrieve evidence）
integrator：single LLM call、structured JSON 回答 / abstain
LLM provider：Gemma 4 31B IT via Google AI Studio (Gemini API)
"""
from __future__ import annotations

import json

from google.genai import types

from urusai.agent.llm_client import DEFAULT_MODEL, make_gemini_client
from urusai.agent.prompts import INTEGRATOR_SYSTEM, integrator_user_prompt
from urusai.agent.state import AgentState
from urusai.domain.evidence import EvidenceClaim
from urusai.store.ingest_store import IngestState


def retrieve_dialogue_evidence(
    ingest: IngestState, query: str
) -> list[EvidenceClaim]:
    """Phase 1 retrieval：先 substring match、無命中就回傳全部 dialogue claims。

    Phase 2+ 可換 embedding similarity。
    """
    claims = ingest.dialogue.all_claims()
    if not claims:
        return []
    q_lower = query.lower()
    matches = [c for c in claims if q_lower in c.claim_text.lower()]
    return matches if matches else claims


def orchestrator_node(state: AgentState, ingest: IngestState) -> AgentState:
    """Rule-based：inventory check → 結構性 abstain or 取 evidence。"""
    inv_avail = ingest.inventory.inventory

    if not inv_avail.has_speech and not inv_avail.has_manual_subs:
        state.abstain_kind = "structural"
        state.abstain_reason = (
            "影片無語音也無人工字幕、對白本為空、無法回答對白相關 query。"
        )
        state.history.append(
            {"node": "orchestrator", "decision": "structural_abstain"}
        )
        return state

    state.retrieved_evidence = retrieve_dialogue_evidence(ingest, state.query)
    state.history.append(
        {
            "node": "orchestrator",
            "decision": "retrieve_then_integrate",
            "n_evidence": len(state.retrieved_evidence),
        }
    )
    return state


def integrator_node(state: AgentState, ingest: IngestState) -> AgentState:
    """單次 LLM call、parse JSON。"""
    if state.abstain_kind == "structural":
        return state

    client = make_gemini_client()
    user_msg = integrator_user_prompt(
        state.query, ingest.inventory, state.retrieved_evidence
    )

    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=INTEGRATOR_SYSTEM,
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        raw = response.text or ""
    except Exception as exc:
        state.abstain_kind = "evidence_insufficient"
        state.abstain_reason = f"LLM call failed: {exc}"
        state.history.append({"node": "integrator", "error": str(exc)})
        return state

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        state.abstain_kind = "evidence_insufficient"
        state.abstain_reason = f"LLM returned invalid JSON: {raw[:200]}"
        state.history.append({"node": "integrator", "raw": raw[:500]})
        return state

    status = parsed.get("status")
    if status == "answered":
        state.final_answer = parsed.get("answer")
        cited = parsed.get("cited_evidence_indices") or []
        state.cited_indices = [int(i) for i in cited if isinstance(i, (int, str))]
        if not state.final_answer or not state.cited_indices:
            state.final_answer = None
            state.cited_indices = []
            state.abstain_kind = "evidence_insufficient"
            state.abstain_reason = "LLM 回 answered 但缺 answer 或 cited_evidence_indices"
    elif status == "abstain":
        state.abstain_kind = parsed.get("abstain_kind") or "evidence_insufficient"
        state.abstain_reason = parsed.get("abstain_reason") or "(LLM 未說明)"
    else:
        state.abstain_kind = "evidence_insufficient"
        state.abstain_reason = f"LLM 回了未知 status: {status}"

    state.history.append({"node": "integrator", "status": status})
    return state
