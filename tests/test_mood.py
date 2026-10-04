from mood import decide_mood


# Helper so each test does not repeat the same four arguments.
def _mood(cpu=0, battery=100, idle_seconds=0, plugged_in=True):
    return decide_mood(cpu, battery, idle_seconds, plugged_in)


# Happy is the default when nothing special is happening.
def test_happy_when_everything_is_fine():
    assert _mood(cpu=20, battery=80, idle_seconds=10, plugged_in=True) == "happy"


# Low battery and unplugged should panic, even if CPU and idle are also high.
def test_panicking_wins_when_two_conditions_are_true():
    assert _mood(cpu=90, battery=10, idle_seconds=200, plugged_in=False) == "panicking"


# High CPU beats idle sleep when both are true (and we are not panicking).
def test_sweating_wins_over_sleeping():
    assert _mood(cpu=90, battery=80, idle_seconds=200, plugged_in=True) == "sweating"


# High idle with a calm CPU should sleep.
def test_sleeping_when_idle_is_high():
    assert _mood(cpu=10, battery=80, idle_seconds=200, plugged_in=True) == "sleeping"


# Desktops have no battery. None must not crash, and must not count as panicking.
def test_battery_none_is_not_panicking():
    assert _mood(cpu=10, battery=None, idle_seconds=0, plugged_in=None) == "happy"


# No battery plus high CPU should still sweat (skip panic, then check CPU).
def test_battery_none_can_still_sweat():
    assert _mood(cpu=90, battery=None, idle_seconds=0, plugged_in=None) == "sweating"


# Plugged in with a low battery is charging, so do not panic.
def test_low_battery_but_plugged_in_is_not_panicking():
    assert _mood(cpu=10, battery=10, idle_seconds=0, plugged_in=True) == "happy"


# CPU exactly 80 is not above 80, so it should not sweat.
def test_cpu_exactly_80_is_not_sweating():
    assert _mood(cpu=80, battery=80, idle_seconds=0, plugged_in=True) == "happy"


# CPU just above 80 should sweat.
def test_cpu_above_80_is_sweating():
    assert _mood(cpu=80.1, battery=80, idle_seconds=0, plugged_in=True) == "sweating"


# Idle exactly 120 is not above 120, so it should not sleep.
def test_idle_exactly_120_is_not_sleeping():
    assert _mood(cpu=10, battery=80, idle_seconds=120, plugged_in=True) == "happy"


# Idle just above 120 should sleep.
def test_idle_above_120_is_sleeping():
    assert _mood(cpu=10, battery=80, idle_seconds=121, plugged_in=True) == "sleeping"


# Battery exactly 15 is not below 15, so it should not panic.
def test_battery_exactly_15_unplugged_is_not_panicking():
    assert _mood(cpu=10, battery=15, idle_seconds=0, plugged_in=False) == "happy"


# Battery just below 15 and unplugged should panic.
def test_battery_below_15_unplugged_is_panicking():
    assert _mood(cpu=10, battery=14.9, idle_seconds=0, plugged_in=False) == "panicking"
