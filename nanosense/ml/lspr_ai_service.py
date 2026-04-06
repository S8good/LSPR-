from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

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
    prediction_model_mode: str
    prediction_backend: str
    fallback_applied: bool
    fallback_reason: Optional[str]
    generator_model_mode: Optional[str] = None
    generator_backend: Optional[str] = None


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
    generator_model_mode: str
    generator_backend: str
    generator_supported: bool
    prediction_model_mode: Optional[str]
    fallback_applied: bool
    fallback_reason: Optional[str]


@dataclass
class LSPRDigitalTwinResult:
    concentration_ng_ml: float
    wavelengths: List[float]
    baseline_spectrum: List[float]
    physical_spectrum: List[float]
    ai_spectrum: Optional[List[float]]
    metrics: Dict[str, Any]
    backend: str
    generator_model_mode: str


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

    def predict_single_spectrum(self, wavelengths: List[float], intensities: List[float], model_mode: str = 'auto', prediction_model_mode: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> LSPRPredictionResult:
        requested_prediction_model = str(prediction_model_mode or model_mode or 'auto')
        response: PredictionResponse = self.backend.predict_single(
            PredictSingleRequest(
                wavelengths=list(wavelengths),
                intensities=list(intensities),
                model_mode=requested_prediction_model,
                metadata=metadata or {},
            )
        )
        self._raise_if_error(response)
        metrics = dict(response.metrics)
        resolved_prediction_model = str(metrics.get('resolved_prediction_model') or response.model_mode)
        return LSPRPredictionResult(
            predicted_concentration_ng_ml=float(response.predicted_concentration_ng_ml),
            report_mode=str(response.report_mode),
            reported_text=str(response.reported_text),
            uloq_ng_ml=response.uloq_ng_ml,
            super_quant_bin=response.super_quant_bin,
            metrics=metrics,
            backend=response.backend,
            model_mode=response.model_mode,
            prediction_model_mode=resolved_prediction_model,
            prediction_backend=response.backend,
            fallback_applied=bool(metrics.get('fallback_applied', False)),
            fallback_reason=metrics.get('fallback_reason'),
        )

    def build_spectrum_comparison(self, wavelengths: List[float], intensities: List[float], model_mode: str = 'auto', prediction_model_mode: Optional[str] = None, generator_model_mode: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> LSPRSpectrumComparisonResult:
        requested_prediction_model = str(prediction_model_mode or 'auto')
        requested_generator_model = str(generator_model_mode or model_mode or 'auto')
        request_metadata = dict(metadata or {})
        request_metadata['prediction_model_mode'] = requested_prediction_model
        request_metadata['generator_model_mode'] = requested_generator_model
        response: ComparisonResponse = self.backend.build_comparison(
            BuildComparisonRequest(
                wavelengths=list(wavelengths),
                intensities=list(intensities),
                model_mode=requested_generator_model,
                metadata=request_metadata,
            )
        )
        self._raise_if_error(response)
        metrics = dict(response.metrics)
        generated_spectrum = list(response.generated_spectrum)
        generator_supported = metrics.get('generator_supported')
        if generator_supported is None:
            generated_array = np.asarray(generated_spectrum, dtype=float).reshape(-1)
            generator_supported = bool(generated_array.size > 1 and np.ptp(generated_array) > 1e-8)
        return LSPRSpectrumComparisonResult(
            wavelengths=list(response.wavelengths),
            input_spectrum=list(response.input_spectrum),
            generated_spectrum=generated_spectrum,
            aligned_spectrum=list(response.aligned_spectrum),
            physical_spectrum=list(response.physical_spectrum) if response.physical_spectrum is not None else None,
            metrics=metrics,
            backend=response.backend,
            model_mode=response.model_mode,
            generator_model_mode=str(metrics.get('resolved_generator_model') or response.model_mode),
            generator_backend=response.backend,
            generator_supported=bool(generator_supported),
            prediction_model_mode=metrics.get('resolved_prediction_model'),
            fallback_applied=bool(metrics.get('fallback_applied', False)),
            fallback_reason=metrics.get('fallback_reason'),
        )

    def build_digital_twin_context(self, concentration_ng_ml: float, experimental_wavelengths: Optional[List[float]] = None, experimental_intensities: Optional[List[float]] = None, model_mode: str = 'auto', generator_model_mode: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> LSPRDigitalTwinResult:
        requested_generator_model = str(generator_model_mode or model_mode or 'auto')
        response: DigitalTwinResponse = self.backend.build_digital_twin(
            BuildDigitalTwinRequest(
                concentration_ng_ml=float(concentration_ng_ml),
                experimental_wavelengths=list(experimental_wavelengths) if experimental_wavelengths is not None else None,
                experimental_intensities=list(experimental_intensities) if experimental_intensities is not None else None,
                model_mode=requested_generator_model,
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
            generator_model_mode=str(response.metrics.get('resolved_generator_model', requested_generator_model)),
        )

    def compare_models(self, wavelengths: List[float], intensities: List[float], model_modes: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        modes = list(model_modes or self.discover_model_modes())
        prediction_rows = []
        generator_rows = []
        comparisons = []
        for mode in modes:
            try:
                prediction = self.predict_single_spectrum(
                    wavelengths,
                    intensities,
                    prediction_model_mode=mode,
                    metadata=metadata,
                )
            except Exception as exc:
                prediction_rows.append({
                    'prediction_model_mode': mode,
                    'predicted_concentration_ng_ml': None,
                    'report_mode': 'error',
                    'reported_text': str(exc),
                    'backend': getattr(self.backend, '__class__', type(self.backend)).__name__,
                    'error': str(exc),
                })
                continue

            prediction_row = {
                'prediction_model_mode': mode,
                'predicted_concentration_ng_ml': prediction.predicted_concentration_ng_ml,
                'report_mode': prediction.report_mode,
                'reported_text': prediction.reported_text,
                'backend': prediction.prediction_backend,
                'resolved_prediction_model': prediction.prediction_model_mode,
                'fallback_applied': prediction.fallback_applied,
                'fallback_reason': prediction.fallback_reason,
            }
            try:
                comparison = self.build_spectrum_comparison(
                    wavelengths,
                    intensities,
                    prediction_model_mode=mode,
                    generator_model_mode=mode,
                    metadata=metadata,
                )
                comparisons.append(comparison)
                generator_rows.append({
                    'generator_model_mode': mode,
                    'resolved_generator_model': comparison.generator_model_mode,
                    'generator_supported': comparison.generator_supported,
                    'backend': comparison.generator_backend,
                    'fallback_applied': comparison.fallback_applied,
                    'fallback_reason': comparison.fallback_reason,
                })
            except Exception as exc:
                prediction_row['comparison_error'] = str(exc)
                generator_rows.append({
                    'generator_model_mode': mode,
                    'resolved_generator_model': None,
                    'generator_supported': False,
                    'backend': getattr(self.backend, '__class__', type(self.backend)).__name__,
                    'error': str(exc),
                })
            prediction_rows.append(prediction_row)
        return {
            'prediction_rows': prediction_rows,
            'generator_rows': generator_rows,
            'comparisons': comparisons,
            'available_prediction_model_modes': modes,
            'available_generator_model_modes': modes,
            'recommended_prediction_model_mode': 'auto',
            'recommended_generator_model_mode': 'auto',
        }

    def predict_batch(self, items: List[Dict[str, Any]], model_mode: str = 'auto', metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self.backend.predict_batch(BatchPredictRequest(items=list(items), model_mode=model_mode, metadata=metadata or {}))
        self._raise_if_error(response)
        return {'rows': list(response.rows), 'backend': response.backend}
