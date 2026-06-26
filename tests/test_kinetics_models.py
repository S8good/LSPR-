import numpy as np

from nanosense.algorithms.kinetics import (
    association_model,
    dissociation_model,
    fit_association,
    fit_dissociation,
    fit_global_kinetics,
    fit_interval,
)


def test_fit_association_recovers_kobs_and_fit_statistics():
    t = np.linspace(0.0, 120.0, 80)
    signal = association_model(t, dlam_eq=6.5, k_obs=0.035, baseline=0.2)

    result = fit_association(t, signal)

    assert result is not None
    assert result["model"] == "association"
    assert result["k_obs"] == np.float64(result["k_obs"])
    assert np.isclose(result["k_obs"], 0.035, rtol=0.03)
    assert np.isclose(result["dlam_eq"], 6.5, rtol=0.03)
    assert result["r2"] > 0.999
    assert result["residuals"].shape == signal.shape
    assert len(result["t_fit"]) == 200
    assert len(result["y_fit"]) == 200


def test_fit_dissociation_recovers_koff_and_fit_statistics():
    t = np.linspace(200.0, 340.0, 90)
    signal = dissociation_model(t - t[0], dlam_0=5.2, k_off=0.024, baseline=0.35)

    result = fit_dissociation(t, signal)

    assert result is not None
    assert result["model"] == "dissociation"
    assert np.isclose(result["k_off"], 0.024, rtol=0.03)
    assert np.isclose(result["dlam_0"], 5.2, rtol=0.03)
    assert result["r2"] > 0.999
    assert result["residuals"].shape == signal.shape
    assert len(result["t_fit"]) == 200
    assert len(result["y_fit"]) == 200


def test_fit_interval_auto_selects_association_or_dissociation():
    t = np.linspace(0.0, 100.0, 70)
    rising = association_model(t, dlam_eq=3.0, k_obs=0.05, baseline=0.1)
    falling = dissociation_model(t, dlam_0=3.0, k_off=0.05, baseline=0.1)

    assert fit_interval(t, rising, model="auto")["model"] == "association"
    assert fit_interval(t, falling, model="auto")["model"] == "dissociation"


def test_fit_global_kinetics_recovers_ka_kd_and_kd_ratio():
    concentrations = np.array([1.0e-9, 2.0e-9, 5.0e-9, 10.0e-9])
    k_a = 1.2e5
    k_d = 0.0025
    k_obs_values = k_a * concentrations + k_d

    result = fit_global_kinetics(concentrations, k_obs_values)

    assert result is not None
    assert result["model"] == "global"
    assert np.isclose(result["k_a"], k_a, rtol=1e-9)
    assert np.isclose(result["k_d"], k_d, rtol=1e-9)
    assert np.isclose(result["K_D"], k_d / k_a, rtol=1e-9)
    assert result["r2"] > 0.999999
    assert len(result["c_fit"]) == 100
    assert len(result["y_fit"]) == 100
