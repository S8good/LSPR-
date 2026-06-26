from nanosense.gui.peak_metrics_dialog import normalize_peak_metric_data


def test_normalize_peak_metric_data_uses_custom_axis_labels_for_raman_peaks():
    normalized = normalize_peak_metric_data(
        {
            "positions": [520.0, 1001.0],
            "heights": [12.0, 25.0],
            "fwhms": [8.0, 11.0],
            "position_label": "Peak Wavenumber (cm^-1)",
            "fwhm_label": "FWHM (cm^-1)",
        }
    )

    assert normalized["position_label"] == "Peak Wavenumber (cm^-1)"
    assert normalized["fwhm_label"] == "FWHM (cm^-1)"
    assert normalized["positions"] == [520.0, 1001.0]


def test_normalize_peak_metric_data_keeps_wavelength_data_backward_compatible():
    normalized = normalize_peak_metric_data(
        {
            "wavelengths": [650.0],
            "heights": [3.0],
            "fwhms": [4.5],
        }
    )

    assert normalized["position_label"] == "Peak Wavelength (nm)"
    assert normalized["fwhm_label"] == "FWHM (nm)"
    assert normalized["positions"] == [650.0]
