import json
import re
from pathlib import Path

import pandas as pd


def _safe_name(value):
    text = str(value or "Unknown").strip()
    text = re.sub(r"[^\w\-. ]+", "_", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text)
    return text.strip("._") or "Unknown"


def _series_frame(payload):
    rows = payload.get("series") or []
    return pd.DataFrame(rows, columns=["time_s", "peak_nm"])


def _fit_curves_frame(payload):
    association = payload.get("association") or {}
    dissociation = payload.get("dissociation") or {}
    return pd.DataFrame({
        "association_fit_time_s": pd.Series(association.get("fit_time_s") or []),
        "association_fit_peak_nm": pd.Series(association.get("fit_response_nm") or []),
        "dissociation_fit_time_s": pd.Series(dissociation.get("fit_time_s") or []),
        "dissociation_fit_peak_nm": pd.Series(dissociation.get("fit_response_nm") or []),
    })


def _residuals_frame(payload):
    diagnostics = payload.get("diagnostics") or {}
    return pd.DataFrame({
        "time_s": pd.Series(diagnostics.get("residual_time_s") or []),
        "residual_nm": pd.Series(diagnostics.get("residual_nm") or []),
    })


def _summary_frame(payload):
    biomarker = payload.get("biomarker") or {}
    parameters = payload.get("parameters") or {}
    regions = payload.get("regions") or {}

    rows = [
        ("Biomarker", "Label", biomarker.get("label")),
        ("Biomarker", "Key", biomarker.get("key")),
        ("Biomarker", "Name", biomarker.get("name")),
        ("Experiment", "Concentration (nM)", payload.get("concentration_nM")),
    ]
    for key, value in regions.items():
        rows.append(("Regions", key, value))
    for key, value in parameters.items():
        rows.append(("Fit Parameters", key, value))
    return pd.DataFrame(rows, columns=["Category", "Parameter", "Value"])


def _plot_context():
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt.rc_context({
        "font.family": "Times New Roman",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.unicode_minus": False,
    }), plt


def _style_axes(ax):
    ax.grid(True, color="#D1D5DB", linewidth=0.6, alpha=0.7)
    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(0.8)
    ax.tick_params(axis="both", colors="black", width=0.8)


def _save_plot(path, draw_func):
    context, plt = _plot_context()
    with context:
        fig, ax = plt.subplots(figsize=(6.4, 4.6))
        draw_func(ax)
        _style_axes(ax)
        fig.tight_layout()
        fig.savefig(path, dpi=600, bbox_inches="tight")
        plt.close(fig)


def _plot_sensorgram(payload, path):
    series = _series_frame(payload)
    biomarker = (payload.get("biomarker") or {}).get("label", "")

    def draw(ax):
        ax.plot(series["time_s"], series["peak_nm"], color="#1F77B4", linewidth=2, marker="o", markersize=3)
        ax.set_title(f"Sensorgram - {biomarker}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Peak Wavelength (nm)")

    _save_plot(path, draw)


def _plot_main_fit(payload, path):
    series = _series_frame(payload)
    association = payload.get("association") or {}
    dissociation = payload.get("dissociation") or {}
    biomarker = (payload.get("biomarker") or {}).get("label", "")

    def draw(ax):
        ax.scatter(series["time_s"], series["peak_nm"], color="#4B5563", s=14, label="Measured")
        ax.plot(
            association.get("fit_time_s") or [],
            association.get("fit_response_nm") or [],
            color="#00897B",
            linewidth=2,
            label="Association Fit",
        )
        ax.plot(
            dissociation.get("fit_time_s") or [],
            dissociation.get("fit_response_nm") or [],
            color="#D32F2F",
            linewidth=2,
            label="Dissociation Fit",
        )
        ax.set_title(f"Association and Dissociation Fit - {biomarker}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Peak Wavelength (nm)")
        ax.legend(loc="best", frameon=True)

    _save_plot(path, draw)


def _plot_segment_fit(payload, path, segment_key, title, color):
    segment = payload.get(segment_key) or {}
    biomarker = (payload.get("biomarker") or {}).get("label", "")

    def draw(ax):
        ax.scatter(
            segment.get("time_s") or [],
            segment.get("response_nm") or [],
            color="#4B5563",
            s=16,
            label="Measured",
        )
        ax.plot(
            segment.get("fit_time_s") or [],
            segment.get("fit_response_nm") or [],
            color=color,
            linewidth=2,
            label="Fit",
        )
        ax.set_title(f"{title} - {biomarker}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Peak Wavelength (nm)")
        ax.legend(loc="best", frameon=True)

    _save_plot(path, draw)


def _plot_residuals(payload, path):
    residuals = _residuals_frame(payload)

    def draw(ax):
        ax.axhline(0.0, color="black", linewidth=0.9)
        ax.scatter(residuals["time_s"], residuals["residual_nm"], color="#8E24AA", s=16)
        ax.set_title("Residual Plot")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Residual (Actual - Fit)")

    _save_plot(path, draw)


def _plot_deviation(payload, path):
    diagnostics = payload.get("diagnostics") or {}

    def draw(ax):
        ax.plot(
            diagnostics.get("derivative_time_s") or [],
            diagnostics.get("derivative_nm_per_s") or [],
            color="#374151",
            linewidth=1.8,
            marker="o",
            markersize=3,
        )
        ax.set_title("Deviation Plot")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Delta Response / Delta t")

    _save_plot(path, draw)


def _plot_self_exponent(payload, path):
    diagnostics = payload.get("diagnostics") or {}

    def draw(ax):
        ax.scatter(
            diagnostics.get("normalized_response") or [],
            diagnostics.get("self_exponent_derivative") or [],
            color="#1E88E5",
            s=16,
        )
        ax.set_title("Self-Exponent Plot")
        ax.set_xlabel("Normalized Response")
        ax.set_ylabel("Delta Response / Delta t")

    _save_plot(path, draw)


def _write_figures(payload, figures_dir):
    figures_dir.mkdir(parents=True, exist_ok=True)
    figure_paths = {
        "sensorgram": figures_dir / "01_sensorgram_peak_wavelength.png",
        "main_fit": figures_dir / "02_main_fit_association_dissociation.png",
        "association_fit": figures_dir / "03_association_fit.png",
        "dissociation_fit": figures_dir / "04_dissociation_fit.png",
        "residual": figures_dir / "05_residual_plot.png",
        "deviation": figures_dir / "06_deviation_plot.png",
        "self_exponent": figures_dir / "07_self_exponent_plot.png",
    }

    _plot_sensorgram(payload, figure_paths["sensorgram"])
    _plot_main_fit(payload, figure_paths["main_fit"])
    _plot_segment_fit(payload, figure_paths["association_fit"], "association", "Association Fit", "#00897B")
    _plot_segment_fit(payload, figure_paths["dissociation_fit"], "dissociation", "Dissociation Fit", "#D32F2F")
    _plot_residuals(payload, figure_paths["residual"])
    _plot_deviation(payload, figure_paths["deviation"])
    _plot_self_exponent(payload, figure_paths["self_exponent"])
    return figure_paths


def export_kinetics_fit_report(payload, base_dir, timestamp):
    base_path = Path(base_dir)
    biomarker = payload.get("biomarker") or {}
    biomarker_name = _safe_name(biomarker.get("name") or biomarker.get("key") or "Unknown")
    export_dir = base_path / f"Kinetics_{biomarker_name}_{timestamp}"
    export_dir.mkdir(parents=True, exist_ok=True)

    summary_df = _summary_frame(payload)
    time_series_df = _series_frame(payload)
    fit_curves_df = _fit_curves_frame(payload)
    residuals_df = _residuals_frame(payload)

    summary_path = export_dir / "summary.xlsx"
    with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        time_series_df.to_excel(writer, sheet_name="Time Series", index=False)
        fit_curves_df.to_excel(writer, sheet_name="Fit Curves", index=False)
        residuals_df.to_excel(writer, sheet_name="Residuals", index=False)

    result_json_path = export_dir / "result.json"
    result_json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    time_series_path = export_dir / "time_series.csv"
    fit_curves_path = export_dir / "fit_curves.csv"
    residuals_path = export_dir / "residuals.csv"
    time_series_df.to_csv(time_series_path, index=False, encoding="utf-8-sig")
    fit_curves_df.to_csv(fit_curves_path, index=False, encoding="utf-8-sig")
    residuals_df.to_csv(residuals_path, index=False, encoding="utf-8-sig")

    figures = _write_figures(payload, export_dir / "figures_600dpi")

    return {
        "export_dir": str(export_dir),
        "files": {
            "summary": str(summary_path),
            "result_json": str(result_json_path),
            "time_series": str(time_series_path),
            "fit_curves": str(fit_curves_path),
            "residuals": str(residuals_path),
        },
        "figures": {key: str(path) for key, path in figures.items()},
    }
