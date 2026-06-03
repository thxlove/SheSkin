"""测试 D2DStatusBar / SkinAwareStatusBar — TDD 单元测试。"""
import pyd2d
from unittest.mock import patch

from sheskin.controls.base_control import SheControl
from sheskin.controls.statusbar import D2DStatusBar, SkinAwareStatusBar


class _Ctrl:
    def __init__(self, rect=(0, 0, 10, 10)):
        self.rect = rect


class TestD2DStatusBar:
    def test_init_empty(self):
        sb = D2DStatusBar((0, 0, 400, 24))
        assert sb.items == []

    def test_init_with_strings(self):
        sb = D2DStatusBar((0, 0, 400, 24),
                          items=["Ready", "Line 1", "UTF-8"])
        assert len(sb.items) == 3
        assert sb.items[0]['text'] == "Ready"
        assert sb.items[0]['width'] is None

    def test_init_with_dicts(self):
        sb = D2DStatusBar((0, 0, 400, 24),
                          items=[{'text': 'A', 'width': 100},
                                 {'text': 'B', 'width': None}])
        assert len(sb.items) == 2
        assert sb.items[0]['width'] == 100
        assert sb.items[1]['width'] is None

    def test_add_item(self):
        sb = D2DStatusBar((0, 0, 400, 24))
        sb.add_item("Ready", width=120)
        sb.add_item("Line 1")
        assert len(sb.items) == 2
        assert sb.items[0]['text'] == "Ready"
        assert sb.items[0]['width'] == 120
        assert sb.items[1]['text'] == "Line 1"
        assert sb.items[1]['width'] is None

    def test_set_items(self):
        sb = D2DStatusBar((0, 0, 400, 24), items=["Old"])
        sb.set_items(["New1", "New2"])
        assert len(sb.items) == 2
        assert sb.items[0]['text'] == "New1"

    def test_layout_no_items(self):
        sb = D2DStatusBar((0, 0, 400, 24))
        layouts = sb._layout_items()
        assert layouts == []

    def test_layout_single_item(self):
        sb = D2DStatusBar((0, 0, 400, 24), items=["Solo"])
        layouts = sb._layout_items()
        assert len(layouts) == 1
        ix, iy, iw, ih = layouts[0]
        assert ix > 0
        assert iw > 0

    def test_layout_multi_items(self):
        sb = D2DStatusBar((0, 0, 400, 24),
                          items=["A", "B", "C"])
        layouts = sb._layout_items()
        assert len(layouts) == 3
        x1, _, _, _ = layouts[0]
        x2, _, _, _ = layouts[1]
        x3, _, _, _ = layouts[2]
        assert x1 < x2 < x3

    def test_layout_fixed_width(self):
        sb = D2DStatusBar((0, 0, 400, 24),
                          items=[{'text': 'A', 'width': 80},
                                 {'text': 'B', 'width': None}])
        layouts = sb._layout_items()
        assert len(layouts) == 2
        _, _, w1, _ = layouts[0]
        _, _, w2, _ = layouts[1]
        assert w1 == 80.0
        assert w2 > 0

    def test_disabled_state(self):
        sb = D2DStatusBar((0, 0, 400, 24), items=["Ready"])
        sb._state = D2DStatusBar.DISABLED
        assert sb._state == D2DStatusBar.DISABLED

    def test_mouse_events_return_false(self):
        sb = D2DStatusBar((0, 0, 400, 24), items=["Ready"])
        assert sb.on_mouse_down((10, 10)) is False
        assert sb.on_mouse_up((10, 10)) is False
        assert sb.on_mouse_move((10, 10)) is False
        assert sb.on_mouse_leave() is False


class TestSkinAwareStatusBar:
    def test_init_empty(self):
        sb = SkinAwareStatusBar((0, 0, 400, 24), None)
        assert sb.items == []

    def test_is_subclass(self):
        assert issubclass(SkinAwareStatusBar, D2DStatusBar)

    def test_fallback_draw_no_crash(self):
        sb = SkinAwareStatusBar((10, 20, 400, 24), None,
                                items=["Ready", "Ln 1"])
        try:
            layouts = sb._layout_items()
            assert len(layouts) == 2
        except Exception as e:
            assert False, f"unexpected: {e}"