"""D2DTabCtrl 单元测试 — 页面管理、布局、状态、hit_test、鼠标交互、disabled。"""
import unittest
from unittest.mock import MagicMock
from sheskin.controls.tabctrl import (
    D2DTabCtrl, TABCTRL_MIN_TAB_WIDTH, TABCTRL_TAB_PAD_X,
    TABCTRL_BTN_MIN_HEIGHT,
)


class _MockCtrl:
    def __init__(self):
        self._visible = True


class TestD2DTabCtrlInit(unittest.TestCase):

    def test_init_defaults(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        self.assertEqual(tc.rect, (0, 0, 400, 300))
        self.assertEqual(tc.orientation, D2DTabCtrl.TOP)
        self.assertEqual(tc.page_count, 0)
        self.assertEqual(tc.selected, -1)
        self.assertIsNone(tc._on_change)
        self.assertEqual(tc._hovered, -1)
        self.assertEqual(tc._pressed_tab, -1)
        self.assertFalse(tc._captured)

    def test_init_with_orientation(self):
        tc = D2DTabCtrl((0, 0, 400, 300), orientation=D2DTabCtrl.BOTTOM)
        self.assertEqual(tc.orientation, D2DTabCtrl.BOTTOM)

    def test_init_with_on_change(self):
        calls = []
        tc = D2DTabCtrl((0, 0, 400, 300), on_change=lambda i, o: calls.append(i))
        self.assertIsNotNone(tc._on_change)

    def test_init_with_default_page(self):
        tc = D2DTabCtrl((0, 0, 400, 300), default_page=0)
        self.assertEqual(tc._default_page, 0)


class TestD2DTabCtrlAddPage(unittest.TestCase):

    def test_add_page_returns_index(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        idx = tc.add_page('Tab1')
        self.assertEqual(idx, 0)
        self.assertEqual(tc.page_count, 1)

    def test_add_multiple_pages(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc.add_page('C')
        self.assertEqual(tc.page_count, 3)

    def test_first_page_auto_selected(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('First')
        self.assertEqual(tc.selected, 0)

    def test_add_page_disabled(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('Disabled', disabled=True)
        self.assertTrue(tc._pages[0]['disabled'])

    def test_add_page_with_controls(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        ctrl = _MockCtrl()
        tc.add_page('Tab', controls=[ctrl])
        self.assertEqual(list(tc._page_vboxes[0]._walk_controls()), [ctrl])

    def test_add_page_clears_layout(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc._tab_layouts = [(0, 0, 100, 24)]
        tc.add_page('B')
        self.assertEqual(tc._tab_layouts, [])

    def test_default_page_selects_correct_page(self):
        tc = D2DTabCtrl((0, 0, 400, 300), default_page=1)
        tc.add_page('A')
        self.assertEqual(tc.selected, -1)
        tc.add_page('B')
        self.assertEqual(tc.selected, 1)

    def test_default_page_zero_auto_selects(self):
        tc = D2DTabCtrl((0, 0, 400, 300), default_page=0)
        tc.add_page('First')
        self.assertEqual(tc.selected, 0)


class TestD2DTabCtrlSelectPage(unittest.TestCase):

    def test_select_page(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc.select_page(1)
        self.assertEqual(tc.selected, 1)

    def test_select_same_page_no_change(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc.select_page(0)
        self.assertEqual(tc.selected, 0)

    def test_select_invalid_index(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.select_page(99)
        self.assertEqual(tc.selected, 0)

    def test_select_page_triggers_on_change(self):
        calls = []
        tc = D2DTabCtrl((0, 0, 400, 300),
                        on_change=lambda i, o: calls.append((i, o)))
        tc.add_page('A')
        tc.add_page('B')
        tc.select_page(1)
        self.assertEqual(calls, [(1, 0)])

    def test_select_page_updates_visibility(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        c1 = _MockCtrl()
        c2 = _MockCtrl()
        tc.add_page('A', controls=[c1])
        tc.add_page('B', controls=[c2])
        tc.select_page(1)
        self.assertFalse(c1._visible)
        self.assertTrue(c2._visible)


class TestD2DTabCtrlSetPageControls(unittest.TestCase):

    def test_set_page_controls(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        ctrl = _MockCtrl()
        tc.set_page_controls(0, [ctrl])
        self.assertEqual(list(tc._page_vboxes[0]._walk_controls()), [ctrl])

    def test_set_page_controls_invalid_index(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.set_page_controls(99, [])
        self.assertEqual(tc._page_vboxes, [])

    def test_set_page_controls_marks_stale(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc._page_visibility_stale = False
        tc.set_page_controls(0, [_MockCtrl()])
        self.assertTrue(tc._page_visibility_stale)


class TestD2DTabCtrlPageVisibility(unittest.TestCase):

    def test_apply_page_visibility(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        c1 = _MockCtrl()
        c2 = _MockCtrl()
        c3 = _MockCtrl()
        tc.add_page('A', controls=[c1])
        tc.add_page('B', controls=[c2])
        tc.add_page('C', controls=[c3])
        tc._apply_page_visibility(1)
        self.assertFalse(c1._visible)
        self.assertTrue(c2._visible)
        self.assertFalse(c3._visible)

    def test_flush_page_visibility(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        c1 = _MockCtrl()
        c2 = _MockCtrl()
        tc.add_page('A', controls=[c1])
        tc.add_page('B', controls=[c2])
        tc._page_visibility_stale = True
        tc._flush_page_visibility()
        self.assertFalse(tc._page_visibility_stale)
        self.assertTrue(c1._visible)
        self.assertFalse(c2._visible)

    def test_flush_not_stale_no_op(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc._page_visibility_stale = False
        tc._flush_page_visibility()
        self.assertFalse(tc._page_visibility_stale)


class TestD2DTabCtrlState(unittest.TestCase):

    def test_normal_state(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        self.assertEqual(tc._get_state_name(0), 'pressed')

    def test_hover_state(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc._hovered = 1
        self.assertEqual(tc._get_state_name(1), 'hover')

    def test_pressed_state(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc._captured = True
        tc._pressed_tab = 1
        self.assertEqual(tc._get_state_name(1), 'pressed')

    def test_selected_shows_pressed(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc.select_page(1)
        self.assertEqual(tc._get_state_name(1), 'pressed')

    def test_disabled_overrides_all(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B', disabled=True)
        tc._hovered = 1
        self.assertEqual(tc._get_state_name(1), 'disabled')

    def test_out_of_range_returns_normal(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        self.assertEqual(tc._get_state_name(99), 'normal')


class TestD2DTabCtrlHitTest(unittest.TestCase):

    def setUp(self):
        self._saved_fmt = D2DTabCtrl._dwrite_text_fmt
        D2DTabCtrl._dwrite_text_fmt = MagicMock()

    def tearDown(self):
        D2DTabCtrl._dwrite_text_fmt = self._saved_fmt

    def test_hit_tab_first(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc._ensure_layout()
        idx = tc._hit_tab((20, 12))
        self.assertEqual(idx, 0)

    def test_hit_tab_second(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc._ensure_layout()
        l0 = tc._tab_layouts[0]
        l1 = tc._tab_layouts[1]
        mid_x = l1[0] + l1[2] / 2
        idx = tc._hit_tab((mid_x, 12))
        self.assertEqual(idx, 1)

    def test_hit_tab_miss(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc._ensure_layout()
        idx = tc._hit_tab((200, 100))
        self.assertEqual(idx, -1)

    def test_hit_tab_empty(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        idx = tc._hit_tab((10, 10))
        self.assertEqual(idx, -1)

    def test_hit_test_returns_bool(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc._ensure_layout()
        self.assertTrue(tc.hit_test((20, 12)))
        self.assertFalse(tc.hit_test((200, 100)))


class TestD2DTabCtrlMouseEvents(unittest.TestCase):

    def setUp(self):
        self._saved_fmt = D2DTabCtrl._dwrite_text_fmt
        D2DTabCtrl._dwrite_text_fmt = MagicMock()

    def tearDown(self):
        D2DTabCtrl._dwrite_text_fmt = self._saved_fmt

    def _setup_tc(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc.add_page('C', disabled=True)
        tc._ensure_layout()
        return tc

    def _tab_center(self, tc, idx):
        tx, ty, tw, th = tc._tab_layouts[idx]
        return (tx + tw / 2, ty + th / 2)

    def test_mouse_down_on_enabled(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 1)
        self.assertTrue(tc.on_mouse_down(pt))
        self.assertTrue(tc._captured)
        self.assertEqual(tc._pressed_tab, 1)

    def test_mouse_down_on_disabled(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 2)
        self.assertFalse(tc.on_mouse_down(pt))
        self.assertFalse(tc._captured)

    def test_mouse_down_miss(self):
        tc = self._setup_tc()
        self.assertFalse(tc.on_mouse_down((200, 100)))

    def test_mouse_up_selects_page(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 1)
        tc.on_mouse_down(pt)
        tc.on_mouse_up(pt)
        self.assertEqual(tc.selected, 1)
        self.assertFalse(tc._captured)
        self.assertEqual(tc._pressed_tab, -1)

    def test_mouse_up_drag_out_cancels(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 1)
        tc.on_mouse_down(pt)
        result = tc.on_mouse_up((200, 100))
        self.assertTrue(result)
        self.assertEqual(tc.selected, 0)

    def test_mouse_up_without_down(self):
        tc = self._setup_tc()
        self.assertFalse(tc.on_mouse_up((10, 10)))

    def test_mouse_move_hover(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 1)
        self.assertTrue(tc.on_mouse_move(pt))
        self.assertEqual(tc._hovered, 1)

    def test_mouse_move_same_no_change(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 1)
        tc.on_mouse_move(pt)
        self.assertFalse(tc.on_mouse_move(pt))

    def test_mouse_move_leave(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 1)
        tc.on_mouse_move(pt)
        self.assertTrue(tc.on_mouse_move((200, 100)))
        self.assertEqual(tc._hovered, -1)

    def test_mouse_move_during_capture(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 1)
        tc.on_mouse_down(pt)
        self.assertFalse(tc.on_mouse_move((200, 100)))

    def test_mouse_move_disabled_tab(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 2)
        tc.on_mouse_move(pt)
        self.assertEqual(tc._hovered, -1)

    def test_mouse_leave(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 1)
        tc.on_mouse_move(pt)
        self.assertTrue(tc.on_mouse_leave())
        self.assertEqual(tc._hovered, -1)
        self.assertFalse(tc._captured)

    def test_mouse_leave_no_hover(self):
        tc = self._setup_tc()
        self.assertFalse(tc.on_mouse_leave())

    def test_mouse_leave_clears_capture(self):
        tc = self._setup_tc()
        pt = self._tab_center(tc, 1)
        tc.on_mouse_down(pt)
        tc.on_mouse_leave()
        self.assertFalse(tc._captured)
        self.assertEqual(tc._pressed_tab, -1)


class TestD2DTabCtrlLayout(unittest.TestCase):

    def setUp(self):
        self._saved_fmt = D2DTabCtrl._dwrite_text_fmt
        D2DTabCtrl._dwrite_text_fmt = MagicMock()

    def tearDown(self):
        D2DTabCtrl._dwrite_text_fmt = self._saved_fmt

    def test_horizontal_layout(self):
        tc = D2DTabCtrl((0, 0, 400, 300), orientation=D2DTabCtrl.TOP)
        tc.add_page('A')
        tc.add_page('B')
        tc._ensure_layout()
        self.assertEqual(len(tc._tab_layouts), 2)
        l0 = tc._tab_layouts[0]
        l1 = tc._tab_layouts[1]
        self.assertAlmostEqual(l1[0], l0[0] + l0[2])
        self.assertGreaterEqual(l0[2], TABCTRL_MIN_TAB_WIDTH)
        self.assertGreaterEqual(l0[3], TABCTRL_BTN_MIN_HEIGHT)

    def test_vertical_layout(self):
        tc = D2DTabCtrl((0, 0, 400, 300), orientation=D2DTabCtrl.LEFT)
        tc.add_page('A')
        tc.add_page('B')
        tc._ensure_layout()
        self.assertEqual(len(tc._tab_layouts), 2)
        l0 = tc._tab_layouts[0]
        l1 = tc._tab_layouts[1]
        self.assertAlmostEqual(l1[1], l0[1] + l0[3])

    def test_body_rect_horizontal(self):
        tc = D2DTabCtrl((0, 0, 400, 300), orientation=D2DTabCtrl.TOP)
        tc.add_page('A')
        tc._ensure_layout()
        bx, by, bw, bh = tc._body_rect
        self.assertGreater(by, 0)
        self.assertGreater(bh, 0)

    def test_body_rect_vertical(self):
        tc = D2DTabCtrl((0, 0, 400, 300), orientation=D2DTabCtrl.LEFT)
        tc.add_page('A')
        tc._ensure_layout()
        bx, by, bw, bh = tc._body_rect
        self.assertGreater(bx, 0)
        self.assertGreater(bw, 0)

    def test_is_horizontal(self):
        tc_top = D2DTabCtrl((0, 0, 400, 300), orientation=D2DTabCtrl.TOP)
        tc_bottom = D2DTabCtrl((0, 0, 400, 300), orientation=D2DTabCtrl.BOTTOM)
        tc_left = D2DTabCtrl((0, 0, 400, 300), orientation=D2DTabCtrl.LEFT)
        tc_right = D2DTabCtrl((0, 0, 400, 300), orientation=D2DTabCtrl.RIGHT)
        self.assertTrue(tc_top._is_horizontal())
        self.assertTrue(tc_bottom._is_horizontal())
        self.assertFalse(tc_left._is_horizontal())
        self.assertFalse(tc_right._is_horizontal())

    def test_estimate_text_width(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        w = tc._estimate_text_width('Hello')
        self.assertGreaterEqual(w, TABCTRL_MIN_TAB_WIDTH)

    def test_empty_pages_layout(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc._layout_tabs(None)
        self.assertEqual(tc._tab_layouts, [])

    def test_layout_cached(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc._ensure_layout()
        layouts1 = list(tc._tab_layouts)
        tc._ensure_layout()
        self.assertEqual(tc._tab_layouts, layouts1)

    def test_layout_invalidated_on_new_page(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc._ensure_layout()
        self.assertEqual(len(tc._tab_layouts), 1)
        tc.add_page('B')
        self.assertEqual(tc._tab_layouts, [])
        tc._ensure_layout()
        self.assertEqual(len(tc._tab_layouts), 2)


class TestD2DTabCtrlGetSelected(unittest.TestCase):

    def test_get_selected(self):
        tc = D2DTabCtrl((0, 0, 400, 300))
        tc.add_page('A')
        tc.add_page('B')
        tc.select_page(1)
        self.assertEqual(tc.get_selected(), 1)


if __name__ == '__main__':
    unittest.main()
