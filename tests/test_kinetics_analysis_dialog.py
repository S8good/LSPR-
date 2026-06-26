import os
from pathlib import Path

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from nanosense.algorithms.kinetics import association_model, dissociation_model
from nanosense.gui.kinetics_analysis_dialog import KineticsAnalysisDialog


def _make_app():
    return QApplication.instance() or QApplication([])


def test_kinetics_analysis_dialog_uses_explicit_models_and_shows_fit_quality():
    app = _make_app()
    assoc_t = np.linspace(0.0, 100.0, 80)
    diss_t = np.linspace(130.0, 250.0, 90)
    assoc_y = association_model(assoc_t, dlam_eq=4.0, k_obs=0.04, baseline=0.1)
    diss_y = dissociation_model(diss_t - diss_t[0], dlam_0=3.5, k_off=0.015, baseline=0.2)

    dialog = KineticsAnalysisDialog(
        np.concatenate([assoc_t, diss_t]),
        np.concatenate([assoc_y, diss_y]),
        biomarker={"key": "CEA", "label": "1 CEA", "name": "CEA"},
    )
    dialog.assoc_start_line.setValue(0.0)
    dialog.assoc_end_line.setValue(100.0)
    dialog.dissoc_start_line.setValue(130.0)
    dialog.dissoc_end_line.setValue(250.0)
    dialog.concentration_input.setValue(1.0)

    dialog._perform_analysis()

    assert np.isclose(float(dialog.k_obs_label.text()), 0.04, rtol=0.05)
    assert np.isclose(float(dialog.k_d_label.text()), 0.015, rtol=0.05)
    assert float(dialog.k_obs_err_label.text()) >= 0.0
    assert float(dialog.k_d_err_label.text()) >= 0.0
    assert float(dialog.assoc_r2_label.text()) > 0.999
    assert float(dialog.dissoc_r2_label.text()) > 0.999
    assert dialog.save_to_db_button.isEnabled()
    assert dialog.save_local_button.isEnabled()
    assert dialog.last_results_data["biomarker_key"] == "CEA"
    assert dialog.last_export_payload["biomarker"]["label"] == "1 CEA"

    dialog.close()
    app.processEvents()


def test_kinetics_analysis_dialog_defaults_to_first_biomarker_when_none_supplied():
    app = _make_app()
    dialog = KineticsAnalysisDialog([0, 1, 2, 3, 4], [650, 651, 652, 653, 654])

    assert dialog.biomarker["key"] == "CEA"
    assert dialog.biomarker_value_label.text() == "1 CEA"

    dialog.close()
    app.processEvents()


def test_kinetics_analysis_dialog_keeps_new_ui_text_translatable():
    source = Path("nanosense/gui/kinetics_analysis_dialog.py").read_text(encoding="utf-8")

    hardcoded_ui_text = [
        "请拖拽竖线选择",
        "主拟合图",
        "偏差图",
        "自指数图",
        "残差图",
    ]
    for text in hardcoded_ui_text:
        assert text not in source
