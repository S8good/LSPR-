from dataclasses import dataclass

import pyqtgraph as pg


@dataclass(frozen=True)
class PlotTheme:
    name: str
    background: str
    foreground: str
    text: str
    title: str
    axis: str
    grid_alpha: float
    border: str
    legend_background: str
    legend_border: str


_LIGHT_THEME = PlotTheme(
    name="light",
    background="#F5F7FA",
    foreground="#111827",
    text="#111827",
    title="#1F2937",
    axis="#374151",
    grid_alpha=0.18,
    border="#CBD5E1",
    legend_background="#FFFFFF",
    legend_border="#CBD5E1",
)

_DARK_THEME = PlotTheme(
    name="dark",
    background="#1F2735",
    foreground="#E2E8F0",
    text="#E2E8F0",
    title="#E2E8F0",
    axis="#90A4AE",
    grid_alpha=0.18,
    border="#39475A",
    legend_background="#1A202C",
    legend_border="#4A5568",
)


def normalize_theme(theme=None):
    return "light" if str(theme).lower() == "light" else "dark"


def get_plot_theme(theme=None):
    return _LIGHT_THEME if normalize_theme(theme) == "light" else _DARK_THEME


def configure_pyqtgraph_theme(theme=None):
    palette = get_plot_theme(theme)
    pg.setConfigOption("background", palette.background)
    pg.setConfigOption("foreground", palette.foreground)
    return palette


def _style_axis(axis_item, palette):
    axis_item.setPen(pg.mkPen(palette.axis, width=1))
    axis_item.setTextPen(pg.mkPen(palette.text))
    axis_item.setStyle(tickLength=6)

    label_text = getattr(axis_item, "labelText", "")
    label_units = getattr(axis_item, "labelUnits", "")
    if label_text:
        axis_item.setLabel(label_text, units=label_units, color=palette.text)


def style_plot_legend(plot_widget, theme=None):
    palette = get_plot_theme(theme)
    legend = plot_widget.getPlotItem().legend
    if not legend:
        return None

    anchor_plot_legend_top_right(plot_widget)

    if hasattr(legend, "setBrush"):
        legend.setBrush(pg.mkBrush(palette.legend_background))
    if hasattr(legend, "setPen"):
        legend.setPen(pg.mkPen(palette.legend_border))

    for _sample, label in legend.items:
        text = getattr(label, "text", "")
        if text:
            label.setText(text, color=palette.text)
    return legend


def anchor_plot_legend_top_right(plot_widget, offset=(-10, 10)):
    legend = plot_widget.getPlotItem().legend
    if not legend:
        return None
    legend.anchor((1, 0), (1, 0), offset=offset)
    return legend


def set_plot_legend_visible(plot_widget, visible):
    legend = plot_widget.getPlotItem().legend
    if not legend:
        return None
    legend.setVisible(bool(visible))
    return legend


def apply_plot_theme(plot_widget, theme=None):
    palette = get_plot_theme(theme)
    plot_widget.setBackground(palette.background)

    plot_item = plot_widget.getPlotItem()
    plot_item.showGrid(x=True, y=True, alpha=palette.grid_alpha)
    plot_widget.getViewBox().setBorder(pg.mkPen(palette.border, width=1))

    for axis_name in ("left", "bottom", "right", "top"):
        axis_item = plot_item.getAxis(axis_name)
        if axis_item is not None:
            _style_axis(axis_item, palette)

    title_text = getattr(plot_item.titleLabel, "text", "")
    if title_text:
        plot_item.setTitle(title_text, color=palette.title, size="12pt")

    style_plot_legend(plot_widget, theme)
    return palette


def apply_plot_theme_to_widget_tree(root_widget, theme=None):
    palette = get_plot_theme(theme)
    for plot_widget in root_widget.findChildren(pg.PlotWidget):
        apply_plot_theme(plot_widget, palette.name)
    return palette
