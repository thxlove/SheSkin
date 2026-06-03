"""D2DTrackBar 单元测试。"""
import pytest
from sheskin.controls.trackbar import D2DTrackBar


class TestD2DTrackBarInit:
    def test_init_defaults(self):
        tb = D2DTrackBar((10, 20, 200, 28))
        assert tb.value == 0
        assert tb.min_value == 0
        assert tb.max_value == 100
        assert tb.step == 1
        assert tb.page_step == 10
        assert tb.orientation == D2DTrackBar.HORIZONTAL
        assert tb.resolution == 1

    def test_init_with_value(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        assert tb.value == 50

    def test_init_clamps_value(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=150, max_value=100)
        assert tb.value == 100
        tb2 = D2DTrackBar((0, 0, 200, 28), value=-5, min_value=0)
        assert tb2.value == 0

    def test_init_with_range(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=5, min_value=0, max_value=10)
        assert tb.min_value == 0
        assert tb.max_value == 10
        assert tb.value == 5

    def test_init_vertical(self):
        tb = D2DTrackBar((0, 0, 28, 200), orientation=D2DTrackBar.VERTICAL)
        assert tb.orientation == D2DTrackBar.VERTICAL

    def test_init_resolution(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=5.5,
                          min_value=0, max_value=10, resolution=0.1)
        assert tb.resolution == 0.1
        assert tb.value == 5.5

    def test_init_resolution_snaps_value(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=5.57,
                          min_value=0, max_value=10, resolution=0.1)
        assert abs(tb.value - 5.6) < 1e-9


class TestD2DTrackBarProperties:
    def test_set_value(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        changed = tb.set_value(75)
        assert tb.value == 75
        assert changed is True

    def test_set_value_same(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        changed = tb.set_value(50)
        assert tb.value == 50
        assert changed is False

    def test_set_value_clamps(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tb.set_value(200)
        assert tb.value == 100
        tb.set_value(-10)
        assert tb.value == 0

    def test_set_value_snaps_resolution(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=0,
                          min_value=0, max_value=10, resolution=0.1)
        tb.set_value(3.37)
        assert abs(tb.value - 3.4) < 1e-9

    def test_set_value_resolution_integer(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=0, resolution=1)
        tb.set_value(33.7)
        assert tb.value == 34

    def test_set_range(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tb.set_range(0, 200)
        assert tb.min_value == 0
        assert tb.max_value == 200
        assert tb.value == 50

    def test_set_range_clamps_value(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=80)
        tb.set_range(0, 50)
        assert tb.value == 50

    def test_on_change_callback(self):
        results = []
        tb = D2DTrackBar((0, 0, 200, 28), value=50,
                          on_change=lambda v: results.append(v))
        tb.set_value(75)
        assert results == [75]

    def test_on_change_not_called_same_value(self):
        results = []
        tb = D2DTrackBar((0, 0, 200, 28), value=50,
                          on_change=lambda v: results.append(v))
        tb.set_value(50)
        assert results == []

    def test_set_on_change(self):
        results = []
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tb.set_on_change(lambda v: results.append(v))
        tb.set_value(75)
        assert results == [75]


class TestD2DTrackBarHitTest:
    def test_hit_thumb_center(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tx, ty, tw, th = tb._get_thumb_rect()
        cx = tx + tw * 0.5
        cy = ty + th * 0.5
        assert tb._hit_thumb((cx, cy)) is True

    def test_hit_thumb_outside(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=0)
        assert tb._hit_thumb((190, 14)) is False

    def test_hit_track_inside(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        assert tb._hit_track((100, 14)) is True

    def test_hit_track_outside(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        assert tb._hit_track((250, 14)) is False


class TestD2DTrackBarMouseEvents:
    def test_mouse_down_on_thumb(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tx, ty, tw, th = tb._get_thumb_rect()
        result = tb.on_mouse_down((tx + tw * 0.5, ty + th * 0.5))
        assert result is True
        assert tb._thumb_state == D2DTrackBar.PRESSED
        assert tb._dragging is True

    def test_mouse_down_on_track(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=0)
        result = tb.on_mouse_down((150, 14))
        assert result is True
        assert tb._dragging is True

    def test_mouse_down_disabled(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tb._state = D2DTrackBar.DISABLED
        result = tb.on_mouse_down((100, 14))
        assert result is False

    def test_mouse_up_after_drag(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tx, ty, tw, th = tb._get_thumb_rect()
        tb.on_mouse_down((tx + tw * 0.5, ty + th * 0.5))
        result = tb.on_mouse_up((120, 14))
        assert tb._dragging is False
        assert tb._captured is False

    def test_mouse_up_without_down(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        result = tb.on_mouse_up((100, 14))
        assert result is False

    def test_mouse_move_dragging(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tx, ty, tw, th = tb._get_thumb_rect()
        tb.on_mouse_down((tx + tw * 0.5, ty + th * 0.5))
        result = tb.on_mouse_move((150, 14))
        assert result is True

    def test_mouse_move_hover_thumb(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tx, ty, tw, th = tb._get_thumb_rect()
        result = tb.on_mouse_move((tx + tw * 0.5, ty + th * 0.5))
        assert result is True
        assert tb._thumb_state == D2DTrackBar.HOVER

    def test_mouse_move_leave_thumb(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tx, ty, tw, th = tb._get_thumb_rect()
        tb.on_mouse_move((tx + tw * 0.5, ty + th * 0.5))
        result = tb.on_mouse_move((0, 0))
        assert tb._thumb_state == D2DTrackBar.NORMAL

    def test_mouse_leave(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tx, ty, tw, th = tb._get_thumb_rect()
        tb.on_mouse_move((tx + tw * 0.5, ty + th * 0.5))
        result = tb.on_mouse_leave()
        assert tb._thumb_state == D2DTrackBar.NORMAL

    def test_mouse_leave_while_dragging(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        tx, ty, tw, th = tb._get_thumb_rect()
        tb.on_mouse_down((tx + tw * 0.5, ty + th * 0.5))
        tb.on_mouse_leave()
        assert tb._dragging is False
        assert tb._captured is False


class TestD2DTrackBarPosToValue:
    def test_pos_to_value_left(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        thumb_sz = 18
        val = tb._pos_to_value((thumb_sz * 0.5, 14))
        assert abs(val - 0) < 1

    def test_pos_to_value_right(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        thumb_sz = 18
        val = tb._pos_to_value((200 - thumb_sz * 0.5, 14))
        assert abs(val - 100) < 1

    def test_pos_to_value_middle(self):
        tb = D2DTrackBar((0, 0, 200, 28), value=50)
        thumb_sz = 18
        val = tb._pos_to_value((100, 14))
        assert abs(val - 50) < 2


class TestD2DTrackBarStateName:
    def test_normal_state(self):
        tb = D2DTrackBar((0, 0, 200, 28))
        assert tb._state_name() == 'normal'

    def test_hover_state(self):
        tb = D2DTrackBar((0, 0, 200, 28))
        tb._thumb_state = D2DTrackBar.HOVER
        assert tb._state_name() == 'hover'

    def test_pressed_state(self):
        tb = D2DTrackBar((0, 0, 200, 28))
        tb._thumb_state = D2DTrackBar.PRESSED
        assert tb._state_name() == 'pressed'

    def test_disabled_state(self):
        tb = D2DTrackBar((0, 0, 200, 28))
        tb._state = D2DTrackBar.DISABLED
        assert tb._state_name() == 'disabled'
