"""D2DBitmapButton / SkinAwareBitmapButton 单元测试。"""
import unittest
from unittest.mock import MagicMock
import wx

app = None


def _get_app():
    global app
    if app is None:
        app = wx.GetApp() or wx.App(False)
    return app


def _make_icon(r=60, g=160, b=60, size=16):
    """创建测试用图标。"""
    img = wx.Image(size, size)
    img.SetRGB(wx.Rect(0, 0, size, size), r, g, b)
    img.SetAlpha(bytearray([200] * size * size))
    return wx.Bitmap(img)


class TestD2DBitmapButton(unittest.TestCase):
    """D2DBitmapButton 核心逻辑测试。"""

    def setUp(self):
        _get_app()

    def test_init_default(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton, ICON_LEFT_TEXT
        btn = D2DBitmapButton((10, 20, 80, 36))
        self.assertEqual(btn._rect, (10, 20, 80, 36))
        self.assertEqual(btn._text, '')
        self.assertIsNone(btn._icon_img)
        self.assertEqual(btn._layout_mode, ICON_LEFT_TEXT)
        self.assertEqual(btn._state, btn.NORMAL)

    def test_init_with_icon_and_text(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton, ICON_ONLY
        icon = _make_icon()
        btn = D2DBitmapButton((0, 0, 36, 36), icon=icon, text="Test",
                               layout_mode=ICON_ONLY,
                               on_click=lambda: None)
        self.assertIsNotNone(btn._icon_img)
        self.assertEqual(btn._text, "Test")
        self.assertEqual(btn._layout_mode, ICON_ONLY)

    def test_set_icon(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton
        btn = D2DBitmapButton((0, 0, 36, 36))
        self.assertIsNone(btn._icon_img)
        icon = _make_icon()
        btn.set_icon(icon)
        self.assertIsNotNone(btn._icon_img)

    def test_set_layout_mode(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton, ICON_ABOVE_TEXT
        btn = D2DBitmapButton((0, 0, 36, 36))
        btn.set_layout_mode(ICON_ABOVE_TEXT)
        self.assertEqual(btn._layout_mode, ICON_ABOVE_TEXT)

    def test_state_machine_normal(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton
        btn = D2DBitmapButton((0, 0, 36, 36))
        self.assertEqual(btn._state, btn.NORMAL)

    def test_hit_test(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton
        btn = D2DBitmapButton((10, 20, 80, 36))
        self.assertTrue(btn.hit_test((50, 38)))
        self.assertFalse(btn.hit_test((5, 38)))
        self.assertFalse(btn.hit_test((50, 10)))

    def test_mouse_down_hover_up(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton
        clicked = []
        btn = D2DBitmapButton((0, 0, 80, 36), on_click=lambda: clicked.append(1))
        # mouse_down → PRESSED
        btn.on_mouse_down((40, 18))
        self.assertEqual(btn._state, btn.PRESSED)
        self.assertTrue(btn._captured)
        # mouse_up in bounds → HOVER + activate
        btn.on_mouse_up((40, 18))
        self.assertEqual(btn._state, btn.HOVER)
        self.assertFalse(btn._captured)
        self.assertEqual(len(clicked), 1)

    def test_mouse_down_drag_out_up(self):
        """拖出按钮区域后松开 — 不触发 click，状态回到 NORMAL。"""
        from sheskin.controls.bitmapbutton import D2DBitmapButton
        clicked = []
        btn = D2DBitmapButton((0, 0, 80, 36), on_click=lambda: clicked.append(1))
        btn.on_mouse_down((40, 18))
        # mouse_move out of bounds while captured → stay PRESSED
        btn.on_mouse_move((200, 200))
        self.assertEqual(btn._state, btn.PRESSED)
        # mouse_up out of bounds → NORMAL, no click
        btn.on_mouse_up((200, 200))
        self.assertEqual(btn._state, btn.NORMAL)
        self.assertEqual(len(clicked), 0)

    def test_disabled_no_interaction(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton
        clicked = []
        btn = D2DBitmapButton((0, 0, 80, 36), on_click=lambda: clicked.append(1))
        btn._state = btn.DISABLED
        self.assertFalse(btn.on_mouse_down((40, 18)))
        self.assertFalse(btn.on_mouse_up((40, 18)))
        self.assertEqual(len(clicked), 0)

    def test_mouse_leave(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton
        btn = D2DBitmapButton((0, 0, 80, 36))
        btn.on_mouse_move((40, 18))  # hover
        self.assertEqual(btn._state, btn.HOVER)
        btn.on_mouse_leave()
        self.assertEqual(btn._state, btn.NORMAL)

    def test_set_on_click(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton
        btn = D2DBitmapButton((0, 0, 80, 36))
        clicked = []
        btn.set_on_click(lambda: clicked.append(1))
        btn.on_mouse_down((40, 18))
        btn.on_mouse_up((40, 18))
        self.assertEqual(len(clicked), 1)

    def test_icon_cache_cleared_on_set_icon(self):
        from sheskin.controls.bitmapbutton import D2DBitmapButton
        btn = D2DBitmapButton((0, 0, 36, 36), icon=_make_icon())
        btn._icon_cache['test'] = 'dummy'
        btn._grey_icon_cache['test'] = 'dummy'
        btn.set_icon(_make_icon(200, 80, 80))
        self.assertEqual(len(btn._icon_cache), 0)
        self.assertEqual(len(btn._grey_icon_cache), 0)


class TestSkinAwareBitmapButton(unittest.TestCase):
    """SkinAwareBitmapButton 测试。"""

    def setUp(self):
        _get_app()

    def test_init_with_mock_ctx(self):
        from sheskin.controls.bitmapbutton import SkinAwareBitmapButton
        mock_ctx = MagicMock()
        mock_ctx.get_font_info.return_value = None
        btn = SkinAwareBitmapButton((0, 0, 80, 36), mock_ctx, icon=_make_icon(),
                                     text="Test")
        self.assertEqual(btn._text, "Test")
        self.assertIsNotNone(btn._icon_img)

    def test_fallback_draw(self):
        """无皮肤数据时 fallback 到 D2DBitmapButton.draw。"""
        from sheskin.controls.bitmapbutton import SkinAwareBitmapButton
        mock_ctx = MagicMock()
        mock_ctx.get_block.return_value = None  # 无皮肤 block
        btn = SkinAwareBitmapButton((0, 0, 80, 36), mock_ctx, text="FB")
        # 验证不崩溃 — draw 需要 D2D 上下文，此处仅验证 fallback 路径可达
        self.assertIsNotNone(btn._draw_fallback)


class TestBitmapButtonConstants(unittest.TestCase):
    """布局模式常量测试。"""

    def test_layout_mode_values(self):
        from sheskin.controls.bitmapbutton import ICON_ONLY, ICON_ABOVE_TEXT, ICON_LEFT_TEXT
        self.assertEqual(ICON_ONLY, 0)
        self.assertEqual(ICON_ABOVE_TEXT, 1)
        self.assertEqual(ICON_LEFT_TEXT, 2)


if __name__ == '__main__':
    unittest.main()
