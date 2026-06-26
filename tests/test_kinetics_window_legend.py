import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from nanosense.gui.kinetics_window import KineticsWindow


def _legend_anchor(legend):
    return (
        getattr(legend, "_GraphicsWidgetAnchor__itemAnchor"),
        getattr(legend, "_GraphicsWidgetAnchor__parentAnchor"),
        getattr(legend, "_GraphicsWidgetAnchor__offset"),
    )


def test_kinetics_window_legends_are_top_right_and_sensorgram_label_is_peak_wavelength():
    app = QApplication.instance() or QApplication([])
    window = KineticsWindow()

    sensorgram_legend = window.sensorgram_plot.getPlotItem().legend
    peak_shift_legend = window.peak_shift_plot.getPlotItem().legend
    comparison_legend = window.comparison_plot.getPlotItem().legend

    assert sensorgram_legend.items[0][1].text == "Peak Wavelength"
    for legend in (sensorgram_legend, peak_shift_legend, comparison_legend):
        assert _legend_anchor(legend) == ((1, 0), (1, 0), (-10, 10))

    window.close()
    app.processEvents()


def test_kinetics_window_exposes_biomarker_selection_for_analysis():
    app = QApplication.instance() or QApplication([])
    window = KineticsWindow()

    assert window.biomarker_combo.count() == 10
    assert window.biomarker_combo.itemText(0) == "1 CEA"

    window.biomarker_combo.setCurrentIndex(6)
    assert window.selected_biomarker()["key"] == "CA125"
    assert window.selected_biomarker()["label"] == "7 CA125"

    window.close()
    app.processEvents()
