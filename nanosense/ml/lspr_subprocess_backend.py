from __future__ import annotations

import json
import os
import subprocess
import sys
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


class SubprocessLSPRBackend(LSPRBackend):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.timeout_seconds = int(self.config.get('lspr_subprocess_timeout_seconds', 20))
        self.python_executable = str(self.config.get('lspr_subprocess_python', sys.executable))

    def _resolve_runner_path(self) -> Optional[Path]:
        explicit = self.config.get('lspr_runner_path')
        if explicit:
            return Path(explicit).expanduser().resolve()
        master_root = self.config.get('lspr_master_root')
        if not master_root:
            return None
        return Path(master_root).expanduser().resolve() / 'scripts' / 'lspr_bridge_runner.py'

    def _invoke_runner(self, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        runner_path = self._resolve_runner_path()
        if runner_path is None or not runner_path.exists():
            return {
                'ok': False,
                'backend': 'subprocess',
                'details': {'command': command, 'runner_path': str(runner_path) if runner_path else None},
                'error': {'code': 'runner_missing', 'message': 'subprocess runner does not exist'},
            }
        env = self._build_subprocess_env()
        proc = subprocess.run(
            [self.python_executable, str(runner_path), command],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=self.timeout_seconds,
            check=False,
            env=env,
        )
        if proc.returncode != 0:
            return {
                'ok': False,
                'backend': 'subprocess',
                'details': {
                    'command': command,
                    'runner_path': str(runner_path),
                    'stderr': proc.stderr.strip(),
                    'returncode': proc.returncode,
                },
                'error': {'code': 'runner_failed', 'message': proc.stderr.strip() or 'subprocess execution failed'},
            }
        try:
            return json.loads(proc.stdout or '{}')
        except json.JSONDecodeError:
            return {
                'ok': False,
                'backend': 'subprocess',
                'details': {'command': command, 'runner_path': str(runner_path), 'stdout': proc.stdout},
                'error': {'code': 'invalid_json', 'message': 'subprocess returned invalid JSON'},
            }

    def _build_subprocess_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        python_path = Path(self.python_executable).expanduser().resolve()
        env_root = python_path.parent
        prepend = []
        for candidate in (env_root / 'bin', env_root / 'Library' / 'bin', env_root / 'Scripts'):
            if candidate.exists():
                prepend.append(str(candidate).replace('\\', '/'))
        current_path = env.get('PATH', '')
        if prepend:
            env['PATH'] = ';'.join(prepend + [current_path])
        return env

    def health_check(self) -> HealthCheckResponse:
        result = self._invoke_runner('health', {})
        error = result.get('error')
        return HealthCheckResponse(
            ok=bool(result.get('ok', False)),
            backend='subprocess',
            details=result.get('details', {}),
            error=ErrorResponse(**error) if isinstance(error, dict) else None,
        )

    def predict_single(self, request: PredictSingleRequest) -> PredictionResponse:
        result = self._invoke_runner('predict_single', request.to_payload())
        error = result.get('error')
        return PredictionResponse(
            ok=bool(result.get('ok', False)),
            backend='subprocess',
            model_mode=result.get('model_mode', request.model_mode),
            predicted_concentration_ng_ml=result.get('predicted_concentration_ng_ml'),
            report_mode=result.get('report_mode'),
            reported_text=result.get('reported_text'),
            uloq_ng_ml=result.get('uloq_ng_ml'),
            super_quant_bin=result.get('super_quant_bin'),
            metrics=result.get('metrics', {}),
            error=ErrorResponse(**error) if isinstance(error, dict) else None,
        )

    def build_comparison(self, request: BuildComparisonRequest) -> ComparisonResponse:
        result = self._invoke_runner('build_comparison', request.to_payload())
        error = result.get('error')
        return ComparisonResponse(
            ok=bool(result.get('ok', False)),
            backend='subprocess',
            model_mode=result.get('model_mode', request.model_mode),
            wavelengths=result.get('wavelengths', []),
            input_spectrum=result.get('input_spectrum', []),
            generated_spectrum=result.get('generated_spectrum', []),
            aligned_spectrum=result.get('aligned_spectrum', []),
            physical_spectrum=result.get('physical_spectrum'),
            metrics=result.get('metrics', {}),
            error=ErrorResponse(**error) if isinstance(error, dict) else None,
        )

    def build_digital_twin(self, request: BuildDigitalTwinRequest) -> DigitalTwinResponse:
        result = self._invoke_runner('build_digital_twin', request.to_payload())
        error = result.get('error')
        return DigitalTwinResponse(
            ok=bool(result.get('ok', False)),
            backend='subprocess',
            concentration_ng_ml=float(result.get('concentration_ng_ml', request.concentration_ng_ml)),
            wavelengths=result.get('wavelengths', []),
            baseline_spectrum=result.get('baseline_spectrum', []),
            physical_spectrum=result.get('physical_spectrum', []),
            ai_spectrum=result.get('ai_spectrum'),
            metrics=result.get('metrics', {}),
            error=ErrorResponse(**error) if isinstance(error, dict) else None,
        )

    def predict_batch(self, request: BatchPredictRequest) -> BatchPredictionResponse:
        result = self._invoke_runner('predict_batch', request.to_payload())
        error = result.get('error')
        return BatchPredictionResponse(
            ok=bool(result.get('ok', False)),
            backend='subprocess',
            rows=result.get('rows', []),
            error=ErrorResponse(**error) if isinstance(error, dict) else None,
        )
