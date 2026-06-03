"""测试 D2DProgress / SkinAwareProgress — TDD 单元测试。"""
import pyd2d
from unittest.mock import patch

from sheskin.controls.base_control import SheControl
from sheskin.controls.progress import D2DProgress, SkinAwareProgress


class _Ctrl:
    """Mock 控件 — 满足 D2DLayout.getattr(ctrl, 'rect', ...) 等需求。"""

    def __init__(self, rect=(0, 0, 10, 10)):
        self.rect = rect


class TestD2DProgress:
    def test_init_default(self):
        p = D2DProgress((10, 20, 200, 24))
        assert p.value == 0
        assert p.max_value == 100
        assert p.orientation == D2DProgress.HORIZONTAL

    def test_init_with_value(self):
        p = D2DProgress((0, 0, 200, 24), value=75)
        assert p.value == 75

    def test_init_vertical(self):
        p = D2DProgress((0, 0, 24, 200), value=50,
                        orientation=D2DProgress.VERTICAL)
        assert p.orientation == D2DProgress.VERTICAL

    def test_value_clamp_high(self):
        p = D2DProgress((0, 0, 200, 24), value=150)
        assert p.value == 100

    def test_value_clamp_low(self):
        p = D2DProgress((0, 0, 200, 24), value=-10)
        assert p.value == 0

    def test_set_value_returns_true_on_change(self):
        p = D2DProgress((0, 0, 200, 24), value=0)
        assert p.set_value(50) is True

    def test_set_value_returns_false_on_no_change(self):
        p = D2DProgress((0, 0, 200, 24), value=50)
        assert p.set_value(50) is False

    def test_set_range(self):
        p = D2DProgress((0, 0, 200, 24))
        changed = p.set_range(50, 200)
        assert changed is True
        assert p.value == 50
        assert p.max_value == 200

    def test_set_range_no_change(self):
        p = D2DProgress((0, 0, 200, 24), value=50, max_value=200)
        changed = p.set_range(50, 200)
        assert changed is False

    def test_set_orientation(self):
        p = D2DProgress((0, 0, 200, 24))
        p.set_orientation(D2DProgress.VERTICAL)
        assert p.orientation == D2DProgress.VERTICAL

    def test_non_interactive(self):
        p = D2DProgress((0, 0, 200, 24))
        assert p.on_mouse_down((10, 10)) is False
        assert p.on_mouse_up((10, 10)) is False
        assert p.on_mouse_move((10, 10)) is False
        assert p.on_mouse_leave() is False

    def test_disabled_state(self):
        p = D2DProgress((0, 0, 200, 24), value=50)
        p._state = D2DProgress.DISABLED
        assert p._state == D2DProgress.DISABLED

    def test_rect_access(self):
        p = D2DProgress((10, 20, 200, 24))
        assert p.rect == (10, 20, 200, 24)

    def test_set_rect(self):
        p = D2DProgress((0, 0, 200, 24))
        p.set_rect((5, 5, 100, 20))
        assert p.rect == (5, 5, 100, 20)

    def test_shecontrol_inheritance(self):
        p = D2DProgress((0, 0, 200, 24))
        assert isinstance(p, SheControl)

    def test_max_value_zero_ratio(self):
        p = D2DProgress((0, 0, 200, 24), value=50, max_value=0)
        assert p.max_value == 0


class TestSkinAwareProgress:
    def test_init(self):
        p = SkinAwareProgress((0, 0, 200, 24), None, value=50)
        assert p.value == 50
        assert p.orientation == D2DProgress.HORIZONTAL

    def test_init_vertical(self):
        p = SkinAwareProgress((0, 0, 24, 200), None, value=30,
                              orientation=D2DProgress.VERTICAL)
        assert p.orientation == D2DProgress.VERTICAL

    def test_custom_slots(self):
        p = SkinAwareProgress(
            (0, 0, 200, 24), None, value=50,
            h_bg_slots={'normal': 10, 'disabled': 11},
            h_fg_slots={'normal': 20, 'disabled': 21})
        assert p._h_bg_slots['normal'] == 10
        assert p._h_fg_slots['disabled'] == 21

    def test_set_value_in_skin_aware(self):
        p = SkinAwareProgress((0, 0, 200, 24), None)
        assert p.set_value(75) is True
        assert p.value == 75

    def test_set_range_in_skin_aware(self):
        p = SkinAwareProgress((0, 0, 200, 24), None)
        p.set_range(40, 80)
        assert p.value == 40
        assert p.max_value == 80