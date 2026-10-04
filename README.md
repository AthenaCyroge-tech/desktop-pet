# 🍎 Desktop Pet: The Apple Tree

![tests](https://github.com/AthenaCyroge-tech/desktop-pet/actions/workflows/tests.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.10--3.12-blue)

A tiny apple tree that lives on your screen and reacts to your computer in real time. When your laptop is healthy, the tree is happy. When it struggles, the tree suffers.

It sits in a borderless, transparent, always-on-top window. The tree is drawn with Tkinter Canvas shapes, so there are no image files.


## What it does

| Mood | Trigger | What the tree does |
|---|---|---|
| 😊 Happy | Everything normal | Smiling face, red apples, gentle sway, occasional blink |
| 😴 Sleeping | No keyboard or mouse for 2+ minutes | Eyes close, "z" floats up, apples fall one by one |
| 🥵 Sweating | CPU above 80% | Apples slowly rot, leaves turn yellow, flies buzz around |
| 😱 Panicking | Battery below 15% and unplugged | Tree shakes and drops its apples fast |

When things calm down, the apples grow back. A speech bubble pops up on each mood change, and every change is logged so you get a daily summary.

**Controls:** drag the tree to move it, click it to cheer it up for 3 seconds, right-click for the menu (Quit).

## How it works

Every second, `main.py` runs a tick scheduled with `root.after(1000, ...)`. That timer does not freeze the window (unlike `time.sleep`).

Each tick:

1. **`monitor.py`** reads CPU percent (averaged over the last 5 samples), battery percent and plug state, and idle seconds.
2. **`mood.py`** turns those numbers into one mood, in this priority order:
   - **panicking**: battery below 15% and not plugged in
   - **sweating**: CPU above 80%
   - **sleeping**: no keyboard or mouse for more than 120 seconds
   - **happy**: none of the above
3. **`pet.py`** passes the mood to the tree and shows a speech bubble if it changed.
4. **`tree.py`** animates about 20 frames per second: gravity for falling apples, a slow color blend for rotting, sway and shake.
5. **`journal.py`** appends each mood change to `mood_log.json`. On startup the app prints a summary like `Your pet panicked 3 times today.`

### Design decisions

- **Logic is separate from the UI.** `mood.py`, `monitor.py` and `journal.py` don't touch the window, and `tree.py` only draws on a canvas it is given. That is why most of the code is unit tested without opening a window.
- **Priority order with early returns.** If several conditions are true at once, the most urgent one wins (battery, then CPU, then idle). There is a test for the case where all three are true.
- **Smoothing.** A single CPU spike would make the tree flicker between moods, so readings are averaged over 5 samples.
- **Gradual rot.** Rot rises 0.01 per frame while the CPU is overloaded and falls when it isn't, so a short burst doesn't ruin the tree.
- **Idle detection with pynput.** Global keyboard and mouse listeners run on daemon background threads and only record a timestamp, so they never block Tkinter.
- **Always on top.** Tkinter's `-topmost` flag is unreliable on borderless windows, so on Windows the app also calls `SetWindowPos` every 200 ms. It pauses this while the right-click menu is open so the tree doesn't cover the menu.

## Install and run

Requires Python 3.10 to 3.12. `tkinter` ships with the standard Python installer (on Linux: `sudo apt install python3-tk`).

```bash
git clone https://github.com/AthenaCyroge-tech/desktop-pet.git
cd desktop-pet
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Useful extras:

```bash
python main.py --debug      # keys 1-4 force a mood, 0 = real stats; also adds items to the right-click menu
python journal.py           # print today's summary
python monitor.py           # print raw stats once per second
```

### Try each mood

- **Easiest:** run with `--debug`, then right-click the tree and pick *Force sweating*, *Force sleeping*, etc.
- **Sweating for real:** open 3 or 4 terminals and run `python -c "while True: pass"` in each. Stop with `Ctrl + C`.
- **Sleeping for real:** leave the keyboard and mouse alone for 2 minutes.
- **Panicking for real:** needs a laptop under 15% battery and unplugged. Desktop PCs have no battery, so use the debug menu.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The tests cover:

- mood priority, exact threshold values (80 CPU, 120 idle, 15 battery), desktops without a battery, and all three conditions at once
- the tree animation: apples fall and land, panic drops faster than sleep, apples regrow, rot builds slowly and heals
- the CPU smoothing and battery reading
- the daily summary, including singular and plural wording, other days, and a corrupted log file

They run automatically on every push with GitHub Actions.

## Project structure

```
desktop-pet/
├── main.py              # starts the app and runs the 1-second update tick
├── pet.py               # window: always on top, drag, click, speech bubble, menu
├── tree.py              # tree animation state and drawing
├── monitor.py           # reads CPU, battery, idle time
├── mood.py              # stats -> mood (pure logic)
├── journal.py           # mood history log and daily summary
├── tests/
├── requirements.txt
└── requirements-dev.txt
```

## Limitations

- The see-through background and the always-on-top fix use Windows APIs. On macOS and Linux the app runs, but the background won't be transparent.
- Fullscreen apps (games, fullscreen video) can still cover the tree. The OS doesn't allow anything above them.
- On macOS, pynput needs Accessibility permission for idle detection.
- Desktop PCs have no battery, so *panicking* is only reachable through `--debug`.

## Future: AI personality

The tree already has a few canned speech-bubble lines ("CPU is cooking"). A later version could give it a real personality:

- Send recent stats and the history in `mood_log.json` to a local or cloud language model.
- Let the model write the bubble line in the tree's voice, falling back to the built-in lines if the API is down.
- Keep the model call off the UI thread (same idea as pynput: never block `mainloop`).
- Make it opt-in so the tree stays fully offline by default.

## License

MIT
