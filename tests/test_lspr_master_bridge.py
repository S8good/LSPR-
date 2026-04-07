from pathlib import Path

import pytest

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from nanosense.ml.lspr_backend_factory import create_lspr_backend
from nanosense.ml.lspr_backend_protocol import (
    BuildComparisonRequest,
    BuildDigitalTwinRequest,
    BatchPredictRequest,
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


def test_inprocess_backend_build_comparison_returns_visual_arrays_and_metrics(monkeypatch):
    backend = InProcessLSPRBackend(config={})

    class StubEngine:
        def predict_spectrum_from_spectrum(self, intensities):
            assert intensities == [0.1, 0.2, 0.3]
            return {
                "wavelengths": [500.0, 501.0, 502.0],
                "input_resampled": [0.1, 0.2, 0.3],
                "pred_spectrum_raw": [0.15, 0.25, 0.35],
                "pred_spectrum": [0.12, 0.22, 0.32],
                "intensity_scale": 1.2,
                "intensity_offset": -0.03,
                "pred_concentration": 12.34,
                "report_mode": "quantitative",
                "reported_text": "12.3400 ng/ml",
                "uloq_ng_ml": 18.0,
                "super_quant_bin": None,
            }

    class StubBridge:
        def create_ai_engine(self):
            return StubEngine()

    monkeypatch.setattr(backend, "_get_bridge", lambda: StubBridge())

    result = backend.build_comparison(
        BuildComparisonRequest(
            wavelengths=[500.0, 501.0, 502.0],
            intensities=[0.1, 0.2, 0.3],
            model_mode="auto",
            metadata={"source": "unit-test"},
        )
    )

    assert result.ok is True
    assert result.wavelengths == [500.0, 501.0, 502.0]
    assert result.input_spectrum == [0.1, 0.2, 0.3]
    assert result.generated_spectrum == [0.15, 0.25, 0.35]
    assert result.aligned_spectrum == [0.12, 0.22, 0.32]
    assert result.metrics["predicted_concentration_ng_ml"] == 12.34
    assert result.metrics["intensity_scale"] == 1.2
    assert result.metrics["intensity_offset"] == -0.03


def test_subprocess_backend_build_comparison_maps_runner_response(monkeypatch):
    backend = SubprocessLSPRBackend(config={"lspr_master_root": "C:/stub"})

    monkeypatch.setattr(
        backend,
        "_invoke_runner",
        lambda command, payload: {
            "ok": True,
            "backend": "subprocess",
            "wavelengths": [500.0, 501.0, 502.0],
            "input_spectrum": [0.1, 0.2, 0.3],
            "generated_spectrum": [0.15, 0.25, 0.35],
            "aligned_spectrum": [0.12, 0.22, 0.32],
            "physical_spectrum": None,
            "metrics": {
                "predicted_concentration_ng_ml": 12.34,
                "intensity_scale": 1.2,
                "intensity_offset": -0.03,
            },
            "error": None,
        },
    )

    result = backend.build_comparison(
        BuildComparisonRequest(
            wavelengths=[500.0, 501.0, 502.0],
            intensities=[0.1, 0.2, 0.3],
            model_mode="auto",
            metadata={"source": "unit-test"},
        )
    )

    assert result.ok is True
    assert result.generated_spectrum == [0.15, 0.25, 0.35]
    assert result.aligned_spectrum == [0.12, 0.22, 0.32]
    assert result.metrics["predicted_concentration_ng_ml"] == 12.34


def test_inprocess_backend_build_digital_twin_returns_plot_context(monkeypatch):
    backend = InProcessLSPRBackend(config={})

    class StubPrediction:
        peak_wavelength = 612.5
        delta_lambda = 2.5
        peak_intensity = 0.88

    class StubContext:
        wavelengths = [500.0, 501.0, 502.0]
        bsa_spectrum = [0.05, 0.06, 0.07]
        physical_spectrum = [0.15, 0.16, 0.17]
        ai_spectrum_raw = [0.14, 0.15, 0.16]
        ai_spectrum_aligned = [0.145, 0.155, 0.165]
        prediction = StubPrediction()

    class StubDigitalTwinService:
        def build_plot_context(self, concentration):
            assert concentration == 5.0
            return StubContext()

    class StubBridge:
        def create_digital_twin_service(self):
            return StubDigitalTwinService()

    monkeypatch.setattr(backend, "_get_bridge", lambda: StubBridge())

    result = backend.build_digital_twin(
        BuildDigitalTwinRequest(concentration_ng_ml=5.0, model_mode="auto", metadata={"source": "unit-test"})
    )

    assert result.ok is True
    assert result.wavelengths == [500.0, 501.0, 502.0]
    assert result.baseline_spectrum == [0.05, 0.06, 0.07]
    assert result.physical_spectrum == [0.15, 0.16, 0.17]
    assert result.ai_spectrum == [0.145, 0.155, 0.165]
    assert result.metrics["peak_wavelength_nm"] == 612.5
    assert result.metrics["delta_lambda_nm"] == 2.5


def test_subprocess_backend_build_digital_twin_maps_runner_response(monkeypatch):
    backend = SubprocessLSPRBackend(config={"lspr_master_root": "C:/stub"})

    monkeypatch.setattr(
        backend,
        "_invoke_runner",
        lambda command, payload: {
            "ok": True,
            "backend": "subprocess",
            "concentration_ng_ml": 5.0,
            "wavelengths": [500.0, 501.0, 502.0],
            "baseline_spectrum": [0.05, 0.06, 0.07],
            "physical_spectrum": [0.15, 0.16, 0.17],
            "ai_spectrum": [0.145, 0.155, 0.165],
            "metrics": {
                "peak_wavelength_nm": 612.5,
                "delta_lambda_nm": 2.5,
                "peak_intensity": 0.88,
            },
            "error": None,
        },
    )

    result = backend.build_digital_twin(
        BuildDigitalTwinRequest(concentration_ng_ml=5.0, model_mode="auto", metadata={"source": "unit-test"})
    )

    assert result.ok is True
    assert result.ai_spectrum == [0.145, 0.155, 0.165]
    assert result.metrics["peak_intensity"] == 0.88


def test_subprocess_backend_predict_batch_maps_runner_response(monkeypatch):
    backend = SubprocessLSPRBackend(config={"lspr_master_root": "C:/stub"})

    monkeypatch.setattr(
        backend,
        "_invoke_runner",
        lambda command, payload: {
            "ok": True,
            "backend": "subprocess",
            "rows": [
                {
                    "label": "sample_1",
                    "predicted_concentration_ng_ml": 2.5,
                    "report_mode": "quantitative",
                    "reported_text": "2.5000 ng/ml",
                }
            ],
            "error": None,
        },
    )

    result = backend.predict_batch(
        BatchPredictRequest(items=[{"label": "sample_1", "intensities": [0.1, 0.2]}], model_mode="auto")
    )

    assert result.ok is True
    assert result.rows[0]["label"] == "sample_1"
    assert result.rows[0]["predicted_concentration_ng_ml"] == 2.5
