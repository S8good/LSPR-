from types import MethodType, SimpleNamespace

import numpy as np

from nanosense.gui.measurement_widget import MeasurementWidget


class _Value:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class _Combo:
    def __init__(self, text, data=None):
        self._text = text
        self._data = data

    def currentText(self):
        return self._text

    def currentData(self):
        return self._data


class _Check:
    def __init__(self, checked):
        self._checked = checked

    def isChecked(self):
        return self._checked


def _fake_measurement_widget():
    fake = SimpleNamespace()
    fake.mode_name = "Raman"
    fake.controller = SimpleNamespace(
        serial_number="SN-RAMAN",
        name="OceanDirect-QEPro",
        hardware_vendor="ocean",
    )
    fake.integration_time_spinbox = _Value(250)
    fake.scans_to_average_spinbox = _Value(8)
    fake.excitation_wavelength_spinbox = _Value(785.0)
    fake.laser_power_spinbox = _Value(35.0)
    fake.laser_button = _Check(True)
    fake.smooth_method_combo = _Combo("Savitzky-Golay")
    fake.smoothing_window_spinbox = _Value(11)
    fake.poly_order_spinbox = _Value(3)
    fake.baseline_enabled_checkbox = _Check(True)
    fake.baseline_algorithm_combo = _Combo("ALS")
    fake.baseline_lambda_spinbox = _Value(1000000.0)
    fake.baseline_p_spinbox = _Value(0.01)
    fake.baseline_niter_spinbox = _Value(10)
    fake.peak_method_combo = _Combo("Highest Point", "highest_point")
    fake.peak_height_spinbox = _Value(12.5)
    fake.analysis_start_spinbox = _Value(400.0)
    fake.analysis_end_spinbox = _Value(1800.0)
    fake.kinetics_baseline_value = None
    fake.rayleigh_remove_checkbox = _Check(True)
    fake.rayleigh_cutoff_spinbox = _Value(200.0)
    fake.fluorescence_subtract_checkbox = _Check(True)
    fake.normalization_combo = _Combo("Peak Height Normalization")
    fake.wavenumber_toggle = _Check(True)
    fake.latest_peak_metrics = {
        "axis": "raman_shift_cm^-1",
        "peaks": [
            {"position": 520.0, "intensity": 12.0, "fwhm": 8.0},
            {"position": 1001.0, "intensity": 25.0, "fwhm": 11.0},
        ],
    }
    fake._build_raman_processing_metadata = MethodType(
        MeasurementWidget._build_raman_processing_metadata,
        fake,
    )
    return fake


def test_raman_instrument_metadata_includes_acquisition_context():
    fake = _fake_measurement_widget()

    metadata = MeasurementWidget._build_instrument_metadata(fake)

    assert metadata["device_serial"] == "SN-RAMAN"
    assert metadata["integration_time_ms"] == 250.0
    assert metadata["averaging"] == 8
    assert metadata["config"]["spectrometer_name"] == "OceanDirect-QEPro"
    assert metadata["config"]["hardware_vendor"] == "ocean"
    assert metadata["config"]["mode"] == "Raman"
    assert metadata["config"]["excitation_wavelength_nm"] == 785.0
    assert metadata["config"]["laser_power_percent"] == 35.0
    assert metadata["config"]["laser_enabled"] is True


def test_raman_processing_metadata_includes_preprocessing_and_peak_table():
    fake = _fake_measurement_widget()

    metadata = MeasurementWidget._build_processing_metadata(fake, "Result")
    params = metadata["parameters"]

    assert params["mode"] == "Raman"
    assert params["spectrum_role"] == "Result"
    assert params["raman"]["rayleigh_scattering_removal"] is True
    assert params["raman"]["rayleigh_cutoff_cm^-1"] == 200.0
    assert params["raman"]["fluorescence_background_subtraction"] is True
    assert params["raman"]["normalization_method"] == "Peak Height Normalization"
    assert params["raman"]["display_axis"] == "raman_shift_cm^-1"
    assert params["raman"]["peaks"]["count"] == 2
    assert params["raman"]["peaks"]["items"][1]["position"] == 1001.0


def test_save_result_spectrum_returns_saved_file_path(monkeypatch):
    saved = {}

    def fake_save_spectrum(parent, mode_name, x_data, y_data, default_path):
        saved["mode_name"] = mode_name
        saved["x_data"] = list(x_data)
        saved["y_data"] = list(y_data)
        saved["default_path"] = default_path
        return "C:/tmp/raman_result.csv"

    monkeypatch.setattr(
        "nanosense.gui.measurement_widget.save_spectrum",
        fake_save_spectrum,
    )

    fake = SimpleNamespace()
    fake.full_result_x = np.array([400.0, 500.0, 600.0])
    fake.full_result_y = np.array([1.0, 2.0, 3.0])
    fake.analysis_start_spinbox = _Value(450.0)
    fake.analysis_end_spinbox = _Value(650.0)
    fake.app_settings = {"default_save_path": "C:/tmp"}
    fake.mode_name = "Raman"
    fake.db_manager = None
    fake.tr = lambda text: text

    file_path = MeasurementWidget._save_result_spectrum(fake)

    assert file_path == "C:/tmp/raman_result.csv"
    assert saved == {
        "mode_name": "Raman",
        "x_data": [500.0, 600.0],
        "y_data": [2.0, 3.0],
        "default_path": "C:/tmp",
    }
