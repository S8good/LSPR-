import queue
import threading
import time
from collections import deque
from types import SimpleNamespace

import numpy as np

from nanosense.core.spectrum_processor import SpectrumProcessor
from nanosense.gui.measurement_widget import MeasurementWidget
from ocean_direct_api import Wrapper


class _FlakyOceanDevice:
    def __init__(self):
        self.calls = 0

    def get_formatted_spectrum(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("Error: Data transfer error")
        return [1.0, 2.0, 3.0]


class _ThreadTrackedOceanDevice:
    def __init__(self):
        self.active_calls = 0
        self.max_active_calls = 0
        self.call_count = 0

    def get_formatted_spectrum(self):
        self.active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self.active_calls)
        self.call_count += 1
        try:
            time.sleep(0.01)
            return [1.0, 2.0, 3.0]
        finally:
            self.active_calls -= 1


def _make_wrapper_with_device(device):
    wrapper = Wrapper.__new__(Wrapper)
    wrapper._device_ids = [101]
    wrapper._devices = {101: device}
    wrapper._wavelengths_cache = {}
    wrapper._spectrum_retry_delay_s = 0.0
    wrapper._spectrum_retry_count = 1
    return wrapper


def test_ocean_wrapper_retries_transient_data_transfer_error():
    device = _FlakyOceanDevice()
    wrapper = _make_wrapper_with_device(device)

    spectrum = wrapper.getSpectrum(0)

    assert spectrum == [1.0, 2.0, 3.0]
    assert device.calls == 2


def test_ocean_wrapper_serializes_device_reads():
    device = _ThreadTrackedOceanDevice()
    wrapper = _make_wrapper_with_device(device)

    threads = [threading.Thread(target=wrapper.getSpectrum, args=(0,)) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert device.call_count == 5
    assert device.max_active_calls == 1


class _FlakyController:
    def __init__(self, owner):
        self.owner = owner
        self.calls = 0
        self.wavelengths = np.array([500.0, 600.0, 700.0])

    def get_spectrum(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("Error: Data transfer error")
        self.owner.stop_event.set()
        return self.wavelengths, np.array([4.0, 5.0, 6.0])


def test_acquisition_thread_continues_after_spectrum_error():
    fake = SimpleNamespace()
    fake.stop_event = threading.Event()
    fake.controller = _FlakyController(fake)
    fake.is_acquiring = True
    fake.data_queue = queue.Queue(maxsize=10)
    fake.acquisition_error_backoff_s = 0.0
    fake.acquisition_idle_sleep_s = 0.0
    fake.tr = lambda text: text

    MeasurementWidget.acquisition_thread_func(fake)

    assert fake.controller.calls == 2
    assert np.allclose(fake.data_queue.get_nowait(), np.array([4.0, 5.0, 6.0]))


def test_initial_hardware_settings_are_applied_to_controller():
    calls = []
    fake = SimpleNamespace(
        controller=SimpleNamespace(
            set_integration_time=lambda value: calls.append(("integration", value)),
            set_scans_to_average=lambda value: calls.append(("average", value)),
        ),
        integration_time_spinbox=SimpleNamespace(value=lambda: 100),
        scans_to_average_spinbox=SimpleNamespace(value=lambda: 1),
    )

    MeasurementWidget._apply_current_hardware_settings(fake)

    assert calls == [("integration", 100), ("average", 1)]


def _make_average_capture_widget(frames, latest=None):
    processor = SpectrumProcessor(np.array([500.0, 600.0, 700.0]))
    processor.smoothing_method = "No Smoothing"
    if latest is not None:
        processor.latest_signal_spectrum = np.array(latest, dtype=float)
    fake = SimpleNamespace(
        processor=processor,
        recent_signal_frames=deque([np.array(frame, dtype=float) for frame in frames], maxlen=10),
        background_reference_average_count=10,
    )
    fake._average_recent_signal_frames = lambda: MeasurementWidget._average_recent_signal_frames(fake)
    return fake


def test_background_capture_uses_recent_10_frame_average():
    frames = [np.array([float(i), float(i + 1), float(i + 2)]) for i in range(12)]
    fake = _make_average_capture_widget(frames)

    MeasurementWidget._capture_background_average(fake)

    expected = np.mean(np.array(frames[-10:]), axis=0)
    assert np.allclose(fake.processor.background_spectrum, expected)


def test_reference_capture_uses_available_frames_when_less_than_10():
    frames = [
        np.array([1.0, 2.0, 3.0]),
        np.array([3.0, 4.0, 5.0]),
        np.array([5.0, 6.0, 7.0]),
    ]
    fake = _make_average_capture_widget(frames)

    MeasurementWidget._capture_reference_average(fake)

    expected = np.mean(np.array(frames), axis=0)
    assert np.allclose(fake.processor.reference_spectrum, expected)


def test_average_capture_does_not_overwrite_latest_signal():
    fake = _make_average_capture_widget(
        frames=[
            np.array([1.0, 1.0, 1.0]),
            np.array([3.0, 3.0, 3.0]),
        ],
        latest=np.array([9.0, 9.0, 9.0]),
    )

    MeasurementWidget._capture_background_average(fake)

    assert np.allclose(fake.processor.background_spectrum, np.array([2.0, 2.0, 2.0]))
    assert np.allclose(fake.processor.latest_signal_spectrum, np.array([9.0, 9.0, 9.0]))
