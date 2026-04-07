from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .lspr_backend_factory import create_lspr_backend
from .lspr_backend_protocol import (
    BatchPredictRequest,
    BuildComparisonRequest,
    BuildDigitalTwinRequest,
    ComparisonResponse,
    DigitalTwinResponse,
    LSPRBackend,
    PredictSingleRequest,
    PredictionResponse,
)
from .lspr_master_bridge import LSPRMasterBridge


@dataclass
class LSPRPredictionResult:
    predicted_concentration_ng_ml: float
    report_mode: str
    reported_text: str
    uloq_ng_ml: Optional[float]
    super_quant_bin: Optional[str]
    metrics: Dict[str, Any]
    backend: str
    model_mode: str


@dataclass
class LSPRSpectrumComparisonResult:
    wavelengths: List[float]
    input_spectrum: List[float]
    generated_spectrum: List[float]
    aligned_spectrum: List[float]
    physical_spectrum: Optional[List[float]]
    metrics: Dict[str, Any]
    backend: str
    model_mode: str


@dataclass
class LSPRDigitalTwinResult:
    concentration_ng_ml: float
    wavelengths: List[float]
    baseline_spectrum: List[float]
    physical_spectrum: List[float]
    ai_spectrum: Optional[List[float]]
    metrics: Dict[str, Any]
    backend: str


class LSPRAIService:
    def __init__(self, backend: Optional[LSPRBackend] = None, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.backend = backend or create_lspr_backend(self.config)

    @staticmethod
    def _raise_if_error(response) -> None:
        if getattr(response, 'ok', False):
            return
        error = getattr(response, 'error', None)
        if error is not None:
            raise RuntimeError(error.message)
        raise RuntimeError('LSPR backend request failed')

    def discover_model_modes(self) -> List[str]:
        root = self.config.get('lspr_master_root')
        try:
            bridge = LSPRMasterBridge(Path(root) if root else None)
            return bridge.list_available_model_modes()
        except Exception:
            return ['auto']

    def predict_single_spectrum(self, wavelengths: List[float], intensities: List[float], model_mode: str = 'auto', metadata: Optional[Dict[str, Any]] = None) -> LSPRPredictionResult:
        response: PredictionResponse = self.backend.predict_single(
            PredictSingleRequest(wavelengths=list(wavelengths), intensities=list(intensities), model_mode=model_mode, metadata=metadata or {})
        )
        self._raise_if_error(response)
        return LSPRPredictionResult(
            predicted_concentration_ng_ml=float(response.predicted_concentration_ng_ml),
            report_mode=str(response.report_mode),
            reported_text=str(response.reported_text),
            uloq_ng_ml=response.uloq_ng_ml,
            super_quant_bin=response.super_quant_bin,
            metrics=dict(response.metrics),
            backend=response.backend,
            model_mode=response.model_mode,
        )

    def build_spectrum_comparison(self, wavelengths: List[float], intensities: List[float], model_mode: str = 'auto', metadata: Optional[Dict[str, Any]] = None) -> LSPRSpectrumComparisonResult:
        response: ComparisonResponse = self.backend.build_comparison(
            BuildComparisonRequest(wavelengths=list(wavelengths), intensities=list(intensities), model_mode=model_mode, metadata=metadata or {})
        )
        self._raise_if_error(response)
        return LSPRSpectrumComparisonResult(
            wavelengths=list(response.wavelengths),
            input_spectrum=list(response.input_spectrum),
            generated_spectrum=list(response.generated_spectrum),
            aligned_spectrum=list(response.aligned_spectrum),
            physical_spectrum=list(response.physical_spectrum) if response.physical_spectrum is not None else None,
            metrics=dict(response.metrics),
            backend=response.backend,
            model_mode=response.model_mode,
        )

    def build_digital_twin_context(self, concentration_ng_ml: float, experimental_wavelengths: Optional[List[float]] = None, experimental_intensities: Optional[List[float]] = None, model_mode: str = 'auto', metadata: Optional[Dict[str, Any]] = None) -> LSPRDigitalTwinResult:
        response: DigitalTwinResponse = self.backend.build_digital_twin(
            BuildDigitalTwinRequest(
                concentration_ng_ml=float(concentration_ng_ml),
                experimental_wavelengths=list(experimental_wavelengths) if experimental_wavelengths is not None else None,
                experimental_intensities=list(experimental_intensities) if experimental_intensities is not None else None,
                model_mode=model_mode,
                metadata=metadata or {},
            )
        )
        self._raise_if_error(response)
        return LSPRDigitalTwinResult(
            concentration_ng_ml=float(response.concentration_ng_ml),
            wavelengths=list(response.wavelengths),
            baseline_spectrum=list(response.baseline_spectrum),
            physical_spectrum=list(response.physical_spectrum),
            ai_spectrum=list(response.ai_spectrum) if response.ai_spectrum is not None else None,
            metrics=dict(response.metrics),
            backend=response.backend,
        )

    def compare_models(self, wavelengths: List[float], intensities: List[float], model_modes: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        modes = list(model_modes or self.discover_model_modes())
        rows = []
        comparisons = []
        for mode in modes:
            prediction = self.predict_single_spectrum(wavelengths, intensities, model_mode=mode, metadata=metadata)
            comparison = self.build_spectrum_comparison(wavelengths, intensities, model_mode=mode, metadata=metadata)
            rows.append({
                'model_mode': mode,
                'predicted_concentration_ng_ml': prediction.predicted_concentration_ng_ml,
                'report_mode': prediction.report_mode,
                'reported_text': prediction.reported_text,
                'backend': prediction.backend,
            })
            comparisons.append(comparison)
        return {'rows': rows, 'comparisons': comparisons}

    def predict_batch(self, items: List[Dict[str, Any]], model_mode: str = 'auto', metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self.backend.predict_batch(BatchPredictRequest(items=list(items), model_mode=model_mode, metadata=metadata or {}))
        self._raise_if_error(response)
        return {'rows': list(response.rows), 'backend': response.backend}
