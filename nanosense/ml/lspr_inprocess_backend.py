from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

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
            root = self.config.get('lspr_master_root')
            bridge = LSPRMasterBridge(Path(root) if root else None)
            self._bridge = bridge
            return bridge
        except Exception as exc:
            self._bridge_error = exc
            raise

    def health_check(self) -> HealthCheckResponse:
        try:
            bridge = self._get_bridge()
            diagnostics = bridge.diagnostics()
            bridge.import_module('src.core.ai_engine')
            bridge.import_module('src.core.digital_twin_service')
            return HealthCheckResponse(ok=True, backend='inprocess', details=diagnostics)
        except Exception as exc:
            return HealthCheckResponse(
                ok=False,
                backend='inprocess',
                details={'backend_mode': 'inprocess'},
                error=ErrorResponse(code='inprocess_unavailable', message=str(exc)),
            )

    def predict_single(self, request: PredictSingleRequest) -> PredictionResponse:
        try:
            engine = self._get_bridge().create_ai_engine()
            predicted = float(engine.predict_concentration(list(request.intensities), model_mode=request.model_mode))
            report = engine.interpret_concentration(predicted)
            return PredictionResponse(
                ok=True,
                backend='inprocess',
                model_mode=request.model_mode,
                predicted_concentration_ng_ml=predicted,
                report_mode=report.get('mode'),
                reported_text=report.get('reported_text'),
                uloq_ng_ml=report.get('uloq_ng_ml'),
                super_quant_bin=report.get('super_quant_bin'),
                metrics={},
            )
        except Exception as exc:
            return PredictionResponse(
                ok=False,
                backend='inprocess',
                model_mode=request.model_mode,
                predicted_concentration_ng_ml=None,
                report_mode=None,
                reported_text=None,
                uloq_ng_ml=None,
                super_quant_bin=None,
                metrics={},
                error=ErrorResponse(code='predict_single_failed', message=str(exc)),
            )

    def build_comparison(self, request: BuildComparisonRequest) -> ComparisonResponse:
        try:
            engine = self._get_bridge().create_ai_engine()
            try:
                result = engine.predict_spectrum_from_spectrum(list(request.intensities), model_mode=request.model_mode)
            except TypeError:
                result = engine.predict_spectrum_from_spectrum(list(request.intensities))
            return ComparisonResponse(
                ok=True,
                backend='inprocess',
                model_mode=result.get('model_mode', request.model_mode),
                wavelengths=list(np.asarray(result.get('wavelengths', []), dtype=float)),
                input_spectrum=list(np.asarray(result.get('input_resampled', []), dtype=float)),
                generated_spectrum=list(np.asarray(result.get('pred_spectrum_raw', []), dtype=float)),
                aligned_spectrum=list(np.asarray(result.get('pred_spectrum', []), dtype=float)),
                physical_spectrum=None,
                metrics={
                    'predicted_concentration_ng_ml': float(result.get('pred_concentration', 0.0)),
                    'report_mode': result.get('report_mode'),
                    'reported_text': result.get('reported_text'),
                    'uloq_ng_ml': result.get('uloq_ng_ml'),
                    'super_quant_bin': result.get('super_quant_bin'),
                    'intensity_scale': float(result.get('intensity_scale', 1.0)),
                    'intensity_offset': float(result.get('intensity_offset', 0.0)),
                },
            )
        except Exception as exc:
            return ComparisonResponse(
                ok=False,
                backend='inprocess',
                model_mode=request.model_mode,
                wavelengths=[],
                input_spectrum=[],
                generated_spectrum=[],
                aligned_spectrum=[],
                physical_spectrum=None,
                metrics={},
                error=ErrorResponse(code='build_comparison_failed', message=str(exc)),
            )

    def build_digital_twin(self, request: BuildDigitalTwinRequest) -> DigitalTwinResponse:
        try:
            service = self._get_bridge().create_digital_twin_service()
            context = service.build_plot_context(float(request.concentration_ng_ml))
            prediction = context.prediction
            ai_spectrum = context.ai_spectrum_aligned if context.ai_spectrum_aligned is not None else context.ai_spectrum_raw
            return DigitalTwinResponse(
                ok=True,
                backend='inprocess',
                concentration_ng_ml=float(request.concentration_ng_ml),
                wavelengths=list(np.asarray(context.wavelengths, dtype=float)),
                baseline_spectrum=list(np.asarray(context.bsa_spectrum, dtype=float)),
                physical_spectrum=list(np.asarray(context.physical_spectrum, dtype=float)),
                ai_spectrum=list(np.asarray(ai_spectrum, dtype=float)) if ai_spectrum is not None else None,
                metrics={
                    'peak_wavelength_nm': float(prediction.peak_wavelength),
                    'delta_lambda_nm': float(prediction.delta_lambda),
                    'peak_intensity': float(prediction.peak_intensity),
                },
            )
        except Exception as exc:
            return DigitalTwinResponse(
                ok=False,
                backend='inprocess',
                concentration_ng_ml=request.concentration_ng_ml,
                wavelengths=[],
                baseline_spectrum=[],
                physical_spectrum=[],
                ai_spectrum=None,
                metrics={},
                error=ErrorResponse(code='build_digital_twin_failed', message=str(exc)),
            )

    def predict_batch(self, request: BatchPredictRequest) -> BatchPredictionResponse:
        try:
            bridge = self._get_bridge()
            engine = bridge.create_ai_engine()
            data_loader = bridge.import_module('src.utils.data_loader')
            rows = []
            for index, item in enumerate(request.items):
                label = str(item.get('label') or item.get('name') or f'sample_{index + 1}')
                if item.get('intensities') is not None:
                    intensities = list(item.get('intensities') or [])
                elif item.get('file_path'):
                    intensities = list(data_loader.read_spectrum_file(str(item['file_path'])))
                else:
                    intensities = []
                predicted = float(engine.predict_concentration(intensities, model_mode=request.model_mode))
                report = engine.interpret_concentration(predicted)
                rows.append({
                    'label': label,
                    'model_mode': request.model_mode,
                    'predicted_concentration_ng_ml': predicted,
                    'report_mode': report.get('mode'),
                    'reported_text': report.get('reported_text'),
                    'uloq_ng_ml': report.get('uloq_ng_ml'),
                    'super_quant_bin': report.get('super_quant_bin'),
                    'source_file': item.get('file_path'),
                })
            return BatchPredictionResponse(ok=True, backend='inprocess', rows=rows)
        except Exception as exc:
            return BatchPredictionResponse(
                ok=False,
                backend='inprocess',
                rows=[],
                error=ErrorResponse(code='predict_batch_failed', message=str(exc)),
            )
