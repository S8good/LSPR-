"""Small helpers for throttling realtime result processing."""


REALTIME_RESULT_UPDATE_INTERVAL_S = 0.2


def should_process_realtime_result(
    now,
    last_processed,
    interval=REALTIME_RESULT_UPDATE_INTERVAL_S,
):
    """Return True when a realtime result recomputation should run."""
    if last_processed is None:
        return True
    return (now - last_processed) >= interval
