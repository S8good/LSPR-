from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_main_window_uses_relative_imports_for_internal_nanosense_modules():
    source = (PROJECT_ROOT / "nanosense" / "gui" / "main_window.py").read_text(encoding="utf-8")

    assert "from ..utils.file_io import load_spectra_from_path, load_spectrum" in source
    assert "from ..core.controller import FX2000Controller" in source
    assert "from ..core.spectrum_processor import SpectrumProcessor" in source
    assert "from ..core.batch_acquisition import BatchRunDialog, BatchAcquisitionWorker" in source
