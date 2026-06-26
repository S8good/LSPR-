import numpy as np

from nanosense.algorithms.peak_analysis import (
    calculate_raman_shift,
    raman_shift_to_wavelength,
)


def test_calculate_raman_shift_uses_cm_inverse_units_without_extra_scaling():
    wavelengths = np.array([785.0, 850.0])

    shifts = calculate_raman_shift(wavelengths, excitation_wavelength=785.0)

    assert shifts[0] == 0.0
    np.testing.assert_allclose(shifts[1], 974.1476208317727, rtol=0, atol=1e-9)


def test_raman_shift_to_wavelength_round_trips_nm_values():
    wavelengths = np.array([800.0, 850.0, 900.0])
    shifts = calculate_raman_shift(wavelengths, excitation_wavelength=785.0)

    round_tripped = raman_shift_to_wavelength(shifts, excitation_wavelength=785.0)

    np.testing.assert_allclose(round_tripped, wavelengths, rtol=0, atol=1e-9)
