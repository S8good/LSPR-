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
        self.timeout_seconds = int(self.config.get("lspr_subprocess_timeout_seconds", 20))
        self.python_executable = str(self.config.get("lspr_subprocess_python", sys.executable))

    def _resolve_runner_path(self) -> Optional[Path]:
        explicit = self.config.get("lspr_runner_path")
        if explicit:
            runner = Path(explicit).expanduser().resolve()
            return runner

        master_root = self.config.get("lspr_master_root")
        if not master_root:
            return None

        runner = Path(master_root).expanduser().resolve() / "scripts" / "lspr_bridge_runner.py"
        return runner

    def _invoke_runner(self, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        runner_path = self._resolve_runner_path()
        if runner_path is None or not runner_path.exists():
            return {
                "ok": False,
                "backend": "subprocess",
                "details": {
                    "command": command,
                    "runner_path": str(runner_path) if runner_path else None,
                },
                "error": {
                    "code": "runner_missing",
                    "message": "子进程 runner 不存在",
                },
            }

        env = self._build_subprocess_env()
        proc = subprocess.run(
            [self.python_executable, str(runner_path), command],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=self.timeout_seconds,
            check=False,
            env=env,
        )

        if proc.returncode != 0:
            return {
                "ok": False,
                "backend": "subprocess",
                "details": {
                    "command": command,
                    "runner_path": str(runner_path),
                    "stderr": proc.stderr.strip(),
                    "returncode": proc.returncode,
                },
                "error": {
                    "code": "runner_failed",
                    "message": proc.stderr.strip() or "子进程执行失败",
                },
            }

        try:
            return json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            return {
                "ok": False,
                "backend": "subprocess",
                "details": {
                    "command": command,
                    "runner_path": str(runner_path),
                    "stdout": proc.stdout,
                },
                "error": {
                    "code": "invalid_json",
                    "message": "子进程返回了无效 JSON",
                },
            }

    def _build_subprocess_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        python_path = Path(self.python_executable).expanduser().resolve()
        env_root = python_path.parent

        prepend = []
        candidate_dirs = [
            env_root / "bin",
            env_root / "Library" / "bin",
            env_root / "Scripts",
        ]
        for candidate in candidate_dirs:
            if candidate.exists():
                prepend.append(str(candidate).replace("\\", "/"))

        current_path = env.get("PATH", "")
        if prepend:
            env["PATH"] = ";".join(prepend + [current_path])
        return env

    def health_check(self) -> HealthCheckResponse:
        result = self._invoke_runner("health", {})
        error = result.get("error")
        return HealthCheckResponse(
            ok=bool(result.get("ok", False)),
            backend="subprocess",
            details=result.get("details", {}),
            error=ErrorResponse(**error) if isinstance(error, dict) else None,
        )

    def predict_single(self, request: PredictSingleRequest) -> PredictionResponse:
        result = self._invoke_runner("predict_single", request.to_payload())
        error = result.get("error")
        return PredictionResponse(
            ok=bool(result.get("ok", False)),
            backend="subprocess",
            model_mode=request.model_mode,
            predicted_concentration_ng_ml=result.get("predicted_concentration_ng_ml"),
            report_mode=result.get("report_mode"),
            reported_text=result.get("reported_text"),
            uloq_ng_ml=result.get("uloq_ng_ml"),
            super_quant_bin=result.get("super_quant_bin"),
            metrics=result.get("metrics", {}),
            error=ErrorResponse(**error) if isinstance(error, dict) else None,
        )

    def build_comparison(self, request: BuildComparisonRequest) -> ComparisonResponse:
        return ComparisonResponse(
            ok=False,
            backend="subprocess",
            model_mode=request.model_mode,
            wavelengths=[],
            input_spectrum=[],
            generated_spectrum=[],
            aligned_spectrum=[],
            physical_spectrum=None,
            metrics={},
            error=ErrorResponse(code="not_implemented", message="subprocess build_comparison 未实现"),
        )

    def build_digital_twin(self, request: BuildDigitalTwinRequest) -> DigitalTwinResponse:
        return DigitalTwinResponse(
            ok=False,
            backend="subprocess",
            concentration_ng_ml=request.concentration_ng_ml,
            wavelengths=[],
            baseline_spectrum=[],
            physical_spectrum=[],
            ai_spectrum=None,
            metrics={},
            error=ErrorResponse(code="not_implemented", message="subprocess build_digital_twin 未实现"),
        )

    def predict_batch(self, request: BatchPredictRequest) -> BatchPredictionResponse:
        return BatchPredictionResponse(
            ok=False,
            backend="subprocess",
            rows=[],
            error=ErrorResponse(code="not_implemented", message="subprocess predict_batch 未实现"),
        )
