"""D2D 控件 — D2DTextBox / SkinAwareTextBox 多行文本编辑框。"""
import wx
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP
from .headerctrl import draw_ctrl_border
from .scrollbar import D2DScrollBar, SkinAwareScrollBar
from ._edit_utils import (
    TEXT_PAD_X, TEXT_PAD_Y, CARET_WIDTH, CARET_BLINK_MS,
    EDIT_COLORS, clipboard_copy, clipboard_paste,
    get_shift_from_mouse, resolve_edit_colors,
)

SCROLLBAR_WIDTH = 16
LINE_SPACING = 2


class D2DTextBox(SheControl):
    """D2D 自绘多行文本编辑框 — 无 HWND，纯 D2D 渲染。

    Win32 EditBox ES_MULTILINE 行为：
    - 多行文本，自动换行
    - Enter 插入换行符
    - 垂直 + 水平双向 ScrollBar
    - 二维光标 (line, column)
    - 跨行选区
    - 鼠标点击定位、拖拽选区、双击选词、三击选行
    """

    NORMAL = 0
    HOVER = 1
    PRESSED = 2
    DISABLED = 3

    def __init__(self, rect, text='', placeholder='', readonly=False,
                 on_change=None, h_scroll=True, v_scroll=True):
        super().__init__(rect, text)
        self._placeholder = placeholder
        self._readonly = readonly
        self._on_change = on_change
        self._focused = False
        self._caret_visible = True
        self._blink_count = 0
        self._dragging = False
        self._frame = None
        self._cursor_type = wx.CURSOR_IBEAM
        self._h_scroll_enabled = h_scroll
        self._v_scroll_enabled = v_scroll
        self._h_scroll_active = False
        self._v_scroll_active = False
        self._scroll_x = 0.0
        self._scroll_y = 0
        self._dwrite_text_fmt = None
        self._text_layout = None
        self._lines = []
        self._caret_line = 0
        self._caret_col = 0
        self._sel_start_line = 0
        self._sel_start_col = 0
        self._sel_end_line = 0
        self._sel_end_col = 0
        self._v_scrollbar = None
        self._h_scrollbar = None
        self._rebuild_lines()

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
    def text(self):
        return self._text

    def set_text(self, text):
        old = self._text
        super().set_text(text)
        self._rebuild_lines()
        self._clamp_caret()
        self._text_layout = None
        if old != text and self._on_change:
            self._on_change(text)

    @property
    def selected_text(self):
        if not self._has_selection():
            return ''
        sl, sc, el, ec = self._ordered_selection()
        if sl == el:
            return self._lines[sl][sc:ec]
        parts = [self._lines[sl][sc:]]
        for i in range(sl + 1, el):
            parts.append(self._lines[i])
        parts.append(self._lines[el][:ec])
        return '\n'.join(parts)

    @property
    def line_count(self):
        return len(self._lines)

    @property
    def caret_line(self):
        return self._caret_line

    @property
    def caret_col(self):
        return self._caret_col

    def _rebuild_lines(self):
        self._lines = self._text.split('\n') if self._text else ['']

    def _clamp_caret(self):
        if self._caret_line >= len(self._lines):
            self._caret_line = max(0, len(self._lines) - 1)
        line = self._lines[self._caret_line] if self._caret_line < len(self._lines) else ''
        if self._caret_col > len(line):
            self._caret_col = len(line)

    def _has_v_scrollbar(self):
        return self._v_scrollbar is not None and self._v_scroll_active

    def _has_h_scrollbar(self):
        return self._h_scrollbar is not None and self._h_scroll_active

    def _content_rect(self):
        rx, ry, rw, rh = self._rect
        sb_w = SCROLLBAR_WIDTH if self._has_v_scrollbar() else 0
        sb_h = SCROLLBAR_WIDTH if self._has_h_scrollbar() else 0
        return (rx + TEXT_PAD_X, ry + TEXT_PAD_Y,
                rw - 2 * TEXT_PAD_X - sb_w, rh - 2 * TEXT_PAD_Y - sb_h)

    def _corner_rect(self):
        if not self._has_v_scrollbar() or not self._has_h_scrollbar():
            return None
        rx, ry, rw, rh = self._rect
        return (rx + rw - SCROLLBAR_WIDTH, ry + rh - SCROLLBAR_WIDTH,
                SCROLLBAR_WIDTH, SCROLLBAR_WIDTH)

    def _is_scrollbar_area(self, pt):
        if self._v_scrollbar and self._v_scrollbar.hit_test(pt):
            return True
        if self._h_scrollbar and self._h_scrollbar.hit_test(pt):
            return True
        corner = self._corner_rect()
        if corner:
            cx, cy, cw, ch = corner
            px, py = pt
            if cx <= px <= cx + cw and cy <= py <= cy + ch:
                return True
        return False

    def _line_height(self, dw_factory=None):
        fmt = self._get_text_fmt(dw_factory)
        if fmt is None:
            return DEFAULT_FONT_SIZE_DIP + LINE_SPACING
        try:
            factory = dw_factory or pyd2d.GetDWriteFactory()
            if factory is None:
                return DEFAULT_FONT_SIZE_DIP + LINE_SPACING
            layout = factory.CreateTextLayout("Ay", fmt, 100000.0, 1000.0)
            if layout:
                lm = layout.GetLineMetrics()
                if lm:
                    return lm[0].height
        except Exception:
            pass
        return DEFAULT_FONT_SIZE_DIP + LINE_SPACING

    def _caret_metrics(self, dw_factory=None):
        fmt = self._get_text_fmt(dw_factory)
        if fmt is None:
            return DEFAULT_FONT_SIZE_DIP, 0
        try:
            factory = dw_factory or pyd2d.GetDWriteFactory()
            if factory is None:
                return DEFAULT_FONT_SIZE_DIP, 0
            layout = factory.CreateTextLayout(
                "Ay", fmt, 100000.0, 1000.0)
            if layout:
                line_metrics = layout.GetLineMetrics()
                if line_metrics:
                    lm = line_metrics[0]
                    return lm.baseline, 0
        except Exception:
            pass
        return DEFAULT_FONT_SIZE_DIP, 0

    def _total_line_height(self, dw_factory=None):
        return len(self._lines) * self._line_height(dw_factory)

    def _border_state(self):
        if self._state == self.DISABLED:
            return 'disabled'
        if self._focused:
            return 'default'
        if self._state == self.HOVER:
            return 'hover'
        return 'normal'

    def _has_selection(self):
        return (self._sel_start_line != self._sel_end_line or
                self._sel_start_col != self._sel_end_col)

    def _ordered_selection(self):
        if (self._sel_start_line < self._sel_end_line or
                (self._sel_start_line == self._sel_end_line and
                 self._sel_start_col <= self._sel_end_col)):
            return self._sel_start_line, self._sel_start_col, self._sel_end_line, self._sel_end_col
        return self._sel_end_line, self._sel_end_col, self._sel_start_line, self._sel_start_col

    def _select_all(self):
        self._sel_start_line = 0
        self._sel_start_col = 0
        self._caret_line = len(self._lines) - 1
        self._caret_col = len(self._lines[-1]) if self._lines else 0
        self._sel_end_line = self._caret_line
        self._sel_end_col = self._caret_col

    def _delete_selection(self):
        if not self._has_selection():
            return
        sl, sc, el, ec = self._ordered_selection()
        new_text_lines = []
        new_text_lines.append(self._lines[sl][:sc])
        new_text_lines.append(self._lines[el][ec:])
        self._lines[sl] = new_text_lines[0] + new_text_lines[1]
        del self._lines[sl + 1:el + 1]
        self._caret_line = sl
        self._caret_col = sc
        self._sel_start_line = self._sel_end_line = sl
        self._sel_start_col = self._sel_end_col = sc
        self._sync_text_from_lines()

    def _insert_text(self, chars):
        if self._readonly:
            return
        if self._has_selection():
            self._delete_selection()
        insert_lines = chars.split('\n')
        line = self._lines[self._caret_line]
        before = line[:self._caret_col]
        after = line[self._caret_col:]
        if len(insert_lines) == 1:
            self._lines[self._caret_line] = before + insert_lines[0] + after
            self._caret_col += len(insert_lines[0])
        else:
            self._lines[self._caret_line] = before + insert_lines[0]
            new_lines = []
            for i in range(1, len(insert_lines) - 1):
                new_lines.append(insert_lines[i])
            new_lines.append(insert_lines[-1] + after)
            self._lines[self._caret_line + 1:self._caret_line + 1] = new_lines
            self._caret_line += len(insert_lines) - 1
            self._caret_col = len(insert_lines[-1])
        self._sel_start_line = self._sel_end_line = self._caret_line
        self._sel_start_col = self._sel_end_col = self._caret_col
        self._sync_text_from_lines()

    def _sync_text_from_lines(self):
        new_text = '\n'.join(self._lines)
        old = self._text
        self._text = new_text
        self._text_layout = None
        if old != new_text and self._on_change:
            self._on_change(new_text)

    def _ensure_caret_visible(self):
        cx, cy, cw, ch = self._content_rect()
        if cw <= 0 or ch <= 0:
            return
        lh = self._line_height()
        caret_y = self._caret_line * lh
        visible_top = self._scroll_y
        visible_bottom = self._scroll_y + ch
        if caret_y < visible_top:
            self._scroll_y = caret_y
        elif caret_y + lh > visible_bottom:
            self._scroll_y = caret_y + lh - ch
        self._update_scrollbars()

    def _max_line_width(self, dw_factory=None):
        fmt = self._get_text_fmt(dw_factory)
        if fmt is None:
            return max((len(line) * DEFAULT_FONT_SIZE_DIP * 0.6) for line in self._lines) if self._lines else 0
        lh = self._line_height()
        max_w = 0.0
        for line in self._lines:
            if not line:
                continue
            try:
                factory = dw_factory or pyd2d.GetDWriteFactory()
                if factory is None:
                    return max((len(l) * DEFAULT_FONT_SIZE_DIP * 0.6) for l in self._lines) if self._lines else 0
                layout = factory.CreateTextLayout(
                    line, fmt, 100000.0, float(lh))
                if layout:
                    metrics = layout.GetMetrics()
                    max_w = max(max_w, metrics.width)
            except Exception:
                max_w = max(max_w, len(line) * DEFAULT_FONT_SIZE_DIP * 0.6)
        return max_w

    def _update_scrollbars(self, dw_factory=None):
        rx, ry, rw, rh = self._rect
        lh = self._line_height()
        total_h = len(self._lines) * lh

        need_v = self._v_scroll_enabled and total_h > (rh - 2 * TEXT_PAD_Y)
        need_h = self._h_scroll_enabled and self._max_line_width(dw_factory) > (rw - 2 * TEXT_PAD_X - (SCROLLBAR_WIDTH if need_v else 0))

        old_v = self._v_scroll_active
        old_h = self._h_scroll_active
        self._v_scroll_active = bool(need_v and self._v_scrollbar)
        self._h_scroll_active = bool(need_h and self._h_scrollbar)

        if not self._v_scroll_active and self._scroll_y != 0:
            self._scroll_y = 0
        if not self._h_scroll_active and self._scroll_x != 0:
            self._scroll_x = 0

        if self._v_scroll_active != old_v or self._h_scroll_active != old_h:
            self._update_scrollbar_rects()

        cx, cy, cw, ch = self._content_rect()
        if self._v_scrollbar is not None and self._v_scroll_active:
            self._v_scrollbar.set_scroll_info(
                scroll_pos=int(self._scroll_y),
                scroll_max=max(0, int(total_h - ch)),
                page_size=int(ch))
        if self._h_scrollbar is not None and self._h_scroll_active:
            self._h_scrollbar.set_scroll_info(
                scroll_pos=int(self._scroll_x),
                scroll_max=max(0, int(self._max_line_width() - cw)),
                page_size=int(cw))

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
        self._dwrite_text_fmt.SetParagraphAlignment(pyd2d.PARAGRAPH_ALIGNMENT.NEAR)
        self._dwrite_text_fmt.SetWordWrapping(pyd2d.WORD_WRAPPING.NO_WRAP)
        return self._dwrite_text_fmt

    def _invalidate_text_layout(self):
        self._text_layout = None

    def set_focus(self, focused):
        if self._focused == focused:
            return
        self._focused = focused
        if focused:
            self._caret_visible = True
            self._blink_count = 0
        else:
            self._caret_visible = False
            self._sel_start_line = self._sel_end_line = self._caret_line
            self._sel_start_col = self._sel_end_col = self._caret_col
            self._dragging = False
            self._scroll_x = 0.0
            self._scroll_y = 0

    def tick_caret(self):
        if not self._focused:
            return False
        self._blink_count += 1
        if self._blink_count >= CARET_BLINK_MS // 50:
            self._blink_count = 0
            self._caret_visible = not self._caret_visible
            return True
        return False

    def set_rect(self, rect):
        super().set_rect(rect)
        self._update_scrollbar_rects()

    def _update_scrollbar_rects(self):
        rx, ry, rw, rh = self._rect
        has_h = self._has_h_scrollbar()
        has_v = self._has_v_scrollbar()
        if self._v_scrollbar:
            if self._v_scroll_active:
                sb_h = SCROLLBAR_WIDTH if has_h else 0
                self._v_scrollbar.set_rect(
                    (rx + rw - SCROLLBAR_WIDTH, ry, SCROLLBAR_WIDTH, rh - sb_h))
            else:
                self._v_scrollbar.set_rect((0, 0, 0, 0))
        if self._h_scrollbar:
            if self._h_scroll_active:
                sb_w = SCROLLBAR_WIDTH if has_v else 0
                self._h_scrollbar.set_rect(
                    (rx, ry + rh - SCROLLBAR_WIDTH, rw - sb_w, SCROLLBAR_WIDTH))
            else:
                self._h_scrollbar.set_rect((0, 0, 0, 0))

    def bind_to_frame(self, frame):
        self._frame = frame
        rx, ry, rw, rh = self._rect
        if self._v_scroll_enabled:
            sb_h = SCROLLBAR_WIDTH if self._h_scroll_enabled else 0
            self._v_scrollbar = D2DScrollBar(
                (rx + rw - SCROLLBAR_WIDTH, ry, SCROLLBAR_WIDTH, rh - sb_h),
                scroll_pos=0, scroll_max=100, page_size=20,
                orientation=D2DScrollBar.VERTICAL,
                on_scroll=self._on_v_scroll)
        if self._h_scroll_enabled:
            sb_w = SCROLLBAR_WIDTH if self._v_scroll_enabled else 0
            self._h_scrollbar = D2DScrollBar(
                (rx, ry + rh - SCROLLBAR_WIDTH, rw - sb_w, SCROLLBAR_WIDTH),
                scroll_pos=0, scroll_max=100, page_size=20,
                orientation=D2DScrollBar.HORIZONTAL,
                on_scroll=self._on_h_scroll)

    def _on_v_scroll(self, pos):
        self._scroll_y = pos
        self._invalidate_text_layout()

    def _on_h_scroll(self, pos):
        self._scroll_x = pos
        self._invalidate_text_layout()

    def on_key_down(self, key_code, modifiers):
        if self._state == self.DISABLED or not self._focused:
            return False
        ctrl = modifiers & wx.MOD_CONTROL
        shift = modifiers & wx.MOD_SHIFT

        if key_code == wx.WXK_BACK:
            if self._readonly:
                return False
            if self._has_selection():
                self._delete_selection()
            elif self._caret_col > 0:
                line = self._lines[self._caret_line]
                self._lines[self._caret_line] = line[:self._caret_col - 1] + line[self._caret_col:]
                self._caret_col -= 1
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
                self._sync_text_from_lines()
            elif self._caret_line > 0:
                prev_len = len(self._lines[self._caret_line - 1])
                self._lines[self._caret_line - 1] += self._lines[self._caret_line]
                del self._lines[self._caret_line]
                self._caret_line -= 1
                self._caret_col = prev_len
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
                self._sync_text_from_lines()
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_DELETE:
            if self._readonly:
                return False
            if self._has_selection():
                self._delete_selection()
            elif self._caret_col < len(self._lines[self._caret_line]):
                line = self._lines[self._caret_line]
                self._lines[self._caret_line] = line[:self._caret_col] + line[self._caret_col + 1:]
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
                self._sync_text_from_lines()
            elif self._caret_line < len(self._lines) - 1:
                self._lines[self._caret_line] += self._lines[self._caret_line + 1]
                del self._lines[self._caret_line + 1]
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
                self._sync_text_from_lines()
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_LEFT:
            if shift:
                anchor_l = self._sel_start_line if self._has_selection() else self._caret_line
                anchor_c = self._sel_start_col if self._has_selection() else self._caret_col
                self._move_caret_left()
                self._sel_start_line = anchor_l
                self._sel_start_col = anchor_c
                self._sel_end_line = self._caret_line
                self._sel_end_col = self._caret_col
            else:
                if self._has_selection():
                    sl, sc, el, ec = self._ordered_selection()
                    self._caret_line = sl
                    self._caret_col = sc
                else:
                    self._move_caret_left()
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_RIGHT:
            if shift:
                anchor_l = self._sel_start_line if self._has_selection() else self._caret_line
                anchor_c = self._sel_start_col if self._has_selection() else self._caret_col
                self._move_caret_right()
                self._sel_start_line = anchor_l
                self._sel_start_col = anchor_c
                self._sel_end_line = self._caret_line
                self._sel_end_col = self._caret_col
            else:
                if self._has_selection():
                    sl, sc, el, ec = self._ordered_selection()
                    self._caret_line = el
                    self._caret_col = ec
                else:
                    self._move_caret_right()
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_UP:
            if shift:
                anchor_l = self._sel_start_line if self._has_selection() else self._caret_line
                anchor_c = self._sel_start_col if self._has_selection() else self._caret_col
                if self._caret_line > 0:
                    self._caret_line -= 1
                    self._caret_col = min(self._caret_col, len(self._lines[self._caret_line]))
                self._sel_start_line = anchor_l
                self._sel_start_col = anchor_c
                self._sel_end_line = self._caret_line
                self._sel_end_col = self._caret_col
            else:
                if self._has_selection():
                    sl, sc, el, ec = self._ordered_selection()
                    self._caret_line = sl
                    self._caret_col = sc
                elif self._caret_line > 0:
                    self._caret_line -= 1
                    self._caret_col = min(self._caret_col, len(self._lines[self._caret_line]))
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_DOWN:
            if shift:
                anchor_l = self._sel_start_line if self._has_selection() else self._caret_line
                anchor_c = self._sel_start_col if self._has_selection() else self._caret_col
                if self._caret_line < len(self._lines) - 1:
                    self._caret_line += 1
                    self._caret_col = min(self._caret_col, len(self._lines[self._caret_line]))
                self._sel_start_line = anchor_l
                self._sel_start_col = anchor_c
                self._sel_end_line = self._caret_line
                self._sel_end_col = self._caret_col
            else:
                if self._has_selection():
                    sl, sc, el, ec = self._ordered_selection()
                    self._caret_line = el
                    self._caret_col = ec
                elif self._caret_line < len(self._lines) - 1:
                    self._caret_line += 1
                    self._caret_col = min(self._caret_col, len(self._lines[self._caret_line]))
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_HOME:
            if ctrl:
                target_line, target_col = 0, 0
            else:
                target_line, target_col = self._caret_line, 0
            if shift:
                anchor_l = self._sel_start_line if self._has_selection() else self._caret_line
                anchor_c = self._sel_start_col if self._has_selection() else self._caret_col
                self._caret_line = target_line
                self._caret_col = target_col
                self._sel_start_line = anchor_l
                self._sel_start_col = anchor_c
                self._sel_end_line = self._caret_line
                self._sel_end_col = self._caret_col
            else:
                self._caret_line = target_line
                self._caret_col = target_col
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_END:
            if ctrl:
                target_line = len(self._lines) - 1
                target_col = len(self._lines[-1]) if self._lines else 0
            else:
                target_line = self._caret_line
                target_col = len(self._lines[self._caret_line])
            if shift:
                anchor_l = self._sel_start_line if self._has_selection() else self._caret_line
                anchor_c = self._sel_start_col if self._has_selection() else self._caret_col
                self._caret_line = target_line
                self._caret_col = target_col
                self._sel_start_line = anchor_l
                self._sel_start_col = anchor_c
                self._sel_end_line = self._caret_line
                self._sel_end_col = self._caret_col
            else:
                self._caret_line = target_line
                self._caret_col = target_col
                self._sel_start_line = self._sel_end_line = self._caret_line
                self._sel_start_col = self._sel_end_col = self._caret_col
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True

        if key_code == wx.WXK_RETURN:
            if self._readonly:
                return False
            self._insert_text('\n')
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True

        if ctrl:
            if key_code == ord('A'):
                self._select_all()
                self._ensure_caret_visible()
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
                self._ensure_caret_visible()
                self._invalidate_text_layout()
                return True
            if key_code == ord('X'):
                if self._readonly:
                    return False
                sel = self.selected_text
                if sel:
                    clipboard_copy(sel)
                    self._delete_selection()
                self._ensure_caret_visible()
                self._invalidate_text_layout()
                return True

        return False

    def _move_caret_left(self):
        if self._caret_col > 0:
            self._caret_col -= 1
        elif self._caret_line > 0:
            self._caret_line -= 1
            self._caret_col = len(self._lines[self._caret_line])

    def _move_caret_right(self):
        if self._caret_col < len(self._lines[self._caret_line]):
            self._caret_col += 1
        elif self._caret_line < len(self._lines) - 1:
            self._caret_line += 1
            self._caret_col = 0

    def on_char(self, char_code):
        if self._state == self.DISABLED or not self._focused:
            return False
        if self._readonly:
            return False
        if char_code >= 32 and char_code != 127:
            self._insert_text(chr(char_code))
            self._ensure_caret_visible()
            self._invalidate_text_layout()
            return True
        return False

    def _x_to_col(self, line_idx, x, dw_factory=None):
        line_text = self._lines[line_idx] if line_idx < len(self._lines) else ''
        if not line_text:
            return 0
        fmt = self._get_text_fmt(dw_factory)
        if fmt is None:
            return max(0, min(int(x / (DEFAULT_FONT_SIZE_DIP * 0.6)), len(line_text)))
        lh = self._line_height()
        try:
            factory = dw_factory or pyd2d.GetDWriteFactory()
            if factory is None:
                return max(0, min(int(x / (DEFAULT_FONT_SIZE_DIP * 0.6)), len(line_text)))
            layout = factory.CreateTextLayout(
                line_text, fmt, 100000.0, float(lh))
            if layout is None:
                return max(0, min(int(x / (DEFAULT_FONT_SIZE_DIP * 0.6)), len(line_text)))
            result = layout.HitTestPoint(float(x), float(lh / 2))
            if result:
                is_trailing, is_inside, htm = result
                col = htm.textPosition
                if is_trailing and col < len(line_text):
                    col += 1
                return max(0, min(col, len(line_text)))
        except Exception:
            pass
        return max(0, min(int(x / (DEFAULT_FONT_SIZE_DIP * 0.6)), len(line_text)))

    def _pos_from_point(self, x, y):
        cx, cy, cw, ch = self._content_rect()
        rel_y = y - cy + self._scroll_y
        rel_x = x - cx + self._scroll_x
        lh = self._line_height()
        line = int(rel_y / lh) if lh > 0 else 0
        line = max(0, min(line, len(self._lines) - 1))
        col = self._x_to_col(line, rel_x)
        return line, col

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        if not self.hit_test(pt):
            return False
        if self._v_scroll_active and self._v_scrollbar and self._v_scrollbar.hit_test(pt):
            return self._v_scrollbar.on_mouse_down(pt)
        if self._h_scroll_active and self._h_scrollbar and self._h_scrollbar.hit_test(pt):
            return self._h_scrollbar.on_mouse_down(pt)
        if not self._focused and self._frame:
            self._frame.set_focused_control(self)
        elif not self._focused:
            self.set_focus(True)
        shift = get_shift_from_mouse()
        line, col = self._pos_from_point(pt[0], pt[1])
        if shift and self._focused:
            anchor_l = self._sel_start_line if self._has_selection() else self._caret_line
            anchor_c = self._sel_start_col if self._has_selection() else self._caret_col
            self._caret_line = line
            self._caret_col = col
            self._sel_start_line = anchor_l
            self._sel_start_col = anchor_c
            self._sel_end_line = line
            self._sel_end_col = col
        else:
            self._caret_line = line
            self._caret_col = col
            self._sel_start_line = self._sel_end_line = line
            self._sel_start_col = self._sel_end_col = col
        self._dragging = True
        self._caret_visible = True
        self._blink_count = 0
        self._ensure_caret_visible()
        self._invalidate_text_layout()
        return True

    def on_mouse_up(self, pt):
        dirty = False
        if self._v_scrollbar and self._v_scrollbar._captured:
            if self._v_scrollbar.on_mouse_up(pt):
                dirty = True
        if self._h_scrollbar and self._h_scrollbar._captured:
            if self._h_scrollbar.on_mouse_up(pt):
                dirty = True
        if dirty:
            self._invalidate_text_layout()
            return True
        if self._dragging:
            self._dragging = False
            return True
        return False

    def on_mouse_move(self, pt):
        if self._v_scrollbar and self._v_scrollbar._captured:
            result = self._v_scrollbar.on_mouse_move(pt)
            if result:
                self._invalidate_text_layout()
            return result
        if self._h_scrollbar and self._h_scrollbar._captured:
            result = self._h_scrollbar.on_mouse_move(pt)
            if result:
                self._invalidate_text_layout()
            return result
        if self._state == self.DISABLED:
            return False
        in_rect = super().hit_test(pt)
        if in_rect and self._is_scrollbar_area(pt):
            self._cursor_type = wx.CURSOR_ARROW
        elif in_rect:
            self._cursor_type = wx.CURSOR_IBEAM
        if self._dragging and self._focused:
            line, col = self._pos_from_point(pt[0], pt[1])
            if line != self._sel_end_line or col != self._sel_end_col:
                self._sel_end_line = line
                self._sel_end_col = col
                self._caret_line = line
                self._caret_col = col
                self._ensure_caret_visible()
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
        if self._v_scrollbar:
            self._v_scrollbar.on_mouse_leave()
        if self._h_scrollbar:
            self._h_scrollbar.on_mouse_leave()
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
        if self._is_scrollbar_area(pt):
            return False
        if not self._focused:
            if self._frame:
                self._frame.set_focused_control(self)
            else:
                self.set_focus(True)
        line, col = self._pos_from_point(pt[0], pt[1])
        text = self._lines[line] if line < len(self._lines) else ''
        start = col
        end = col
        while start > 0 and text[start - 1] not in (' ', '\t', '\n'):
            start -= 1
        while end < len(text) and text[end] not in (' ', '\t', '\n'):
            end += 1
        self._sel_start_line = self._sel_end_line = line
        self._sel_start_col = start
        self._sel_end_col = end
        self._caret_line = line
        self._caret_col = end
        self._ensure_caret_visible()
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
            self._draw_scrollbars(ctx)
            return

        self._update_scrollbars(ctx.dw_factory)

        fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
        lh = self._line_height()

        rt.PushAxisAlignedClip(float(cx), float(cy),
                               float(cx + cw), float(cy + ch))

        first_visible = max(0, int(self._scroll_y / lh))
        last_visible = min(len(self._lines), int((self._scroll_y + ch) / lh) + 1)

        if self._has_selection():
            sl, sc, el, ec = self._ordered_selection()
            sel_brush = get_brush(rt, *colors['sel_bg'])
            for li in range(max(sl, first_visible), min(el + 1, last_visible + 1)):
                if li >= len(self._lines):
                    break
                line_y = cy + li * lh - self._scroll_y
                if li == sl and li == el:
                    x1 = cx + self._col_to_x(li, sc, ctx.dw_factory) - self._scroll_x
                    x2 = cx + self._col_to_x(li, ec, ctx.dw_factory) - self._scroll_x
                elif li == sl:
                    x1 = cx + self._col_to_x(li, sc, ctx.dw_factory) - self._scroll_x
                    x2 = cx + cw
                elif li == el:
                    x1 = cx - self._scroll_x
                    x2 = cx + self._col_to_x(li, ec, ctx.dw_factory) - self._scroll_x
                else:
                    x1 = cx - self._scroll_x
                    x2 = cx + cw
                rt.FillRectangle(float(x1), float(line_y),
                                 float(x2), float(line_y + lh), sel_brush)

        text_brush = get_brush(rt, *colors['text'])
        for li in range(first_visible, last_visible):
            if li >= len(self._lines):
                break
            line_y = cy + li * lh - self._scroll_y
            line_text = self._lines[li]
            if line_text:
                text_x = cx - self._scroll_x
                rt.DrawText(line_text, fmt,
                            float(text_x), float(line_y),
                            float(text_x + cw + self._scroll_x), float(line_y + lh),
                            text_brush)

        if self._has_selection():
            sl, sc, el, ec = self._ordered_selection()
            sel_text_brush = get_brush(rt, *colors['sel_text'])
            for li in range(max(sl, first_visible), min(el + 1, last_visible + 1)):
                if li >= len(self._lines):
                    break
                line_y = cy + li * lh - self._scroll_y
                if li == sl and li == el:
                    sel_text = self._lines[li][sc:ec]
                    x1 = cx + self._col_to_x(li, sc, ctx.dw_factory) - self._scroll_x
                    x2 = cx + self._col_to_x(li, ec, ctx.dw_factory) - self._scroll_x
                elif li == sl:
                    sel_text = self._lines[li][sc:]
                    x1 = cx + self._col_to_x(li, sc, ctx.dw_factory) - self._scroll_x
                    x2 = cx + cw
                elif li == el:
                    sel_text = self._lines[li][:ec]
                    x1 = cx - self._scroll_x
                    x2 = cx + self._col_to_x(li, ec, ctx.dw_factory) - self._scroll_x
                else:
                    sel_text = self._lines[li]
                    x1 = cx - self._scroll_x
                    x2 = cx + cw
                if sel_text:
                    rt.DrawText(sel_text, fmt,
                                float(x1), float(line_y),
                                float(x2), float(line_y + lh),
                                sel_text_brush)

        if not self._text and self._placeholder:
            ph_brush = get_brush(rt, 0.6, 0.6, 0.6, 1.0)
            rt.DrawText(self._placeholder, fmt,
                        float(cx), float(cy),
                        float(cx + cw), float(cy + ch), ph_brush)

        if self._focused and self._caret_visible:
            caret_y = cy + self._caret_line * lh - self._scroll_y
            caret_x = cx + self._col_to_x(self._caret_line, self._caret_col,
                                           ctx.dw_factory) - self._scroll_x
            caret_h, caret_offset = self._caret_metrics(ctx.dw_factory)
            caret_top = caret_y + caret_offset + 2
            caret_brush = get_brush(rt, *colors['caret'])
            cx_snap = float(int(caret_x) + 0.5)
            rt.DrawLine(cx_snap, float(caret_top),
                        cx_snap, float(caret_top + caret_h),
                        caret_brush, CARET_WIDTH)

        rt.PopAxisAlignedClip()
        self._draw_scrollbars(ctx)

    def _col_to_x(self, line_idx, col, dw_factory):
        fmt = self._get_text_fmt(dw_factory)
        if fmt is None:
            return col * (DEFAULT_FONT_SIZE_DIP * 0.6)
        line_text = self._lines[line_idx] if line_idx < len(self._lines) else ''
        if not line_text or col == 0:
            return 0.0
        lh = self._line_height()
        try:
            layout = dw_factory.CreateTextLayout(line_text, fmt, 100000.0, float(lh))
            if layout is None:
                return col * (DEFAULT_FONT_SIZE_DIP * 0.6)
            if col <= len(line_text):
                point_x, point_y, _ = layout.HitTestTextPosition(min(col, len(line_text) - 1), col >= len(line_text))
            else:
                point_x, point_y, _ = layout.HitTestTextPosition(len(line_text) - 1, True)
            return point_x
        except Exception:
            pass
        return col * (DEFAULT_FONT_SIZE_DIP * 0.6)

    def _draw_scrollbars(self, ctx):
        if self._v_scrollbar and self._v_scroll_active:
            self._v_scrollbar.draw(ctx, self._v_scrollbar._rect)
        if self._h_scrollbar and self._h_scroll_active:
            self._h_scrollbar.draw(ctx, self._h_scrollbar._rect)
        corner = self._corner_rect()
        if corner:
            cx, cy, cw, ch = corner
            brush = get_brush(ctx.rt, 0.93, 0.93, 0.93, 1.0)
            ctx.rt.FillRectangle(float(cx), float(cy), float(cx + cw), float(cy + ch), brush)


class SkinAwareTextBox(D2DTextBox):
    """皮肤化多行文本编辑框 — 使用 CtrlBorder 属性绘制边框。"""

    def __init__(self, rect, skin_context, text='', placeholder='',
                 readonly=False, on_change=None, h_scroll=True, v_scroll=True,
                 subcat='CtrlBorder'):
        super().__init__(rect, text=text, placeholder=placeholder,
                         readonly=readonly, on_change=on_change,
                         h_scroll=h_scroll, v_scroll=v_scroll)
        self._ctx = skin_context
        self._subcat = subcat
        self._dwrite_text_fmt_cached = None

    def _get_text_fmt_cached(self, dw_factory=None):
        if self._dwrite_text_fmt_cached is not None:
            return self._dwrite_text_fmt_cached
        self._dwrite_text_fmt_cached = self._ctx.get_text_format(
            self._subcat, dw_factory=dw_factory,
            alignment=pyd2d.TEXT_ALIGNMENT.LEADING,
            para_alignment=pyd2d.PARAGRAPH_ALIGNMENT.NEAR,
            no_wrap=True)
        return self._dwrite_text_fmt_cached

    def bind_to_frame(self, frame):
        super().bind_to_frame(frame)
        rx, ry, rw, rh = self._rect
        if self._v_scroll_enabled and self._ctx:
            sb_h = SCROLLBAR_WIDTH if self._h_scroll_enabled else 0
            self._v_scrollbar = SkinAwareScrollBar(
                (rx + rw - SCROLLBAR_WIDTH, ry, SCROLLBAR_WIDTH, rh - sb_h),
                self._ctx,
                scroll_pos=0, scroll_max=100, page_size=20,
                orientation=D2DScrollBar.VERTICAL,
                on_scroll=self._on_v_scroll)
        if self._h_scroll_enabled and self._ctx:
            sb_w = SCROLLBAR_WIDTH if self._v_scroll_enabled else 0
            self._h_scrollbar = SkinAwareScrollBar(
                (rx, ry + rh - SCROLLBAR_WIDTH, rw - sb_w, SCROLLBAR_WIDTH),
                self._ctx,
                scroll_pos=0, scroll_max=100, page_size=20,
                orientation=D2DScrollBar.HORIZONTAL,
                on_scroll=self._on_h_scroll)

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
                if tc is not None and hasattr(tc, 'Red'):
                    colors = dict(colors)
                    colors['text'] = (tc.Red() / 255.0, tc.Green() / 255.0,
                                      tc.Blue() / 255.0, tc.Alpha() / 255.0)

        cx, cy, cw, ch = self._content_rect()
        if cw <= 0 or ch <= 0:
            self._draw_scrollbars(ctx)
            return

        self._update_scrollbars(ctx.dw_factory)

        text_fmt = self._get_text_fmt_cached(dw_factory=ctx.dw_factory)
        if text_fmt is None:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)

        lh = self._line_height()

        rt.PushAxisAlignedClip(float(cx), float(cy),
                               float(cx + cw), float(cy + ch))

        first_visible = max(0, int(self._scroll_y / lh))
        last_visible = min(len(self._lines), int((self._scroll_y + ch) / lh) + 1)

        if self._has_selection():
            sl, sc, el, ec = self._ordered_selection()
            sel_brush = get_brush(rt, *colors['sel_bg'])
            for li in range(max(sl, first_visible), min(el + 1, last_visible + 1)):
                if li >= len(self._lines):
                    break
                line_y = cy + li * lh - self._scroll_y
                if li == sl and li == el:
                    x1 = cx + self._col_to_x(li, sc, ctx.dw_factory) - self._scroll_x
                    x2 = cx + self._col_to_x(li, ec, ctx.dw_factory) - self._scroll_x
                elif li == sl:
                    x1 = cx + self._col_to_x(li, sc, ctx.dw_factory) - self._scroll_x
                    x2 = cx + cw
                elif li == el:
                    x1 = cx - self._scroll_x
                    x2 = cx + self._col_to_x(li, ec, ctx.dw_factory) - self._scroll_x
                else:
                    x1 = cx - self._scroll_x
                    x2 = cx + cw
                rt.FillRectangle(float(x1), float(line_y),
                                 float(x2), float(line_y + lh), sel_brush)

        text_brush = get_brush(rt, *colors['text'])
        for li in range(first_visible, last_visible):
            if li >= len(self._lines):
                break
            line_y = cy + li * lh - self._scroll_y
            line_text = self._lines[li]
            if line_text:
                text_x = cx - self._scroll_x
                rt.DrawText(line_text, text_fmt,
                            float(text_x), float(line_y),
                            float(text_x + cw + self._scroll_x), float(line_y + lh),
                            text_brush)

        if self._has_selection():
            sl, sc, el, ec = self._ordered_selection()
            sel_text_brush = get_brush(rt, *colors['sel_text'])
            for li in range(max(sl, first_visible), min(el + 1, last_visible + 1)):
                if li >= len(self._lines):
                    break
                line_y = cy + li * lh - self._scroll_y
                if li == sl and li == el:
                    sel_text = self._lines[li][sc:ec]
                    x1 = cx + self._col_to_x(li, sc, ctx.dw_factory) - self._scroll_x
                    x2 = cx + self._col_to_x(li, ec, ctx.dw_factory) - self._scroll_x
                elif li == sl:
                    sel_text = self._lines[li][sc:]
                    x1 = cx + self._col_to_x(li, sc, ctx.dw_factory) - self._scroll_x
                    x2 = cx + cw
                elif li == el:
                    sel_text = self._lines[li][:ec]
                    x1 = cx - self._scroll_x
                    x2 = cx + self._col_to_x(li, ec, ctx.dw_factory) - self._scroll_x
                else:
                    sel_text = self._lines[li]
                    x1 = cx - self._scroll_x
                    x2 = cx + cw
                if sel_text:
                    rt.DrawText(sel_text, text_fmt,
                                float(x1), float(line_y),
                                float(x2), float(line_y + lh),
                                sel_text_brush)

        if not self._text and self._placeholder:
            ph_brush = get_brush(rt, 0.6, 0.6, 0.6, 1.0)
            rt.DrawText(self._placeholder, text_fmt,
                        float(cx), float(cy),
                        float(cx + cw), float(cy + ch), ph_brush)

        if self._focused and self._caret_visible:
            caret_y = cy + self._caret_line * lh - self._scroll_y
            caret_x = cx + self._col_to_x(self._caret_line, self._caret_col,
                                           ctx.dw_factory) - self._scroll_x
            caret_h, caret_offset = self._caret_metrics(ctx.dw_factory)
            caret_top = caret_y + caret_offset + 2
            caret_brush = get_brush(rt, *colors['caret'])
            cx_snap = float(int(caret_x) + 0.5)
            rt.DrawLine(cx_snap, float(caret_top),
                        cx_snap, float(caret_top + caret_h),
                        caret_brush, CARET_WIDTH)

        rt.PopAxisAlignedClip()
        self._draw_scrollbars(ctx)
