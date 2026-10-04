# CPU must be *above* this percent to count as sweating.
SWEATING_CPU = 80

# Idle time must be *above* this many seconds to count as sleeping.
SLEEPING_IDLE_SECONDS = 120

# Battery must be *below* this percent (and unplugged) to count as panicking.
PANICKING_BATTERY = 15


# Pick one mood from system stats.
# Order matters: panic first, then sweat, then sleep, otherwise happy.
def decide_mood(cpu, battery, idle_seconds, plugged_in):
    # Desktops report battery as None. Skip panic when there is no battery.
    if battery is not None and plugged_in is False and battery < PANICKING_BATTERY:
        return "panicking"

    if cpu > SWEATING_CPU:
        return "sweating"

    if idle_seconds > SLEEPING_IDLE_SECONDS:
        return "sleeping"

    return "happy"
