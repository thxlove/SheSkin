"""D2D 控件 — D2DEditBox / SkinAwareEditBox 编辑框。"""
import wx
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush
from ..d2d_render import d2d_draw_text
from ..layout import CONTROL_SLOTS
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP
from .headerctrl import draw_ctrl_border
from ._edit_utils import (
    TEXT_PAD_X, TEXT_PAD_Y, CARET_WIDTH, CARET_BLINK_MS,
    EDIT_COLORS, clipboard_copy, clipboard_paste,
    get_shift_from_mouse, resolve_edit_colors,
)

EDITBOX_TEXT_PAD_X = TEXT_PAD_X
EDITBOX_TEXT_PAD_Y = TEXT_PAD_Y
EDITBOX_CARET_WIDTH = CARET_WIDTH
EDITBOX_CARET_BLINK_MS = CARET_BLINK_MS
EDITBOX_COLORS = EDIT_COLORS


class D2DEditBox(SheControl):
    """D2D 自绘编辑框 — 单行文本输入，无 HWND，纯 D2D 渲染。

    Win32 EditBox 行为：
    - 获得焦点时边框变蓝（CtrlBorder default 态）+ 显示闪烁光标
    - 失去焦点时边框恢复灰色（CtrlBorder normal 态）+ 隐藏光标
    - 鼠标点击定位光标，拖拽选区
    - 键盘输入：字符/Backspace/Delete/方向键/Home/End/Ctrl+A/Ctrl+C/V/X
    - 选区高亮 + 光标闪烁

    用法：
        edit = D2DEditBox((10, 10, 200, 24), text="Hello")
        frame.register_d2d_control(edit)
        edit.bind_to_frame(frame)  # 绑定键盘事件
    """

    NORMAL = 0
    HOVER = 1
    PRESSED = 2
    DISABLED = 3

    def __init__(self, rect, text='', placeholder='', readonly=False,
                 on_change=None, on_enter=None):
        super().__init__(rect, text)
        self._placeholder = placeholder
        self._readonly = readonly
        self._on_change = on_change
        self._on_enter = on_enter
        self._focused = False
        self._caret_pos = len(text)
        self._sel_start = 0
        self._sel_end = 0
        self._caret_visible = True
        self._caret_timer = None
        self._dragging = False
        self._dwrite_text_fmt = None
        self._text_layout = None
        self._frame = None
        self._scroll_offset = 0.0
        self._cursor_type = wx.CURSOR_IBEAM

    @property
    def focused(self):
        return self._focused

    @property
    def readonly(self):
        return self._readonly

    @readonly.setter
    def readonly(self, value):
        self._readonly = value

    @property
    def placeholder(self):
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value):
        self._placeholder = value

    @property
    def selected_text(self):
        if self._sel_start != self._sel_end:
            lo = min(self._sel_start, self._sel_end)
            hi = max(self._sel_start, self._sel_end)
            return self._text[lo:hi]
        return ''

    def set_text(self, text):
        old = self._text
        super().set_text(text)
        if self._caret_pos > len(text):
            self._caret_pos = len(text)
        self._text_layout = None
        if old != text and self._on_change:
            self._on_change(text)

    def _get_text_fmt(self, dw_factory=None):
        if self._dwrite_text_fmt is not None:
            return self._dwrite_text_fmt
        if dw_factory is None:
            dw_factory = pyd2d.GetDWriteFactory()
        if dw_factory is None:
            return None
        self._dwrite_text_fmt = dw_factory.CreateTextFormat(
            DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
            weight=pyd2d.FONT_WEIGHT.NORMAL,
            style=pyd2d.FONT_STYLE.NORMAL,
            stretch=pyd2d.FONT_STRETCH.NORMAL)
        self._dwrite_text_fmt.SetTextAlignment(pyd2d.TEXT_ALIGNMENT.LEADING)
        self._dwrite_text_fmt.SetParagraphAlignment(pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        self._dwrite_text_fmt.SetWordWrapping(pyd2d.WORD_WRAPPING.NO_WRAP)
        return self._dwrite_text_fmt

    def _ensure_text_layout(self, dw_factory):
        if self._text_layout is not None:
            return self._text_layout
        if dw_factory is None:
            return None
        fmt = self._get_text_fmt(dw_factory)
        if fmt is None:
            return None
        rx, ry, rw, rh = self._rect
        tw = rw - 2 * EDITBOX_TEXT_PAD_X
        th = rh - 2 * EDITBOX_TEXT_PAD_Y
        if tw <= 0 or th <= 0:
            return None
        display_text = self._text if self._text else self._placeholder
        self._text_layout = dw_factory.CreateTextLayout(
            display_text, fmt, float(tw), float(th))
        return self._text_layout

    def _invalidate_text_layout(self):
        self._text_layout = None

    def _text_pixel_width(self, dw_factory):
        layout = self._ensure_text_layout(dw_factory)
        if layout is None:
            return 0.0
        metrics = layout.GetMetrics()
        if isinstance(metrics, dict):
            return metrics.get('width', 0.0)
        return getattr(metrics, 'width', 0.0)

    def _ensure_caret_visible(self, dw_factory=None):
        if dw_factory is None:
            dw_factory = pyd2d.GetDWriteFactory()
        cx, cy, cw, ch = self._content_rect()
        if cw <= 0:
            return
        positions = self._char_x_positions(dw_factory)
        if not positions:
            self._scroll_offset = 0.0
            return
        caret_idx = min(self._caret_pos, len(positions) - 1)
        caret_x = positions[caret_idx]
        visible_caret = caret_x - self._scroll_offset
        if visible_caret < 0:
            self._scroll_offset = caret_x
        elif visible_caret > cw:
            self._scroll_offset = caret_x - cw + EDITBOX_CARET_WIDTH

    def _content_rect(self):
        rx, ry, rw, rh = self._rect
        return (rx + EDITBOX_TEXT_PAD_X, ry + EDITBOX_TEXT_PAD_Y,
                rw - 2 * EDITBOX_TEXT_PAD_X, rh - 2 * EDITBOX_TEXT_PAD_Y)

    def _char_x_positions(self, dw_factory):
        if not self._text:
            return [0.0]
        layout = self._ensure_text_layout(dw_factory)
        if layout is None:
            return []
        positions = []
        for i in range(len(self._text) + 1):
            if i < len(self._text):
                metrics = layout.HitTestTextPosition(i, False)
            else:
                metrics = layout.HitTestTextPosition(max(0, len(self._text) - 1), True)
                if len(self._text) > 0:
                    metrics = layout.HitTestTextPosition(len(self._text) - 1, True)
            if metrics:
                positions.append(metrics.get('x', 0.0) if isinstance(metrics, dict) else metrics[0])
            else:
                positions.append(0.0)
        return positions

    def _pos_from_x(self, x, dw_factory):
        cx, cy, cw, ch = self._content_rect()
        rel_x = x - cx + self._scroll_offset
        positions = self._char_x_positions(dw_factory)
        if not positions:
            return 0
        if rel_x <= 0:
            return 0
        if rel_x >= positions[-1]:
            return len(self._text)
        best = 0
        best_dist = abs(positions[0] - rel_x)
        for i in range(1, len(positions)):
            d = abs(positions[i] - rel_x)
            if d < best_dist:
                best_dist = d
                best = i
        mid = (positions[best] + positions[best + 1]) / 2 if best + 1 < len(positions) else positions[best]
        if rel_x > mid and best < len(self._text):
            return best + 1
        return best

    def _caret_metrics(self, dw_factory=None):
        fmt = self._get_text_fmt(dw_factory)
        if fmt is None:
            return DEFAULT_FONT_SIZE_DIP, 0
        try:
            layout = (dw_factory or pyd2d.GetDWriteFactory()).CreateTextLayout(
                "Ay", fmt, 100000.0, 1000.0)
            if layout:
                line_metrics = layout.GetLineMetrics()
                if line_metrics:
                    return line_metrics[0].baseline, line_metrics[0].height
        except Exception:
            pass
        return DEFAULT_FONT_SIZE_DIP, DEFAULT_FONT_SIZE_DIP + LINE_SPACING

    def _caret_x(self, dw_factory):
        positions = self._char_x_positions(dw_factory)
        if not positions:
            return 0.0
        idx = min(self._caret_pos, len(positions) - 1)
        return positions[idx] if idx < len(positions) else 0.0

    def _border_state(self):
        if self._state == self.DISABLED:
            return 'disabled'
        if self._focused:
            return 'default'
        if self._state == self.HOVER:
            return 'hover'
        return 'normal'

    def _start_caret_timer(self):
        self._stop_caret_timer()
        self._caret_visible = True
        if self._frame and self._focused:
            self._caret_timer = self._frame.Bind(
                wx.EVT_TIMER, self._on_caret_timer) if hasattr(self._frame, 'Bind') else None
            if self._caret_timer is None and hasattr(self._frame, '_timer'):
                pass

    def _stop_caret_timer(self):
        if self._caret_timer is not None:
            self._caret_timer = None
        self._caret_visible = False

    def _on_caret_timer(self, event=None):
        self._caret_visible = not self._caret_visible
        if self._frame:
            self._frame._dirty = True
            self._frame._do_composite()

    def set_focus(self, focused):
        if self._focused == focused:
            return
        self._focused = focused
        if focused:
            self._start_caret_blink()
        else:
            self._stop_caret_blink()
            self._sel_start = self._sel_end = 0
            self._dragging = False
            self._scroll_offset = 0.0

    def _start_caret_blink(self):
        self._caret_visible = True
        self._blink_count = 0

    def _stop_caret_blink(self):
        self._caret_visible = False

    def tick_caret(self):
        if not self._focused:
            return False
        self._blink_count = getattr(self, '_blink_count', 0) + 1
        if self._blink_count >= EDITBOX_CARET_BLINK_MS // 50:
            self._blink_count = 0
            self._caret_visible = not self._caret_visible
            return True
        return False

    def bind_to_frame(self, frame):
        self._frame = frame

    def _select_all(self):
        self._sel_start = 0
        self._sel_end = len(self._text)
        self._caret_pos = len(self._text)

    def _delete_selection(self):
        if self._sel_start == self._sel_end:
            return
        lo = min(self._sel_start, self._sel_end)
        hi = max(self._sel_start, self._sel_end)
        new_text = self._text[:lo] + self._text[hi:]
        self._sel_start = self._sel_end = lo
        self._caret_pos = lo
        self.set_text(new_text)

    def _insert_text(self, chars):
        if self._readonly:
            return
        if self._sel_start != self._sel_end:
            lo = min(self._sel_start, self._sel_end)
            self._delete_selection()
            self._caret_pos = lo
        new_text = self._text[:self._caret_pos] + chars + self._text[self._caret_pos:]
        self._caret_pos += len(chars)
        self._sel_start = self._sel_end = self._caret_pos
        self.set_text(new_text)

    def on_key_down(self, key_code, modifiers):
        if self._state == self.DISABLED or not self._focused:
            return False
        ctrl = modifiers & wx.MOD_CONTROL
        shift = modifiers & wx.MOD_SHIFT

        if key_code == wx.WXK_BACK:
            if self._readonly:
                return False
            if self._sel_start != self._sel_end:
                self._delete_selection()
            elif self._caret_pos > 0:
                new_text = self._text[:self._caret_pos - 1] + self._text[self._caret_pos:]
                self._caret_pos -= 1
                self._sel_start = self._sel_end = self._caret_pos
                self.set_text(new_text)
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_DELETE:
            if self._readonly:
                return False
            if self._sel_start != self._sel_end:
                self._delete_selection()
            elif self._caret_pos < len(self._text):
                new_text = self._text[:self._caret_pos] + self._text[self._caret_pos + 1:]
                self.set_text(new_text)
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_LEFT:
            if shift:
                anchor = self._sel_start if self._sel_start != self._sel_end else self._caret_pos
                if self._caret_pos > 0:
                    self._caret_pos -= 1
                self._sel_start = anchor
                self._sel_end = self._caret_pos
            else:
                if self._sel_start != self._sel_end:
                    self._caret_pos = min(self._sel_start, self._sel_end)
                elif self._caret_pos > 0:
                    self._caret_pos -= 1
                self._sel_start = self._sel_end = self._caret_pos
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_RIGHT:
            if shift:
                anchor = self._sel_start if self._sel_start != self._sel_end else self._caret_pos
                if self._caret_pos < len(self._text):
                    self._caret_pos += 1
                self._sel_start = anchor
                self._sel_end = self._caret_pos
            else:
                if self._sel_start != self._sel_end:
                    self._caret_pos = max(self._sel_start, self._sel_end)
                elif self._caret_pos < len(self._text):
                    self._caret_pos += 1
                self._sel_start = self._sel_end = self._caret_pos
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_HOME:
            if shift:
                anchor = self._sel_start if self._sel_start != self._sel_end else self._caret_pos
                self._caret_pos = 0
                self._sel_start = anchor
                self._sel_end = self._caret_pos
            else:
                self._caret_pos = 0
                self._sel_start = self._sel_end = 0
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_END:
            if shift:
                anchor = self._sel_start if self._sel_start != self._sel_end else self._caret_pos
                self._caret_pos = len(self._text)
                self._sel_start = anchor
                self._sel_end = self._caret_pos
            else:
                self._caret_pos = len(self._text)
                self._sel_start = self._sel_end = self._caret_pos
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_RETURN:
            if self._on_enter:
                self._on_enter()
            return True

        if ctrl:
            if key_code == ord('A'):
                self._select_all()
                self._invalidate_text_layout()
                return True
            if key_code == ord('C'):
                sel = self.selected_text
                if sel:
                    clipboard_copy(sel)
                return True
            if key_code == ord('V'):
                if self._readonly:
                    return False
                paste = clipboard_paste()
                if paste:
                    self._insert_text(paste)
                self._invalidate_text_layout()
                return True
            if key_code == ord('X'):
                if self._readonly:
                    return False
                sel = self.selected_text
                if sel:
                    clipboard_copy(sel)
                    self._delete_selection()
                self._invalidate_text_layout()
                return True

        return False

    def on_char(self, char_code):
        if self._state == self.DISABLED or not self._focused:
            return False
        if self._readonly:
            return False
        if char_code >= 32 and char_code != 127:
            ch = chr(char_code)
            self._insert_text(ch)
            self._invalidate_text_layout()
            return True
        return False

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        if not self.hit_test(pt):
            return False

        if not self._focused and self._frame:
            self._frame.set_focused_control(self)
        elif not self._focused:
            self.set_focus(True)

        shift = get_shift_from_mouse()

        if shift and self._focused:
            anchor = self._sel_start if self._sel_start != self._sel_end else self._caret_pos
            new_pos = self._pos_from_x(pt[0], pyd2d.GetDWriteFactory())
            self._caret_pos = new_pos
            self._sel_start = anchor
            self._sel_end = new_pos
        else:
            new_pos = self._pos_from_x(pt[0], pyd2d.GetDWriteFactory())
            self._caret_pos = new_pos
            self._sel_start = new_pos
            self._sel_end = new_pos

        self._dragging = True
        self._caret_visible = True
        self._blink_count = 0
        self._invalidate_text_layout()
        return True

    def on_mouse_up(self, pt):
        if self._dragging:
            self._dragging = False
            return True
        return False

    def on_mouse_move(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._dragging and self._focused:
            new_pos = self._pos_from_x(pt[0], pyd2d.GetDWriteFactory())
            if new_pos != self._sel_end:
                self._sel_end = new_pos
                self._caret_pos = new_pos
                self._invalidate_text_layout()
                return True
            return False
        inside = self.hit_test(pt)
        if inside and self._state != self.HOVER and not self._focused:
            self._state = self.HOVER
            return True
        if not inside and self._state == self.HOVER and not self._focused:
            self._state = self.NORMAL
            return True
        return False

    def on_mouse_leave(self):
        if self._dragging:
            return False
        if self._state == self.HOVER and not self._focused:
            self._state = self.NORMAL
            return True
        return False

    def on_double_click(self, pt):
        if self._state == self.DISABLED:
            return False
        if not self.hit_test(pt):
            return False
        if not self._text:
            return True
        if not self._focused:
            if self._frame:
                self._frame.set_focused_control(self)
            else:
                self.set_focus(True)
        self._select_all()
        self._invalidate_text_layout()
        return True

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt

        border_state = self._border_state()
        draw_ctrl_border(rt, (rx, ry, rw, rh), state=border_state,
                         skin_context=None)

        colors = resolve_edit_colors(self._focused, self._readonly,
                                     self._state == self.DISABLED, self._state)

        if self._readonly and self._state != self.DISABLED:
            bg_brush = get_brush(rt, *colors['bg'])
            rt.FillRectangle(float(rx + 1), float(ry + 1),
                             float(rx + rw - 1), float(ry + rh - 1), bg_brush)

        cx, cy, cw, ch = self._content_rect()
        if cw <= 0 or ch <= 0:
            return

        self._ensure_caret_visible(ctx.dw_factory)

        fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
        offset = self._scroll_offset

        rt.PushAxisAlignedClip(float(cx), float(cy),
                               float(cx + cw), float(cy + ch))

        if self._text:
            if self._sel_start != self._sel_end:
                lo = min(self._sel_start, self._sel_end)
                hi = max(self._sel_start, self._sel_end)
                positions = self._char_x_positions(ctx.dw_factory)
                if positions and lo < len(positions) and hi <= len(positions):
                    sel_x1 = cx + positions[lo] - offset
                    sel_x2 = cx + (positions[hi] if hi < len(positions) else positions[-1]) - offset
                    sel_brush = get_brush(rt, *colors['sel_bg'])
                    rt.FillRectangle(float(sel_x1), float(cy),
                                     float(sel_x2), float(cy + ch), sel_brush)

            text_x = cx - offset
            text_brush = get_brush(rt, *colors['text'])
            rt.DrawText(self._text, fmt,
                        float(text_x), float(cy),
                        float(text_x + cw + offset), float(cy + ch), text_brush)

            if self._sel_start != self._sel_end:
                lo = min(self._sel_start, self._sel_end)
                hi = max(self._sel_start, self._sel_end)
                positions = self._char_x_positions(ctx.dw_factory)
                if positions and lo < len(positions) and hi <= len(positions):
                    sel_x1 = cx + positions[lo] - offset
                    sel_x2 = cx + (positions[hi] if hi < len(positions) else positions[-1]) - offset
                    sel_text = self._text[lo:hi]
                    sel_brush = get_brush(rt, *colors['sel_text'])
                    rt.DrawText(sel_text, fmt,
                                float(sel_x1), float(cy),
                                float(sel_x2), float(cy + ch), sel_brush)
        else:
            if self._placeholder:
                ph_brush = get_brush(rt, 0.6, 0.6, 0.6, 1.0)
                rt.DrawText(self._placeholder, fmt,
                            float(cx), float(cy),
                            float(cx + cw), float(cy + ch), ph_brush)

        if self._focused and self._caret_visible:
            caret_x = cx + self._caret_x(ctx.dw_factory) - offset
            caret_h, line_h = self._caret_metrics(ctx.dw_factory)
            caret_top = cy + (ch - line_h) / 2 + 2
            caret_brush = get_brush(rt, *colors['caret'])
            cx_snap = float(int(caret_x) + 0.5)
            rt.DrawLine(cx_snap, float(caret_top),
                        cx_snap, float(caret_top + caret_h),
                        caret_brush, EDITBOX_CARET_WIDTH)

        rt.PopAxisAlignedClip()


class SkinAwareEditBox(D2DEditBox):
    """皮肤化编辑框 — 使用 CtrlBorder 属性绘制边框。"""

    def __init__(self, rect, skin_context, text='', placeholder='',
                 readonly=False, on_change=None, on_enter=None,
                 subcat='CtrlBorder'):
        super().__init__(rect, text=text, placeholder=placeholder,
                         readonly=readonly, on_change=on_change,
                         on_enter=on_enter)
        self._ctx = skin_context
        self._subcat = subcat
        self._dwrite_text_fmt_cached = None

    def _get_text_fmt_cached(self, dw_factory=None):
        if self._dwrite_text_fmt_cached is not None:
            return self._dwrite_text_fmt_cached
        self._dwrite_text_fmt_cached = self._ctx.get_text_format(
            self._subcat, dw_factory=dw_factory,
            alignment=pyd2d.TEXT_ALIGNMENT.LEADING,
            para_alignment=pyd2d.PARAGRAPH_ALIGNMENT.CENTER,
            no_wrap=True)
        return self._dwrite_text_fmt_cached

    def _get_text_color(self, state_idx):
        return self._ctx.get_text_color(self._subcat, state_idx)

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt

        border_state = self._border_state()
        draw_ctrl_border(rt, (rx, ry, rw, rh), state=border_state,
                         skin_context=self._ctx)

        colors = resolve_edit_colors(self._focused, self._readonly,
                                     self._state == self.DISABLED, self._state)

        if self._readonly and self._state != self.DISABLED:
            bg_brush = get_brush(rt, *colors['bg'])
            rt.FillRectangle(float(rx + 1), float(ry + 1),
                             float(rx + rw - 1), float(ry + rh - 1), bg_brush)

        if self._ctx and self._ctx.skin:
            props = self._ctx.skin.get_props(self._subcat)
            if props:
                tc_key = 'text_color_d' if self._state == self.DISABLED else 'text_color_n'
                tc = props.get(tc_key)
                if tc is not None:
                    if hasattr(tc, 'Red'):
                        colors = dict(colors)
                        colors = dict(colors)
                        colors['text'] = (tc.Red() / 255.0, tc.Green() / 255.0,
                                          tc.Blue() / 255.0, tc.Alpha() / 255.0)

        cx, cy, cw, ch = self._content_rect()
        if cw <= 0 or ch <= 0:
            return

        self._ensure_caret_visible(ctx.dw_factory)

        text_fmt = self._get_text_fmt_cached(dw_factory=ctx.dw_factory)
        if text_fmt is None:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)

        offset = self._scroll_offset

        rt.PushAxisAlignedClip(float(cx), float(cy),
                               float(cx + cw), float(cy + ch))

        if self._text:
            if self._sel_start != self._sel_end:
                lo = min(self._sel_start, self._sel_end)
                hi = max(self._sel_start, self._sel_end)
                positions = self._char_x_positions(ctx.dw_factory)
                if positions and lo < len(positions) and hi <= len(positions):
                    sel_x1 = cx + positions[lo] - offset
                    sel_x2 = cx + (positions[hi] if hi < len(positions) else positions[-1]) - offset
                    sel_brush = get_brush(rt, *colors['sel_bg'])
                    rt.FillRectangle(float(sel_x1), float(cy),
                                     float(sel_x2), float(cy + ch), sel_brush)

            text_x = cx - offset
            text_brush = get_brush(rt, *colors['text'])
            rt.DrawText(self._text, text_fmt,
                        float(text_x), float(cy),
                        float(text_x + cw + offset), float(cy + ch), text_brush)

            if self._sel_start != self._sel_end:
                lo = min(self._sel_start, self._sel_end)
                hi = max(self._sel_start, self._sel_end)
                positions = self._char_x_positions(ctx.dw_factory)
                if positions and lo < len(positions) and hi <= len(positions):
                    sel_x1 = cx + positions[lo] - offset
                    sel_x2 = cx + (positions[hi] if hi < len(positions) else positions[-1]) - offset
                    sel_text = self._text[lo:hi]
                    sel_brush = get_brush(rt, *colors['sel_text'])
                    rt.DrawText(sel_text, text_fmt,
                                float(sel_x1), float(cy),
                                float(sel_x2), float(cy + ch), sel_brush)
        else:
            if self._placeholder:
                ph_brush = get_brush(rt, 0.6, 0.6, 0.6, 1.0)
                rt.DrawText(self._placeholder, text_fmt,
                            float(cx), float(cy),
                            float(cx + cw), float(cy + ch), ph_brush)

        if self._focused and self._caret_visible:
            caret_x = cx + self._caret_x(ctx.dw_factory) - offset
            caret_h, line_h = self._caret_metrics(ctx.dw_factory)
            caret_top = cy + (ch - line_h) / 2 + 2
            caret_brush = get_brush(rt, *colors['caret'])
            cx_snap = float(int(caret_x) + 0.5)
            rt.DrawLine(cx_snap, float(caret_top),
                        cx_snap, float(caret_top + caret_h),
                        caret_brush, EDITBOX_CARET_WIDTH)

        rt.PopAxisAlignedClip()
