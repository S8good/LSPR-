"""Pure helpers for batch acquisition live preview data."""

import numpy as np


PREVIEW_EMIT_INTERVAL_S = 0.2


def should_emit_preview(now, last_emit, interval=PREVIEW_EMIT_INTERVAL_S):
    """Return True when enough time passed to publish another UI preview."""
    if last_emit is None:
        return True
    return (now - last_emit) >= interval


def calculate_absorbance(signal, background, reference):
    """Compute absorbance from signal, background, and reference spectra."""
    if signal is None or background is None or reference is None:
        return None
    signal = np.array(signal, dtype=float)
    background = np.array(background, dtype=float)
    reference = np.array(reference, dtype=float)
    valid_mask = (
        np.isfinite(signal)
        & np.isfinite(background)
        & np.isfinite(reference)
    )
    if not np.any(valid_mask):
        return None
    absorbance = np.full(signal.shape, np.nan, dtype=float)
    sig_eff = signal[valid_mask] - background[valid_mask]
    ref_eff = reference[valid_mask] - background[valid_mask]
    safe_denominator = np.copy(ref_eff)
    safe_denominator[safe_denominator == 0] = 1e-9
    transmittance = sig_eff / safe_denominator
    transmittance[transmittance <= 0] = 1e-9
    absorbance[valid_mask] = -1 * np.log10(transmittance)
    return absorbance


def _crop_for_result(values, wavelength_mask):
    if values is None:
        return None
    values = np.asarray(values)
    if wavelength_mask is None:
        return values
    return values[wavelength_mask]


def _linear_baseline(values):
    if values.size == 0:
        return values
    x = np.arange(values.size, dtype=float)
    return np.interp(x, [0.0, float(values.size - 1)], [values[0], values[-1]])


def _snip_baseline(values, max_half_window=None):
    """Estimate a simple SNIP-style baseline without external state."""
    if values.size < 3:
        return values.copy()
    baseline = values.astype(float, copy=True)
    if max_half_window is None:
        max_half_window = min(40, max(1, values.size // 2))
    for half_window in range(int(max_half_window), 0, -1):
        if half_window * 2 >= values.size:
            continue
        center = baseline[half_window:-half_window]
        average = (
            baseline[:-2 * half_window]
            + baseline[2 * half_window:]
        ) / 2.0
        baseline[half_window:-half_window] = np.minimum(center, average)
    return baseline


def apply_batch_preprocessing(absorbance, wavelengths, settings):
    """Apply batch smoothing and baseline settings to an absorbance spectrum."""
    processed = np.array(absorbance, dtype=float, copy=True)
    settings = settings or {}

    smoothing_method = settings.get("smoothing_method", "Savitzky-Golay")
    smoothing_window = int(settings.get("smoothing_window", 11))

    if processed.size == 0:
        return processed

    try:
        if smoothing_method == "Savitzky-Golay":
            from scipy.signal import savgol_filter

            smoothing_order = int(settings.get("smoothing_order", 3))
            window = min(smoothing_window, processed.size)
            if window % 2 == 0:
                window -= 1
            if window >= smoothing_order + 2 and window > 2:
                processed = savgol_filter(processed, window, smoothing_order)
        elif smoothing_method == "Moving Average":
            window = min(smoothing_window, processed.size)
            if window % 2 == 0:
                window -= 1
            if window > 1:
                kernel = np.ones(window) / window
                processed = np.convolve(processed, kernel, mode="same")
    except Exception as exc:
        print(f"Smoothing error: {exc}")

    if not settings.get("baseline_enabled", False):
        return processed

    baseline_algorithm = settings.get("baseline_algorithm", "ALS")
    try:
        if baseline_algorithm == "ALS":
            from nanosense.algorithms.preprocessing import baseline_als

            lambda_param = settings.get("baseline_lambda", 5000000)
            p_param = settings.get("baseline_p", 0.001)
            niter = int(settings.get("baseline_niter", 10))
            baseline = baseline_als(
                processed,
                lam=lambda_param,
                p=p_param,
                niter=niter,
            )
        elif baseline_algorithm == "SNIP":
            baseline = _snip_baseline(processed)
        elif baseline_algorithm == "Linear":
            baseline = _linear_baseline(processed)
        else:
            return processed
        processed = processed - baseline
    except Exception as exc:
        print(f"Baseline correction error: {exc}")

    return processed


def build_batch_preview_package(
    *,
    wavelengths,
    live_signal,
    background,
    reference,
    result_wavelengths,
    wavelength_mask,
    all_results,
    preprocess=None,
):
    """Build the live preview payload, including precomputed absorbance."""
    live_result = None
    if result_wavelengths is not None:
        signal_cropped = _crop_for_result(live_signal, wavelength_mask)
        background_cropped = _crop_for_result(background, wavelength_mask)
        reference_cropped = _crop_for_result(reference, wavelength_mask)
        live_result = calculate_absorbance(
            signal_cropped,
            background_cropped,
            reference_cropped,
        )
        if live_result is not None and preprocess is not None:
            live_result = preprocess(live_result, result_wavelengths)

    return {
        "full_wavelengths": wavelengths,
        "live_signal": live_signal,
        "background": background,
        "reference": reference,
        "result_wavelengths": result_wavelengths,
        "live_result": live_result,
        "all_results": all_results,
    }
