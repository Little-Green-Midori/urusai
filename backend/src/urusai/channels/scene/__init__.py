"""Scene channel — providers register at import time."""
from urusai.channels.scene.pyscenedetect import (
    PySceneDetectConfig,
    PySceneDetectScene,
)

# Backward-compat alias for callers that still import the legacy name.
SceneChannel = PySceneDetectScene

__all__ = ["PySceneDetectScene", "PySceneDetectConfig", "SceneChannel"]
