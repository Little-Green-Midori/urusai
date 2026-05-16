"""SQLAlchemy 2.x async ORM + session factory for urusai persistence."""
from urusai.db.models import Base, EvidenceClaim, Ingest, QueryEvidenceLog, QueryLog
from urusai.db.session import (
    dispose_engine,
    get_db,
    get_engine,
    get_session_factory,
    session_scope,
)

__all__ = [
    "Base",
    "EvidenceClaim",
    "Ingest",
    "QueryEvidenceLog",
    "QueryLog",
    "dispose_engine",
    "get_db",
    "get_engine",
    "get_session_factory",
    "session_scope",
]
