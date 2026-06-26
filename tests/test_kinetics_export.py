from pathlib import Path

import numpy as np
from PIL import Image

from nanosense.core.kinetics_export import export_kinetics_fit_report
from nanosense.core.kinetics_metadata import CANCER_BIOMARKERS, get_biomarker_by_key


def _sample_payload():
    time_s = np.linspace(0.0, 60.0, 20)
    peak_nm = 650.0 + 3.0 * (1.0 - np.exp(-0.05 * time_s))
    assoc_time = time_s[:12]
    diss_time = time_s[12:]
    assoc_fit = 650.0 + 3.0 * (1.0 - np.exp(-0.05 * assoc_time))
    diss_fit = peak_nm[12] * np.exp(-0.03 * (diss_time - diss_time[0])) + 646.0
    residual_time = np.concatenate([assoc_time, diss_time])
    residual_nm = np.concatenate([peak_nm[:12] - assoc_fit, peak_nm[12:] - diss_fit])
    derivative = np.diff(peak_nm) / np.diff(time_s)
    normalized = (peak_nm - peak_nm.min()) / (peak_nm.max() - peak_nm.min())

    return {
        "biomarker": {"key": "CEA", "label": "1 CEA", "name": "CEA"},
        "concentration_nM": 1.0,
        "parameters": {
            "k_obs": 0.05,
            "k_obs_err": 0.001,
            "association_r2": 0.998,
            "k_d": 0.03,
            "k_d_err": 0.002,
            "dissociation_r2": 0.996,
            "k_a": 2.0e7,
            "KD": 1.5e-9,
        },
        "regions": {
            "association_start_s": float(assoc_time[0]),
            "association_end_s": float(assoc_time[-1]),
            "dissociation_start_s": float(diss_time[0]),
            "dissociation_end_s": float(diss_time[-1]),
        },
        "series": [
            {"time_s": float(t), "peak_nm": float(y)}
            for t, y in zip(time_s, peak_nm)
        ],
        "association": {
            "time_s": assoc_time.tolist(),
            "response_nm": peak_nm[:12].tolist(),
            "fit_time_s": assoc_time.tolist(),
            "fit_response_nm": assoc_fit.tolist(),
            "residual_nm": (peak_nm[:12] - assoc_fit).tolist(),
        },
        "dissociation": {
            "time_s": diss_time.tolist(),
            "response_nm": peak_nm[12:].tolist(),
            "fit_time_s": diss_time.tolist(),
            "fit_response_nm": diss_fit.tolist(),
            "residual_nm": (peak_nm[12:] - diss_fit).tolist(),
        },
        "diagnostics": {
            "derivative_time_s": time_s[:-1].tolist(),
            "derivative_nm_per_s": derivative.tolist(),
            "normalized_response": normalized[:-1].tolist(),
            "self_exponent_derivative": derivative.tolist(),
            "residual_time_s": residual_time.tolist(),
            "residual_nm": residual_nm.tolist(),
        },
    }


def test_cancer_biomarker_catalog_contains_expected_ten_markers():
    assert [item["key"] for item in CANCER_BIOMARKERS] == [
        "CEA",
        "NSE",
        "Cyfra21-1",
        "ProGPR",
        "SCCA",
        "P53",
        "CA125",
        "TSGF",
        "GAGE 7",
        "MAGE A1",
    ]
    assert get_biomarker_by_key("CEA")["label"] == "1 CEA"
    assert get_biomarker_by_key("missing") == CANCER_BIOMARKERS[0]


def test_export_kinetics_fit_report_writes_data_files_and_600dpi_times_new_roman_pngs(tmp_path):
    result = export_kinetics_fit_report(
        _sample_payload(),
        tmp_path,
        timestamp="20260626_120000",
    )

    export_dir = Path(result["export_dir"])
    assert export_dir.name == "Kinetics_CEA_20260626_120000"
    assert (export_dir / "summary.xlsx").exists()
    assert (export_dir / "result.json").exists()
    assert (export_dir / "time_series.csv").exists()
    assert (export_dir / "fit_curves.csv").exists()
    assert (export_dir / "residuals.csv").exists()

    figures_dir = export_dir / "figures_600dpi"
    expected_figures = {
        "01_sensorgram_peak_wavelength.png",
        "02_main_fit_association_dissociation.png",
        "03_association_fit.png",
        "04_dissociation_fit.png",
        "05_residual_plot.png",
        "06_deviation_plot.png",
        "07_self_exponent_plot.png",
    }
    assert {path.name for path in figures_dir.glob("*.png")} == expected_figures

    for figure_path in figures_dir.glob("*.png"):
        with Image.open(figure_path) as image:
            dpi_x, dpi_y = image.info["dpi"]
            assert 590 <= dpi_x <= 610
            assert 590 <= dpi_y <= 610
