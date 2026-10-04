from tree import APPLE_SPOTS, GROUND_Y, Tree, blend


# Records every drawing call without opening a window.
class FakeCanvas:
    def __init__(self):
        self.calls = 0

    def __getattr__(self, name):
        def method(*args, **kwargs):
            self.calls += 1
        return method


def _run(tree, frames):
    for _ in range(frames):
        tree.step()


def _count(tree, state):
    return sum(1 for a in tree.apples if a["state"] == state)


# ---- blend ----

def test_blend_start_and_end():
    assert blend("#000000", "#ffffff", 0) == "#000000"
    assert blend("#000000", "#ffffff", 1) == "#ffffff"


def test_blend_middle():
    assert blend("#000000", "#fefefe", 0.5) == "#7f7f7f"


# ---- apples ----

def test_starts_happy_with_all_apples_hanging():
    tree = Tree()
    assert tree.mood == "happy"
    assert _count(tree, "hanging") == len(APPLE_SPOTS)


def test_happy_tree_keeps_its_apples():
    tree = Tree()
    _run(tree, 500)
    assert _count(tree, "hanging") == len(APPLE_SPOTS)


def test_sleeping_drops_apples_one_by_one():
    tree = Tree()
    tree.set_mood("sleeping")
    _run(tree, 30)                     # just past the first drop (frame 25)
    assert _count(tree, "hanging") == len(APPLE_SPOTS) - 1
    _run(tree, 300)                    # plenty of time for all of them
    assert _count(tree, "landed") == len(APPLE_SPOTS)


def test_apples_land_near_the_ground():
    tree = Tree()
    tree.set_mood("panicking")
    _run(tree, 200)
    for apple in tree.apples:
        assert apple["state"] == "landed"
        assert GROUND_Y - 6 <= apple["y"] <= GROUND_Y + 3


def test_panicking_drops_apples_faster_than_sleeping():
    sleepy, scared = Tree(), Tree()
    sleepy.set_mood("sleeping")
    scared.set_mood("panicking")
    _run(sleepy, 60)
    _run(scared, 60)
    assert _count(scared, "hanging") < _count(sleepy, "hanging")


def test_apples_grow_back_when_happy():
    tree = Tree()
    tree.set_mood("sleeping")
    _run(tree, 300)
    tree.set_mood("happy")
    assert _count(tree, "hanging") == len(APPLE_SPOTS)


def test_setting_the_same_mood_does_not_reset_apples():
    tree = Tree()
    tree.set_mood("sleeping")
    _run(tree, 60)
    hanging_before = _count(tree, "hanging")
    tree.set_mood("sleeping")
    assert _count(tree, "hanging") == hanging_before


# ---- rot ----

def test_rot_builds_up_slowly_while_sweating():
    tree = Tree()
    tree.set_mood("sweating")
    _run(tree, 10)
    assert 0 < tree.rot < 0.5          # a short burst does not ruin the tree


def test_rot_is_capped_at_one():
    tree = Tree()
    tree.set_mood("sweating")
    _run(tree, 1000)
    assert tree.rot == 1.0


def test_rot_heals_when_cpu_calms_down():
    tree = Tree()
    tree.set_mood("sweating")
    _run(tree, 1000)
    tree.set_mood("happy")
    _run(tree, 100)
    assert tree.rot == 0.0


# ---- drawing smoke test ----

def test_every_mood_draws_without_errors():
    for mood in ("happy", "sleeping", "sweating", "panicking"):
        tree = Tree()
        tree.set_mood(mood)
        _run(tree, 120)                # long enough for rot, flies and falling apples
        canvas = FakeCanvas()
        tree.draw(canvas)
        assert canvas.calls > 0
