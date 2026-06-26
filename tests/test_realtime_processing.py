from nanosense.core.realtime_processing import (
    REALTIME_RESULT_UPDATE_INTERVAL_S,
    should_process_realtime_result,
)


def test_should_process_realtime_result_allows_first_update():
    assert should_process_realtime_result(
        10.0,
        None,
        REALTIME_RESULT_UPDATE_INTERVAL_S,
    ) is True


def test_should_process_realtime_result_throttles_frequent_updates():
    assert should_process_realtime_result(
        10.10,
        10.0,
        REALTIME_RESULT_UPDATE_INTERVAL_S,
    ) is False


def test_should_process_realtime_result_allows_update_after_interval():
    assert should_process_realtime_result(
        10.25,
        10.0,
        REALTIME_RESULT_UPDATE_INTERVAL_S,
    ) is True
