from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .lspr_backend_protocol import (
    BatchPredictRequest,
    BatchPredictionResponse,
    BuildComparisonRequest,
    BuildDigitalTwinRequest,
    ComparisonResponse,
    DigitalTwinResponse,
    ErrorResponse,
    HealthCheckResponse,
    LSPRBackend,
    PredictSingleRequest,
    PredictionResponse,
)
from .lspr_master_bridge import LSPRMasterBridge


class InProcessLSPRBackend(LSPRBackend):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._bridge: Optional[LSPRMasterBridge] = None
        self._bridge_error: Optional[Exception] = None

    def _get_bridge(self) -> LSPRMasterBridge:
        if self._bridge is not None:
            return self._bridge
        if self._bridge_error is not None:
            raise self._bridge_error

        try:
            root = self.config.get("lspr_master_root")
            bridge = LSPRMasterBridge(Path(root) if root else None)
            self._bridge = bridge
            return bridge
        except Exception as exc:  # pragma: no cover - exercised via public methods
            self._bridge_error = exc
            raise

    def health_check(self) -> HealthCheckResponse:
        try:
            bridge = self._get_bridge()
            diagnostics = bridge.diagnostics()
            bridge.import_module("src.core.ai_engine")
            bridge.import_module("src.core.digital_twin_service")
            return HealthCheckResponse(ok=True, backend="inprocess", details=diagnostics)
        except Exception as exc:
            return HealthCheckResponse(
                ok=False,
                backend="inprocess",
                details={"backend_mode": "inprocess"},
                error=ErrorResponse(code="inprocess_unavailable", message=str(exc)),
            )

    def predict_single(self, request: PredictSingleRequest) -> PredictionResponse:
        return PredictionResponse(
            ok=False,
            backend="inprocess",
            model_mode=request.model_mode,
            predicted_concentration_ng_ml=None,
            report_mode=None,
            reported_text=None,
            uloq_ng_ml=None,
            super_quant_bin=None,
            metrics={},
            error=ErrorResponse(code="not_implemented", message="in-process predict_single 未实现"),
        )

    def build_comparison(self, request: BuildComparisonRequest) -> ComparisonResponse:
        return ComparisonResponse(
            ok=False,
            backend="inprocess",
            model_mode=request.model_mode,
            wavelengths=[],
            input_spectrum=[],
            generated_spectrum=[],
            aligned_spectrum=[],
            physical_spectrum=None,
            metrics={},
            error=ErrorResponse(code="not_implemented", message="in-process build_comparison 未实现"),
        )

    def build_digital_twin(self, request: BuildDigitalTwinRequest) -> DigitalTwinResponse:
        return DigitalTwinResponse(
            ok=False,
            backend="inprocess",
            concentration_ng_ml=request.concentration_ng_ml,
            wavelengths=[],
            baseline_spectrum=[],
            physical_spectrum=[],
            ai_spectrum=None,
            metrics={},
            error=ErrorResponse(code="not_implemented", message="in-process build_digital_twin 未实现"),
        )

    def predict_batch(self, request: BatchPredictRequest) -> BatchPredictionResponse:
        return BatchPredictionResponse(
            ok=False,
            backend="inprocess",
            rows=[],
            error=ErrorResponse(code="not_implemented", message="in-process predict_batch 未实现"),
        )
