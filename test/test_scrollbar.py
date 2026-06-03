"""D2DScrollBar 单元测试。"""
import pytest
from sheskin.controls.scrollbar import D2DScrollBar


class TestD2DScrollBarInit:
    def test_init_defaults(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        assert sb.scroll_pos == 0
        assert sb.scroll_max == 100
        assert sb.page_size == 10
        assert sb.orientation == D2DScrollBar.VERTICAL

    def test_init_with_values(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=30,
                           scroll_max=200, page_size=20,
                           orientation=D2DScrollBar.HORIZONTAL)
        assert sb.scroll_pos == 30
        assert sb.scroll_max == 200
        assert sb.page_size == 20
        assert sb.orientation == D2DScrollBar.HORIZONTAL

    def test_init_clamps_pos(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=150,
                           scroll_max=100)
        assert sb.scroll_pos == 100

    def test_init_negative_pos(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=-5)
        assert sb.scroll_pos == 0

    def test_init_page_size_min(self):
        sb = D2DScrollBar((0, 0, 16, 200), page_size=0)
        assert sb.page_size == 1


class TestD2DScrollBarSetScrollPos:
    def test_set_scroll_pos(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        changed = sb.set_scroll_pos(50)
        assert sb.scroll_pos == 50
        assert changed is True

    def test_set_scroll_pos_same(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=50)
        changed = sb.set_scroll_pos(50)
        assert sb.scroll_pos == 50
        assert changed is False

    def test_set_scroll_pos_clamps(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        sb.set_scroll_pos(200)
        assert sb.scroll_pos == 100
        sb.set_scroll_pos(-10)
        assert sb.scroll_pos == 0

    def test_on_scroll_callback(self):
        results = []
        sb = D2DScrollBar((0, 0, 16, 200),
                           on_scroll=lambda v: results.append(v))
        sb.set_scroll_pos(42)
        assert results == [42]

    def test_on_scroll_not_called_same(self):
        results = []
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=42,
                           on_scroll=lambda v: results.append(v))
        sb.set_scroll_pos(42)
        assert results == []

    def test_set_on_scroll(self):
        results = []
        sb = D2DScrollBar((0, 0, 16, 200))
        sb.set_on_scroll(lambda v: results.append(v))
        sb.set_scroll_pos(10)
        assert results == [10]


class TestD2DScrollBarSetScrollInfo:
    def test_set_scroll_max(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        sb.set_scroll_info(scroll_max=200)
        assert sb.scroll_max == 200

    def test_set_page_size(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        sb.set_scroll_info(page_size=30)
        assert sb.page_size == 30

    def test_set_scroll_pos_reclamps(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=80)
        sb.set_scroll_info(scroll_max=50)
        assert sb.scroll_pos == 50

    def test_set_scroll_info_negative_max(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        sb.set_scroll_info(scroll_max=-10)
        assert sb.scroll_max == 0


class TestD2DScrollBarHitTest:
    def test_hit_btn1_vertical(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL)
        part = sb._hit_test((8, 8))
        assert part == D2DScrollBar.BTN1

    def test_hit_btn2_vertical(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL)
        part = sb._hit_test((8, 192))
        assert part == D2DScrollBar.BTN2

    def test_hit_track_vertical(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=0,
                           orientation=D2DScrollBar.VERTICAL)
        part = sb._hit_test((8, 100))
        assert part == D2DScrollBar.TRACK

    def test_hit_thumb_vertical(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=0,
                           orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        tx, ty, tw, th = rects[D2DScrollBar.THUMB]
        part = sb._hit_test((tx + tw / 2, ty + th / 2))
        assert part == D2DScrollBar.THUMB

    def test_hit_btn1_horizontal(self):
        sb = D2DScrollBar((0, 0, 200, 16), orientation=D2DScrollBar.HORIZONTAL)
        part = sb._hit_test((8, 8))
        assert part == D2DScrollBar.BTN1

    def test_hit_btn2_horizontal(self):
        sb = D2DScrollBar((0, 0, 200, 16), orientation=D2DScrollBar.HORIZONTAL)
        part = sb._hit_test((192, 8))
        assert part == D2DScrollBar.BTN2

    def test_hit_outside(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        part = sb._hit_test((100, 100))
        assert part is None


class TestD2DScrollBarPartRects:
    def test_vertical_part_rects(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        assert D2DScrollBar.BTN1 in rects
        assert D2DScrollBar.BTN2 in rects
        assert D2DScrollBar.TRACK in rects
        assert D2DScrollBar.THUMB in rects

    def test_horizontal_part_rects(self):
        sb = D2DScrollBar((0, 0, 200, 16), orientation=D2DScrollBar.HORIZONTAL)
        rects = sb._get_part_rects()
        assert D2DScrollBar.BTN1 in rects
        assert D2DScrollBar.BTN2 in rects
        assert D2DScrollBar.TRACK in rects
        assert D2DScrollBar.THUMB in rects

    def test_vertical_btn1_at_top(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        bx, by, bw, bh = rects[D2DScrollBar.BTN1]
        assert by == 0.0
        assert bh > 0

    def test_vertical_btn2_at_bottom(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        bx, by, bw, bh = rects[D2DScrollBar.BTN2]
        assert by + bh == 200.0

    def test_horizontal_btn1_at_left(self):
        sb = D2DScrollBar((0, 0, 200, 16), orientation=D2DScrollBar.HORIZONTAL)
        rects = sb._get_part_rects()
        bx, by, bw, bh = rects[D2DScrollBar.BTN1]
        assert bx == 0.0
        assert bw > 0

    def test_horizontal_btn2_at_right(self):
        sb = D2DScrollBar((0, 0, 200, 16), orientation=D2DScrollBar.HORIZONTAL)
        rects = sb._get_part_rects()
        bx, by, bw, bh = rects[D2DScrollBar.BTN2]
        assert bx + bw == 200.0


class TestD2DScrollBarThumbSize:
    def test_thumb_size_proportional(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_max=100,
                           page_size=50, orientation=D2DScrollBar.VERTICAL)
        thumb = sb._get_thumb_size()
        assert thumb > 0

    def test_thumb_size_min(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_max=10000,
                           page_size=1, orientation=D2DScrollBar.VERTICAL)
        thumb = sb._get_thumb_size()
        assert thumb >= 18.0

    def test_thumb_size_full_page(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_max=100,
                           page_size=100, orientation=D2DScrollBar.VERTICAL)
        thumb = sb._get_thumb_size()
        assert thumb > 0


class TestD2DScrollBarMouseEvents:
    def test_mouse_down_btn1(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL,
                           scroll_pos=50)
        sb.on_mouse_down((8, 8))
        assert sb._btn1_state == D2DScrollBar.PRESSED
        assert sb.scroll_pos == 49

    def test_mouse_down_btn2(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL,
                           scroll_pos=50)
        sb.on_mouse_down((8, 192))
        assert sb._btn2_state == D2DScrollBar.PRESSED
        assert sb.scroll_pos == 51

    def test_mouse_down_thumb(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=50,
                           orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        tx, ty, tw, th = rects[D2DScrollBar.THUMB]
        sb.on_mouse_down((tx + tw / 2, ty + th / 2))
        assert sb._thumb_state == D2DScrollBar.PRESSED
        assert sb._dragging is True

    def test_mouse_down_track_page_up(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=50,
                           orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        _, track_top, _, _ = rects[D2DScrollBar.TRACK]
        _, thumb_y, _, _ = rects[D2DScrollBar.THUMB]
        click_y = track_top + (thumb_y - track_top) / 2
        sb.on_mouse_down((8, click_y))
        assert sb._track_pressed is True
        assert sb.scroll_pos < 50

    def test_mouse_down_track_page_down(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=50,
                           orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        _, _, _, track_h = rects[D2DScrollBar.TRACK]
        _, track_top, _, _ = rects[D2DScrollBar.TRACK]
        _, thumb_y, _, thumb_h = rects[D2DScrollBar.THUMB]
        click_y = thumb_y + thumb_h + 5
        sb.on_mouse_down((8, click_y))
        assert sb._track_pressed is True
        assert sb.scroll_pos > 50

    def test_mouse_up_after_btn(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL)
        sb.on_mouse_down((8, 8))
        result = sb.on_mouse_up((8, 8))
        assert sb._btn1_state == D2DScrollBar.HOVER
        assert result is True

    def test_mouse_up_after_drag(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=50,
                           orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        tx, ty, tw, th = rects[D2DScrollBar.THUMB]
        sb.on_mouse_down((tx + tw / 2, ty + th / 2))
        result = sb.on_mouse_up((tx + tw / 2, ty + th / 2 + 20))
        assert sb._dragging is False
        assert result is True

    def test_mouse_move_hover_btn1(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL)
        sb.on_mouse_move((8, 8))
        assert sb._btn1_state == D2DScrollBar.HOVER

    def test_mouse_move_hover_btn2(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL)
        sb.on_mouse_move((8, 192))
        assert sb._btn2_state == D2DScrollBar.HOVER

    def test_mouse_move_dragging(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=50,
                           orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        tx, ty, tw, th = rects[D2DScrollBar.THUMB]
        sb.on_mouse_down((tx + tw / 2, ty + th / 2))
        sb.on_mouse_move((tx + tw / 2, ty + th / 2 + 30))
        assert sb._dragging is True

    def test_mouse_leave(self):
        sb = D2DScrollBar((0, 0, 16, 200), orientation=D2DScrollBar.VERTICAL)
        sb.on_mouse_move((8, 8))
        result = sb.on_mouse_leave()
        assert sb._btn1_state == D2DScrollBar.NORMAL
        assert result is True

    def test_mouse_down_disabled(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        sb._state = D2DScrollBar.DISABLED
        result = sb.on_mouse_down((8, 8))
        assert result is False

    def test_mouse_up_without_capture(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        result = sb.on_mouse_up((8, 8))
        assert result is False


class TestD2DScrollBarPosToScroll:
    def test_pos_to_scroll_top(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=0,
                           orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        _, track_top, _, _ = rects[D2DScrollBar.TRACK]
        pos = sb._pos_to_scroll((8, track_top))
        assert pos == 0.0

    def test_pos_to_scroll_bottom(self):
        sb = D2DScrollBar((0, 0, 16, 200), scroll_pos=0,
                           orientation=D2DScrollBar.VERTICAL)
        rects = sb._get_part_rects()
        _, track_top, _, track_h = rects[D2DScrollBar.TRACK]
        pos = sb._pos_to_scroll((8, track_top + track_h))
        assert pos == sb.scroll_max


class TestD2DScrollBarStateName:
    def test_normal_state(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        assert sb._state_for(D2DScrollBar.NORMAL) == 'normal'

    def test_hover_state(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        assert sb._state_for(D2DScrollBar.HOVER) == 'hover'

    def test_pressed_state(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        assert sb._state_for(D2DScrollBar.PRESSED) == 'pressed'

    def test_disabled_state(self):
        sb = D2DScrollBar((0, 0, 16, 200))
        sb._state = D2DScrollBar.DISABLED
        assert sb._state_for(D2DScrollBar.NORMAL) == 'disabled'
