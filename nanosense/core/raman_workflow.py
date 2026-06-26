"""Small state helper for the Raman guided workflow."""


def _step(key, label, status, detail, action_enabled):
    return {
        "key": key,
        "label": label,
        "status": status,
        "detail": detail,
        "action_enabled": action_enabled,
    }


def build_raman_workflow_steps(
    *,
    background_ready,
    laser_enabled,
    acquisition_running,
    result_ready,
    peaks_ready,
    saved,
):
    """Return ordered Raman workflow step state dictionaries."""
    background_status = "done" if background_ready else "pending"
    laser_status = "done" if laser_enabled else "pending"

    sample_blocked = not (background_ready and laser_enabled)
    if result_ready:
        sample_status = "done"
    elif sample_blocked:
        sample_status = "blocked"
    else:
        sample_status = "pending" if not acquisition_running else "done"

    if peaks_ready:
        peaks_status = "done"
    elif result_ready:
        peaks_status = "pending"
    else:
        peaks_status = "blocked"

    if saved:
        save_status = "done"
    elif result_ready and peaks_ready:
        save_status = "pending"
    else:
        save_status = "blocked"

    return [
        _step(
            "background",
            "Capture Background",
            background_status,
            "Acquire dark/background spectrum",
            True,
        ),
        _step(
            "laser",
            "Enable Laser",
            laser_status,
            "Confirm laser safety before measuring",
            not laser_enabled,
        ),
        _step(
            "sample",
            "Acquire Sample",
            sample_status,
            "Start live Raman sample acquisition",
            not sample_blocked and not acquisition_running and not result_ready,
        ),
        _step(
            "peaks",
            "Convert & Find Peaks",
            peaks_status,
            "Switch to Raman shift and detect peaks",
            result_ready and not peaks_ready,
        ),
        _step(
            "save",
            "Save Result",
            save_status,
            "Save spectrum with Raman metadata",
            result_ready and peaks_ready and not saved,
        ),
    ]
