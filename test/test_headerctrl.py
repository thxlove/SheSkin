"""单元测试 — D2DHeaderCtrl / ColumnDef / draw_ctrl_border / CtrlBorder。"""
import pytest
import struct
import wx
import pyd2d
from sheskin.controls.headerctrl import (
    D2DHeaderCtrl, SkinAwareHeaderCtrl, ColumnDef, draw_ctrl_border,
    HEADERCTRL_COLORS, CTRLBORDER_COLORS,
    HEADERCTRL_MIN_COL_WIDTH, HEADERCTRL_TEXT_PAD_X,
)


class TestColumnDef:
    def test_defaults(self):
        c = ColumnDef()
        assert c.text == ''
        assert c.width == 100
        assert c.align == 'left'
        assert c.sortable is False

    def test_custom(self):
        c = ColumnDef('Name', 200, 'center', True)
        assert c.text == 'Name'
        assert c.width == 200
        assert c.align == 'center'
        assert c.sortable is True

    def test_min_width(self):
        c = ColumnDef('X', 5)
        assert c.width == HEADERCTRL_MIN_COL_WIDTH

    def test_zero_width(self):
        c = ColumnDef('X', 0)
        assert c.width == HEADERCTRL_MIN_COL_WIDTH


class TestD2DHeaderCtrl:
    def _make(self, cols=None, **kw):
        if cols is None:
            cols = [
                ColumnDef('Name', 150, sortable=True),
                ColumnDef('Size', 80, align='right'),
                ColumnDef('Type', 100, align='center'),
            ]
        return D2DHeaderCtrl((10, 20, 400, 24), columns=cols, **kw)

    def test_init(self):
        h = self._make()
        assert len(h.columns) == 3
        assert h.col_widths == [150, 80, 100]
        assert h.sort_column == -1
        assert h.sort_ascending is True

    def test_init_empty(self):
        h = D2DHeaderCtrl((0, 0, 200, 24))
        assert len(h.columns) == 0
        assert h.col_widths == []

    def test_set_columns(self):
        h = self._make()
        new_cols = [ColumnDef('A', 50), ColumnDef('B', 60)]
        h.set_columns(new_cols)
        assert len(h.columns) == 2
        assert h.col_widths == [50, 60]
        assert h.sort_column == -1

    def test_set_col_width(self):
        h = self._make()
        h.set_col_width(0, 200)
        assert h.col_widths[0] == 200

    def test_set_col_width_min(self):
        h = self._make()
        h.set_col_width(1, 1)
        assert h.col_widths[1] == HEADERCTRL_MIN_COL_WIDTH

    def test_set_col_width_invalid(self):
        h = self._make()
        h.set_col_width(99, 200)
        assert h.col_widths == [150, 80, 100]

    def test_hit_test_inside(self):
        h = self._make()
        assert h.hit_test((50, 30))

    def test_hit_test_outside(self):
        h = self._make()
        assert not h.hit_test((5, 30))
        assert not h.hit_test((50, 10))

    def test_hit_test_col(self):
        h = self._make()
        assert h._hit_test_col((50, 30)) == 0
        assert h._hit_test_col((200, 30)) == 1
        assert h._hit_test_col((300, 30)) == 2

    def test_hit_test_col_outside(self):
        h = self._make()
        assert h._hit_test_col((5, 30)) == -1
        assert h._hit_test_col((50, 10)) == -1

    def test_col_rect(self):
        h = self._make()
        r = h._col_rect(0)
        assert r == (10, 20, 150, 24)
        r1 = h._col_rect(1)
        assert r1 == (160, 20, 80, 24)

    def test_mouse_down_on_col(self):
        h = self._make()
        result = h.on_mouse_down((50, 30))
        assert result is True
        assert h._pressed_col == 0
        assert h._captured_col == 0

    def test_mouse_down_outside(self):
        h = self._make()
        result = h.on_mouse_down((5, 30))
        assert result is False

    def test_mouse_up_click_same_col(self):
        h = self._make()
        clicks = []
        h2 = D2DHeaderCtrl((10, 20, 400, 24),
                           columns=[ColumnDef('A', 100, sortable=True)],
                           on_col_click=lambda i: clicks.append(i))
        h2.on_mouse_down((50, 30))
        h2.on_mouse_up((50, 30))
        assert clicks == [0]
        assert h2.sort_column == 0
        assert h2.sort_ascending is True

    def test_mouse_up_click_toggle_sort(self):
        h = D2DHeaderCtrl((10, 20, 400, 24),
                          columns=[ColumnDef('A', 100, sortable=True)],
                          on_col_click=lambda i: None)
        h.on_mouse_down((50, 30))
        h.on_mouse_up((50, 30))
        assert h.sort_ascending is True
        h.on_mouse_down((50, 30))
        h.on_mouse_up((50, 30))
        assert h.sort_ascending is False

    def test_mouse_up_click_different_col(self):
        h = D2DHeaderCtrl((10, 20, 400, 24),
                          columns=[ColumnDef('A', 100, sortable=True),
                                   ColumnDef('B', 100, sortable=True)],
                          on_col_click=lambda i: None)
        h.on_mouse_down((50, 30))
        h.on_mouse_up((50, 30))
        assert h.sort_column == 0
        h.on_mouse_down((150, 30))
        h.on_mouse_up((150, 30))
        assert h.sort_column == 1
        assert h.sort_ascending is True

    def test_mouse_up_drag_out(self):
        h = self._make()
        h.on_mouse_down((50, 30))
        result = h.on_mouse_up((5, 30))
        assert result is True
        assert h._captured_col == -1

    def test_mouse_move_hover(self):
        h = self._make()
        result = h.on_mouse_move((50, 30))
        assert result is True
        assert h._hover_col == 0

    def test_mouse_move_hover_change(self):
        h = self._make()
        h.on_mouse_move((50, 30))
        result = h.on_mouse_move((200, 30))
        assert result is True
        assert h._hover_col == 1

    def test_mouse_move_no_change(self):
        h = self._make()
        h.on_mouse_move((50, 30))
        result = h.on_mouse_move((55, 30))
        assert result is False

    def test_mouse_move_captured_stays_pressed(self):
        h = self._make()
        h.on_mouse_down((50, 30))
        h.on_mouse_move((200, 30))
        assert h._col_states[0] == D2DHeaderCtrl.NORMAL
        h.on_mouse_move((50, 30))
        assert h._col_states[0] == D2DHeaderCtrl.PRESSED

    def test_mouse_leave(self):
        h = self._make()
        h.on_mouse_move((50, 30))
        result = h.on_mouse_leave()
        assert result is True
        assert h._hover_col == -1

    def test_mouse_leave_no_hover(self):
        h = self._make()
        result = h.on_mouse_leave()
        assert result is False

    def test_disabled(self):
        h = self._make()
        h._state = D2DHeaderCtrl.DISABLED
        assert h.on_mouse_down((50, 30)) is False
        assert h.on_mouse_up((50, 30)) is False
        assert h.on_mouse_move((50, 30)) is False
        assert h.on_mouse_leave() is False

    def test_on_col_click_callback(self):
        clicks = []
        h = D2DHeaderCtrl((10, 20, 400, 24),
                          columns=[ColumnDef('A', 100, sortable=True)],
                          on_col_click=lambda i: clicks.append(i))
        h.on_mouse_down((50, 30))
        h.on_mouse_up((50, 30))
        assert clicks == [0]


class TestCtrlBorder:
    def test_colors_defined(self):
        for state in ('normal', 'default', 'hover', 'disabled'):
            assert state in CTRLBORDER_COLORS
            c = CTRLBORDER_COLORS[state]
            assert 'outer' in c
            assert 'inner' in c
            assert 'bg' in c

    def test_headerctrl_colors_defined(self):
        for state in ('normal', 'hover', 'pressed', 'disabled'):
            assert state in HEADERCTRL_COLORS
            c = HEADERCTRL_COLORS[state]
            assert 'bg' in c
            assert 'border' in c
            assert 'text' in c


class TestDrawCtrlBorder:
    @classmethod
    def setup_class(cls):
        wx.GetApp() or wx.App(False)

    def _make_rt(self):
        factory = pyd2d.GetD2DFactory()
        wic = pyd2d.GetWICFactory()
        bmp = wic.CreateBitmap(64, 48)
        return factory.CreateWicBitmapRenderTarget(bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)

    def test_draw_no_crash(self):
        rt = self._make_rt()
        rt.BeginDraw()
        draw_ctrl_border(rt, (0, 0, 50, 30), state='normal')
        rt.EndDraw()

    def test_draw_all_states(self):
        rt = self._make_rt()
        for state in ('normal', 'default', 'hover', 'disabled'):
            rt.BeginDraw()
            draw_ctrl_border(rt, (0, 0, 50, 30), state=state)
            rt.EndDraw()

    def test_draw_zero_size(self):
        rt = self._make_rt()
        rt.BeginDraw()
        draw_ctrl_border(rt, (0, 0, 0, 0), state='normal')
        draw_ctrl_border(rt, (0, 0, -1, -1), state='normal')
        rt.EndDraw()

    def test_draw_with_curve(self):
        rt = self._make_rt()
        rt.BeginDraw()
        draw_ctrl_border(rt, (0, 0, 50, 30), state='normal',
                         curve_w=6, curve_h=6)
        rt.EndDraw()


class TestSkinAwareHeaderCtrl:
    def test_init(self):
        from sheskin.controls.skin_context import SkinContext
        from sheskin import SheSkin
        skin = SheSkin('Aero')
        skin.load()
        ctx = SkinContext(skin)
        cols = [ColumnDef('Name', 150), ColumnDef('Size', 80)]
        h = SkinAwareHeaderCtrl((0, 0, 300, 24), ctx, columns=cols)
        assert len(h.columns) == 2
        assert h._ctx is ctx

    def test_has_skin_blocks(self):
        from sheskin.controls.skin_context import SkinContext
        from sheskin import SheSkin
        skin = SheSkin('Aero')
        skin.load()
        ctx = SkinContext(skin)
        cols = [ColumnDef('Name', 150)]
        h = SkinAwareHeaderCtrl((0, 0, 150, 24), ctx, columns=cols)
        assert isinstance(h._has_skin_blocks(), bool)
