"""单元测试 — D2DEditBox / SkinAwareEditBox。"""
import pytest
import wx
import pyd2d

from sheskin.controls.editbox import (
    D2DEditBox, SkinAwareEditBox, EDITBOX_COLORS,
    EDITBOX_TEXT_PAD_X, EDITBOX_TEXT_PAD_Y, EDITBOX_CARET_WIDTH,
)


class TestD2DEditBoxInit:
    def test_defaults(self):
        e = D2DEditBox((10, 20, 200, 24))
        assert e.text == ''
        assert e.placeholder == ''
        assert e.readonly is False
        assert e.focused is False

    def test_with_text(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        assert e.text == "Hello"
        assert e._caret_pos == 5

    def test_with_placeholder(self):
        e = D2DEditBox((0, 0, 200, 24), placeholder="Enter...")
        assert e.placeholder == "Enter..."

    def test_readonly(self):
        e = D2DEditBox((0, 0, 200, 24), text="RO", readonly=True)
        assert e.readonly is True

    def test_callbacks(self):
        changes = []
        enters = []
        e = D2DEditBox((0, 0, 200, 24), on_change=lambda t: changes.append(t),
                        on_enter=lambda: enters.append(1))
        e.set_text("abc")
        assert changes == ["abc"]


class TestD2DEditBoxText:
    def test_set_text(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi")
        e.set_text("Hello")
        assert e.text == "Hello"

    def test_set_text_trims_caret(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        e._caret_pos = 5
        e.set_text("Hi")
        assert e._caret_pos <= 2

    def test_selected_text(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello World")
        e._sel_start = 0
        e._sel_end = 5
        assert e.selected_text == "Hello"

    def test_selected_text_no_sel(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        e._sel_start = e._sel_end = 3
        assert e.selected_text == ''

    def test_readonly_setter(self):
        e = D2DEditBox((0, 0, 200, 24))
        assert e.readonly is False
        e.readonly = True
        assert e.readonly is True

    def test_placeholder_setter(self):
        e = D2DEditBox((0, 0, 200, 24))
        e.placeholder = "New hint"
        assert e.placeholder == "New hint"


class TestD2DEditBoxFocus:
    def test_set_focus_on(self):
        e = D2DEditBox((0, 0, 200, 24))
        e.set_focus(True)
        assert e.focused is True
        assert e._caret_visible is True

    def test_set_focus_off(self):
        e = D2DEditBox((0, 0, 200, 24))
        e.set_focus(True)
        e.set_focus(False)
        assert e.focused is False
        assert e._caret_visible is False
        assert e._sel_start == e._sel_end

    def test_set_focus_no_change(self):
        e = D2DEditBox((0, 0, 200, 24))
        e.set_focus(True)
        result = e.set_focus(True)
        assert result is None


class TestD2DEditBoxKeyboard:
    def _make_focused(self, text="Hello"):
        e = D2DEditBox((0, 0, 200, 24), text=text)
        e.set_focus(True)
        e._caret_pos = len(text)
        return e

    def test_backspace(self):
        e = self._make_focused("Hello")
        e._caret_pos = 5
        e.on_key_down(wx.WXK_BACK, 0)
        assert e.text == "Hell"
        assert e._caret_pos == 4

    def test_backspace_with_selection(self):
        e = self._make_focused("Hello")
        e._sel_start = 1
        e._sel_end = 4
        e._caret_pos = 4
        e.on_key_down(wx.WXK_BACK, 0)
        assert e.text == "Ho"

    def test_delete(self):
        e = self._make_focused("Hello")
        e._caret_pos = 2
        e.on_key_down(wx.WXK_DELETE, 0)
        assert e.text == "Helo"

    def test_delete_with_selection(self):
        e = self._make_focused("Hello")
        e._sel_start = 1
        e._sel_end = 4
        e._caret_pos = 4
        e.on_key_down(wx.WXK_DELETE, 0)
        assert e.text == "Ho"

    def test_left_arrow(self):
        e = self._make_focused("Hello")
        e._caret_pos = 3
        e.on_key_down(wx.WXK_LEFT, 0)
        assert e._caret_pos == 2

    def test_right_arrow(self):
        e = self._make_focused("Hello")
        e._caret_pos = 2
        e.on_key_down(wx.WXK_RIGHT, 0)
        assert e._caret_pos == 3

    def test_home(self):
        e = self._make_focused("Hello")
        e._caret_pos = 3
        e.on_key_down(wx.WXK_HOME, 0)
        assert e._caret_pos == 0

    def test_end(self):
        e = self._make_focused("Hello")
        e._caret_pos = 0
        e.on_key_down(wx.WXK_END, 0)
        assert e._caret_pos == 5

    def test_ctrl_a_select_all(self):
        e = self._make_focused("Hello")
        e.on_key_down(ord('A'), wx.MOD_CONTROL)
        assert e._sel_start == 0
        assert e._sel_end == 5

    def test_shift_left_extend_sel(self):
        e = self._make_focused("Hello")
        e._caret_pos = 3
        e._sel_start = e._sel_end = 3
        e.on_key_down(wx.WXK_LEFT, wx.MOD_SHIFT)
        assert e._caret_pos == 2
        assert e._sel_start == 3
        assert e._sel_end == 2

    def test_shift_right_extend_sel(self):
        e = self._make_focused("Hello")
        e._caret_pos = 2
        e._sel_start = e._sel_end = 2
        e.on_key_down(wx.WXK_RIGHT, wx.MOD_SHIFT)
        assert e._caret_pos == 3
        assert e._sel_start == 2
        assert e._sel_end == 3

    def test_left_clears_selection(self):
        e = self._make_focused("Hello")
        e._sel_start = 1
        e._sel_end = 4
        e.on_key_down(wx.WXK_LEFT, 0)
        assert e._caret_pos == 1
        assert e._sel_start == e._sel_end

    def test_right_clears_selection(self):
        e = self._make_focused("Hello")
        e._sel_start = 1
        e._sel_end = 4
        e.on_key_down(wx.WXK_RIGHT, 0)
        assert e._caret_pos == 4
        assert e._sel_start == e._sel_end

    def test_enter_callback(self):
        enters = []
        e = D2DEditBox((0, 0, 200, 24), text="Hi", on_enter=lambda: enters.append(1))
        e.set_focus(True)
        e.on_key_down(wx.WXK_RETURN, 0)
        assert enters == [1]

    def test_readonly_backspace(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi", readonly=True)
        e.set_focus(True)
        e._caret_pos = 2
        result = e.on_key_down(wx.WXK_BACK, 0)
        assert result is False
        assert e.text == "Hi"

    def test_readonly_delete(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi", readonly=True)
        e.set_focus(True)
        e._caret_pos = 0
        result = e.on_key_down(wx.WXK_DELETE, 0)
        assert result is False
        assert e.text == "Hi"

    def test_disabled_ignores_keys(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi")
        e._state = D2DEditBox.DISABLED
        result = e.on_key_down(wx.WXK_BACK, 0)
        assert result is False

    def test_unfocused_ignores_keys(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi")
        result = e.on_key_down(wx.WXK_BACK, 0)
        assert result is False


class TestD2DEditBoxChar:
    def test_char_input(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi")
        e.set_focus(True)
        e._caret_pos = 2
        e.on_char(ord('!'))
        assert e.text == "Hi!"
        assert e._caret_pos == 3

    def test_char_with_selection(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        e.set_focus(True)
        e._sel_start = 1
        e._sel_end = 4
        e._caret_pos = 4
        e.on_char(ord('X'))
        assert e.text == "HXo"

    def test_char_readonly(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi", readonly=True)
        e.set_focus(True)
        result = e.on_char(ord('!'))
        assert result is False
        assert e.text == "Hi"

    def test_char_control_chars_ignored(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi")
        e.set_focus(True)
        e.on_char(27)
        assert e.text == "Hi"

    def test_char_disabled(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi")
        e._state = D2DEditBox.DISABLED
        result = e.on_char(ord('!'))
        assert result is False


class TestD2DEditBoxMouse:
    def test_mouse_down_sets_focus(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        e.on_mouse_down((100, 12))
        assert e.focused is True

    def test_mouse_down_disabled(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        e._state = D2DEditBox.DISABLED
        result = e.on_mouse_down((100, 12))
        assert result is False

    def test_mouse_down_outside(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        result = e.on_mouse_down((300, 12))
        assert result is False

    def test_mouse_up_ends_drag(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        e.on_mouse_down((100, 12))
        result = e.on_mouse_up((100, 12))
        assert result is True

    def test_mouse_move_drag(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello World")
        e.set_focus(True)
        e.on_mouse_down((10, 12))
        result = e.on_mouse_move((50, 12))
        assert e._dragging is True

    def test_mouse_leave_hover(self):
        e = D2DEditBox((0, 0, 200, 24))
        e._state = D2DEditBox.HOVER
        e.on_mouse_leave()
        assert e._state == D2DEditBox.NORMAL


class TestD2DEditBoxSelection:
    def test_select_all(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        e._select_all()
        assert e._sel_start == 0
        assert e._sel_end == 5

    def test_delete_selection(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello World")
        e._sel_start = 5
        e._sel_end = 11
        e._delete_selection()
        assert e.text == "Hello"

    def test_insert_text(self):
        e = D2DEditBox((0, 0, 200, 24), text="Ho")
        e._caret_pos = 1
        e._insert_text("ell")
        assert e.text == "Hello"

    def test_insert_text_with_selection(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello World")
        e._sel_start = 5
        e._sel_end = 11
        e._caret_pos = 11
        e._insert_text("!")
        assert e.text == "Hello!"

    def test_insert_text_readonly(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hi", readonly=True)
        e._caret_pos = 2
        e._insert_text("!")
        assert e.text == "Hi"


class TestD2DEditBoxBorderState:
    def test_normal(self):
        e = D2DEditBox((0, 0, 200, 24))
        assert e._border_state() == 'normal'

    def test_hover(self):
        e = D2DEditBox((0, 0, 200, 24))
        e._state = D2DEditBox.HOVER
        assert e._border_state() == 'hover'

    def test_focused(self):
        e = D2DEditBox((0, 0, 200, 24))
        e.set_focus(True)
        assert e._border_state() == 'default'

    def test_disabled(self):
        e = D2DEditBox((0, 0, 200, 24))
        e._state = D2DEditBox.DISABLED
        assert e._border_state() == 'disabled'


class TestD2DEditBoxDraw:
    def _make_rt(self):
        factory = pyd2d.GetD2DFactory()
        wic = pyd2d.GetWICFactory()
        bmp = wic.CreateBitmap(200, 24)
        return factory.CreateWicBitmapRenderTarget(bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)

    def test_draw_no_crash(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        rt = self._make_rt()
        rt.BeginDraw()
        e.draw(type('Ctx', (), {'rt': rt, 'dw_factory': pyd2d.GetDWriteFactory()})(),
               (0, 0, 200, 24))
        rt.EndDraw()

    def test_draw_empty(self):
        e = D2DEditBox((0, 0, 200, 24), placeholder="Enter...")
        rt = self._make_rt()
        rt.BeginDraw()
        e.draw(type('Ctx', (), {'rt': rt, 'dw_factory': pyd2d.GetDWriteFactory()})(),
               (0, 0, 200, 24))
        rt.EndDraw()

    def test_draw_focused(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        e.set_focus(True)
        rt = self._make_rt()
        rt.BeginDraw()
        e.draw(type('Ctx', (), {'rt': rt, 'dw_factory': pyd2d.GetDWriteFactory()})(),
               (0, 0, 200, 24))
        rt.EndDraw()

    def test_draw_disabled(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello")
        e._state = D2DEditBox.DISABLED
        rt = self._make_rt()
        rt.BeginDraw()
        e.draw(type('Ctx', (), {'rt': rt, 'dw_factory': pyd2d.GetDWriteFactory()})(),
               (0, 0, 200, 24))
        rt.EndDraw()

    def test_draw_with_selection(self):
        e = D2DEditBox((0, 0, 200, 24), text="Hello World")
        e.set_focus(True)
        e._sel_start = 0
        e._sel_end = 5
        rt = self._make_rt()
        rt.BeginDraw()
        e.draw(type('Ctx', (), {'rt': rt, 'dw_factory': pyd2d.GetDWriteFactory()})(),
               (0, 0, 200, 24))
        rt.EndDraw()


class TestSkinAwareEditBox:
    def test_init(self):
        ctx = type('Ctx', (), {
            'skin': type('Skin', (), {
                'get_props': lambda self, name: {},
                'get_block': lambda self, slot: None,
            })(),
            'get_text_format': lambda self, *a, **kw: None,
            'get_text_color': lambda self, *a: (0, 0, 0, 255),
            'cache': None,
        })()
        e = SkinAwareEditBox((0, 0, 200, 24), ctx, text="Test")
        assert e.text == "Test"
        assert e._ctx is ctx

    def test_readonly(self):
        ctx = type('Ctx', (), {
            'skin': type('Skin', (), {
                'get_props': lambda self, name: {},
                'get_block': lambda self, slot: None,
            })(),
            'get_text_format': lambda self, *a, **kw: None,
            'get_text_color': lambda self, *a: (0, 0, 0, 255),
            'cache': None,
        })()
        e = SkinAwareEditBox((0, 0, 200, 24), ctx, text="RO", readonly=True)
        assert e.readonly is True


class TestEditBoxColors:
    def test_colors_defined(self):
        assert 'normal' in EDITBOX_COLORS
        assert 'focused' in EDITBOX_COLORS
        assert 'disabled' in EDITBOX_COLORS

    def test_color_keys(self):
        for state in EDITBOX_COLORS.values():
            assert 'bg' in state
            assert 'text' in state
            assert 'sel_bg' in state
            assert 'sel_text' in state
            assert 'caret' in state
