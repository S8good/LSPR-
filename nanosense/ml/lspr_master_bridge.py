from __future__ import annotations

import importlib
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, Optional


@dataclass
class LSPRMasterDiagnostics:
    master_root: str
    src_root: str
    models_root: str
    pretrained_root: str


class LSPRMasterBridge:
    REQUIRED_FILES = (
        ("src/core/ai_engine.py", "缺少 ai_engine.py"),
        ("src/core/digital_twin_service.py", "缺少 digital_twin_service.py"),
        ("models/pretrained/spectral_predictor_v2.pth", "缺少 spectral_predictor_v2.pth"),
        ("models/pretrained/predictor_v2_norm_params.pth", "缺少 predictor_v2_norm_params.pth"),
    )

    def __init__(self, master_root: Optional[Path] = None):
        self.master_root = self._resolve_master_root(master_root)
        self.src_root = self.master_root / "src"
        self.models_root = self.master_root / "models"
        self.pretrained_root = self.models_root / "pretrained"
        self.validate_required_files()

    @staticmethod
    def _resolve_master_root(master_root: Optional[Path]) -> Path:
        if master_root is None:
            env_value = os.environ.get("LSPR_MASTER_ROOT")
            if env_value:
                master_root = Path(env_value)
            else:
                master_root = Path(r"C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/DeepLearning/LSPR_Spectra_Master")

        resolved = Path(master_root).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"LSPR_Spectra_Master 根目录不存在: {resolved}")
        return resolved

    def validate_required_files(self) -> None:
        for rel_path, reason in self.REQUIRED_FILES:
            full_path = self.master_root / rel_path
            if not full_path.exists():
                raise FileNotFoundError(f"{reason}: {full_path}")

    def diagnostics(self) -> Dict[str, str]:
        data = LSPRMasterDiagnostics(
            master_root=str(self.master_root),
            src_root=str(self.src_root),
            models_root=str(self.models_root),
            pretrained_root=str(self.pretrained_root),
        )
        return data.__dict__.copy()

    @contextmanager
    def import_context(self) -> Iterator[None]:
        root_str = str(self.master_root)
        inserted = False
        if root_str not in sys.path:
            sys.path.insert(0, root_str)
            inserted = True
        try:
            yield
        finally:
            if inserted and root_str in sys.path:
                sys.path.remove(root_str)

    def import_module(self, module_name: str):
        with self.import_context():
            return importlib.import_module(module_name)

    def create_ai_engine(self):
        module = self.import_module("src.core.ai_engine")
        return module.FullSpectrumAIEngine(models_dir=str(self.models_root))

    def create_digital_twin_service(self):
        module = self.import_module("src.core.digital_twin_service")
        return module.DigitalTwinService(base_dir=str(self.master_root))

    def list_available_model_modes(self):
        engine = self.create_ai_engine()
        return list(engine.available_model_modes())
