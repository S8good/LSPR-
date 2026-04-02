from __future__ import annotations

from typing import Any, Dict, Optional

from .lspr_backend_protocol import LSPRBackend
from .lspr_inprocess_backend import InProcessLSPRBackend
from .lspr_subprocess_backend import SubprocessLSPRBackend


def create_lspr_backend(config: Optional[Dict[str, Any]] = None) -> LSPRBackend:
    config = config or {}
    backend_mode = str(config.get("backend_mode", "auto")).lower()

    if backend_mode == "inprocess":
        return InProcessLSPRBackend(config)

    if backend_mode == "subprocess":
        return SubprocessLSPRBackend(config)

    if backend_mode != "auto":
        raise ValueError(f"Unsupported backend_mode: {backend_mode}")

    inprocess_backend = InProcessLSPRBackend(config)
    inprocess_health = inprocess_backend.health_check()
    if inprocess_health.ok:
        return inprocess_backend

    subprocess_backend = SubprocessLSPRBackend(config)
    subprocess_health = subprocess_backend.health_check()
    if subprocess_health.ok:
        return subprocess_backend

    return subprocess_backend
