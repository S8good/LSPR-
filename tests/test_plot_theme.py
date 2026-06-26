import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg

from nanosense.utils.plot_theme import (
    anchor_plot_legend_top_right,
    apply_plot_theme,
    configure_pyqtgraph_theme,
    get_plot_theme,
    set_plot_legend_visible,
)


def _make_plot_with_legend():
    app = QApplication.instance() or QApplication([])
    plot = pg.PlotWidget()
    plot.setTitle("Theme Test")
    plot.setLabel("bottom", "Time", units="s")
    plot.setLabel("left", "Response")
    plot.addLegend()
    plot.plot([0, 1], [1, 2], name="Curve")
    return app, plot


def test_light_plot_theme_uses_dark_text_for_title_axes_and_legend():
    _app, plot = _make_plot_with_legend()

    apply_plot_theme(plot, "light")

    palette = get_plot_theme("light")
    plot_item = plot.getPlotItem()

    assert plot_item.titleLabel.opts["color"] == palette.title
    assert plot_item.getAxis("bottom").labelStyle["color"] == palette.text
    assert plot_item.getAxis("left").labelStyle["color"] == palette.text

    legend_label = plot_item.legend.items[0][1]
    assert legend_label.opts["color"] == palette.text


def test_dark_plot_theme_uses_light_text_for_title_axes_and_legend():
    _app, plot = _make_plot_with_legend()

    apply_plot_theme(plot, "dark")

    palette = get_plot_theme("dark")
    plot_item = plot.getPlotItem()

    assert plot_item.titleLabel.opts["color"] == palette.title
    assert plot_item.getAxis("bottom").labelStyle["color"] == palette.text
    assert plot_item.getAxis("left").labelStyle["color"] == palette.text

    legend_label = plot_item.legend.items[0][1]
    assert legend_label.opts["color"] == palette.text


def test_global_pyqtgraph_theme_tracks_selected_theme():
    configure_pyqtgraph_theme("light")
    assert pg.getConfigOption("foreground") == get_plot_theme("light").text

    configure_pyqtgraph_theme("dark")
    assert pg.getConfigOption("foreground") == get_plot_theme("dark").text


def test_set_plot_legend_visible_hides_and_restores_existing_legend():
    _app, plot = _make_plot_with_legend()
    legend = plot.getPlotItem().legend

    set_plot_legend_visible(plot, False)
    assert not legend.isVisible()

    set_plot_legend_visible(plot, True)
    assert legend.isVisible()


def test_anchor_plot_legend_top_right_sets_legend_anchor():
    _app, plot = _make_plot_with_legend()
    legend = plot.getPlotItem().legend

    anchor_plot_legend_top_right(plot)

    assert getattr(legend, "_GraphicsWidgetAnchor__itemAnchor") == (1, 0)
    assert getattr(legend, "_GraphicsWidgetAnchor__parentAnchor") == (1, 0)
    assert getattr(legend, "_GraphicsWidgetAnchor__offset") == (-10, 10)
