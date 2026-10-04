import threading
import time

import psutil

# Stores the most recent CPU percents so we can average them.
# We keep this list at module level so it survives between function calls.
_cpu_history = []
_MAX_CPU_READINGS = 5

# Last time the user typed or moved the mouse. monotonic() is a timer
# that does not jump if the system clock is changed.
_last_activity = time.monotonic()
_activity_lock = threading.Lock()
_listeners_started = False


# Read the current CPU usage as a percent (0 to 100).
# interval=None so this returns immediately and does not freeze the app.
def get_cpu():
    return psutil.cpu_percent(interval=None)


# Read battery percent and whether the charger is plugged in.
# Desktops often have no battery, so psutil returns None and we return (None, None).
def get_battery():
    battery = psutil.sensors_battery()
    if battery is None:
        return (None, None)
    return (battery.percent, battery.power_plugged)


# Called from pynput's background threads on any keyboard or mouse event.
def _mark_activity(*args, **kwargs):
    global _last_activity
    with _activity_lock:
        _last_activity = time.monotonic()


# Start global mouse and keyboard listeners on background threads.
# listener.start() returns right away. listener.join() would freeze tkinter.
def start_idle_listener():
    global _listeners_started
    if _listeners_started:
        return
    _listeners_started = True
    _mark_activity()

    # Imported here, not at the top, so tests and CI can import this file
    # on machines with no display (pynput needs one).
    from pynput import keyboard, mouse

    mouse_listener = mouse.Listener(
        on_move=_mark_activity,
        on_click=_mark_activity,
        on_scroll=_mark_activity,
    )
    keyboard_listener = keyboard.Listener(
        on_press=_mark_activity,
        on_release=_mark_activity,
    )
    # Daemon threads stop when the main window closes, so they cannot hang the app.
    mouse_listener.daemon = True
    keyboard_listener.daemon = True
    mouse_listener.start()
    keyboard_listener.start()


# Seconds since the last keyboard or mouse activity.
# Starts the listener on first use so a forgotten start() still works.
def get_idle_seconds():
    start_idle_listener()
    with _activity_lock:
        last = _last_activity
    return time.monotonic() - last


# Keep the last 5 CPU readings and return their average.
# Averaging smooths spikes so the pet does not flicker between moods every second.
def get_cpu_average():
    reading = get_cpu()
    _cpu_history.append(reading)
    if len(_cpu_history) > _MAX_CPU_READINGS:
        _cpu_history.pop(0)
    return sum(_cpu_history) / len(_cpu_history)


# Print stats once per second so you can check the values in a terminal.
if __name__ == "__main__":
    print("Reading system stats. Press Ctrl+C to stop.")
    # First cpu_percent() is often 0.0, so take one extra reading before the loop.
    get_cpu()
    while True:
        cpu = get_cpu()
        cpu_avg = get_cpu_average()
        percent, plugged_in = get_battery()
        idle = get_idle_seconds()
        print(
            f"cpu={cpu:.1f}%  cpu_avg={cpu_avg:.1f}%  "
            f"battery={percent}  plugged_in={plugged_in}  idle={idle}s"
        )
        time.sleep(1)
