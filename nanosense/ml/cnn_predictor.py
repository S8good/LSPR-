import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
try:
    import torch
    import torch.nn.functional as F
    TORCH_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    torch = None
    F = None
    TORCH_IMPORT_ERROR = exc


@dataclass
class CNNPredictionResult:
    pred_class_id: int
    pred_class_name: str
    confidence: float
    topk: List[Dict[str, float]]
    class_probs: Dict[int, float]
    class_ids: np.ndarray
    id_to_label: Dict[int, str]
    target_wavelengths: np.ndarray
    query_norm: np.ndarray
    pred_prototype_norm: np.ndarray


if torch is not None:
    class _ResidualBlock1D(torch.nn.Module):
        def __init__(self, in_ch: int, out_ch: int, stride: int = 1, kernel_size: int = 7):
            super().__init__()
            padding = kernel_size // 2
            self.conv1 = torch.nn.Conv1d(in_ch, out_ch, kernel_size, stride=stride, padding=padding, bias=False)
            self.bn1 = torch.nn.BatchNorm1d(out_ch)
            self.conv2 = torch.nn.Conv1d(out_ch, out_ch, kernel_size, stride=1, padding=padding, bias=False)
            self.bn2 = torch.nn.BatchNorm1d(out_ch)
            self.relu = torch.nn.ReLU(inplace=True)
            self.downsample = None
            if stride != 1 or in_ch != out_ch:
                self.downsample = torch.nn.Sequential(
                    torch.nn.Conv1d(in_ch, out_ch, kernel_size=1, stride=stride, bias=False),
                    torch.nn.BatchNorm1d(out_ch),
                )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            identity = x
            out = self.relu(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            if self.downsample is not None:
                identity = self.downsample(x)
            out = self.relu(out + identity)
            return out


    def _make_layer(in_ch: int, out_ch: int, blocks: int, stride: int) -> torch.nn.Sequential:
        layers = [_ResidualBlock1D(in_ch, out_ch, stride=stride)]
        for _ in range(1, blocks):
            layers.append(_ResidualBlock1D(out_ch, out_ch, stride=1))
        return torch.nn.Sequential(*layers)


    class _ResNet1DEncoder(torch.nn.Module):
        def __init__(self, embedding_dim: int = 128):
            super().__init__()
            self.stem = torch.nn.Sequential(
                torch.nn.Conv1d(1, 32, kernel_size=7, stride=2, padding=3, bias=False),
                torch.nn.BatchNorm1d(32),
                torch.nn.ReLU(inplace=True),
            )
            self.layer1 = _make_layer(32, 64, blocks=2, stride=2)
            self.layer2 = _make_layer(64, 128, blocks=2, stride=2)
            self.layer3 = _make_layer(128, 128, blocks=2, stride=1)
            self.pool = torch.nn.AdaptiveAvgPool1d(1)
            self.fc = torch.nn.Linear(128, embedding_dim)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = self.stem(x)
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = self.pool(x).squeeze(-1)
            x = self.fc(x)
            return x
else:
    class _ResNet1DEncoder:  # pragma: no cover
        pass


class CNNSpectrumPredictor:
    def __init__(
        self,
        encoder_path: Optional[Path] = None,
        dataset_dir: Optional[Path] = None,
        temperature: float = 0.2,
    ):
        self.temperature = max(float(temperature), 1e-6)
        self.project_root = self._find_project_root()
        self.deep_root = self.project_root / "DeepLearning" / "Cnn"

        default_encoder = self._find_default_encoder_path()
        default_dataset = self.deep_root / "data" / "real_fewshot_cea_20260204"

        self.encoder_path = Path(encoder_path) if encoder_path else default_encoder
        self.dataset_dir = Path(dataset_dir) if dataset_dir else default_dataset
        self.device = torch.device("cuda" if (torch is not None and torch.cuda.is_available()) else "cpu")

        self._initialized = False
        self._normalize_mode = "minmax"
        self._target_wl: Optional[np.ndarray] = None
        self._id_to_label: Dict[int, str] = {}
        self._encoder: Optional[_ResNet1DEncoder] = None
        self._proto_emb: Optional[np.ndarray] = None
        self._proto_spec: Optional[np.ndarray] = None
        self._class_ids: Optional[np.ndarray] = None

    def _find_default_encoder_path(self) -> Path:
        stage2_root = self.deep_root / "outputs" / "stage2_domain_pretrain"
        if stage2_root.exists():
            cands = sorted(stage2_root.glob("run_*/encoder_stage2_best.pth"))
            if cands:
                return cands[-1]
        raise FileNotFoundError(
            f"Stage-2 encoder not found under: {stage2_root}. "
            "Please run stage2 domain pretraining first."
        )

    def get_stage1_encoder_path(self) -> Path:
        return (
            self.deep_root
            / "outputs"
            / "exp_20260324_real20260204_v1"
            / "pretrain"
            / "enc_s2026"
            / "lspr_encoder_v1.pth"
        )

    def get_stage2_encoder_path(self) -> Path:
        return self._find_default_encoder_path()

    def _find_project_root(self) -> Path:
        cur = Path(__file__).resolve()
        for p in cur.parents:
            if (p / "DeepLearning" / "Cnn").exists():
                return p
        raise FileNotFoundError("Cannot locate project root containing DeepLearning/Cnn")

    def _normalize(self, x: np.ndarray) -> np.ndarray:
        if self._normalize_mode == "none":
            return x
        if self._normalize_mode == "zscore":
            std = float(np.std(x))
            if std <= 1e-12:
                return np.zeros_like(x, dtype=np.float32)
            return ((x - float(np.mean(x))) / std).astype(np.float32)
        x_min = float(np.min(x))
        x_max = float(np.max(x))
        span = x_max - x_min
        if span <= 1e-12:
            return np.zeros_like(x, dtype=np.float32)
        return ((x - x_min) / span).astype(np.float32)

    def _extract_embeddings(self, spectra: np.ndarray, batch_size: int = 64) -> np.ndarray:
        assert self._encoder is not None
        ds = torch.utils.data.TensorDataset(torch.from_numpy(spectra).unsqueeze(1))
        loader = torch.utils.data.DataLoader(
            ds,
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,
            pin_memory=(self.device.type == "cuda"),
        )
        out = []
        self._encoder.eval()
        with torch.no_grad():
            for (x,) in loader:
                emb = self._encoder(x.to(self.device)).cpu().numpy()
                out.append(emb)
        return np.concatenate(out, axis=0)

    def initialize(self) -> None:
        if self._initialized:
            return
        if torch is None:
            raise RuntimeError(f"PyTorch import failed: {TORCH_IMPORT_ERROR}")
        if not self.encoder_path.exists():
            raise FileNotFoundError(f"Encoder not found: {self.encoder_path}")
        if not self.dataset_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {self.dataset_dir}")

        label_map_path = self.dataset_dir / "label_map.json"
        spectra_path = self.dataset_dir / "spectra.npy"
        labels_path = self.dataset_dir / "labels.npy"
        wavelengths_path = self.dataset_dir / "wavelengths.npy"
        if not (label_map_path.exists() and spectra_path.exists() and labels_path.exists() and wavelengths_path.exists()):
            raise FileNotFoundError("Dataset artifacts are incomplete (need label_map/spectra/labels/wavelengths).")

        with label_map_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        raw_map = payload.get("id_to_label", {})
        self._id_to_label = {int(k): str(v) for k, v in raw_map.items()}
        self._normalize_mode = str(payload.get("normalize", "minmax")).lower()

        spectra = np.load(spectra_path).astype(np.float32)
        labels = np.load(labels_path).astype(np.int64)
        self._target_wl = np.load(wavelengths_path).astype(np.float32)

        encoder = _ResNet1DEncoder(embedding_dim=128)
        encoder.load_state_dict(torch.load(str(self.encoder_path), map_location="cpu"))
        encoder.to(self.device)
        encoder.eval()
        self._encoder = encoder

        embs = self._extract_embeddings(spectra)
        class_ids = np.unique(labels).astype(np.int64)
        proto_emb = []
        proto_spec = []
        for cid in class_ids:
            mask = labels == cid
            proto_emb.append(embs[mask].mean(axis=0))
            proto_spec.append(spectra[mask].mean(axis=0))

        self._class_ids = class_ids
        self._proto_emb = np.asarray(proto_emb, dtype=np.float32)
        self._proto_spec = np.asarray(proto_spec, dtype=np.float32)
        self._initialized = True

    def get_normalized_prototype_for_class(self, class_id: int) -> np.ndarray:
        self.initialize()
        assert self._class_ids is not None
        assert self._proto_spec is not None
        matches = np.where(self._class_ids == int(class_id))[0]
        if matches.size == 0:
            raise ValueError(f"class_id {class_id} not found in predictor classes")
        proto = self._proto_spec[int(matches[0])].astype(np.float32)
        return self._normalize(proto)

    def predict(self, x_raw: np.ndarray, y_raw: np.ndarray, topk: int = 3) -> CNNPredictionResult:
        self.initialize()
        assert self._target_wl is not None
        assert self._encoder is not None
        assert self._class_ids is not None
        assert self._proto_emb is not None
        assert self._proto_spec is not None

        x_raw = np.asarray(x_raw, dtype=np.float32).ravel()
        y_raw = np.asarray(y_raw, dtype=np.float32).ravel()
        if x_raw.size < 4 or y_raw.size < 4 or x_raw.size != y_raw.size:
            raise ValueError("Input spectrum must contain >=4 valid points with matched x/y.")

        order = np.argsort(x_raw)
        x_sorted = x_raw[order]
        y_sorted = y_raw[order]

        # Resample to training wavelength axis and apply the same normalization mode.
        query = np.interp(self._target_wl, x_sorted, y_sorted).astype(np.float32)
        query = self._normalize(query)

        with torch.no_grad():
            q = torch.from_numpy(query).float().view(1, 1, -1).to(self.device)
            q_emb = self._encoder(q)
            q_emb = F.normalize(q_emb, dim=1)
            p_emb = F.normalize(torch.from_numpy(self._proto_emb).float().to(self.device), dim=1)
            logits = (q_emb @ p_emb.t()) / self.temperature
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]

        pred_pos = int(np.argmax(probs))
        pred_id = int(self._class_ids[pred_pos])
        pred_name = self._id_to_label.get(pred_id, str(pred_id))

        order_idx = np.argsort(-probs)[: max(1, int(topk))]
        topk_list: List[Dict[str, float]] = []
        for i in order_idx:
            cid = int(self._class_ids[int(i)])
            topk_list.append(
                {
                    "class_id": cid,
                    "class_name": self._id_to_label.get(cid, str(cid)),
                    "prob": float(probs[int(i)]),
                }
            )

        pred_proto = self._proto_spec[pred_pos].astype(np.float32)
        pred_proto = self._normalize(pred_proto)

        return CNNPredictionResult(
            pred_class_id=pred_id,
            pred_class_name=pred_name,
            confidence=float(probs[pred_pos]),
            topk=topk_list,
            class_probs={int(self._class_ids[i]): float(probs[i]) for i in range(len(self._class_ids))},
            class_ids=self._class_ids.copy(),
            id_to_label=dict(self._id_to_label),
            target_wavelengths=self._target_wl.copy(),
            query_norm=query,
            pred_prototype_norm=pred_proto,
        )
