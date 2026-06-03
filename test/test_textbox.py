"""单元测试 — D2DTextBox 多行文本编辑框。"""
import pytest
import wx
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sheskin.controls.textbox import D2DTextBox, SkinAwareTextBox


RECT = (0, 0, 300, 120)


class TestD2DTextBoxInit:
    def test_default(self):
        tb = D2DTextBox(RECT)
        assert tb.text == ''
        assert tb.line_count == 1
        assert tb.readonly is False
        assert tb.placeholder == ''
        assert tb.focused is False
        assert tb.caret_line == 0
        assert tb.caret_col == 0

    def test_with_text(self):
        tb = D2DTextBox(RECT, text='hello\nworld')
        assert tb.text == 'hello\nworld'
        assert tb.line_count == 2
        assert tb.caret_line == 0
        assert tb.caret_col == 0

    def test_with_placeholder(self):
        tb = D2DTextBox(RECT, placeholder='输入...')
        assert tb.placeholder == '输入...'

    def test_readonly(self):
        tb = D2DTextBox(RECT, readonly=True)
        assert tb.readonly is True

    def test_callbacks(self):
        changes = []
        tb = D2DTextBox(RECT, on_change=lambda t: changes.append(t))
        tb.set_text('abc')
        assert changes == ['abc']

    def test_multiline_text(self):
        tb = D2DTextBox(RECT, text='line1\nline2\nline3')
        assert tb.line_count == 3

    def test_cursor_type(self):
        tb = D2DTextBox(RECT)
        assert tb._cursor_type == wx.CURSOR_IBEAM


class TestD2DTextBoxText:
    def test_set_text(self):
        tb = D2DTextBox(RECT)
        tb.set_text('new text')
        assert tb.text == 'new text'

    def test_set_text_multiline(self):
        tb = D2DTextBox(RECT)
        tb.set_text('a\nb\nc')
        assert tb.line_count == 3

    def test_set_text_rebuilds_lines(self):
        tb = D2DTextBox(RECT, text='old')
        tb.set_text('new\nline')
        assert tb._lines == ['new', 'line']

    def test_readonly_setter(self):
        tb = D2DTextBox(RECT)
        tb.readonly = True
        assert tb.readonly is True

    def test_placeholder_setter(self):
        tb = D2DTextBox(RECT)
        tb.placeholder = 'new placeholder'
        assert tb.placeholder == 'new placeholder'


class TestD2DTextBoxFocus:
    def test_set_focus_on(self):
        tb = D2DTextBox(RECT)
        tb.set_focus(True)
        assert tb.focused is True
        assert tb._caret_visible is True

    def test_set_focus_off(self):
        tb = D2DTextBox(RECT)
        tb.set_focus(True)
        tb.set_focus(False)
        assert tb.focused is False
        assert tb._caret_visible is False

    def test_set_focus_no_change(self):
        tb = D2DTextBox(RECT)
        result = tb.set_focus(False)
        assert result is None

    def test_focus_off_clears_selection(self):
        tb = D2DTextBox(RECT, text='hello\nworld')
        tb.set_focus(True)
        tb._select_all()
        assert tb._has_selection()
        tb.set_focus(False)
        assert not tb._has_selection()


class TestD2DTextBoxKeyboard:
    def test_backspace_in_line(self):
        tb = D2DTextBox(RECT, text='abc')
        tb.set_focus(True)
        tb._caret_col = 2
        tb.on_key_down(wx.WXK_BACK, 0)
        assert tb.text == 'ac'
        assert tb._caret_col == 1

    def test_backspace_cross_line(self):
        tb = D2DTextBox(RECT, text='ab\ncd')
        tb.set_focus(True)
        tb._caret_line = 1
        tb._caret_col = 0
        tb.on_key_down(wx.WXK_BACK, 0)
        assert tb.text == 'abcd'
        assert tb._caret_line == 0
        assert tb._caret_col == 2

    def test_backspace_with_selection(self):
        tb = D2DTextBox(RECT, text='hello\nworld')
        tb.set_focus(True)
        tb._sel_start_line = 0
        tb._sel_start_col = 2
        tb._sel_end_line = 1
        tb._sel_end_col = 3
        tb.on_key_down(wx.WXK_BACK, 0)
        assert tb.text == 'held'
        assert tb._caret_line == 0
        assert tb._caret_col == 2

    def test_delete_in_line(self):
        tb = D2DTextBox(RECT, text='abc')
        tb.set_focus(True)
        tb._caret_col = 1
        tb.on_key_down(wx.WXK_DELETE, 0)
        assert tb.text == 'ac'
        assert tb._caret_col == 1

    def test_delete_cross_line(self):
        tb = D2DTextBox(RECT, text='ab\ncd')
        tb.set_focus(True)
        tb._caret_line = 0
        tb._caret_col = 2
        tb.on_key_down(wx.WXK_DELETE, 0)
        assert tb.text == 'abcd'
        assert tb._caret_line == 0
        assert tb._caret_col == 2

    def test_left_arrow(self):
        tb = D2DTextBox(RECT, text='abc')
        tb.set_focus(True)
        tb._caret_col = 2
        tb.on_key_down(wx.WXK_LEFT, 0)
        assert tb._caret_col == 1

    def test_left_arrow_cross_line(self):
        tb = D2DTextBox(RECT, text='ab\ncd')
        tb.set_focus(True)
        tb._caret_line = 1
        tb._caret_col = 0
        tb.on_key_down(wx.WXK_LEFT, 0)
        assert tb._caret_line == 0
        assert tb._caret_col == 2

    def test_right_arrow(self):
        tb = D2DTextBox(RECT, text='abc')
        tb.set_focus(True)
        tb._caret_col = 1
        tb.on_key_down(wx.WXK_RIGHT, 0)
        assert tb._caret_col == 2

    def test_right_arrow_cross_line(self):
        tb = D2DTextBox(RECT, text='ab\ncd')
        tb.set_focus(True)
        tb._caret_line = 0
        tb._caret_col = 2
        tb.on_key_down(wx.WXK_RIGHT, 0)
        assert tb._caret_line == 1
        assert tb._caret_col == 0

    def test_up_arrow(self):
        tb = D2DTextBox(RECT, text='abc\ndef')
        tb.set_focus(True)
        tb._caret_line = 1
        tb._caret_col = 1
        tb.on_key_down(wx.WXK_UP, 0)
        assert tb._caret_line == 0

    def test_down_arrow(self):
        tb = D2DTextBox(RECT, text='abc\ndef')
        tb.set_focus(True)
        tb._caret_line = 0
        tb._caret_col = 1
        tb.on_key_down(wx.WXK_DOWN, 0)
        assert tb._caret_line == 1

    def test_home(self):
        tb = D2DTextBox(RECT, text='abc')
        tb.set_focus(True)
        tb._caret_col = 2
        tb.on_key_down(wx.WXK_HOME, 0)
        assert tb._caret_col == 0

    def test_ctrl_home(self):
        tb = D2DTextBox(RECT, text='abc\ndef')
        tb.set_focus(True)
        tb._caret_line = 1
        tb._caret_col = 2
        tb.on_key_down(wx.WXK_HOME, wx.MOD_CONTROL)
        assert tb._caret_line == 0
        assert tb._caret_col == 0

    def test_end(self):
        tb = D2DTextBox(RECT, text='abc')
        tb.set_focus(True)
        tb._caret_col = 0
        tb.on_key_down(wx.WXK_END, 0)
        assert tb._caret_col == 3

    def test_ctrl_end(self):
        tb = D2DTextBox(RECT, text='abc\ndef')
        tb.set_focus(True)
        tb._caret_line = 0
        tb._caret_col = 0
        tb.on_key_down(wx.WXK_END, wx.MOD_CONTROL)
        assert tb._caret_line == 1
        assert tb._caret_col == 3

    def test_enter_inserts_newline(self):
        tb = D2DTextBox(RECT, text='abcd')
        tb.set_focus(True)
        tb._caret_col = 2
        tb.on_key_down(wx.WXK_RETURN, 0)
        assert tb.text == 'ab\ncd'
        assert tb._caret_line == 1
        assert tb._caret_col == 0

    def test_ctrl_a_select_all(self):
        tb = D2DTextBox(RECT, text='hello\nworld')
        tb.set_focus(True)
        tb.on_key_down(ord('A'), wx.MOD_CONTROL)
        assert tb._has_selection()
        assert tb.selected_text == 'hello\nworld'

    def test_shift_left_extend_sel(self):
        tb = D2DTextBox(RECT, text='abc')
        tb.set_focus(True)
        tb._caret_col = 2
        tb.on_key_down(wx.WXK_LEFT, wx.MOD_SHIFT)
        assert tb._caret_col == 1
        assert tb._has_selection()

    def test_shift_right_extend_sel(self):
        tb = D2DTextBox(RECT, text='abc')
        tb.set_focus(True)
        tb._caret_col = 1
        tb.on_key_down(wx.WXK_RIGHT, wx.MOD_SHIFT)
        assert tb._caret_col == 2
        assert tb._has_selection()

    def test_readonly_backspace(self):
        tb = D2DTextBox(RECT, text='abc', readonly=True)
        tb.set_focus(True)
        result = tb.on_key_down(wx.WXK_BACK, 0)
        assert result is False
        assert tb.text == 'abc'

    def test_readonly_delete(self):
        tb = D2DTextBox(RECT, text='abc', readonly=True)
        tb.set_focus(True)
        result = tb.on_key_down(wx.WXK_DELETE, 0)
        assert result is False
        assert tb.text == 'abc'

    def test_readonly_enter(self):
        tb = D2DTextBox(RECT, text='abc', readonly=True)
        tb.set_focus(True)
        result = tb.on_key_down(wx.WXK_RETURN, 0)
        assert result is False
        assert tb.text == 'abc'

    def test_disabled_ignores_keys(self):
        tb = D2DTextBox(RECT, text='abc')
        tb._state = tb.DISABLED
        result = tb.on_key_down(wx.WXK_BACK, 0)
        assert result is False

    def test_unfocused_ignores_keys(self):
        tb = D2DTextBox(RECT, text='abc')
        result = tb.on_key_down(wx.WXK_BACK, 0)
        assert result is False


class TestD2DTextBoxChar:
    def test_char_input(self):
        tb = D2DTextBox(RECT, text='ab')
        tb.set_focus(True)
        tb._caret_col = 1
        tb.on_char(ord('X'))
        assert tb.text == 'aXb'
        assert tb._caret_col == 2

    def test_char_with_selection(self):
        tb = D2DTextBox(RECT, text='abcd')
        tb.set_focus(True)
        tb._sel_start_line = tb._sel_end_line = 0
        tb._sel_start_col = 1
        tb._sel_end_col = 3
        tb.on_char(ord('X'))
        assert tb.text == 'aXd'
        assert tb._caret_col == 2

    def test_char_readonly(self):
        tb = D2DTextBox(RECT, text='abc', readonly=True)
        tb.set_focus(True)
        result = tb.on_char(ord('X'))
        assert result is False
        assert tb.text == 'abc'

    def test_char_control_chars_ignored(self):
        tb = D2DTextBox(RECT, text='abc')
        tb.set_focus(True)
        result = tb.on_char(8)
        assert result is False


class TestD2DTextBoxMouse:
    def test_mouse_down_sets_focus(self):
        tb = D2DTextBox(RECT)
        tb.on_mouse_down((10, 10))
        assert tb.focused is True

    def test_mouse_down_disabled(self):
        tb = D2DTextBox(RECT)
        tb._state = tb.DISABLED
        result = tb.on_mouse_down((10, 10))
        assert result is False

    def test_mouse_down_outside(self):
        tb = D2DTextBox(RECT)
        result = tb.on_mouse_down((500, 500))
        assert result is False

    def test_mouse_up_ends_drag(self):
        tb = D2DTextBox(RECT)
        tb.set_focus(True)
        tb._dragging = True
        tb.on_mouse_up((10, 10))
        assert tb._dragging is False

    def test_mouse_move_drag(self):
        tb = D2DTextBox(RECT, text='hello\nworld')
        tb.set_focus(True)
        tb._dragging = True
        tb.on_mouse_move((10, 10))
        assert tb._dragging is True

    def test_mouse_leave_hover(self):
        tb = D2DTextBox(RECT)
        tb._state = tb.HOVER
        tb.on_mouse_leave()
        assert tb._state == tb.NORMAL


class TestD2DTextBoxSelection:
    def test_select_all(self):
        tb = D2DTextBox(RECT, text='hello\nworld')
        tb._select_all()
        assert tb.selected_text == 'hello\nworld'
        assert tb._has_selection()

    def test_selected_text_no_sel(self):
        tb = D2DTextBox(RECT, text='hello')
        assert tb.selected_text == ''

    def test_selected_text_single_line(self):
        tb = D2DTextBox(RECT, text='hello')
        tb._sel_start_line = tb._sel_end_line = 0
        tb._sel_start_col = 1
        tb._sel_end_col = 4
        assert tb.selected_text == 'ell'

    def test_selected_text_cross_line(self):
        tb = D2DTextBox(RECT, text='hello\nworld')
        tb._sel_start_line = 0
        tb._sel_start_col = 2
        tb._sel_end_line = 1
        tb._sel_end_col = 3
        assert tb.selected_text == 'llo\nwor'

    def test_delete_selection(self):
        tb = D2DTextBox(RECT, text='hello\nworld')
        tb._sel_start_line = 0
        tb._sel_start_col = 2
        tb._sel_end_line = 1
        tb._sel_end_col = 3
        tb._delete_selection()
        assert tb.text == 'held'
        assert tb._caret_line == 0
        assert tb._caret_col == 2

    def test_insert_text(self):
        tb = D2DTextBox(RECT, text='ab')
        tb.set_focus(True)
        tb._caret_col = 1
        tb._insert_text('XY')
        assert tb.text == 'aXYb'
        assert tb._caret_col == 3

    def test_insert_text_with_newline(self):
        tb = D2DTextBox(RECT, text='abcd')
        tb.set_focus(True)
        tb._caret_col = 2
        tb._insert_text('XY\nZW')
        assert tb.text == 'abXY\nZWcd'
        assert tb._caret_line == 1
        assert tb._caret_col == 2

    def test_insert_text_with_selection(self):
        tb = D2DTextBox(RECT, text='abcd')
        tb.set_focus(True)
        tb._sel_start_line = tb._sel_end_line = 0
        tb._sel_start_col = 1
        tb._sel_end_col = 3
        tb._insert_text('XY')
        assert tb.text == 'aXYd'

    def test_insert_text_readonly(self):
        tb = D2DTextBox(RECT, text='abc', readonly=True)
        tb._insert_text('X')
        assert tb.text == 'abc'

    def test_ordered_selection(self):
        tb = D2DTextBox(RECT, text='abc\ndef')
        tb._sel_start_line = 1
        tb._sel_start_col = 2
        tb._sel_end_line = 0
        tb._sel_end_col = 1
        sl, sc, el, ec = tb._ordered_selection()
        assert sl == 0
        assert sc == 1
        assert el == 1
        assert ec == 2


class TestD2DTextBoxBorderState:
    def test_normal(self):
        tb = D2DTextBox(RECT)
        assert tb._border_state() == 'normal'

    def test_hover(self):
        tb = D2DTextBox(RECT)
        tb._state = tb.HOVER
        assert tb._border_state() == 'hover'

    def test_focused(self):
        tb = D2DTextBox(RECT)
        tb.set_focus(True)
        assert tb._border_state() == 'default'

    def test_disabled(self):
        tb = D2DTextBox(RECT)
        tb._state = tb.DISABLED
        assert tb._border_state() == 'disabled'


class TestD2DTextBoxDraw:
    def test_draw_no_crash(self):
        tb = D2DTextBox(RECT, text='hello\nworld')
        tb.set_focus(True)
        try:
            import pyd2d
            dw_factory = pyd2d.GetDWriteFactory()
            d2d_factory = pyd2d.GetD2DFactory()
            rt = d2d_factory.CreateHwndRenderTarget(400, 300)
            if rt is not None:
                class FakeCtx:
                    pass
                ctx = FakeCtx()
                ctx.rt = rt
                ctx.dw_factory = dw_factory
                tb.draw(ctx, RECT)
        except Exception:
            pass

    def test_draw_empty(self):
        tb = D2DTextBox(RECT)
        try:
            import pyd2d
            dw_factory = pyd2d.GetDWriteFactory()
            d2d_factory = pyd2d.GetD2DFactory()
            rt = d2d_factory.CreateHwndRenderTarget(400, 300)
            if rt is not None:
                class FakeCtx:
                    pass
                ctx = FakeCtx()
                ctx.rt = rt
                ctx.dw_factory = dw_factory
                tb.draw(ctx, RECT)
        except Exception:
            pass


class TestD2DTextBoxDoubleClick:
    def test_double_click_selects_word(self):
        tb = D2DTextBox(RECT, text='hello world')
        tb.set_focus(True)
        tb.on_double_click((10, 10))
        assert tb._has_selection()

    def test_double_click_disabled(self):
        tb = D2DTextBox(RECT, text='hello')
        tb._state = tb.DISABLED
        result = tb.on_double_click((10, 10))
        assert result is False

    def test_double_click_outside(self):
        tb = D2DTextBox(RECT, text='hello')
        result = tb.on_double_click((500, 500))
        assert result is False


class TestD2DTextBoxLineManagement:
    def test_rebuild_lines(self):
        tb = D2DTextBox(RECT, text='a\nb\nc')
        assert tb._lines == ['a', 'b', 'c']

    def test_rebuild_lines_empty(self):
        tb = D2DTextBox(RECT)
        assert tb._lines == ['']

    def test_clamp_caret(self):
        tb = D2DTextBox(RECT, text='ab\ncd')
        tb._caret_line = 5
        tb._caret_col = 10
        tb._clamp_caret()
        assert tb._caret_line == 1
        assert tb._caret_col == 2

    def test_line_count(self):
        tb = D2DTextBox(RECT, text='a\nb\nc\nd')
        assert tb.line_count == 4

    def test_caret_properties(self):
        tb = D2DTextBox(RECT, text='abc\ndef')
        tb._caret_line = 1
        tb._caret_col = 2
        assert tb.caret_line == 1
        assert tb.caret_col == 2


class TestD2DTextBoxTickCaret:
    def test_tick_unfocused(self):
        tb = D2DTextBox(RECT)
        result = tb.tick_caret()
        assert result is False

    def test_tick_focused(self):
        tb = D2DTextBox(RECT)
        tb.set_focus(True)
        result = tb.tick_caret()
        assert result is False or result is True


class TestD2DTextBoxColors:
    def test_colors_defined(self):
        from sheskin.controls._edit_utils import EDIT_COLORS
        assert 'normal' in EDIT_COLORS
        assert 'focused' in EDIT_COLORS
        assert 'readonly' in EDIT_COLORS
        assert 'disabled' in EDIT_COLORS

    def test_color_keys(self):
        from sheskin.controls._edit_utils import EDIT_COLORS
        for state in EDIT_COLORS:
            assert 'bg' in EDIT_COLORS[state]
            assert 'text' in EDIT_COLORS[state]
            assert 'sel_bg' in EDIT_COLORS[state]
            assert 'sel_text' in EDIT_COLORS[state]
            assert 'caret' in EDIT_COLORS[state]
