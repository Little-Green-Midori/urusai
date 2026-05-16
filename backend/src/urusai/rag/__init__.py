"""URUSAI RAG layer — embed + index + retrieve + (optional) rerank.

RAG layer: embedding, Milvus index, hybrid retrieval, reranker.

Module surface:
- urusai.rag.embedder    — gemini-embedding-2 wrapper (multimodal)
- urusai.rag.index       — Milvus client + collection schema
- urusai.rag.writer      — claim to embed to Postgres + Milvus insert pipeline
- urusai.rag.retriever   — hybrid_search + SQL tiebreaker
- urusai.rag.reranker    — optional reranker provider
"""
from urusai.rag.embedder import GeminiEmbedder
from urusai.rag.retriever import hybrid_search
from urusai.rag.writer import write_claims

__all__ = ["GeminiEmbedder", "hybrid_search", "write_claims"]
