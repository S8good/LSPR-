# Kinetics Monitoring Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the realtime kinetics monitoring window stable during repeated open/close cycles and long Absorbance runs.

**Architecture:** Keep the existing MeasurementWidget -> KineticsWindow signal flow, but fix lifecycle ownership and align kinetics sampling with realtime result recomputation. Keep UI-only fixes local to the kinetics window and use small pure helpers where timing behavior needs tests.

**Tech Stack:** Python, PyQt5, pyqtgraph, pytest.

---

## File Structure

- Modify: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/measurement_widget.py`
  - Disconnect `kinetics_data_updated` when the kinetics window closes.
  - Enforce a kinetics sampling interval no faster than realtime result recomputation.
  - Reset result-processing timing when kinetics starts.
- Modify: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/kinetics_window.py`
  - Remove debug prints.
  - Make “Clear Kinetics Data” update baseline UI and emit baseline reset to the measurement page.
  - Stop redrawing the comparison popout from scratch on every sample.
- Create: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_kinetics_monitoring.py`
  - Qt offscreen smoke tests for signal lifecycle and clear-state behavior.
- Modify: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_realtime_processing.py`
  - Add a helper-level test for the minimum effective kinetics interval, if a helper is introduced.

## Task 1: Fix Kinetics Signal Disconnect On Close

**Files:**
- Modify: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/measurement_widget.py:1678`
- Test: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_kinetics_monitoring.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_kinetics_monitoring.py`:

```python
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PyQt5.QtWidgets import QApplication

from nanosense.core.spectrum_processor import SpectrumProcessor
from nanosense.gui.measurement_widget import MeasurementWidget


class _FakeController:
    def __init__(self):
        self.wavelengths = np.linspace(400.0, 900.0, 16)
        self.serial_number = "KINETICS-TEST"
        self.name = "Fake Spectrometer"
        self.hardware_vendor = "fake"

    def set_integration_time(self, value):
        pass

    def set_scans_to_average(self, value):
        pass

    def get_spectrum(self):
        return self.wavelengths, np.ones_like(self.wavelengths)


def _make_widget():
    app = QApplication.instance() or QApplication([])
    controller = _FakeController()
    processor = SpectrumProcessor(controller.wavelengths)
    widget = MeasurementWidget(controller, processor)
    return app, widget


def test_kinetics_signal_disconnects_when_window_closes():
    app, widget = _make_widget()

    assert widget.receivers(widget.kinetics_data_updated) == 0

    widget._toggle_kinetics_window()
    assert widget.receivers(widget.kinetics_data_updated) == 1

    widget.kinetics_window.close()
    app.processEvents()

    assert widget.kinetics_window is None
    assert widget.receivers(widget.kinetics_data_updated) == 0

    widget.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -q tests/test_kinetics_monitoring.py::test_kinetics_signal_disconnects_when_window_closes
```

Expected: FAIL because `receivers(widget.kinetics_data_updated)` remains `1` after close.

- [ ] **Step 3: Implement disconnect in `_on_kinetics_window_closed`**

In `nanosense/gui/measurement_widget.py`, replace the top of `_on_kinetics_window_closed` with:

```python
    def _on_kinetics_window_closed(self):
        """当动力学窗口关闭时调用的槽函数（无参数）。"""
        window = self.kinetics_window
        if window is not None:
            try:
                self.kinetics_data_updated.disconnect(window.update_kinetics_data)
            except (TypeError, RuntimeError):
                pass
            self.kinetics_baseline_value = window.baseline_peak_wavelength

        self.is_kinetics_monitoring = False
        self.toggle_kinetics_button.setText(self.tr("Start Monitoring"))
        self.kinetics_interval_spinbox.setEnabled(True)
        self.kinetics_window = None
        self.kinetics_start_time = None
        self.kinetics_last_sample_time = None
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest -q tests/test_kinetics_monitoring.py::test_kinetics_signal_disconnects_when_window_closes
```

Expected: PASS.

## Task 2: Align Kinetics Sampling With Result Recompute Rate

**Files:**
- Modify: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/measurement_widget.py:517`
- Test: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_kinetics_monitoring.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kinetics_monitoring.py`:

```python
def test_kinetics_interval_is_not_faster_than_result_processing():
    _app, widget = _make_widget()

    assert widget.kinetics_interval_spinbox.minimum() >= widget.result_processing_interval_s

    widget.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -q tests/test_kinetics_monitoring.py::test_kinetics_interval_is_not_faster_than_result_processing
```

Expected: FAIL because the current minimum is `0.05` while result recomputation is `0.2`.

- [ ] **Step 3: Raise the kinetics minimum interval**

In `nanosense/gui/measurement_widget.py`, change the kinetics interval spinbox setup from:

```python
self.kinetics_interval_spinbox.setRange(0.05, 3600.0)
```

to:

```python
self.kinetics_interval_spinbox.setRange(self.result_processing_interval_s, 3600.0)
```

- [ ] **Step 4: Reset result processing when kinetics starts**

In `_toggle_kinetics_window`, after `self.is_kinetics_monitoring = True`, add:

```python
self.last_result_processing_time = None
```

This makes the next live frame recompute `full_result_y` before the first kinetics sample window.

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
python -m pytest -q tests/test_kinetics_monitoring.py::test_kinetics_interval_is_not_faster_than_result_processing
```

Expected: PASS.

## Task 3: Remove Debug Output From Kinetics Window

**Files:**
- Modify: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/kinetics_window.py:1077`
- Test: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_kinetics_monitoring.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kinetics_monitoring.py`:

```python
from nanosense.gui.kinetics_window import KineticsWindow


def test_kinetics_update_does_not_print_debug_output(capsys):
    app = QApplication.instance() or QApplication([])
    window = KineticsWindow()

    window.update_kinetics_data(
        {
            "result_x": np.array([500.0, 600.0, 700.0]),
            "result_y": np.array([0.1, 0.5, 0.2]),
            "elapsed_time": 1.0,
            "peak_wl": 600.0,
        }
    )

    captured = capsys.readouterr()
    assert "DEBUG" not in captured.out

    window.close()
    app.processEvents()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -q tests/test_kinetics_monitoring.py::test_kinetics_update_does_not_print_debug_output
```

Expected: FAIL because current code prints `DEBUG:` lines.

- [ ] **Step 3: Remove debug prints**

In `nanosense/gui/kinetics_window.py`, delete these print blocks from `update_kinetics_data`:

```python
if result_y is not None:
    print(f"DEBUG: 接收数据 Y值范围: min={np.min(result_y):.4f}, max={np.max(result_y):.4f}, len={len(result_y)}")
```

Delete the first-frame debug prints:

```python
print(f"DEBUG: main_window存在: {self.main_window is not None}")
print(f"DEBUG: measurement_widget存在: {measurement_widget is not None}")
print(f"DEBUG: 分析范围值 = {analysis_start} - {analysis_end}")
print("DEBUG: 无法获取分析范围spinbox")
```

Keep concise state messages only if needed, but do not print once per sample.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest -q tests/test_kinetics_monitoring.py::test_kinetics_update_does_not_print_debug_output
```

Expected: PASS.

## Task 4: Make Clear Kinetics Data Synchronize Baseline State

**Files:**
- Modify: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/kinetics_window.py:1016`
- Test: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_kinetics_monitoring.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kinetics_monitoring.py`:

```python
def test_clear_kinetics_data_resets_and_emits_baseline_state():
    app = QApplication.instance() or QApplication([])
    window = KineticsWindow()
    emitted = []
    window.baseline_changed.connect(emitted.append)

    window.set_baseline_peak_wavelength(650.0)
    window._clear_kinetics_data()

    assert window.baseline_peak_wavelength is None
    assert window.baseline_spinbox.value() == window.baseline_spinbox.minimum()
    assert "Not Set" in window.baseline_status_label.text()
    assert emitted[-1] is None

    window.close()
    app.processEvents()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -q tests/test_kinetics_monitoring.py::test_clear_kinetics_data_resets_and_emits_baseline_state
```

Expected: FAIL because `_clear_kinetics_data` clears the internal baseline but does not update UI or emit `baseline_changed`.

- [ ] **Step 3: Update clear behavior**

In `KineticsWindow._clear_kinetics_data`, after:

```python
self.baseline_peak_wavelength = None
```

add:

```python
block = self.baseline_spinbox.blockSignals(True)
self.baseline_spinbox.setValue(self.baseline_spinbox.minimum())
self.baseline_spinbox.blockSignals(block)
self._update_baseline_status()
self.baseline_changed.emit(None)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest -q tests/test_kinetics_monitoring.py::test_clear_kinetics_data_resets_and_emits_baseline_state
```

Expected: PASS.

## Task 5: Stop Replotting Comparison Popout From Scratch

**Files:**
- Modify: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/kinetics_window.py:972`
- Modify: `C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/kinetics_window.py:1190`
- Test: smoke test command below.

- [ ] **Step 1: Create reusable comparison curves when the popout opens**

In `_open_comparison_popout`, replace the direct `window.plot_widget.plot(...)` calls with:

```python
window.baseline_curve = window.plot_widget.plot(
    pen=pg.mkPen('#1E88E5', width=2),
    name='Baseline'
)
window.realtime_curve = window.plot_widget.plot(
    pen=pg.mkPen('#E53935', width=2),
    name='Real-time'
)

if self.baseline_spectrum_x is not None and self.baseline_spectrum_y is not None:
    window.baseline_curve.setData(self.baseline_spectrum_x, self.baseline_spectrum_y)

if self.realtime_spectrum_x is not None and self.realtime_spectrum_y is not None:
    window.realtime_curve.setData(self.realtime_spectrum_x, self.realtime_spectrum_y)
```

- [ ] **Step 2: Update comparison popout with setData**

In `_refresh_popouts`, replace the `kind == "comparison"` branch with:

```python
elif kind == "comparison":
    if (
        hasattr(window, "baseline_curve")
        and self.baseline_spectrum_x is not None
        and self.baseline_spectrum_y is not None
    ):
        window.baseline_curve.setData(self.baseline_spectrum_x, self.baseline_spectrum_y)
    if (
        hasattr(window, "realtime_curve")
        and self.realtime_spectrum_x is not None
        and self.realtime_spectrum_y is not None
    ):
        window.realtime_curve.setData(self.realtime_spectrum_x, self.realtime_spectrum_y)
```

- [ ] **Step 3: Run Qt smoke test**

Run:

```bash
$env:QT_QPA_PLATFORM='offscreen'; @'
import numpy as np
from PyQt5.QtWidgets import QApplication
from nanosense.gui.kinetics_window import KineticsWindow

app = QApplication.instance() or QApplication([])
window = KineticsWindow()
window.update_kinetics_data({
    "result_x": np.array([500.0, 600.0, 700.0]),
    "result_y": np.array([0.1, 0.5, 0.2]),
    "elapsed_time": 1.0,
    "peak_wl": 600.0,
})
window._open_comparison_popout()
window.update_kinetics_data({
    "result_x": np.array([500.0, 600.0, 700.0]),
    "result_y": np.array([0.2, 0.6, 0.3]),
    "elapsed_time": 2.0,
    "peak_wl": 600.0,
})
assert window._popout_windows
popout = window._popout_windows[0]["window"]
assert hasattr(popout, "baseline_curve")
assert hasattr(popout, "realtime_curve")
window.close()
app.processEvents()
print("comparison popout smoke ok")
'@ | python -
```

Expected: prints `comparison popout smoke ok`.

## Task 6: Verification

**Files:**
- All modified files above.

- [ ] **Step 1: Compile changed modules**

Run:

```bash
python -m py_compile nanosense/gui/measurement_widget.py nanosense/gui/kinetics_window.py nanosense/gui/kinetics_analysis_dialog.py
```

Expected: exit code `0`.

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest -q tests/test_kinetics_monitoring.py tests/test_realtime_processing.py
```

Expected: all tests pass.

- [ ] **Step 3: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass. Known acceptable warning: existing `datetime.utcnow()` deprecation warnings from migration tests.

- [ ] **Step 4: Run diff whitespace check**

Run:

```bash
git diff --check
```

Expected: exit code `0`; CRLF conversion warnings are acceptable.

## Self-Review

- Spec coverage: The plan covers the confirmed P1 lifecycle leak, the confirmed sampling/recompute mismatch, debug output cleanup, baseline clear synchronization, and comparison popout redraw cost.
- Placeholder scan: No TODO/TBD placeholders remain.
- Type consistency: Methods and properties match existing code: `kinetics_data_updated`, `update_kinetics_data`, `result_processing_interval_s`, `baseline_changed`, `_clear_kinetics_data`, `_refresh_popouts`.
