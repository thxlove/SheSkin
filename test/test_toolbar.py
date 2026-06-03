"""D2DToolBar 单元测试 — 布局、状态、hit_test、disabled、图标灰化、set_rect。"""
import unittest
from unittest.mock import patch, MagicMock
import wx
from sheskin.controls.toolbar import (
    D2DToolBar, _make_grey_image, _icon_to_image,
    TOOLBAR_BTN_MIN_WIDTH, TOOLBAR_SEP_WIDTH, TOOLBAR_ICON_SIZE,
)

_app = None


def _ensure_app():
    global _app
    if _app is None:
        _app = wx.GetApp() or wx.App(False)


class TestMakeGreyImage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _ensure_app()

    def test_none_returns_none(self):
        self.assertIsNone(_make_grey_image(None))

    def test_grey_luminance(self):
        img = wx.Image(1, 1)
        img.SetRGB(wx.Rect(0, 0, 1, 1), 255, 0, 128)
        img.SetAlpha(bytearray([200]))
        grey = _make_grey_image(img)
        d = grey.GetData()
        lum = int(0.299 * 255 + 0.587 * 0 + 0.114 * 128)
        expected = int(lum * 0.6 + 128 * 0.4)
        self.assertEqual(d[0], expected)
        self.assertEqual(d[1], expected)
        self.assertEqual(d[2], expected)

    def test_grey_preserves_alpha(self):
        img = wx.Image(2, 2)
        img.SetRGB(wx.Rect(0, 0, 2, 2), 100, 150, 200)
        alpha = bytearray([50, 100, 150, 200])
        img.SetAlpha(bytes(alpha))
        grey = _make_grey_image(img)
        self.assertEqual(grey.GetAlpha(), bytes(alpha))

    def test_white_becomes_bright_grey(self):
        img = wx.Image(1, 1)
        img.SetRGB(wx.Rect(0, 0, 1, 1), 255, 255, 255)
        img.SetAlpha(bytearray([255]))
        grey = _make_grey_image(img)
        d = grey.GetData()
        self.assertEqual(d[0], d[1])
        self.assertEqual(d[1], d[2])
        self.assertGreater(d[0], 128)

    def test_black_becomes_dim_grey(self):
        img = wx.Image(1, 1)
        img.SetRGB(wx.Rect(0, 0, 1, 1), 0, 0, 0)
        img.SetAlpha(bytearray([255]))
        grey = _make_grey_image(img)
        d = grey.GetData()
        self.assertEqual(d[0], d[1])
        self.assertEqual(d[1], d[2])
        self.assertLess(d[0], 128)

    def test_no_alpha_image(self):
        img = wx.Image(2, 2)
        img.SetRGB(wx.Rect(0, 0, 2, 2), 128, 64, 32)
        grey = _make_grey_image(img)
        self.assertTrue(grey.HasAlpha())
        d = grey.GetData()
        self.assertEqual(d[0], d[1])
        self.assertEqual(d[1], d[2])


class TestIconToImage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _ensure_app()

    def test_none_returns_none(self):
        self.assertIsNone(_icon_to_image(None))

    def test_wx_image_passthrough(self):
        img = wx.Image(16, 16)
        result = _icon_to_image(img)
        self.assertIs(result, img)

    def test_wx_bitmap_converted(self):
        bmp = wx.Bitmap(wx.Image(16, 16))
        result = _icon_to_image(bmp)
        self.assertIsInstance(result, wx.Image)
        self.assertEqual(result.GetWidth(), 16)

    def test_other_type_returns_none(self):
        self.assertIsNone(_icon_to_image("not_an_icon"))


class TestD2DToolBarInit(unittest.TestCase):

    def test_init_defaults(self):
        tb = D2DToolBar((0, 0, 400, 30))
        self.assertEqual(tb.rect, (0, 0, 400, 30))
        self.assertEqual(tb._items, [])
        self.assertEqual(tb._hovered, -1)
        self.assertEqual(tb._pressed, -1)
        self.assertFalse(tb._captured)
        self.assertTrue(tb._layout_dirty)

    def test_init_with_on_click(self):
        calls = []
        tb = D2DToolBar((0, 0, 400, 30), on_click=lambda i, d: calls.append(i))
        self.assertIsNotNone(tb._on_click)


class TestD2DToolBarAddItems(unittest.TestCase):

    def test_add_button(self):
        tb = D2DToolBar((0, 0, 400, 30))
        idx = tb.add_button('Open')
        self.assertEqual(idx, 0)
        self.assertEqual(len(tb._items), 1)
        self.assertEqual(tb._items[0]['type'], 'button')
        self.assertEqual(tb._items[0]['text'], 'Open')
        self.assertFalse(tb._items[0]['disabled'])

    def test_add_button_disabled(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('Print', disabled=True)
        self.assertTrue(tb._items[0]['disabled'])

    def test_add_button_with_data(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('Save', data='save_cmd')
        self.assertEqual(tb._items[0]['data'], 'save_cmd')

    def test_add_button_with_icon(self):
        _ensure_app()
        img = wx.Image(16, 16)
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('New', icon=img)
        self.assertIsNotNone(tb._items[0]['icon'])

    def test_add_separator(self):
        tb = D2DToolBar((0, 0, 400, 30))
        idx = tb.add_separator()
        self.assertEqual(idx, 0)
        self.assertEqual(tb._items[0]['type'], 'separator')

    def test_add_marks_dirty(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb._layout_dirty = False
        tb.add_button('A')
        self.assertTrue(tb._layout_dirty)

    def test_add_separator_marks_dirty(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb._layout_dirty = False
        tb.add_separator()
        self.assertTrue(tb._layout_dirty)


class TestD2DToolBarSetButtonDisabled(unittest.TestCase):

    def test_disable_button(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A')
        result = tb.set_button_disabled(0, True)
        self.assertTrue(result)
        self.assertTrue(tb._items[0]['disabled'])
        self.assertTrue(tb._layout_dirty)

    def test_enable_button(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A', disabled=True)
        result = tb.set_button_disabled(0, False)
        self.assertTrue(result)
        self.assertFalse(tb._items[0]['disabled'])

    def test_no_change_returns_false(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A')
        result = tb.set_button_disabled(0, False)
        self.assertFalse(result)

    def test_invalid_index_returns_false(self):
        tb = D2DToolBar((0, 0, 400, 30))
        result = tb.set_button_disabled(99, True)
        self.assertFalse(result)

    def test_separator_index_returns_false(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_separator()
        result = tb.set_button_disabled(0, True)
        self.assertFalse(result)


class TestD2DToolBarSetRect(unittest.TestCase):

    def test_same_rect_no_invalidation(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb._layout_dirty = False
        tb.set_rect((0, 0, 400, 30))
        self.assertFalse(tb._layout_dirty)

    def test_different_rect_invalidates(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb._layout_dirty = False
        tb.set_rect((0, 0, 500, 30))
        self.assertTrue(tb._layout_dirty)

    def test_position_change_invalidates(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb._layout_dirty = False
        tb.set_rect((10, 0, 400, 30))
        self.assertTrue(tb._layout_dirty)


class TestD2DToolBarLayout(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _ensure_app()

    def setUp(self):
        self._saved_fmt = D2DToolBar._dwrite_text_fmt
        D2DToolBar._dwrite_text_fmt = MagicMock()

    def tearDown(self):
        D2DToolBar._dwrite_text_fmt = self._saved_fmt

    def test_horizontal_text_buttons(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A')
        tb.add_button('B')
        tb._ensure_layout()
        layouts = tb._item_layouts
        self.assertEqual(len(layouts), 2)
        self.assertEqual(layouts[0][4], 'button')
        self.assertEqual(layouts[1][4], 'button')
        self.assertGreater(layouts[0][2], 0)
        self.assertGreaterEqual(layouts[0][2], TOOLBAR_BTN_MIN_WIDTH)

    def test_horizontal_with_separator(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A')
        tb.add_separator()
        tb.add_button('B')
        tb._ensure_layout()
        self.assertEqual(len(tb._item_layouts), 3)
        self.assertEqual(tb._item_layouts[1][4], 'separator')
        self.assertAlmostEqual(tb._item_layouts[1][2], TOOLBAR_SEP_WIDTH)

    def test_buttons_are_adjacent(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A')
        tb.add_button('B')
        tb._ensure_layout()
        l0 = tb._item_layouts[0]
        l1 = tb._item_layouts[1]
        self.assertAlmostEqual(l1[0], l0[0] + l0[2])

    def test_layout_cleared_on_dirty(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A')
        tb._ensure_layout()
        self.assertFalse(tb._layout_dirty)
        tb.add_button('B')
        self.assertTrue(tb._layout_dirty)
        tb._ensure_layout()
        self.assertEqual(len(tb._item_layouts), 2)

    def test_fallback_text_width_without_d2d(self):
        D2DToolBar._dwrite_text_fmt = None
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('AB')
        with patch('sheskin.controls.toolbar.pyd2d') as mock_pyd2d:
            mock_dw = MagicMock()
            mock_pyd2d.GetDWriteFactory.return_value = mock_dw
            mock_pyd2d.FONT_WEIGHT.NORMAL = 0
            mock_pyd2d.FONT_STYLE.NORMAL = 0
            mock_pyd2d.FONT_STRETCH.NORMAL = 0
            mock_pyd2d.PARAGRAPH_ALIGNMENT.CENTER = 0
            mock_fmt = MagicMock()
            mock_dw.CreateTextFormat.return_value = mock_fmt
            tb._ensure_layout()
        l = tb._item_layouts[0]
        expected_w = max(len('AB') * 8.0 + 2 * 6, TOOLBAR_BTN_MIN_WIDTH)
        self.assertAlmostEqual(l[2], expected_w)


class TestD2DToolBarHitTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _ensure_app()

    def setUp(self):
        self._saved_fmt = D2DToolBar._dwrite_text_fmt
        D2DToolBar._dwrite_text_fmt = MagicMock()

    def tearDown(self):
        D2DToolBar._dwrite_text_fmt = self._saved_fmt

    def _setup_tb(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A')
        tb.add_button('B')
        tb.add_separator()
        tb.add_button('C')
        tb._ensure_layout()
        return tb

    def test_hit_first_button(self):
        tb = self._setup_tb()
        x, y, w, h, _ = tb._item_layouts[0]
        idx = tb._hit_test((x + w / 2, y + h / 2))
        self.assertEqual(idx, 0)

    def test_hit_second_button(self):
        tb = self._setup_tb()
        x, y, w, h, _ = tb._item_layouts[1]
        idx = tb._hit_test((x + w / 2, y + h / 2))
        self.assertEqual(idx, 1)

    def test_separator_not_hit(self):
        tb = self._setup_tb()
        x, y, w, h, _ = tb._item_layouts[2]
        idx = tb._hit_test((x + w / 2, y + h / 2))
        self.assertEqual(idx, -1)

    def test_miss_returns_negative(self):
        tb = self._setup_tb()
        idx = tb._hit_test((-10, -10))
        self.assertEqual(idx, -1)


class TestD2DToolBarMouseEvents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _ensure_app()

    def setUp(self):
        self._saved_fmt = D2DToolBar._dwrite_text_fmt
        D2DToolBar._dwrite_text_fmt = MagicMock()

    def tearDown(self):
        D2DToolBar._dwrite_text_fmt = self._saved_fmt

    def _setup_tb(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A')
        tb.add_button('B', disabled=True)
        tb._ensure_layout()
        return tb

    def _btn_center(self, tb, idx):
        x, y, w, h, _ = tb._item_layouts[idx]
        return (x + w / 2, y + h / 2)

    def test_mouse_down_on_enabled(self):
        tb = self._setup_tb()
        pt = self._btn_center(tb, 0)
        self.assertTrue(tb.on_mouse_down(pt))
        self.assertTrue(tb._captured)
        self.assertEqual(tb._pressed, 0)

    def test_mouse_down_on_disabled(self):
        tb = self._setup_tb()
        pt = self._btn_center(tb, 1)
        self.assertFalse(tb.on_mouse_down(pt))

    def test_mouse_down_outside(self):
        tb = self._setup_tb()
        self.assertFalse(tb.on_mouse_down((-10, -10)))

    def test_mouse_up_triggers_click(self):
        calls = []
        tb = D2DToolBar((0, 0, 400, 30), on_click=lambda i, d: calls.append(i))
        tb.add_button('A')
        tb._ensure_layout()
        pt = self._btn_center(tb, 0)
        tb.on_mouse_down(pt)
        tb.on_mouse_up(pt)
        self.assertEqual(calls, [0])

    def test_mouse_up_outside_no_click(self):
        calls = []
        tb = D2DToolBar((0, 0, 400, 30), on_click=lambda i, d: calls.append(i))
        tb.add_button('A')
        tb._ensure_layout()
        pt = self._btn_center(tb, 0)
        tb.on_mouse_down(pt)
        tb.on_mouse_up((-10, -10))
        self.assertEqual(calls, [])

    def test_mouse_up_without_down(self):
        tb = self._setup_tb()
        self.assertFalse(tb.on_mouse_up((10, 10)))

    def test_mouse_move_hover(self):
        tb = self._setup_tb()
        pt = self._btn_center(tb, 0)
        self.assertTrue(tb.on_mouse_move(pt))
        self.assertEqual(tb._hovered, 0)

    def test_mouse_move_same_no_change(self):
        tb = self._setup_tb()
        pt = self._btn_center(tb, 0)
        tb.on_mouse_move(pt)
        self.assertFalse(tb.on_mouse_move(pt))

    def test_mouse_move_leave_area(self):
        tb = self._setup_tb()
        pt = self._btn_center(tb, 0)
        tb.on_mouse_move(pt)
        self.assertTrue(tb.on_mouse_move((-10, -10)))
        self.assertEqual(tb._hovered, -1)

    def test_mouse_move_during_capture(self):
        tb = self._setup_tb()
        pt = self._btn_center(tb, 0)
        tb.on_mouse_down(pt)
        result = tb.on_mouse_move((-10, -10))
        self.assertFalse(result)
        self.assertTrue(tb._captured)

    def test_mouse_leave(self):
        tb = self._setup_tb()
        pt = self._btn_center(tb, 0)
        tb.on_mouse_move(pt)
        self.assertTrue(tb.on_mouse_leave())
        self.assertEqual(tb._hovered, -1)

    def test_mouse_leave_no_hover(self):
        tb = self._setup_tb()
        self.assertFalse(tb.on_mouse_leave())

    def test_mouse_leave_clears_capture(self):
        tb = self._setup_tb()
        pt = self._btn_center(tb, 0)
        tb.on_mouse_down(pt)
        self.assertTrue(tb._captured)
        tb.on_mouse_leave()
        self.assertFalse(tb._captured)
        self.assertEqual(tb._pressed, -1)


class TestD2DToolBarBtnState(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _ensure_app()

    def setUp(self):
        self._saved_fmt = D2DToolBar._dwrite_text_fmt
        D2DToolBar._dwrite_text_fmt = MagicMock()

    def tearDown(self):
        D2DToolBar._dwrite_text_fmt = self._saved_fmt

    def _setup_tb(self):
        tb = D2DToolBar((0, 0, 400, 30))
        tb.add_button('A')
        tb.add_button('B', disabled=True)
        tb._ensure_layout()
        return tb

    def test_normal_state(self):
        tb = self._setup_tb()
        self.assertEqual(tb._get_btn_state(0), 'normal')

    def test_hover_state(self):
        tb = self._setup_tb()
        tb._hovered = 0
        self.assertEqual(tb._get_btn_state(0), 'hover')

    def test_pressed_state(self):
        tb = self._setup_tb()
        tb._pressed = 0
        tb._captured = True
        self.assertEqual(tb._get_btn_state(0), 'pressed')

    def test_disabled_state(self):
        tb = self._setup_tb()
        self.assertEqual(tb._get_btn_state(1), 'disabled')

    def test_disabled_overrides_hover(self):
        tb = self._setup_tb()
        tb._hovered = 1
        self.assertEqual(tb._get_btn_state(1), 'disabled')

    def test_disabled_overrides_pressed(self):
        tb = self._setup_tb()
        tb._pressed = 1
        tb._captured = True
        self.assertEqual(tb._get_btn_state(1), 'disabled')


class TestD2DToolBarIconCache(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _ensure_app()

    def test_separate_caches(self):
        tb = D2DToolBar((0, 0, 400, 30))
        self.assertEqual(tb._icon_cache, {})
        self.assertEqual(tb._grey_icon_cache, {})


if __name__ == '__main__':
    unittest.main()
