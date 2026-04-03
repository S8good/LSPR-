from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


def _json_compatible(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_compatible(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


@dataclass
class ErrorResponse:
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass
class PredictSingleRequest:
    wavelengths: List[float]
    intensities: List[float]
    model_mode: str = "auto"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass
class BuildComparisonRequest:
    wavelengths: List[float]
    intensities: List[float]
    model_mode: str = "auto"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass
class BuildDigitalTwinRequest:
    concentration_ng_ml: float
    experimental_wavelengths: Optional[List[float]] = None
    experimental_intensities: Optional[List[float]] = None
    model_mode: str = "auto"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass
class BatchPredictRequest:
    items: List[Dict[str, Any]]
    model_mode: str = "auto"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass
class HealthCheckResponse:
    ok: bool
    backend: str
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[ErrorResponse] = None

    def to_payload(self) -> Dict[str, Any]:
        payload = _json_compatible(asdict(self))
        if self.error is None:
            payload["error"] = None
        return payload


@dataclass
class PredictionResponse:
    ok: bool
    backend: str
    model_mode: str
    predicted_concentration_ng_ml: Optional[float]
    report_mode: Optional[str]
    reported_text: Optional[str]
    uloq_ng_ml: Optional[float]
    super_quant_bin: Optional[str]
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[ErrorResponse] = None

    def to_payload(self) -> Dict[str, Any]:
        payload = _json_compatible(asdict(self))
        if self.error is None:
            payload["error"] = None
        return payload


@dataclass
class ComparisonResponse:
    ok: bool
    backend: str
    model_mode: str
    wavelengths: List[float]
    input_spectrum: List[float]
    generated_spectrum: List[float]
    aligned_spectrum: List[float]
    physical_spectrum: Optional[List[float]] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[ErrorResponse] = None

    def to_payload(self) -> Dict[str, Any]:
        payload = _json_compatible(asdict(self))
        if self.error is None:
            payload["error"] = None
        return payload


@dataclass
class DigitalTwinResponse:
    ok: bool
    backend: str
    concentration_ng_ml: float
    wavelengths: List[float]
    baseline_spectrum: List[float]
    physical_spectrum: List[float]
    ai_spectrum: Optional[List[float]]
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[ErrorResponse] = None

    def to_payload(self) -> Dict[str, Any]:
        payload = _json_compatible(asdict(self))
        if self.error is None:
            payload["error"] = None
        return payload


@dataclass
class BatchPredictionResponse:
    ok: bool
    backend: str
    rows: List[Dict[str, Any]]
    error: Optional[ErrorResponse] = None

    def to_payload(self) -> Dict[str, Any]:
        payload = _json_compatible(asdict(self))
        if self.error is None:
            payload["error"] = None
        return payload


class LSPRBackend(ABC):
    @abstractmethod
    def health_check(self) -> HealthCheckResponse:
        raise NotImplementedError

    @abstractmethod
    def predict_single(self, request: PredictSingleRequest) -> PredictionResponse:
        raise NotImplementedError

    @abstractmethod
    def build_comparison(self, request: BuildComparisonRequest) -> ComparisonResponse:
        raise NotImplementedError

    @abstractmethod
    def build_digital_twin(self, request: BuildDigitalTwinRequest) -> DigitalTwinResponse:
        raise NotImplementedError

    @abstractmethod
    def predict_batch(self, request: BatchPredictRequest) -> BatchPredictionResponse:
        raise NotImplementedError
