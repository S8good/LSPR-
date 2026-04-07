# LSPR AI Workbench Task 2-3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add LSPR AI workbench settings plus the first usable GUI flow for opening the workbench, loading a single spectrum, and showing a comparison tab.

**Architecture:** Keep task 1's service layer as the only AI integration point. Add a small workbench window with two tabs and wire it into the existing menu and main window. Store workbench defaults in the existing config system and expose them through the existing settings dialog.

**Tech Stack:** PyQt5, pyqtgraph, existing `nanosense` GUI patterns, pytest

---

### Task 1: Add failing smoke tests for settings and workbench shell

**Files:**
- Create: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/tests/test_lspr_ai_workbench_plan_smoke.py`
- Modify: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/tests/test_menu_bar.py`

- [ ] Add tests that assert default settings include the new `lspr_*` keys.
- [ ] Add tests that assert `settings_dialog.py` defines an `LSPR AI` section and persists the new keys.
- [ ] Add tests that assert `menu_bar.py` exposes `lspr_ai_workbench_action`.
- [ ] Add tests that assert `main_window.py` wires a workbench open method and preload handling.
- [ ] Add tests that assert `lspr_ai_workbench.py` defines the `Single Spectrum` and `Spectrum Comparison` tabs.
- [ ] Run: `pytest tests/test_menu_bar.py tests/test_lspr_ai_workbench_plan_smoke.py -q`

### Task 2: Implement settings defaults and settings dialog UI

**Files:**
- Modify: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/nanosense/utils/config_manager.py`
- Modify: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/nanosense/gui/settings_dialog.py`

- [ ] Add the new `lspr_*` settings to `get_default_settings()`.
- [ ] Extend the settings dialog with an `LSPR AI` group containing root path, default model, artifact dir, batch export dir, and digital twin overlay.
- [ ] Persist the new values through `get_settings()`.
- [ ] Run: `pytest tests/test_lspr_ai_workbench_plan_smoke.py -q`

### Task 3: Implement workbench shell and main window wiring

**Files:**
- Create: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/nanosense/gui/lspr_result_summary_widget.py`
- Create: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/nanosense/gui/lspr_spectrum_comparison_widget.py`
- Create: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/nanosense/gui/lspr_single_prediction_widget.py`
- Create: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/nanosense/gui/lspr_ai_workbench.py`
- Modify: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/nanosense/gui/menu_bar.py`
- Modify: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/nanosense/gui/main_window.py`

- [ ] Add the new analysis menu action.
- [ ] Add a reusable workbench window reference in `MainWindow`.
- [ ] Implement `_open_lspr_ai_workbench(...)` and preload routing.
- [ ] Build a minimal workbench with two tabs and service-backed single-spectrum prediction.
- [ ] Route prediction output into the comparison tab.
- [ ] Run: `pytest tests/test_menu_bar.py tests/test_lspr_ai_workbench_plan_smoke.py tests/test_lspr_ai_service.py -q`

### Task 4: Verify and checkpoint

**Files:**
- Modify: `C:/Users/Spc/.config/superpowers/worktrees/LSPR_code/feature-lspr-task1-bridge/docs/lspr_ai_workbench/2026-04-02-task1-progress-checklist.md`

- [ ] Update the progress doc to note task 2/3 scope has started.
- [ ] Run the focused test set again.
- [ ] Commit the task 2/3 increment.
