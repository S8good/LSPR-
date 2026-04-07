from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from nanosense.ml.lspr_ai_service import LSPRAIService
from nanosense.ml.lspr_backend_protocol import (
    BatchPredictionResponse,
    ComparisonResponse,
    DigitalTwinResponse,
    ErrorResponse,
    PredictionResponse,
)


class _StubBackend:
    def health_check(self):
        return None

    def predict_single(self, request):
        return PredictionResponse(
            ok=True,
            backend="stub",
            model_mode="auto",
            predicted_concentration_ng_ml=12.34,
            report_mode="quantitative",
            reported_text="12.3400 ng/ml",
            uloq_ng_ml=18.0,
            super_quant_bin=None,
            metrics={"peak_wavelength_nm": 612.5},
        )

    def build_comparison(self, request):
        return ComparisonResponse(
            ok=True,
            backend="stub",
            model_mode="auto",
            wavelengths=[500.0, 501.0, 502.0],
            input_spectrum=[0.1, 0.2, 0.3],
            generated_spectrum=[0.11, 0.21, 0.31],
            aligned_spectrum=[0.12, 0.22, 0.32],
            physical_spectrum=[0.09, 0.19, 0.29],
            metrics={"delta_lambda_nm": 2.5},
        )

    def build_digital_twin(self, request):
        return DigitalTwinResponse(
            ok=True,
            backend="stub",
            concentration_ng_ml=5.0,
            wavelengths=[500.0, 501.0, 502.0],
            baseline_spectrum=[0.05, 0.06, 0.07],
            physical_spectrum=[0.15, 0.16, 0.17],
            ai_spectrum=[0.14, 0.15, 0.16],
            metrics={
                "peak_wavelength_nm": 610.0,
                "delta_lambda_nm": 1.5,
                "peak_intensity": 0.88,
            },
        )

    def predict_batch(self, request):
        return BatchPredictionResponse(
            ok=True,
            backend="stub",
            rows=[
                {
                    "label": "sample_1",
                    "predicted_concentration_ng_ml": 2.5,
                    "report_mode": "quantitative",
                    "reported_text": "2.5000 ng/ml",
                }
            ],
        )


class _ErrorBackend(_StubBackend):
    def predict_single(self, request):
        return PredictionResponse(
            ok=False,
            backend="stub",
            model_mode="auto",
            predicted_concentration_ng_ml=None,
            report_mode=None,
            reported_text=None,
            uloq_ng_ml=None,
            super_quant_bin=None,
            metrics={},
            error=ErrorResponse(code="prediction_failed", message="model missing"),
        )


def test_service_predict_single_returns_expected_summary_fields():
    service = LSPRAIService(backend=_StubBackend())

    result = service.predict_single_spectrum(
        wavelengths=[500.0, 501.0, 502.0],
        intensities=[0.1, 0.2, 0.3],
    )

    assert result.predicted_concentration_ng_ml == 12.34
    assert result.reported_text == "12.3400 ng/ml"
    assert result.metrics["peak_wavelength_nm"] == 612.5


def test_service_build_comparison_returns_visual_arrays():
    service = LSPRAIService(backend=_StubBackend())

    result = service.build_spectrum_comparison(
        wavelengths=[500.0, 501.0, 502.0],
        intensities=[0.1, 0.2, 0.3],
    )

    assert result.wavelengths == [500.0, 501.0, 502.0]
    assert result.input_spectrum == [0.1, 0.2, 0.3]
    assert result.generated_spectrum == [0.11, 0.21, 0.31]
    assert result.aligned_spectrum == [0.12, 0.22, 0.32]


def test_service_build_digital_twin_returns_expected_metrics():
    service = LSPRAIService(backend=_StubBackend())

    result = service.build_digital_twin_context(concentration_ng_ml=5.0)

    assert result.metrics["peak_wavelength_nm"] == 610.0
    assert result.metrics["delta_lambda_nm"] == 1.5
    assert result.ai_spectrum == [0.14, 0.15, 0.16]


def test_service_raises_runtime_error_when_backend_returns_error_response():
    service = LSPRAIService(backend=_ErrorBackend())

    try:
        service.predict_single_spectrum(
            wavelengths=[500.0, 501.0, 502.0],
            intensities=[0.1, 0.2, 0.3],
        )
    except RuntimeError as exc:
        assert "model missing" in str(exc)
    else:
        raise AssertionError("expected RuntimeError when backend returns error response")


def test_service_compare_models_returns_one_row_per_model_mode():
    service = LSPRAIService(backend=_StubBackend(), config={"lspr_master_root": "C:/stub"})

    result = service.compare_models(
        wavelengths=[500.0, 501.0, 502.0],
        intensities=[0.1, 0.2, 0.3],
        model_modes=["v1", "v2"],
    )

    assert len(result["rows"]) == 2
    assert result["rows"][0]["model_mode"] == "v1"
    assert result["rows"][1]["model_mode"] == "v2"


def test_service_predict_batch_returns_structured_rows():
    service = LSPRAIService(backend=_StubBackend())

    result = service.predict_batch(
        items=[
            {
                "label": "sample_1",
                "wavelengths": [500.0, 501.0, 502.0],
                "intensities": [0.1, 0.2, 0.3],
            }
        ],
        model_mode="auto",
    )

    assert result["backend"] == "stub"
    assert result["rows"][0]["label"] == "sample_1"
    assert result["rows"][0]["predicted_concentration_ng_ml"] == 2.5
