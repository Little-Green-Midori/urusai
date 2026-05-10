"""Static + dynamic graph layers.

靜態層 (eager)：時間軸圖 / entity occurrence / cross-modal alignment
動態層 (lazy)：對話動作關係 / 因果推論邊 / 主題

紀律：
- 節點 = 觀察、必 cite 對應筆記條目
- 觀察邊 = 直接讀
- 推論邊 = 要 explicit chain
- 任何 update 留 history (audit trail)
"""
from enum import Enum
from typing import Any

import networkx as nx

from .evidence import EvidenceClaim


class NodeType(str, Enum):
    DIALOGUE_SPAN = "dialogue_span"
    OCR_TEXT = "ocr_text"
    SCENE = "scene"
    ENTITY = "entity"
    SOUND_EVENT = "sound_event"


class ObservationEdgeType(str, Enum):
    OCCURS_IN_SCENE = "occurs_in_scene"
    CO_OCCURS_AT = "co_occurs_at"
    PRECEDES = "precedes"
    ALIGNED_WITH = "aligned_with"


class InferenceEdgeType(str, Enum):
    CAUSED_BY = "caused_by"
    RELATED_TO = "related_to"
    PART_OF_THEME = "part_of_theme"


class _AuditedGraph:
    def __init__(self) -> None:
        self.g: nx.MultiDiGraph = nx.MultiDiGraph()
        self.history: list[dict[str, Any]] = []

    def _record(self, op: str, **payload: Any) -> None:
        self.history.append({"op": op, **payload})


class StaticGraph(_AuditedGraph):
    """靜態層——eager 建（時間軸 / entity / cross-modal）。"""

    def add_evidence_node(
        self, node_id: str, node_type: NodeType, claim: EvidenceClaim
    ) -> None:
        if self.g.has_node(node_id):
            return
        self.g.add_node(
            node_id,
            type=node_type.value,
            time_start=claim.time_range.start,
            time_end=claim.time_range.end,
            channel=claim.channel,
            claim_text=claim.claim_text,
            source_tool=claim.source_tool,
        )
        self._record("add_node", node_id=node_id, type=node_type.value)

    def add_observation_edge(
        self, src: str, dst: str, edge_type: ObservationEdgeType
    ) -> None:
        self.g.add_edge(src, dst, type=edge_type.value)
        self._record(
            "add_edge", src=src, dst=dst, type=edge_type.value, kind="observation"
        )

    def nodes_by_type(self, node_type: NodeType) -> list[str]:
        return [
            n
            for n, d in self.g.nodes(data=True)
            if d.get("type") == node_type.value
        ]

    def nodes_in_time_range(self, start: float, end: float) -> list[str]:
        result = []
        for n, d in self.g.nodes(data=True):
            ns = d.get("time_start")
            ne = d.get("time_end")
            if ns is None or ne is None:
                continue
            if ne >= start and ns <= end:
                result.append(n)
        return result

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        if self.g.has_node(node_id):
            return dict(self.g.nodes[node_id])
        return None

    def neighbors_by_edge_type(
        self, node_id: str, edge_type: ObservationEdgeType
    ) -> list[str]:
        if not self.g.has_node(node_id):
            return []
        result = []
        for _, dst, edata in self.g.out_edges(node_id, data=True):
            if edata.get("type") == edge_type.value:
                result.append(dst)
        return result


class DynamicGraph(_AuditedGraph):
    """動態層——lazy 建（因果 / 關係 / 主題）。推論邊必須帶 chain。"""

    def add_inference_edge(
        self,
        src: str,
        dst: str,
        edge_type: InferenceEdgeType,
        chain: list[str],
        strength: str,
    ) -> None:
        if not chain:
            raise ValueError("inference edge must carry non-empty chain")
        self.g.add_edge(
            src, dst, type=edge_type.value, chain=chain, strength=strength
        )
        self._record(
            "add_edge",
            src=src,
            dst=dst,
            type=edge_type.value,
            kind="inference",
            strength=strength,
        )
