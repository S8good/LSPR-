from pathlib import Path

import pytest

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from nanosense.ml.lspr_backend_factory import create_lspr_backend
from nanosense.ml.lspr_backend_protocol import (
    ErrorResponse,
    HealthCheckResponse,
    PredictSingleRequest,
)
from nanosense.ml.lspr_inprocess_backend import InProcessLSPRBackend
from nanosense.ml.lspr_master_bridge import LSPRMasterBridge
from nanosense.ml.lspr_subprocess_backend import SubprocessLSPRBackend


def test_bridge_rejects_missing_master_root():
    with pytest.raises(FileNotFoundError):
        LSPRMasterBridge(master_root=PROJECT_ROOT / "DeepLearning" / "missing_repo")


def test_bridge_rejects_missing_pretrained_artifacts(tmp_path: Path):
    master_root = tmp_path / "LSPR_Spectra_Master"
    (master_root / "src" / "core").mkdir(parents=True)
    (master_root / "models").mkdir(parents=True)

    with pytest.raises(FileNotFoundError):
        LSPRMasterBridge(master_root=master_root)


def test_auto_backend_prefers_inprocess_when_health_check_passes(monkeypatch):
    class HealthyInProcess(InProcessLSPRBackend):
        def health_check(self):
            return HealthCheckResponse(ok=True, backend="inprocess", details={"mode": "healthy"})

    class FailingSubprocess(SubprocessLSPRBackend):
        def health_check(self):
            return HealthCheckResponse(ok=False, backend="subprocess", details={"mode": "unused"})

    monkeypatch.setattr("nanosense.ml.lspr_backend_factory.InProcessLSPRBackend", HealthyInProcess)
    monkeypatch.setattr("nanosense.ml.lspr_backend_factory.SubprocessLSPRBackend", FailingSubprocess)

    backend = create_lspr_backend({"backend_mode": "auto"})
    assert isinstance(backend, HealthyInProcess)


def test_auto_backend_falls_back_to_subprocess_when_inprocess_fails(monkeypatch):
    class FailingInProcess(InProcessLSPRBackend):
        def health_check(self):
            return HealthCheckResponse(
                ok=False,
                backend="inprocess",
                details={"reason": "import_failed"},
                error=ErrorResponse(code="import_failed", message="failed"),
            )

    class HealthySubprocess(SubprocessLSPRBackend):
        def health_check(self):
            return HealthCheckResponse(ok=True, backend="subprocess", details={"mode": "healthy"})

    monkeypatch.setattr("nanosense.ml.lspr_backend_factory.InProcessLSPRBackend", FailingInProcess)
    monkeypatch.setattr("nanosense.ml.lspr_backend_factory.SubprocessLSPRBackend", HealthySubprocess)

    backend = create_lspr_backend({"backend_mode": "auto"})
    assert isinstance(backend, HealthySubprocess)


def test_subprocess_backend_health_check_returns_structured_response():
    backend = SubprocessLSPRBackend()
    result = backend.health_check()

    assert isinstance(result, HealthCheckResponse)
    assert result.backend == "subprocess"


def test_subprocess_backend_prepends_conda_dll_paths():
    backend = SubprocessLSPRBackend(
        config={"lspr_subprocess_python": r"C:/ProgramData/anaconda3/envs/py39/python.exe"}
    )

    env = backend._build_subprocess_env()
    path_value = env["PATH"]

    assert path_value.startswith("C:/ProgramData/anaconda3/envs/py39/bin;")
    assert "C:/ProgramData/anaconda3/envs/py39/Library/bin;" in path_value


def test_inprocess_backend_health_check_reports_import_failure(monkeypatch):
    backend = InProcessLSPRBackend(config={})

    class StubBridge:
        def diagnostics(self):
            return {"master_root": "stub"}

        def import_module(self, module_name: str):
            raise ImportError(f"cannot import {module_name}")

    monkeypatch.setattr(backend, "_get_bridge", lambda: StubBridge())

    result = backend.health_check()

    assert result.ok is False
    assert result.backend == "inprocess"
    assert result.error is not None
    assert result.error.code == "inprocess_unavailable"


def test_predict_single_request_can_be_serialized_to_json_compatible_payload():
    request = PredictSingleRequest(
        wavelengths=[500.0, 501.0, 502.0],
        intensities=[0.1, 0.2, 0.3],
        model_mode="auto",
        metadata={"source": "unit-test"},
    )

    payload = request.to_payload()

    assert payload["wavelengths"] == [500.0, 501.0, 502.0]
    assert payload["intensities"] == [0.1, 0.2, 0.3]
    assert payload["model_mode"] == "auto"
    assert payload["metadata"]["source"] == "unit-test"
