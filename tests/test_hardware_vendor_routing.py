import os
import sys
import types
from pathlib import Path


def test_ideaoptics_driver_path_points_to_project_drivers(monkeypatch):
    from nanosense.core import controller as controller_module
    from nanosense.core.controller import FX2000Controller

    FX2000Controller.disconnect()

    expected_driver_dir = str(Path(controller_module.__file__).resolve().parents[2] / "drivers")
    wrong_driver_dir = str(Path(controller_module.__file__).resolve().parents[1] / "drivers")

    original_sys_path = list(sys.path)
    original_path_env = os.environ.get("PATH")
    sys.path[:] = [p for p in sys.path if p not in {expected_driver_dir, wrong_driver_dir}]

    fake_clr = types.SimpleNamespace(AddReference=lambda _name: None)

    class FakeWrapper:
        def OpenAllSpectrometers(self):
            return 1

        def getName(self, _index):
            return "Fake IdeaOptics"

        def getSerialNumber(self, _index):
            return "FAKE-SN"

        def getWavelengths(self, _index):
            return [500.0, 600.0]

        def closeAllSpectrometers(self):
            pass

    fake_ideaoptics = types.ModuleType("IdeaOptics")
    fake_ideaoptics.Wrapper = FakeWrapper

    monkeypatch.setitem(sys.modules, "clr", fake_clr)
    monkeypatch.setitem(sys.modules, "IdeaOptics", fake_ideaoptics)

    try:
        instance = FX2000Controller.connect(use_real_hardware=True, hardware_vendor="ideaoptics")
        assert instance is not None
        assert expected_driver_dir in sys.path
        assert wrong_driver_dir not in sys.path
    finally:
        FX2000Controller.disconnect()
        sys.path[:] = original_sys_path
        if original_path_env is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = original_path_env


def test_show_welcome_screen_normalizes_mock_vendor_when_real_hardware_requested():
    import main

    use_real, vendor = main._resolve_welcome_hardware_selection(
        use_real_hardware=True,
        hardware_vendor="mock",
        settings={},
    )

    assert use_real is True
    assert vendor == "ideaoptics"


def test_welcome_retranslate_preserves_selected_ocean_vendor():
    from nanosense.gui.welcome_widget import WelcomeWidget

    class FakeCombo:
        def __init__(self):
            self.items = ["Real Hardware (IdeaOptics)", "Real Hardware (Ocean Optics)", "Mock API"]
            self.index = 1

        def count(self):
            return len(self.items)

        def currentIndex(self):
            return self.index

        def blockSignals(self, _blocked):
            pass

        def clear(self):
            self.items = []

        def addItem(self, label):
            self.items.append(label)

        def setCurrentIndex(self, index):
            self.index = index

    class FakeLabel:
        def setText(self, _text):
            pass

    fake = types.SimpleNamespace()
    fake.hardware_mode_combo = FakeCombo()
    fake._hardware_mode_items = [
        ("Real Hardware (IdeaOptics)", "ideaoptics"),
        ("Real Hardware (Ocean Optics)", "ocean"),
        ("Mock API", "mock"),
    ]
    fake._current_vendor_cache = "ideaoptics"
    fake.title_label = FakeLabel()
    fake.subtitle_label = FakeLabel()
    fake.buttons_info = []
    fake.mode_buttons = []
    fake.setWindowTitle = lambda _title: None
    fake.tr = lambda text: text
    fake._current_vendor = types.MethodType(WelcomeWidget._current_vendor, fake)

    WelcomeWidget._retranslate_ui(fake)

    assert fake._current_vendor() == "ocean"


def test_initial_welcome_screen_reads_saved_hardware_vendor():
    import main

    use_real, vendor = main._resolve_welcome_hardware_selection(
        use_real_hardware=None,
        hardware_vendor=None,
        settings={"use_real_hardware": True, "hardware_vendor": "ocean"},
    )

    assert use_real is True
    assert vendor == "ocean"
