"""测试 D2DSpinCtrl / SkinAwareSpinCtrl — TDD 单元测试。"""
import pyd2d
from unittest.mock import patch

from sheskin.controls.base_control import SheControl
from sheskin.controls.spinctrl import D2DSpinCtrl, SkinAwareSpinCtrl


class _Ctrl:
    def __init__(self, rect=(0, 0, 10, 10)):
        self.rect = rect


class TestD2DSpinCtrl:
    def test_init_default(self):
        sp = D2DSpinCtrl((10, 20, 120, 30))
        assert sp.value == 0
        assert sp.min_value == 0
        assert sp.max_value == 100
        assert sp.step == 1
        assert sp.orientation == D2DSpinCtrl.VERTICAL

    def test_init_with_value(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), value=50)
        assert sp.value == 50

    def test_init_horizontal(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), orientation=D2DSpinCtrl.HORIZONTAL)
        assert sp.orientation == D2DSpinCtrl.HORIZONTAL

    def test_value_clamp_high(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), value=150, max_value=100)
        assert sp.value == 100

    def test_value_clamp_low(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), value=-10, min_value=0)
        assert sp.value == 0

    def test_set_value_returns_true_on_change(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), value=0)
        assert sp.set_value(50) is True

    def test_set_value_returns_false_on_no_change(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), value=50)
        assert sp.set_value(50) is False

    def test_increase_btn(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), value=0, step=5,
                         orientation=D2DSpinCtrl.VERTICAL)
        assert sp._increase_btn() == D2DSpinCtrl.BTN_UP

    def test_increase_btn_horizontal(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), value=0,
                         orientation=D2DSpinCtrl.HORIZONTAL)
        assert sp._increase_btn() == D2DSpinCtrl.BTN_RIGHT

    def test_decrease_btn(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), value=50,
                         orientation=D2DSpinCtrl.VERTICAL)
        assert sp._decrease_btn() == D2DSpinCtrl.BTN_DOWN

    def test_decrease_btn_horizontal(self):
        sp = D2DSpinCtrl((0, 0, 120, 30), value=50,
                         orientation=D2DSpinCtrl.HORIZONTAL)
        assert sp._decrease_btn() == D2DSpinCtrl.BTN_LEFT

    def test_button_rects_vertical(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), orientation=D2DSpinCtrl.VERTICAL)
        rects = sp._get_button_rects()
        assert D2DSpinCtrl.BTN_UP in rects
        assert D2DSpinCtrl.BTN_DOWN in rects
        bx, by, bw, bh = rects[D2DSpinCtrl.BTN_UP]
        assert bw == 20.0
        assert by == 0.0
        bx2, by2, bw2, bh2 = rects[D2DSpinCtrl.BTN_DOWN]
        assert by2 == 20.0
        assert bh2 == 20.0

    def test_button_rects_horizontal(self):
        sp = D2DSpinCtrl((0, 0, 100, 30),
                         orientation=D2DSpinCtrl.HORIZONTAL)
        rects = sp._get_button_rects()
        assert D2DSpinCtrl.BTN_LEFT in rects
        assert D2DSpinCtrl.BTN_RIGHT in rects
        bx, by, bw, bh = rects[D2DSpinCtrl.BTN_LEFT]
        assert bx == 0.0
        bx2, by2, bw2, bh2 = rects[D2DSpinCtrl.BTN_RIGHT]
        assert bx2 == 80.0

    def test_text_rect_vertical(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), orientation=D2DSpinCtrl.VERTICAL)
        tx, ty, tw, th = sp._get_text_rect()
        assert tx > 0
        assert tw < 100

    def test_text_rect_horizontal(self):
        sp = D2DSpinCtrl((0, 0, 100, 40),
                         orientation=D2DSpinCtrl.HORIZONTAL)
        tx, ty, tw, th = sp._get_text_rect()
        assert tw < 100

    def test_hit_button_on_up(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), orientation=D2DSpinCtrl.VERTICAL)
        rects = sp._get_button_rects()
        _, by, _, bh = rects[D2DSpinCtrl.BTN_UP]
        mid_y = by + bh * 0.5
        btn = sp._hit_button((96, int(mid_y)))
        assert btn == D2DSpinCtrl.BTN_UP

    def test_hit_button_on_down(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), orientation=D2DSpinCtrl.VERTICAL)
        rects = sp._get_button_rects()
        _, by, _, bh = rects[D2DSpinCtrl.BTN_DOWN]
        mid_y = by + bh * 0.5
        btn = sp._hit_button((96, int(mid_y)))
        assert btn == D2DSpinCtrl.BTN_DOWN

    def test_hit_button_outside(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), orientation=D2DSpinCtrl.VERTICAL)
        btn = sp._hit_button((10, 10))
        assert btn is None

    def test_disabled_ignores_mouse(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), value=0,
                         orientation=D2DSpinCtrl.VERTICAL)
        sp._state = D2DSpinCtrl.DISABLED
        result = sp.on_mouse_down((96, 10))
        assert result is False
        assert sp.value == 0

    def test_mouse_down_increases(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), value=0,
                         orientation=D2DSpinCtrl.VERTICAL)
        sp.on_mouse_down((96, 10))
        assert sp.value == 1
        assert sp._captured is True

    def test_mouse_down_decreases(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), value=50,
                         orientation=D2DSpinCtrl.VERTICAL)
        sp.on_mouse_down((96, 30))
        assert sp.value == 49

    def test_mouse_down_no_button(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), value=50,
                         orientation=D2DSpinCtrl.VERTICAL)
        result = sp.on_mouse_down((10, 10))
        assert result is False
        assert sp.value == 50

    def test_mouse_up_releases(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), value=0,
                         orientation=D2DSpinCtrl.VERTICAL)
        sp.on_mouse_down((96, 10))
        result = sp.on_mouse_up((96, 10))
        assert result is True
        assert sp._captured is False
        assert sp._btn_increase_state == D2DSpinCtrl.NORMAL

    def test_mouse_leave_resets(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), value=0,
                         orientation=D2DSpinCtrl.VERTICAL)
        sp.on_mouse_down((96, 10))
        result = sp.on_mouse_leave()
        assert result is True
        assert sp._captured is False

    def test_on_change_callback(self):
        values = []

        def cb(v):
            values.append(v)

        sp = D2DSpinCtrl((0, 0, 100, 40), value=0,
                         orientation=D2DSpinCtrl.VERTICAL, on_change=cb)
        sp.set_value(42)
        assert values == [42]

    def test_set_range(self):
        sp = D2DSpinCtrl((0, 0, 100, 40), value=50)
        sp.set_range(0, 50)
        assert sp.value == 50
        sp.set_range(0, 30)
        assert sp.value == 30

    def test_hover_state(self):
        sp = D2DSpinCtrl((0, 0, 100, 40),
                         orientation=D2DSpinCtrl.VERTICAL)
        sp.on_mouse_move((96, 10))
        assert sp._btn_increase_state == D2DSpinCtrl.HOVER
        assert sp._btn_decrease_state == D2DSpinCtrl.NORMAL

    def test_hover_on_down_button(self):
        sp = D2DSpinCtrl((0, 0, 100, 40),
                         orientation=D2DSpinCtrl.VERTICAL)
        sp.on_mouse_move((96, 30))
        assert sp._btn_decrease_state == D2DSpinCtrl.HOVER
        assert sp._btn_increase_state == D2DSpinCtrl.NORMAL

    def test_hover_off_buttons(self):
        sp = D2DSpinCtrl((0, 0, 100, 40),
                         orientation=D2DSpinCtrl.VERTICAL)
        sp.on_mouse_move((96, 10))
        sp.on_mouse_move((10, 10))
        assert sp._btn_increase_state == D2DSpinCtrl.NORMAL
        assert sp._btn_decrease_state == D2DSpinCtrl.NORMAL


class TestSkinAwareSpinCtrl:
    def test_init_default(self):
        sp = SkinAwareSpinCtrl((0, 0, 120, 30), None)
        assert sp.value == 0
        assert sp.orientation == D2DSpinCtrl.VERTICAL

    def test_is_subclass(self):
        assert issubclass(SkinAwareSpinCtrl, D2DSpinCtrl)

    def test_fallback_draw_no_crash(self):
        sp = SkinAwareSpinCtrl((10, 20, 120, 30), None, value=42)
        try:
            sp.set_value(42)
        except Exception as e:
            assert False, f"unexpected: {e}"