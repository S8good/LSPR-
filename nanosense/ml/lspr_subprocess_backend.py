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
        configured_python = self.config.get('lspr_subprocess_python')
        self.python_executable = str(configured_python).strip() if configured_python else sys.executable

    def _python_candidates(self):
        configured = str(self.config.get('lspr_subprocess_python') or '').strip()
        candidates = []
        if configured:
            candidates.append(configured)
        else:
            candidates.append(sys.executable)
            for extra in (
                r"C:/ProgramData/anaconda3/envs/py39/python.exe",
                r"C:/ProgramData/anaconda3/envs/gan/python.exe",
            ):
                if extra not in candidates and Path(extra).exists():
                    candidates.append(extra)
        return candidates

    def _resolve_runner_path(self) -> Optional[Path]:
        explicit = self.config.get('lspr_runner_path')
        if explicit:
            return Path(explicit).expanduser().resolve()

        candidate_roots = []
        master_root = self.config.get('lspr_master_root')
        if master_root:
            candidate_roots.append(Path(master_root).expanduser().resolve())

        env_root = os.environ.get('LSPR_MASTER_ROOT')
        if env_root:
            candidate_roots.append(Path(env_root).expanduser().resolve())

        workspace_root = Path(__file__).resolve().parents[3]
        candidate_roots.append(workspace_root / 'DeepLearning' / 'LSPR_Spectra_Master')

        for root in candidate_roots:
            candidate = root / 'scripts' / 'lspr_bridge_runner.py'
            if candidate.exists():
                return candidate

        if candidate_roots:
            return candidate_roots[0] / 'scripts' / 'lspr_bridge_runner.py'
        return None

    def _invoke_runner_with_python(self, python_executable: str, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        runner_path = self._resolve_runner_path()
        if runner_path is None or not runner_path.exists():
            return {
                'ok': False,
                'backend': 'subprocess',
                'details': {'command': command, 'runner_path': str(runner_path) if runner_path else None},
                'error': {'code': 'runner_missing', 'message': 'subprocess runner does not exist'},
            }
        env = self._build_subprocess_env(python_executable)
        proc = subprocess.run(
            [python_executable, str(runner_path), command],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
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
        parsed = self._parse_runner_json(proc.stdout or '')
        if parsed is not None:
            return parsed
        return {
            'ok': False,
            'backend': 'subprocess',
            'details': {'command': command, 'runner_path': str(runner_path), 'stdout': proc.stdout},
            'error': {'code': 'invalid_json', 'message': 'subprocess returned invalid JSON'},
        }

    def _invoke_runner(self, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        last_result = None
        for python_executable in self._python_candidates():
            result = self._invoke_runner_with_python(python_executable, command, payload)
            if result.get('ok'):
                self.python_executable = python_executable
                return result
            last_result = result
        return last_result or {
            'ok': False,
            'backend': 'subprocess',
            'details': {'command': command},
            'error': {'code': 'runner_failed', 'message': 'subprocess execution failed'},
        }

    @staticmethod
    def _parse_runner_json(stdout_text: str) -> Optional[Dict[str, Any]]:
        text = (stdout_text or '').strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Some environments may prepend/append logs to stdout; try to recover the last JSON object.
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None

    def _build_subprocess_env(self, python_executable: Optional[str] = None) -> Dict[str, str]:
        env = os.environ.copy()
        python_path = Path(python_executable or self.python_executable).expanduser().resolve()
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
