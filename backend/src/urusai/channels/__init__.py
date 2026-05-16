"""urusai.channels — perception modules producing EvidenceClaim lists.

Importing this package eagerly loads every channel sub-package, which triggers
provider registration via `@ChannelRegistry.register` decorators.
"""
from urusai.channels import asr, audio_event, mss, ocr, scene, vlm  # noqa: F401

__all__ = ["asr", "scene", "ocr", "vlm", "audio_event", "mss"]
