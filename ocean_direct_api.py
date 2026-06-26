"""OceanDirect 光谱仪 Wrapper 适配层

将海洋光学 OceanDirect SDK 封装成与 IdeaOptics.Wrapper 相同形态的接口，
这样 FX2000Controller 不需要为新厂商写第二套调用代码。

暴露的方法（与 IdeaOptics.Wrapper 对齐）：
    OpenAllSpectrometers() -> int
    closeAllSpectrometers()
    getName(index) -> str
    getSerialNumber(index) -> str
    getWavelengths(index) -> list[float]
    setIntegrationTime(index, time_ms)
    setScansToAverage(index, n)
    getSpectrum(index) -> list[float]
"""

import os
import sys
import threading
import time
from pathlib import Path


class Wrapper:
    """OceanDirect 适配器，行为与 IdeaOptics.Wrapper 对齐。"""

    def __init__(self):
        self._api = None
        self._device_ids = []
        self._devices = {}
        self._wavelengths_cache = {}
        self._device_lock = threading.RLock()
        self._spectrum_retry_count = 1
        self._spectrum_retry_delay_s = 0.05

        # 把 drivers/Oceandirect 加入 sys.path 以便 import oceandirect
        driver_dir = Path(__file__).resolve().parent / "drivers" / "Oceandirect"
        driver_dir_str = str(driver_dir)
        if driver_dir_str not in sys.path:
            sys.path.insert(0, driver_dir_str)
        # OceanDirect 的 native dll 也在 oceandirect/lib 下，加到 PATH
        lib_dir = driver_dir / "oceandirect" / "lib"
        if lib_dir.exists():
            os.environ["PATH"] = f"{lib_dir};{os.environ.get('PATH', '')}"

        from oceandirect.OceanDirectAPI import OceanDirectAPI  # noqa: E402

        self._api = OceanDirectAPI()

    # ── 设备管理 ────────────────────────────────────────────

    def OpenAllSpectrometers(self):
        """发现并打开所有海洋光学光谱仪，返回设备数。"""
        try:
            device_count = self._api.find_usb_devices()
            self._device_ids = list(self._api.get_device_ids())
            for did in self._device_ids:
                self._devices[did] = self._api.open_device(did)
            return len(self._device_ids)
        except Exception as e:
            print(f"[OceanDirect] OpenAllSpectrometers 失败: {e}")
            return 0

    def closeAllSpectrometers(self):
        with self._lock():
            for did in list(self._device_ids):
                try:
                    self._api.close_device(did)
                except Exception:
                    pass
            self._device_ids = []
            self._devices = {}
            self._wavelengths_cache = {}

    # ── 信息查询 ────────────────────────────────────────────

    def _device(self, index):
        if index < 0 or index >= len(self._device_ids):
            raise IndexError(f"无效的设备索引: {index}")
        return self._devices[self._device_ids[index]]

    def _lock(self):
        if not hasattr(self, "_device_lock"):
            self._device_lock = threading.RLock()
        return self._device_lock

    def _is_transient_spectrum_error(self, error):
        return "data transfer error" in str(error).lower()

    def getName(self, index):
        with self._lock():
            try:
                dev = self._device(index)
                # OceanDirect SDK 没有统一 getName，用型号或序列号占位
                for attr in ("get_model", "get_device_name"):
                    if hasattr(dev, attr):
                        return str(getattr(dev, attr)())
                return f"OceanDirect-{dev.get_serial_number()}"
            except Exception:
                return "OceanDirect"

    def getSerialNumber(self, index):
        with self._lock():
            try:
                return str(self._device(index).get_serial_number())
            except Exception:
                return ""

    def getWavelengths(self, index):
        with self._lock():
            if index in self._wavelengths_cache:
                return self._wavelengths_cache[index]
            wl = list(self._device(index).get_wavelengths())
            self._wavelengths_cache[index] = wl
            return wl

    # ── 参数设置 ────────────────────────────────────────────

    def setIntegrationTime(self, index, time_ms):
        # IdeaOptics 用毫秒，OceanDirect 用微秒
        with self._lock():
            self._device(index).set_integration_time(int(time_ms) * 1000)

    def setScansToAverage(self, index, num_scans):
        with self._lock():
            dev = self._device(index)
            if hasattr(dev, "set_scans_to_average"):
                dev.set_scans_to_average(int(num_scans))

    # ── 光谱采集 ────────────────────────────────────────────

    def getSpectrum(self, index):
        retry_count = getattr(self, "_spectrum_retry_count", 1)
        retry_delay_s = getattr(self, "_spectrum_retry_delay_s", 0.05)
        for attempt in range(retry_count + 1):
            try:
                with self._lock():
                    return list(self._device(index).get_formatted_spectrum())
            except Exception as exc:
                if attempt >= retry_count or not self._is_transient_spectrum_error(exc):
                    raise
                print(f"[OceanDirect] getSpectrum transient error, retrying: {exc}")
                time.sleep(retry_delay_s)
