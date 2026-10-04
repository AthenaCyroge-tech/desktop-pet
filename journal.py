import json
from datetime import datetime, date
from pathlib import Path


# Saved next to this file so the log stays with the project folder.
LOG_PATH = Path(__file__).resolve().parent / "mood_log.json"

# Words used in the daily sentence for each mood name.
MOOD_VERBS = {
    "panicking": "panicked",
    "sweating": "sweated",
    "sleeping": "fell asleep",
    "happy": "was happy",
}


# Load the list of events from disk. Return [] if the file is missing or broken.
def _read_events():
    if not LOG_PATH.exists():
        return []
    try:
        data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return data


# Write the full event list. We rewrite the file so it stays valid JSON.
def _write_events(events):
    LOG_PATH.write_text(json.dumps(events, indent=2), encoding="utf-8")


# Append one mood change with a local timestamp. Call only when the mood is new.
def log_mood_change(mood):
    events = _read_events()
    events.append(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "mood": mood,
        }
    )
    _write_events(events)


# Turn a count into "1 time" or "3 times".
def _times_phrase(count):
    if count == 1:
        return "1 time"
    return f"{count} times"


# Build a sentence like "Your pet panicked 3 times today".
def daily_summary(day=None):
    if day is None:
        day = date.today()

    counts = {mood: 0 for mood in MOOD_VERBS}
    for event in _read_events():
        timestamp = event.get("timestamp", "")
        mood = event.get("mood")
        try:
            event_day = datetime.fromisoformat(timestamp).date()
        except ValueError:
            continue
        if event_day == day and mood in counts:
            counts[mood] += 1

    parts = []
    for mood, verb in MOOD_VERBS.items():
        count = counts[mood]
        if count > 0:
            parts.append(f"{verb} {_times_phrase(count)}")

    if not parts:
        return "Your pet has no mood changes logged today."

    if len(parts) == 1:
        return f"Your pet {parts[0]} today."
    if len(parts) == 2:
        return f"Your pet {parts[0]} and {parts[1]} today."
    return "Your pet " + ", ".join(parts[:-1]) + f", and {parts[-1]} today."


# Print today's summary from the terminal: python journal.py
if __name__ == "__main__":
    print(daily_summary())
