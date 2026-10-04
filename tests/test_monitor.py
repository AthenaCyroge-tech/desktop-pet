import monitor


# Feed fake CPU readings to get_cpu_average() instead of the real CPU.
def _feed(monkeypatch, values):
    monitor._cpu_history.clear()
    readings = iter(values)
    monkeypatch.setattr(monitor, "get_cpu", lambda: next(readings))


def test_average_of_readings(monkeypatch):
    _feed(monkeypatch, [10, 20, 30])
    monitor.get_cpu_average()
    monitor.get_cpu_average()
    assert monitor.get_cpu_average() == 20


def test_only_last_five_readings_count(monkeypatch):
    _feed(monkeypatch, [100, 0, 0, 0, 0, 0])
    for _ in range(5):
        monitor.get_cpu_average()
    assert monitor.get_cpu_average() == 0     # the 100 has dropped out


def test_single_spike_is_smoothed(monkeypatch):
    _feed(monkeypatch, [10, 10, 10, 10, 100])
    for _ in range(4):
        monitor.get_cpu_average()
    assert monitor.get_cpu_average() < 80     # one spike alone must not mean "sweating"


def test_no_battery_returns_none_pair(monkeypatch):
    monkeypatch.setattr(monitor.psutil, "sensors_battery", lambda: None)
    assert monitor.get_battery() == (None, None)


def test_battery_returns_percent_and_plug_state(monkeypatch):
    class FakeBattery:
        percent = 42
        power_plugged = False

    monkeypatch.setattr(monitor.psutil, "sensors_battery", lambda: FakeBattery())
    assert monitor.get_battery() == (42, False)
