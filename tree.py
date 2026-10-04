"""The apple tree: its animation state and its drawing.

No window code and no system stats live here. Pet (pet.py) owns the window
and hands this class a canvas to draw on, so the animation logic can be
unit tested without opening a window.
"""

import math
import random

# The tree is designed on a 140 x 170 grid. SCALE shrinks (or grows) the whole
# thing on screen: 1.0 = original size, 0.7 = about half the screen area.
SCALE = 0.7
WIDTH, HEIGHT = 140, 170
GROUND_Y = 148

# Size of the tree on screen after scaling.
VIEW_WIDTH = round(WIDTH * SCALE)
VIEW_HEIGHT = round(HEIGHT * SCALE)

# This exact color becomes see-through on Windows, so never draw with it.
TRANSPARENT = "#010101"
FACE_COLOR = "#3b2418"

# Where apples hang on the tree (x, y).
APPLE_SPOTS = [(48, 55), (70, 32), (92, 55), (55, 78), (85, 78), (70, 57)]

# Frames (one frame = 50 ms) between drops while sleeping / panicking.
SLEEP_DROP_EVERY = 25
PANIC_DROP_EVERY = 6


# Mix two hex colors. t=0 gives c1, t=1 gives c2.
# Used to smoothly turn fresh apples and leaves into rotten ones.
def blend(c1, c2, t):
    r1, g1, b1 = (int(c1[i:i + 2], 16) for i in (1, 3, 5))
    r2, g2, b2 = (int(c2[i:i + 2], 16) for i in (1, 3, 5))
    return "#{:02x}{:02x}{:02x}".format(
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )


class Tree:
    """Animation state for the tree: apples, rot, and the current mood."""

    def __init__(self):
        self.mood = "happy"
        self.frame = 0
        self.rot = 0.0  # 0 = fresh, 1 = fully rotten
        self.apples = []
        self.grow_apples()

    # Put every apple back on the tree.
    def grow_apples(self):
        self.apples = [
            {"x": x, "y": y, "state": "hanging", "vy": 0, "land_y": 0}
            for x, y in APPLE_SPOTS
        ]

    # Change mood. Apples grow back when things calm down (happy) or when
    # the tree starts to rot (sweating), so there is always fruit to spoil.
    def set_mood(self, mood):
        if mood == self.mood:
            return
        if mood in ("happy", "sweating"):
            self.grow_apples()
        self.mood = mood

    # Pick one hanging apple and let it fall.
    def drop_one(self):
        hanging = [a for a in self.apples if a["state"] == "hanging"]
        if hanging:
            apple = random.choice(hanging)
            apple["state"] = "falling"
            apple["vy"] = 0
            apple["land_y"] = GROUND_Y - 2 + random.randint(-3, 4)

    # Move falling apples down. vy grows each frame, which acts like gravity.
    def update_apples(self):
        for a in self.apples:
            if a["state"] == "falling":
                a["vy"] += 0.5
                a["y"] += a["vy"]
                if a["y"] >= a["land_y"]:
                    a["y"] = a["land_y"]
                    a["state"] = "landed"

    # Advance the animation by one frame (the caller runs this every 50 ms).
    def step(self):
        self.frame += 1

        # Rot grows slowly while the CPU is overloaded, and heals otherwise.
        if self.mood == "sweating":
            self.rot = min(1.0, self.rot + 0.01)
        else:
            self.rot = max(0.0, self.rot - 0.02)

        if self.mood == "sleeping" and self.frame % SLEEP_DROP_EVERY == 0:
            self.drop_one()
        if self.mood == "panicking" and self.frame % PANIC_DROP_EVERY == 0:
            self.drop_one()

        self.update_apples()

    # ---------- drawing ----------

    # True for a few frames every ~4 seconds so the happy tree blinks.
    def _blinking(self):
        return self.frame % 80 < 3

    def _draw_face(self, c, cx):
        ey, my = 118, 128
        lx, rx = cx - 7, cx + 7

        for bx in (lx - 3, rx + 3):  # blush
            c.create_oval(bx - 4, ey + 4, bx + 4, ey + 9, fill="#ffb3c1", outline="")

        closed = self.mood == "sleeping" or (self._blinking() and self.mood in ("happy", "sweating"))

        if closed:
            for ex in (lx, rx):  # closed eyes
                c.create_arc(ex - 3, ey - 2, ex + 3, ey + 4, start=200, extent=140,
                             style="arc", outline=FACE_COLOR, width=2)

        if self.mood == "sleeping":
            c.create_oval(cx - 2, my - 1, cx + 2, my + 3, outline=FACE_COLOR, width=1)
        elif self.mood == "panicking":
            for ex in (lx, rx):  # big shocked eyes
                c.create_oval(ex - 4, ey - 4, ex + 4, ey + 4, fill="white", outline=FACE_COLOR)
                c.create_oval(ex - 1.5, ey - 1.5, ex + 1.5, ey + 1.5, fill=FACE_COLOR, outline="")
            c.create_oval(cx - 3, my - 2, cx + 3, my + 5, fill=FACE_COLOR, outline="")
        elif self.mood == "sweating":
            if not closed:
                for ex in (lx, rx):  # tired eyes
                    c.create_oval(ex - 2, ey - 2, ex + 2, ey + 2, fill=FACE_COLOR, outline="")
            c.create_line(cx - 4, my + 2, cx - 2, my, cx, my + 2, cx + 2, my,
                          cx + 4, my + 2, fill=FACE_COLOR, width=2, smooth=True)
            c.create_oval(rx + 6, ey - 8, rx + 11, ey, fill="#7fd0ff", outline="")  # sweat drop
        else:
            if not closed:
                for ex in (lx, rx):  # happy eyes with a shine
                    c.create_oval(ex - 2.5, ey - 2.5, ex + 2.5, ey + 2.5, fill=FACE_COLOR, outline="")
                    c.create_oval(ex - 1.5, ey - 1.8, ex - 0.2, ey - 0.5, fill="white", outline="")
            c.create_arc(cx - 5, my - 4, cx + 5, my + 3, start=200, extent=140,
                         style="arc", outline=FACE_COLOR, width=2)

    # Redraw the whole tree on `canvas` for the current frame.
    def draw(self, canvas):
        c = canvas
        c.delete("all")

        # Sideways movement: gentle sway, or shaking when panicking.
        if self.mood == "panicking":
            dx = math.sin(self.frame * 1.5) * 3
        else:
            dx = math.sin(self.frame * 0.1) * 1

        # Grassy mound + tiny flowers.
        c.create_oval(10, GROUND_Y - 8, 130, HEIGHT - 3, fill="#9ccc78", outline="")
        c.create_oval(25, GROUND_Y - 4, 115, HEIGHT - 2, fill="#8bbf68", outline="")
        for fx, fy, col in [(22, 152, "#ffd6e0"), (112, 155, "#fff3b0"), (32, 160, "#ffffff")]:
            c.create_oval(fx - 2, fy - 2, fx + 2, fy + 2, fill=col, outline="")

        # Trunk (rounded) + face.
        tx = dx / 2
        c.create_rectangle(58 + tx, 92, 82 + tx, GROUND_Y, fill="#b07d5b", outline="")
        c.create_oval(58 + tx, GROUND_Y - 6, 82 + tx, GROUND_Y + 4, fill="#b07d5b", outline="")
        self._draw_face(c, 70 + tx)

        # Fluffy canopy with lighter highlights. Leaves yellow as the tree rots.
        leaf = blend("#7bc67e", "#c9c36a", self.rot)
        light = blend("#a5dfa0", "#ddd788", self.rot)
        if self.mood == "sleeping":
            leaf, light = "#5fa86a", "#78bd80"
        for box in [(18, 38, 80, 98), (60, 38, 122, 98), (36, 10, 104, 72), (38, 40, 102, 100)]:
            c.create_oval(box[0] + dx, box[1], box[2] + dx, box[3], fill=leaf, outline="")
        for hx, hy in [(42, 28), (28, 55), (95, 50)]:
            c.create_oval(hx + dx, hy, hx + 14 + dx, hy + 8, fill=light, outline="")

        # Apples with a little shine. Red turns brown with rot.
        apple_color = blend("#ff6b6b", "#8a6a4a", self.rot)
        for a in self.apples:
            x = a["x"] + (dx if a["state"] == "hanging" else 0)
            y = a["y"]
            c.create_oval(x - 5.5, y - 5.5, x + 5.5, y + 5.5, fill=apple_color, outline="")
            c.create_line(x, y - 5, x + 1, y - 9, fill="#5a3b22", width=1.5)
            c.create_oval(x - 3.5, y - 3.5, x - 1.5, y - 1.5, fill="white", outline="")
            if self.rot > 0.5:
                c.create_oval(x + 1, y, x + 4, y + 3, fill="#4a3320", outline="")

        # Flies when the CPU has been overloaded for a while.
        if self.mood == "sweating" and self.rot > 0.4:
            for i in range(3):
                angle = self.frame * 0.3 + i * 2.1
                fx = 70 + math.cos(angle) * (38 + i * 8)
                fy = 60 + math.sin(angle * 1.3) * 22
                c.create_oval(fx - 1.5, fy - 1.5, fx + 1.5, fy + 1.5, fill="black")

        # Floating z's when sleeping.
        if self.mood == "sleeping":
            for i in range(3):
                offset = (self.frame * 0.4 + i * 10) % 30
                c.create_text(108 + i * 8, 32 - offset, text="z", fill="white",
                              font=("Arial", max(5, round((7 + i * 3) * SCALE)), "bold"))

        # Everything above was drawn on the 140 x 170 grid. Shrink it to screen size.
        c.scale("all", 0, 0, SCALE, SCALE)
