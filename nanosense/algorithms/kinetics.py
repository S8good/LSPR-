import numpy as np
from scipy.optimize import curve_fit


def linear_fit(x_values, y_values):
    if len(x_values) < 2:
        return None
    m, b = np.polyfit(x_values, y_values, 1)
    r_squared = np.corrcoef(x_values, y_values)[0, 1] ** 2
    return {'slope': m, 'intercept': b, 'r_squared': r_squared}


def association_model(t, dlam_eq, k_obs, baseline):
    return baseline + dlam_eq * (1.0 - np.exp(-k_obs * t))


def dissociation_model(t, dlam_0, k_off, baseline):
    return baseline + dlam_0 * np.exp(-k_off * t)


def _r_squared(y_values, fitted_values):
    y_values = np.asarray(y_values, dtype=float)
    fitted_values = np.asarray(fitted_values, dtype=float)
    ss_res = float(np.sum((y_values - fitted_values) ** 2))
    ss_tot = float(np.sum((y_values - np.mean(y_values)) ** 2))
    if ss_tot <= 0:
        return 0.0
    return 1.0 - ss_res / ss_tot


def _parameter_errors(covariance, count):
    if covariance is None:
        return np.zeros(count, dtype=float)
    diag = np.diag(covariance)
    return np.sqrt(np.maximum(diag, 0.0))


def _clean_xy(time_data, signal):
    t = np.asarray(time_data, dtype=float)
    y = np.asarray(signal, dtype=float)
    if t.shape != y.shape:
        return None, None

    finite_mask = np.isfinite(t) & np.isfinite(y)
    t = t[finite_mask]
    y = y[finite_mask]
    if t.size == 0:
        return t, y

    order = np.argsort(t)
    return t[order], y[order]


def fit_association(time_data, signal):
    t, y = _clean_xy(time_data, signal)
    if t is None or len(t) < 4:
        return None

    t0 = t[0]
    t_norm = t - t0
    span = max(float(t_norm[-1]), 1e-6)

    p0 = [float(y[-1] - y[0]), 3.0 / span, float(y[0])]
    bounds = ([-np.inf, 1e-9, -np.inf], [np.inf, 1e3, np.inf])

    try:
        popt, pcov = curve_fit(
            association_model,
            t_norm,
            y,
            p0=p0,
            bounds=bounds,
            maxfev=10000,
        )
    except (RuntimeError, ValueError, FloatingPointError):
        return None

    perr = _parameter_errors(pcov, 3)
    fitted = association_model(t_norm, *popt)
    t_fit = np.linspace(t[0], t[-1], 200)
    y_fit = association_model(t_fit - t0, *popt)

    return {
        "model": "association",
        "dlam_eq": float(popt[0]),
        "k_obs": float(popt[1]),
        "baseline": float(popt[2]),
        "dlam_eq_err": float(perr[0]),
        "k_obs_err": float(perr[1]),
        "baseline_err": float(perr[2]),
        "r2": _r_squared(y, fitted),
        "residuals": y - fitted,
        "t_fit": t_fit,
        "y_fit": y_fit,
    }


def fit_dissociation(time_data, signal):
    t, y = _clean_xy(time_data, signal)
    if t is None or len(t) < 4:
        return None

    t0 = t[0]
    t_norm = t - t0
    span = max(float(t_norm[-1]), 1e-6)

    p0 = [float(y[0] - y[-1]), 3.0 / span, float(y[-1])]
    bounds = ([-np.inf, 1e-9, -np.inf], [np.inf, 1e3, np.inf])

    try:
        popt, pcov = curve_fit(
            dissociation_model,
            t_norm,
            y,
            p0=p0,
            bounds=bounds,
            maxfev=10000,
        )
    except (RuntimeError, ValueError, FloatingPointError):
        return None

    perr = _parameter_errors(pcov, 3)
    fitted = dissociation_model(t_norm, *popt)
    t_fit = np.linspace(t[0], t[-1], 200)
    y_fit = dissociation_model(t_fit - t0, *popt)

    return {
        "model": "dissociation",
        "dlam_0": float(popt[0]),
        "k_off": float(popt[1]),
        "baseline": float(popt[2]),
        "dlam_0_err": float(perr[0]),
        "k_off_err": float(perr[1]),
        "baseline_err": float(perr[2]),
        "r2": _r_squared(y, fitted),
        "residuals": y - fitted,
        "t_fit": t_fit,
        "y_fit": y_fit,
    }


def fit_interval(time_data, signal, model="auto"):
    t, y = _clean_xy(time_data, signal)
    if t is None or len(t) < 4:
        return None

    selected_model = model
    if selected_model == "auto":
        selected_model = "association" if y[-1] >= y[0] else "dissociation"

    if selected_model == "association":
        return fit_association(t, y)
    if selected_model == "dissociation":
        return fit_dissociation(t, y)
    return None


def fit_global_kinetics(concentrations, k_obs_values):
    concentrations = np.asarray(concentrations, dtype=float)
    k_obs_values = np.asarray(k_obs_values, dtype=float)
    if concentrations.shape != k_obs_values.shape or len(concentrations) < 2:
        return None

    finite_mask = np.isfinite(concentrations) & np.isfinite(k_obs_values)
    concentrations = concentrations[finite_mask]
    k_obs_values = k_obs_values[finite_mask]
    if len(concentrations) < 2:
        return None

    order = np.argsort(concentrations)
    concentrations = concentrations[order]
    k_obs_values = k_obs_values[order]

    try:
        if len(concentrations) >= 3:
            coeffs, covariance = np.polyfit(concentrations, k_obs_values, 1, cov=True)
            errors = _parameter_errors(covariance, 2)
        else:
            coeffs = np.polyfit(concentrations, k_obs_values, 1)
            errors = np.zeros(2, dtype=float)
    except (ValueError, np.linalg.LinAlgError):
        return None

    k_a = float(coeffs[0])
    k_d = float(coeffs[1])
    fitted = np.polyval(coeffs, concentrations)
    kd_ratio = k_d / k_a if abs(k_a) > 1e-30 else float("inf")
    c_fit = np.linspace(concentrations.min(), concentrations.max(), 100)
    y_fit = np.polyval(coeffs, c_fit)

    return {
        "model": "global",
        "k_a": k_a,
        "k_d": k_d,
        "K_D": float(kd_ratio),
        "k_a_err": float(errors[0]),
        "k_d_err": float(errors[1]),
        "r2": _r_squared(k_obs_values, fitted),
        "c_fit": c_fit,
        "y_fit": y_fit,
    }


def mono_exponential_decay(t, a, b, c):
    return a * np.exp(-b * t) + c


def fit_kinetics_curve(time_data, y_data):
    time_data = np.array(time_data)
    y_data = np.array(y_data)

    if len(time_data) < 3:
        return None

    try:
        # --- 遵照论文公式 4-4 到 4-11 实现初始值估算 ---
        # 1. 估算 c (f(t->inf))
        c_guess = np.mean(y_data[-3:])
        # 2. 估算 a (f(0) - c)
        f0_guess = np.mean(y_data[:3])
        a_guess = f0_guess - c_guess

        # 3. 估算 b (1/tau)
        # 找到y值下降到 (a/e + c) 时的时间点 tau
        target_y = a_guess / np.e + c_guess
        # 找到与target_y最接近的数据点的索引
        tau_index = np.argmin(np.abs(y_data - target_y))
        tau_guess = time_data[tau_index]

        # 避免除以零的边界情况
        if tau_guess == 0:
            tau_guess = time_data[int(len(time_data) / 2)] if len(time_data) > 1 else 1.0

        b_guess = 1 / tau_guess

        initial_guesses = [a_guess, b_guess, c_guess]

        popt, pcov = curve_fit(
            mono_exponential_decay,
            time_data,
            y_data,
            p0=initial_guesses,
            maxfev=5000  # 增加最大迭代次数以提高收敛成功率
        )

        return {'a': popt[0], 'b': popt[1], 'c': popt[2]}

    except RuntimeError:
        return None
    except Exception:
        return None


def calculate_residuals(time_data, y_data, fit_params):
    if fit_params is None:
        return np.zeros_like(y_data)
    fitted_y = mono_exponential_decay(time_data, **fit_params)
    return y_data - fitted_y


def correct_drift(time_data, y_data, baseline_start_time, baseline_end_time):
    time_data, y_data = np.array(time_data), np.array(y_data)
    baseline_mask = (time_data >= baseline_start_time) & (time_data <= baseline_end_time)
    baseline_time, baseline_y = time_data[baseline_mask], y_data[baseline_mask]
    if len(baseline_time) < 2:
        return y_data
    drift_rate, intercept = np.polyfit(baseline_time, baseline_y, 1)
    drift_trend = drift_rate * time_data + intercept
    return y_data - drift_trend
