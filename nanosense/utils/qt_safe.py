# nanosense/utils/qt_safe.py
"""
跨线程 worker 安全 emit 工具。

PyQt5 里跑在子线程的 QObject，如果主线程把它 deleteLater 掉，
而 run() 还在跑，再 emit 信号就会抛 RuntimeError 把进程带崩。

把这一对工具混进 worker 类即可统一拦掉。
"""

try:
    from PyQt5 import sip as _sip
except ImportError:  # 旧版 PyQt5 把 sip 放在顶层
    import sip as _sip


def is_alive(qobj) -> bool:
    """C++ 端对象是否还在。worker 跨线程跑，外面 deleteLater 之后必须用这个守卫。"""
    try:
        return not _sip.isdeleted(qobj)
    except Exception:
        return False


def safe_emit(qobj, signal, *args) -> bool:
    """
    只有 C++ 端还活着时才 emit；否则吞掉。
    返回 False 表示 emit 没成功，调用方可以据此跳出循环。
    """
    if not is_alive(qobj):
        return False
    try:
        signal.emit(*args)
        return True
    except RuntimeError:
        return False


class SafeEmitMixin:
    """
    给 QObject 子类混进来，提供 self._is_alive() / self._safe_emit() 方法。
    用法：

        class MyWorker(SafeEmitMixin, QObject):
            done = pyqtSignal()
            def run(self):
                while self._is_alive() and self._is_running:
                    ...
                    if not self._safe_emit(self.done):
                        break

    实现说明：worker 自身被 sip.delete 之后，访问任何 self 属性都会抛
    RuntimeError，所以这里把整个调用都包在 try 里，让调用方拿到 False
    而不是异常。
    """

    def _is_alive(self) -> bool:
        try:
            return is_alive(self)
        except RuntimeError:
            return False

    def _safe_emit(self, signal, *args) -> bool:
        try:
            ok = safe_emit(self, signal, *args)
        except RuntimeError:
            ok = False
        if not ok:
            try:
                self._is_running = False
            except Exception:
                pass
        return ok
