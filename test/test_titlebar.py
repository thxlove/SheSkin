"""SheTitleBar 单元测试 — 布局、状态、hit_test、disabled、restore slot。"""
import unittest
import os
import wx
from sheskin.skin import SheSkin
from sheskin.titlebar import SheTitleBar

wx.GetApp() or wx.App(False)


def _get_skin():
    return SheSkin('Aero')


class TestTitleBarLayout(unittest.TestCase):
    """_layout() 返回值与按钮集合验证。"""

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls.skin = _get_skin()
        cls.skin.load()

    def _layout(self, has_max=True, has_min=True, has_help=False,
                is_maximized=False):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        info = tb._layout((0, 0, 800, 30), 'active',
                          has_max, has_min, has_help, is_maximized)
        return tb, info

    def test_all_buttons_enabled(self):
        tb, info = self._layout()
        self.assertIn('close', info['buttons'])
        self.assertIn('max', info['buttons'])
        self.assertIn('min', info['buttons'])
        self.assertNotIn('help', info['buttons'])
        self.assertEqual(tb._disabled_btns, set())

    def test_has_max_false_shows_disabled(self):
        tb, info = self._layout(has_max=False)
        self.assertIn('max', info['buttons'])
        self.assertIn('max', tb._disabled_btns)

    def test_has_min_false_shows_disabled(self):
        tb, info = self._layout(has_min=False)
        self.assertIn('min', info['buttons'])
        self.assertIn('min', tb._disabled_btns)

    def test_both_disabled(self):
        tb, info = self._layout(has_max=False, has_min=False)
        self.assertIn('max', tb._disabled_btns)
        self.assertIn('min', tb._disabled_btns)

    def test_has_help_true(self):
        tb, info = self._layout(has_help=True)
        self.assertIn('help', info['buttons'])

    def test_has_help_false_not_in_layout(self):
        tb, info = self._layout(has_help=False)
        self.assertNotIn('help', info['buttons'])

    def test_maximized_uses_restore_slot(self):
        tb, info = self._layout(is_maximized=True)
        max_slots = info['buttons']['max']['slots']
        self.assertEqual(max_slots['normal'], 16)
        self.assertEqual(max_slots['hover'], 17)
        self.assertEqual(max_slots['pressed'], 18)
        self.assertEqual(max_slots['disabled'], 19)

    def test_not_maximized_uses_max_slot(self):
        tb, info = self._layout(is_maximized=False)
        max_slots = info['buttons']['max']['slots']
        self.assertEqual(max_slots['normal'], 12)

    def test_close_button_always_present(self):
        _, info = self._layout()
        self.assertIn('close', info['buttons'])

    def test_tool_window_no_max_min(self):
        tb = SheTitleBar(self.skin, 'ToolWindow')
        info = tb._layout((0, 0, 400, 20), 'active', True, True, False, False)
        if info is not None:
            self.assertIn('close', info['buttons'])
            self.assertNotIn('max', info['buttons'])
            self.assertNotIn('min', info['buttons'])


class TestTitleBarBtnState(unittest.TestCase):
    """_btn_state_name() 逻辑验证。"""

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls.skin = _get_skin()
        cls.skin.load()

    def test_normal_state(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        self.assertEqual(tb._btn_state_name('close'), 'normal')

    def test_hover_state(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        tb._hover_btn = 'close'
        self.assertEqual(tb._btn_state_name('close'), 'hover')

    def test_pressed_state(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        tb._pressed_btn = 'close'
        self.assertEqual(tb._btn_state_name('close'), 'pressed')

    def test_pressed_overrides_hover(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        tb._hover_btn = 'close'
        tb._pressed_btn = 'close'
        self.assertEqual(tb._btn_state_name('close'), 'pressed')

    def test_disabled_overrides_all(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb._layout((0, 0, 800, 30), 'active', False, True, False, False)
        tb._hover_btn = 'max'
        tb._pressed_btn = 'max'
        self.assertEqual(tb._btn_state_name('max'), 'disabled')

    def test_disabled_does_not_affect_other_buttons(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb._layout((0, 0, 800, 30), 'active', False, True, False, False)
        self.assertEqual(tb._btn_state_name('close'), 'normal')
        self.assertEqual(tb._btn_state_name('min'), 'normal')


class TestTitleBarHitTest(unittest.TestCase):
    """hit_test() 返回值与 disabled 穿透验证。"""

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls.skin = _get_skin()
        cls.skin.load()

    def _btn_center(self, info, btn_name):
        bx, by, bw, bh = info['buttons'][btn_name]['rect']
        return (bx + bw / 2, by + bh / 2)

    def test_hit_close(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        info = tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        pt = self._btn_center(info, 'close')
        self.assertEqual(tb.hit_test(pt, (0, 0, 800, 30), 'active',
                                     True, True, False, False), 'close')

    def test_hit_max(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        info = tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        pt = self._btn_center(info, 'max')
        self.assertEqual(tb.hit_test(pt, (0, 0, 800, 30), 'active',
                                     True, True, False, False), 'max')

    def test_hit_min(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        info = tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        pt = self._btn_center(info, 'min')
        self.assertEqual(tb.hit_test(pt, (0, 0, 800, 30), 'active',
                                     True, True, False, False), 'min')

    def test_disabled_max_penetrates_to_titlebar(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        info = tb._layout((0, 0, 800, 30), 'active', False, True, False, False)
        pt = self._btn_center(info, 'max')
        result = tb.hit_test(pt, (0, 0, 800, 30), 'active',
                             False, True, False, False)
        self.assertNotEqual(result, 'max')
        self.assertEqual(result, 'titlebar')

    def test_disabled_min_penetrates_to_titlebar(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        info = tb._layout((0, 0, 800, 30), 'active', True, False, False, False)
        pt = self._btn_center(info, 'min')
        result = tb.hit_test(pt, (0, 0, 800, 30), 'active',
                             True, False, False, False)
        self.assertNotEqual(result, 'min')

    def test_hit_titlebar_area(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        result = tb.hit_test((400, 15), (0, 0, 800, 30), 'active',
                             True, True, False, False)
        self.assertEqual(result, 'titlebar')

    def test_hit_outside_returns_none(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        result = tb.hit_test((400, 100), (0, 0, 800, 30), 'active',
                             True, True, False, False)
        self.assertIsNone(result)


class TestTitleBarMouseEvents(unittest.TestCase):
    """on_mouse_down/up/move/leave 交互验证。"""

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls.skin = _get_skin()
        cls.skin.load()

    def _btn_center(self, tb, btn_name, has_max=True, has_min=True):
        info = tb._layout((0, 0, 800, 30), 'active',
                          has_max, has_min, False, False)
        bx, by, bw, bh = info['buttons'][btn_name]['rect']
        return (bx + bw / 2, by + bh / 2)

    def test_mouse_down_on_close(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        pt = self._btn_center(tb, 'close')
        self.assertTrue(tb.on_mouse_down(pt, (0, 0, 800, 30), 'active',
                                         True, True, False, False))
        self.assertEqual(tb._pressed_btn, 'close')

    def test_mouse_down_on_disabled_max(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        pt = self._btn_center(tb, 'max', has_max=False)
        self.assertFalse(tb.on_mouse_down(pt, (0, 0, 800, 30), 'active',
                                          False, True, False, False))

    def test_mouse_up_clears_pressed(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        pt = self._btn_center(tb, 'close')
        tb.on_mouse_down(pt, (0, 0, 800, 30), 'active', True, True, False, False)
        self.assertTrue(tb.on_mouse_up(pt, (0, 0, 800, 30), 'active',
                                       True, True, False, False))
        self.assertIsNone(tb._pressed_btn)

    def test_mouse_move_hover(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        pt = self._btn_center(tb, 'close')
        self.assertTrue(tb.on_mouse_move(pt, (0, 0, 800, 30), 'active',
                                         True, True, False, False))
        self.assertEqual(tb._hover_btn, 'close')

    def test_mouse_leave_clears_hover(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        pt = self._btn_center(tb, 'close')
        tb.on_mouse_move(pt, (0, 0, 800, 30), 'active', True, True, False, False)
        self.assertTrue(tb.on_mouse_leave())
        self.assertIsNone(tb._hover_btn)

    def test_mouse_leave_no_hover(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        self.assertFalse(tb.on_mouse_leave())

    def test_set_hover(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb.set_hover('close')
        self.assertEqual(tb._hover_btn, 'close')

    def test_set_pressed(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb.set_pressed('max')
        self.assertEqual(tb._pressed_btn, 'max')

    def test_reset_state(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb.set_hover('close')
        tb.set_pressed('max')
        tb.reset_state()
        self.assertIsNone(tb._hover_btn)
        self.assertIsNone(tb._pressed_btn)


class TestTitleBarSyncContext(unittest.TestCase):
    """sync_context 上下文传递验证。"""

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls.skin = _get_skin()
        cls.skin.load()

    def test_sync_context_stores_values(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb.sync_context((10, 20, 300, 30), 'inactive', False, False, True, True)
        self.assertEqual(tb._ctx_rect, (10, 20, 300, 30))
        self.assertEqual(tb._ctx_state, 'inactive')
        self.assertFalse(tb._ctx_has_max)
        self.assertFalse(tb._ctx_has_min)
        self.assertTrue(tb._ctx_has_help)
        self.assertTrue(tb._ctx_is_maximized)

    def test_sync_context_default_is_maximized(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb.sync_context((0, 0, 800, 30), 'active', True, True, False)
        self.assertFalse(tb._ctx_is_maximized)

    def test_hit_test_uses_context(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        tb.sync_context((0, 0, 800, 30), 'active', True, True, False, False)
        result = tb.hit_test((400, 15))
        self.assertEqual(result, 'titlebar')


class TestTitleBarNcHitTest(unittest.TestCase):
    """get_nchittest_code 代理 hit_test 验证。"""

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls.skin = _get_skin()
        cls.skin.load()

    def test_get_nchittest_code_close(self):
        tb = SheTitleBar(self.skin, 'NormalWindow')
        info = tb._layout((0, 0, 800, 30), 'active', True, True, False, False)
        bx, by, bw, bh = info['buttons']['close']['rect']
        tb.sync_context((0, 0, 800, 30), 'active', True, True, False, False)
        result = tb.get_nchittest_code((bx + bw / 2, by + bh / 2))
        self.assertEqual(result, 'close')


if __name__ == '__main__':
    unittest.main()
