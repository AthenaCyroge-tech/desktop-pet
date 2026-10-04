import sys
import time
import tkinter as tk

from tree import TRANSPARENT, VIEW_HEIGHT, VIEW_WIDTH, Tree

if sys.platform == "win32":
    import ctypes


# The window is a small speech-bubble strip on top of the tree.
BUBBLE_WIDTH = 104
BUBBLE_HEIGHT = 30
WINDOW_WIDTH = max(VIEW_WIDTH, BUBBLE_WIDTH)
WINDOW_HEIGHT = BUBBLE_HEIGHT + VIEW_HEIGHT

# One animation frame every 50 ms (about 20 per second).
FRAME_MS = 50

# How long the speech bubble stays visible after a mood change or a click.
BUBBLE_SECONDS = 4

# Short line shown in the bubble for each mood.
MOOD_MESSAGES = {
    "happy": "All good!",
    "sweating": "CPU is cooking",
    "sleeping": "Just resting",
    "panicking": "Low battery!",
}
BOOST_MESSAGE = "Thanks!"

# Maps debug number keys to mood names.
DEBUG_KEY_MOODS = {
    "1": "happy",
    "2": "sweating",
    "3": "sleeping",
    "4": "panicking",
}

# How far the mouse can move before a press counts as a drag, not a click.
CLICK_MOVE_LIMIT = 6


class Pet:
    """A small always-on-top window that shows the apple tree and a speech bubble."""

    # Create the window, start the animation, and wire up click, drag and menu.
    # on_mood_change is called with the new mood string whenever it actually changes.
    def __init__(self, on_mood_change=None):
        self.root = tk.Tk()
        self._on_mood_change = on_mood_change
        self._mood = "happy"
        self._last_logged_mood = None
        self._boost_job = None
        self._menu_open = False
        self._bubble_text = None
        self._bubble_until = 0.0
        self._bubble_drawn = None
        self.tree = Tree()
        self._make_window()
        self.bubble_canvas, self.canvas = self._make_canvases()
        self._setup_pointer()
        self._setup_menu()
        self._keep_on_top()
        self._show_bubble(MOOD_MESSAGES["happy"])
        self._animate()

    # Window flags: no title bar, always on top, see-through background,
    # and start in the bottom-right corner of the screen.
    def _make_window(self):
        self.root.title("Desktop Pet")
        self.root.overrideredirect(True)
        x = self.root.winfo_screenwidth() - WINDOW_WIDTH - 20
        y = self.root.winfo_screenheight() - WINDOW_HEIGHT - 60
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.root.configure(bg=TRANSPARENT)
        self.root.update_idletasks()
        try:
            self.root.attributes("-transparentcolor", TRANSPARENT)  # Windows only
        except tk.TclError:
            pass
        self.root.attributes("-topmost", True)

    # Two drawing surfaces: a strip for the speech bubble, and the tree below it.
    # Both use the see-through color so only the drawn shapes are visible.
    def _make_canvases(self):
        bubble = tk.Canvas(
            self.root, width=WINDOW_WIDTH, height=BUBBLE_HEIGHT,
            bg=TRANSPARENT, highlightthickness=0,
        )
        bubble.pack()
        tree_canvas = tk.Canvas(
            self.root, width=VIEW_WIDTH, height=VIEW_HEIGHT,
            bg=TRANSPARENT, highlightthickness=0,
        )
        tree_canvas.pack()
        return bubble, tree_canvas

    # Change the tree's mood, unless a click boost is holding "happy" for 3 seconds.
    def show_mood(self, mood):
        if self._boost_job is not None:
            return
        self._log_mood_if_changed(mood)
        if mood != self._mood:
            self._show_bubble(MOOD_MESSAGES.get(mood, ""))
        self._mood = mood
        self.tree.set_mood(mood)

    # Tell journal.py (or tests) only when the mood string is different from last time.
    def _log_mood_if_changed(self, mood):
        if mood == self._last_logged_mood:
            return
        self._last_logged_mood = mood
        if self._on_mood_change is not None:
            self._on_mood_change(mood)

    # Show the speech bubble with `text` for a few seconds.
    def _show_bubble(self, text):
        self._bubble_text = text
        self._bubble_until = time.monotonic() + BUBBLE_SECONDS

    # Draw the bubble only when its text changes, so it does not flicker.
    def _draw_bubble(self):
        text = self._bubble_text if time.monotonic() < self._bubble_until else None
        if text == self._bubble_drawn:
            return
        self._bubble_drawn = text
        c = self.bubble_canvas
        c.delete("all")
        if not text:
            return
        mid = WINDOW_WIDTH / 2
        bottom = BUBBLE_HEIGHT - 9
        c.create_rectangle(3, 3, WINDOW_WIDTH - 3, bottom, fill="#fff8e7", outline="#5a4a3a", width=1.5)
        c.create_polygon(mid - 5, bottom, mid + 5, bottom, mid, BUBBLE_HEIGHT - 2,
                         fill="#fff8e7", outline="#5a4a3a", width=1.5)
        # Cover the polygon's top stroke so the tail joins the rectangle.
        c.create_line(mid - 4, bottom, mid + 4, bottom, fill="#fff8e7", width=3)
        c.create_text(mid, (3 + bottom) / 2, text=text, fill="#3b2f25", font=("Arial", 8, "bold"))

    # Move the tree one frame and redraw. Uses after(), not sleep.
    def _animate(self):
        self.tree.step()
        self.tree.draw(self.canvas)
        self._draw_bubble()
        self.root.after(FRAME_MS, self._animate)

    # Windows drops "always on top" from borderless windows when you switch apps,
    # so ask the OS directly every 200 ms. Paused while the menu is open,
    # otherwise the tree would cover the menu.
    def _keep_on_top(self):
        if not self._menu_open:
            if sys.platform == "win32":
                try:
                    hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
                    flags = 0x0002 | 0x0001 | 0x0010 | 0x0040  # NOMOVE|NOSIZE|NOACTIVATE|SHOWWINDOW
                    ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, flags)
                except Exception:
                    pass
            self.root.attributes("-topmost", True)
        self.root.after(200, self._keep_on_top)

    # Remember the press point so we can drag, and tell click from drag apart.
    def _on_press(self, event):
        self.root.focus_force()
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._did_drag = False

    # Move the window while the button is held. A large move means this is a drag.
    def _on_drag(self, event):
        moved_x = abs(event.x - self._drag_start_x)
        moved_y = abs(event.y - self._drag_start_y)
        if moved_x > CLICK_MOVE_LIMIT or moved_y > CLICK_MOVE_LIMIT:
            self._did_drag = True
        new_x = self.root.winfo_pointerx() - self._drag_start_x
        new_y = self.root.winfo_pointery() - self._drag_start_y
        self.root.geometry(f"+{new_x}+{new_y}")

    # A still click (no drag) makes the tree happy for 3 seconds.
    def _on_release(self, event):
        if not self._did_drag:
            self._boost_happy()

    # Switch to happy now, then clear the boost later with after(3000).
    def _boost_happy(self):
        self._log_mood_if_changed("happy")
        self._mood = "happy"
        self.tree.set_mood("happy")
        self._show_bubble(BOOST_MESSAGE)
        if self._boost_job is not None:
            self.root.after_cancel(self._boost_job)
        self._boost_job = self.root.after(3000, self._end_boost)

    # Allow show_mood() to follow real stats (or debug keys) again.
    def _end_boost(self):
        self._boost_job = None

    # Bind press, drag, and release on the window and both canvases.
    def _setup_pointer(self):
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._did_drag = False
        for widget in (self.root, self.bubble_canvas, self.canvas):
            widget.bind("<Button-1>", self._on_press)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<ButtonRelease-1>", self._on_release)

    # Right-click menu. A borderless window has no close button, so Quit lives here.
    def _setup_menu(self):
        self._menu = tk.Menu(self.root, tearoff=0)
        self._menu.add_command(label="Quit", command=self.root.destroy)
        for widget in (self.root, self.bubble_canvas, self.canvas):
            widget.bind("<Button-3>", self._show_menu)

    # Show the menu at the mouse. The flag pauses _keep_on_top while it is open.
    def _show_menu(self, event):
        self._menu_open = True
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()
            self._menu_open = False

    # Debug helper: keys 1-4 force a mood (0 = back to real stats),
    # and the same choices are added to the top of the right-click menu.
    def bind_debug_keys(self, on_force_mood):
        def make_handler(mood):
            def handler(event):
                on_force_mood(mood)
            return handler

        for key, mood in DEBUG_KEY_MOODS.items():
            self.root.bind_all(key, make_handler(mood))

        def clear_force(event):
            on_force_mood(None)

        self.root.bind_all("0", clear_force)

        self._menu.insert_separator(0)
        for mood in reversed(list(DEBUG_KEY_MOODS.values())):
            self._menu.insert_command(0, label=f"Force {mood}", command=lambda m=mood: on_force_mood(m))
        self._menu.insert_command(0, label="Automatic (real stats)", command=lambda: on_force_mood(None))
        self.root.focus_force()

    # Hand control to tkinter until the user closes the app.
    def run(self):
        self.root.mainloop()
