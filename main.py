import argparse

from journal import daily_summary, log_mood_change
from monitor import (
    get_battery,
    get_cpu,
    get_cpu_average,
    get_idle_seconds,
    start_idle_listener,
)
from mood import decide_mood
from pet import Pet


# Read command-line flags. --debug turns on keys 1-4 and menu items to force a mood.
def parse_args():
    parser = argparse.ArgumentParser(description="A desktop pet that reacts to system stats.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Click the tree, then press 1-4 to force a mood (0 = real stats). "
             "Also adds force-mood items to the right-click menu.",
    )
    return parser.parse_args()


# Build the pet, start a 1-second update tick, then run the tkinter loop.
def main():
    args = parse_args()
    print(daily_summary())
    pet = Pet(on_mood_change=log_mood_change)
    # None means "use real stats". A string means the user forced that mood.
    forced_mood = {"value": None}

    # Called by debug keys. Stores the forced mood and redraws right away.
    def on_force_mood(mood):
        forced_mood["value"] = mood
        if mood is None:
            print("Debug: using real stats again")
        else:
            print(f"Debug: forcing mood {mood}")
            pet.show_mood(mood)

    if args.debug:
        pet.bind_debug_keys(on_force_mood)
        print("Debug mode: click the tree, then press (or use the right-click menu):")
        print("  1 happy   2 sweating   3 sleeping   4 panicking   0 auto")

    # Read stats, pick a mood, redraw. Schedule the next run with after(), not sleep.
    # Always call show_mood so a 3-second click-boost can expire back to this mood.
    def tick():
        cpu = get_cpu_average()
        battery, plugged_in = get_battery()
        idle = get_idle_seconds()
        if forced_mood["value"] is None:
            mood = decide_mood(cpu, battery, idle, plugged_in)
        else:
            mood = forced_mood["value"]
        pet.show_mood(mood)
        pet.root.after(1000, tick)

    # First cpu_percent() is often 0.0, so take one sample before the loop.
    get_cpu()
    # Start pynput in the background before mainloop, so idle time is tracked
    # without blocking tkinter.
    start_idle_listener()
    tick()
    pet.run()


if __name__ == "__main__":
    main()
