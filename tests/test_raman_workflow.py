from nanosense.core.raman_workflow import build_raman_workflow_steps


def test_raman_workflow_marks_required_steps_before_measurement():
    steps = build_raman_workflow_steps(
        background_ready=False,
        laser_enabled=False,
        acquisition_running=False,
        result_ready=False,
        peaks_ready=False,
        saved=False,
    )

    by_key = {step["key"]: step for step in steps}

    assert by_key["background"]["status"] == "pending"
    assert by_key["laser"]["status"] == "pending"
    assert by_key["sample"]["status"] == "blocked"
    assert by_key["peaks"]["status"] == "blocked"
    assert by_key["save"]["status"] == "blocked"


def test_raman_workflow_advances_when_signal_result_and_peaks_exist():
    steps = build_raman_workflow_steps(
        background_ready=True,
        laser_enabled=True,
        acquisition_running=True,
        result_ready=True,
        peaks_ready=True,
        saved=False,
    )

    by_key = {step["key"]: step for step in steps}

    assert by_key["background"]["status"] == "done"
    assert by_key["laser"]["status"] == "done"
    assert by_key["sample"]["status"] == "done"
    assert by_key["peaks"]["status"] == "done"
    assert by_key["save"]["status"] == "pending"


def test_raman_workflow_reports_complete_after_save():
    steps = build_raman_workflow_steps(
        background_ready=True,
        laser_enabled=True,
        acquisition_running=False,
        result_ready=True,
        peaks_ready=True,
        saved=True,
    )

    assert all(step["status"] == "done" for step in steps)


def test_raman_workflow_exposes_action_enabled_flags():
    steps = build_raman_workflow_steps(
        background_ready=True,
        laser_enabled=False,
        acquisition_running=False,
        result_ready=False,
        peaks_ready=False,
        saved=False,
    )

    by_key = {step["key"]: step for step in steps}

    assert by_key["background"]["action_enabled"] is True
    assert by_key["laser"]["action_enabled"] is True
    assert by_key["sample"]["action_enabled"] is False
    assert by_key["peaks"]["action_enabled"] is False
    assert by_key["save"]["action_enabled"] is False
