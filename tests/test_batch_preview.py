import numpy as np

from nanosense.core.batch_preview import (
    PREVIEW_EMIT_INTERVAL_S,
    apply_batch_preprocessing,
    build_batch_preview_package,
    should_emit_preview,
)


def test_should_emit_preview_limits_high_frequency_updates():
    assert should_emit_preview(1.0, None, PREVIEW_EMIT_INTERVAL_S) is True
    assert should_emit_preview(1.10, 1.0, PREVIEW_EMIT_INTERVAL_S) is False
    assert should_emit_preview(1.25, 1.0, PREVIEW_EMIT_INTERVAL_S) is True


def test_build_batch_preview_package_precomputes_processed_live_result():
    wavelengths = np.array([500.0, 600.0, 700.0, 800.0])
    mask = np.array([False, True, True, False])
    live_signal = np.array([10.0, 50.0, 25.0, 10.0])
    background = np.array([1.0, 5.0, 5.0, 1.0])
    reference = np.array([100.0, 95.0, 95.0, 100.0])

    calls = []

    def preprocess(absorbance, result_wavelengths):
        calls.append((absorbance.copy(), result_wavelengths.copy()))
        return absorbance + 1.0

    package = build_batch_preview_package(
        wavelengths=wavelengths,
        live_signal=live_signal,
        background=background,
        reference=reference,
        result_wavelengths=wavelengths[mask],
        wavelength_mask=mask,
        all_results=[],
        preprocess=preprocess,
    )

    expected_raw = -np.log10(
        (live_signal[mask] - background[mask])
        / (reference[mask] - background[mask])
    )

    assert np.allclose(package["live_result"], expected_raw + 1.0)
    assert np.array_equal(package["result_wavelengths"], wavelengths[mask])
    assert len(calls) == 1
    assert np.allclose(calls[0][0], expected_raw)


def test_apply_batch_preprocessing_supports_linear_baseline():
    wavelengths = np.linspace(500.0, 900.0, 21)
    absorbance = np.linspace(0.2, 0.4, 21)
    absorbance[10] += 0.5

    processed = apply_batch_preprocessing(
        absorbance,
        wavelengths,
        {
            "smoothing_method": "No Smoothing",
            "baseline_enabled": True,
            "baseline_algorithm": "Linear",
        },
    )

    assert np.isfinite(processed).all()
    assert abs(processed[0]) < 1e-12
    assert abs(processed[-1]) < 1e-12
    assert processed[10] > 0.45


def test_apply_batch_preprocessing_supports_snip_baseline_without_errors():
    wavelengths = np.linspace(500.0, 900.0, 51)
    absorbance = 0.2 + 0.01 * np.sin(np.linspace(0, 3, 51))
    absorbance[25] += 0.5

    processed = apply_batch_preprocessing(
        absorbance,
        wavelengths,
        {
            "smoothing_method": "No Smoothing",
            "baseline_enabled": True,
            "baseline_algorithm": "SNIP",
        },
    )

    assert processed.shape == absorbance.shape
    assert np.isfinite(processed).all()
