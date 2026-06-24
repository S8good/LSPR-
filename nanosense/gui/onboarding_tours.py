# nanosense/gui/onboarding_tours.py
"""
新手指引各场景的步骤脚本工厂。

每个工厂函数接受需要的 host 与上下文控件，返回 step 列表，
然后传给 OnboardingTour 即可。文案都用 QObject.tr() 实时翻译。
"""

from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QCoreApplication

from .onboarding import OnboardingTour


def _tr(text: str) -> str:
    return QCoreApplication.translate("Onboarding", text)


def build_welcome_steps(welcome_widget) -> List[Dict[str, Any]]:
    """欢迎页指引：硬件模式选择 + 进入主程序。"""
    first_button = welcome_widget.mode_buttons[0] if welcome_widget.mode_buttons else None
    return [
        {
            "target": None,
            "title": _tr("Welcome to NanoSense"),
            "text": _tr(
                "This short tour walks you through the key parts of the system. "
                "You can revisit it any time from the Help menu."
            ),
        },
        {
            "target": welcome_widget.hardware_mode_combo,
            "title": _tr("Choose hardware mode"),
            "text": _tr(
                "Switch between Real Hardware and Mock API here. "
                "Use Mock API to explore features without a physical spectrometer."
            ),
        },
        {
            "target": first_button,
            "title": _tr("Pick a measurement mode"),
            "text": _tr(
                "Click any tile (Absorbance, Transmission, Reflectance, Raman, Fluorescence, Color) "
                "to launch the main window in that mode."
            ),
        },
    ]


def build_main_window_steps(main_window) -> List[Dict[str, Any]]:
    """主窗口基本操作指引：采集 / 暗参考 / 寻峰 / 保存 / 切换模式。"""
    page = getattr(main_window, "measurement_page", None)
    menu = main_window.menuBar()

    steps: List[Dict[str, Any]] = [
        {
            "target": None,
            "title": _tr("Main workspace"),
            "text": _tr(
                "The left panel holds controls; the right side shows live spectra. "
                "Let's walk through the most-used buttons."
            ),
        }
    ]

    if page is not None:
        if hasattr(page, "toggle_acq_button"):
            steps.append({
                "target": page.toggle_acq_button,
                "title": _tr("Start / Stop Acquisition"),
                "text": _tr(
                    "Toggle continuous acquisition. The live plot updates as data streams in."
                ),
            })
        if hasattr(page, "capture_dark_button"):
            steps.append({
                "target": page.capture_dark_button,
                "title": _tr("Capture Dark"),
                "text": _tr(
                    "Block the light path and click here to record a dark reference. "
                    "Required for accurate absorbance and transmission."
                ),
            })
        if hasattr(page, "capture_ref_button"):
            steps.append({
                "target": page.capture_ref_button,
                "title": _tr("Capture Reference"),
                "text": _tr(
                    "Record a reference spectrum (e.g. solvent only) before measuring your sample."
                ),
            })
        if hasattr(page, "find_main_peak_button"):
            steps.append({
                "target": page.find_main_peak_button,
                "title": _tr("Find Main Peak"),
                "text": _tr(
                    "One-click resonance peak detection on the current spectrum. "
                    "Shortcut: Ctrl+P."
                ),
            })
        if hasattr(page, "save_data_button"):
            steps.append({
                "target": page.save_data_button,
                "title": _tr("Save Spectrum"),
                "text": _tr(
                    "Save the processed result spectrum to disk. "
                    "Use 'Save All Spectra' to dump every captured frame."
                ),
            })

    if hasattr(menu, "windows_menu"):
        steps.append({
            "target": menu.windows_menu,
            "title": _tr("Switch back to launcher"),
            "text": _tr(
                "Use Windows → Back to Welcome Screen (Ctrl+H) to change measurement mode or hardware."
            ),
        })

    steps.append({
        "target": None,
        "title": _tr("You're set"),
        "text": _tr(
            "That covers the basics. Open Help → Onboarding any time to revisit a topic."
        ),
    })
    return steps


def build_analysis_steps(main_window) -> List[Dict[str, Any]]:
    """分析模块指引：Analysis 菜单中的关键入口。"""
    menu = main_window.menuBar()
    steps: List[Dict[str, Any]] = [
        {
            "target": None,
            "title": _tr("Analysis tools"),
            "text": _tr(
                "The Analysis menu groups all post-processing dialogs. "
                "We'll highlight the most useful ones."
            ),
        }
    ]

    if hasattr(menu, "analysis_menu"):
        steps.append({
            "target": menu.analysis_menu,
            "title": _tr("Analysis menu"),
            "text": _tr(
                "Open this menu to access reports, sensitivity, calibration, "
                "affinity (KD), kinetics linearization, and noise tools."
            ),
        })

    if hasattr(menu, "batch_report_action"):
        steps.append({
            "target": menu.batch_report_action,
            "title": _tr("Generate Analysis Report"),
            "text": _tr(
                "Pick a multi-spectrum file and produce a full report (peaks, shifts, plots) "
                "with one click."
            ),
        })

    if hasattr(menu, "sensitivity_action"):
        steps.append({
            "target": menu.sensitivity_action,
            "title": _tr("Sensitivity Calculation"),
            "text": _tr(
                "Compute refractive-index sensitivity (nm/RIU) from a calibration series."
            ),
        })

    if hasattr(menu, "affinity_action"):
        steps.append({
            "target": menu.affinity_action,
            "title": _tr("Affinity Analysis (KD)"),
            "text": _tr(
                "Fit binding curves and extract dissociation constants from kinetic series."
            ),
        })

    if hasattr(menu, "lspr_ai_workbench_action"):
        steps.append({
            "target": menu.lspr_ai_workbench_action,
            "title": _tr("LSPR AI Workbench"),
            "text": _tr(
                "Run AI-powered prediction, simulation comparison, and digital twin overlays."
            ),
        })

    steps.append({
        "target": None,
        "title": _tr("Tip"),
        "text": _tr(
            "Most analysis dialogs accept either the live spectrum or imported files. "
            "Look for 'Send to ...' buttons in the main view to chain steps."
        ),
    })
    return steps


def build_batch_steps(main_window) -> List[Dict[str, Any]]:
    """批处理流程指引：板布局、批量采集、批量分析、报告。"""
    menu = main_window.menuBar()
    steps: List[Dict[str, Any]] = [
        {
            "target": None,
            "title": _tr("Batch workflow"),
            "text": _tr(
                "Batch mode runs many wells or samples in one go and produces a combined report."
            ),
        }
    ]

    if hasattr(menu, "data_menu"):
        steps.append({
            "target": menu.data_menu,
            "title": _tr("Data menu"),
            "text": _tr(
                "Batch acquisition, batch analysis, Δλ visualization, and the database explorer "
                "all live here."
            ),
        })

    if hasattr(menu, "batch_acquisition_action"):
        steps.append({
            "target": menu.batch_acquisition_action,
            "title": _tr("Batch Acquisition Setup"),
            "text": _tr(
                "Define a plate layout, integration time, and per-well metadata, then run unattended."
            ),
        })

    if hasattr(menu, "data_analysis_action"):
        steps.append({
            "target": menu.data_analysis_action,
            "title": _tr("Batch Data Analysis"),
            "text": _tr(
                "Analyze a folder or database group of spectra in one pass — peaks, shifts, exports."
            ),
        })

    if hasattr(menu, "delta_visualization_action"):
        steps.append({
            "target": menu.delta_visualization_action,
            "title": _tr("Δλ Visualization"),
            "text": _tr(
                "3D / heatmap view of resonance shifts across a plate or kinetic series."
            ),
        })

    if hasattr(menu, "database_explorer_action"):
        steps.append({
            "target": menu.database_explorer_action,
            "title": _tr("Database Explorer"),
            "text": _tr(
                "Browse, query and export every spectrum stored in the local SQLite database."
            ),
        })

    steps.append({
        "target": None,
        "title": _tr("All set"),
        "text": _tr(
            "Pair Batch Acquisition → Batch Data Analysis → Generate Analysis Report "
            "for an end-to-end workflow."
        ),
    })
    return steps


# ---------- helpers to launch tours from outside ----------

def run_welcome_tour(welcome_widget, on_finished=None) -> Optional[OnboardingTour]:
    steps = build_welcome_steps(welcome_widget)
    return _run(welcome_widget, steps, on_finished)


def run_main_window_tour(main_window, on_finished=None) -> Optional[OnboardingTour]:
    steps = build_main_window_steps(main_window)
    return _run(main_window, steps, on_finished)


def run_analysis_tour(main_window, on_finished=None) -> Optional[OnboardingTour]:
    steps = build_analysis_steps(main_window)
    return _run(main_window, steps, on_finished)


def run_batch_tour(main_window, on_finished=None) -> Optional[OnboardingTour]:
    steps = build_batch_steps(main_window)
    return _run(main_window, steps, on_finished)


def _run(host, steps, on_finished):
    if not steps:
        return None
    tour = OnboardingTour(host, steps)
    if on_finished is not None:
        tour.finished.connect(on_finished)
    tour.start()
    return tour
