"""D2D 控件 — D2DListBox / SkinAwareListBox 列表框。"""
import wx
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush
from ..d2d_render import d2d_draw_text
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP
from .headerctrl import draw_ctrl_border
from .scrollbar import D2DScrollBar, SkinAwareScrollBar

SCROLLBAR_WIDTH = 16
ITEM_PAD_X = 6
ITEM_PAD_Y = 2

LISTBOX_COLORS = {
    'normal': {
        'bg': (1.0, 1.0, 1.0, 1.0),
        'item_bg': None,
        'item_text': (0.0, 0.0, 0.0, 1.0),
    },
    'hover': {
        'item_bg': (0.90, 0.93, 0.98, 1.0),
        'item_text': (0.0, 0.0, 0.0, 1.0),
    },
    'selected': {
        'item_bg': (0.20, 0.45, 0.78, 1.0),
        'item_text': (1.0, 1.0, 1.0, 1.0),
    },
    'selected_no_focus': {
        'item_bg': (0.70, 0.75, 0.82, 1.0),
        'item_text': (1.0, 1.0, 1.0, 1.0),
    },
    'disabled': {
        'bg': (0.96, 0.96, 0.97, 1.0),
        'item_text': (0.55, 0.55, 0.58, 1.0),
    },
}


class D2DListBox(SheControl):
    """D2D 自绘列表框 — 无 HWND，纯 D2D 渲染。

    Win32 ListBox 行为：
    - 单选/多选模式
    - 点击选中项，Ctrl+点击多选切换，Shift+点击范围选
    - 纵向 ScrollBar（内容超出时自动激活）
    - 键盘导航：Up/Down 移动选中，Home/End 首尾，Space 切换选中
    - 双击触发 on_double_click 回调
    - 焦点时选中项高亮，失焦时灰色高亮
    """

    NORMAL = 0
    HOVER = 1
    PRESSED = 2
    DISABLED = 3

    SINGLE = 0
    MULTIPLE = 1
    EXTENDED = 2

    def __init__(self, rect, items=None, selected=None, mode=0,
                 on_change=None, on_double_click=None):
        super().__init__(rect, "")
        self._items = list(items or [])
        self._selected = set(selected or [])
        self._mode = mode
        self._on_change = on_change
        self._on_double_click = on_double_click
        self._focused = False
        self._hover_index = -1
        self._anchor_index = -1
        self._frame = None
        self._cursor_type = wx.CURSOR_ARROW
        self._scroll_y = 0
        self._v_scrollbar = None
        self._dwrite_text_fmt = None

    @property
    def items(self):
        return list(self._items)

    @property
    def selected_indices(self):
        return sorted(self._selected)

    @property
    def selected_index(self):
        indices = sorted(self._selected)
        return indices[0] if indices else -1

    @property
    def selected_item(self):
        idx = self.selected_index
        return self._items[idx] if 0 <= idx < len(self._items) else None

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value

    @property
    def focused(self):
        return self._focused

    def set_items(self, items):
        self._items = list(items or [])
        self._selected.clear()
        self._hover_index = -1
        self._anchor_index = -1
        self._scroll_y = 0
        self._update_scrollbar()

    def add_item(self, item):
        self._items.append(item)
        self._update_scrollbar()

    def insert_item(self, index, item):
        self._items.insert(index, item)
        new_selected = set()
        for s in self._selected:
            if s >= index:
                new_selected.add(s + 1)
            else:
                new_selected.add(s)
        self._selected = new_selected
        self._update_scrollbar()

    def remove_item(self, index):
        if 0 <= index < len(self._items):
            self._items.pop(index)
            new_selected = set()
            for s in self._selected:
                if s == index:
                    continue
                elif s > index:
                    new_selected.add(s - 1)
                else:
                    new_selected.add(s)
            self._selected = new_selected
            self._update_scrollbar()

    def clear(self):
        self._items.clear()
        self._selected.clear()
        self._hover_index = -1
        self._anchor_index = -1
        self._scroll_y = 0
        self._update_scrollbar()

    def select(self, index):
        if 0 <= index < len(self._items):
            self._selected.add(index)

    def deselect(self, index):
        self._selected.discard(index)

    def select_all(self):
        if self._mode != self.SINGLE:
            self._selected = set(range(len(self._items)))

    def deselect_all(self):
        self._selected.clear()

    def is_selected(self, index):
        return index in self._selected

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
        self._dwrite_text_fmt.SetParagraphAlignment(pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return self._dwrite_text_fmt

    def _line_height(self, dw_factory=None):
        fmt = self._get_text_fmt(dw_factory)
        if fmt is None:
            return DEFAULT_FONT_SIZE_DIP + ITEM_PAD_Y * 2
        try:
            factory = dw_factory or pyd2d.GetDWriteFactory()
            if factory is None:
                return DEFAULT_FONT_SIZE_DIP + ITEM_PAD_Y * 2
            layout = factory.CreateTextLayout("Ay", fmt, 100000.0, 1000.0)
            if layout:
                lm = layout.GetLineMetrics()
                if lm:
                    return lm[0].height + ITEM_PAD_Y * 2
        except Exception:
            pass
        return DEFAULT_FONT_SIZE_DIP + ITEM_PAD_Y * 2

    def _content_rect(self):
        rx, ry, rw, rh = self._rect
        sb_w = SCROLLBAR_WIDTH if self._has_v_scrollbar() else 0
        return (rx + 2, ry + 2, rw - 4 - sb_w, rh - 4)

    def _has_v_scrollbar(self):
        return self._v_scrollbar is not None

    def _total_height(self, dw_factory=None):
        lh = self._line_height(dw_factory)
        return len(self._items) * lh

    def _visible_count(self, dw_factory=None):
        _, _, _, ch = self._content_rect()
        lh = self._line_height(dw_factory)
        if lh <= 0:
            return 0
        return int(ch // lh)

    def _item_rect(self, index, dw_factory=None):
        cx, cy, cw, ch = self._content_rect()
        lh = self._line_height(dw_factory)
        y = cy + index * lh - self._scroll_y
        return (cx, y, cw, lh)

    def _index_from_y(self, py, dw_factory=None):
        cx, cy, cw, ch = self._content_rect()
        lh = self._line_height(dw_factory)
        if lh <= 0:
            return -1
        idx = int((py - cy + self._scroll_y) // lh)
        if 0 <= idx < len(self._items):
            return idx
        return -1

    def _update_scrollbar(self, dw_factory=None):
        if self._v_scrollbar is None:
            return
        lh = self._line_height(dw_factory)
        total = len(self._items) * lh
        _, _, _, ch = self._content_rect()
        self._v_scrollbar.set_scroll_info(
            scroll_max=max(0, total - ch),
            page_size=ch)
        max_scroll = max(0, total - ch)
        if self._scroll_y > max_scroll:
            self._scroll_y = max_scroll
        self._v_scrollbar.set_scroll_pos(self._scroll_y)

    def _ensure_visible(self, index, dw_factory=None):
        if index < 0 or index >= len(self._items):
            return
        lh = self._line_height(dw_factory)
        _, _, _, ch = self._content_rect()
        item_top = index * lh
        if item_top < self._scroll_y:
            self._scroll_y = item_top
        elif item_top + lh > self._scroll_y + ch:
            self._scroll_y = item_top + lh - ch
        self._scroll_y = max(0, self._scroll_y)
        if self._v_scrollbar:
            self._v_scrollbar.set_scroll_pos(self._scroll_y)

    def _border_state(self):
        if self._state == self.DISABLED:
            return 'disabled'
        if self._focused:
            return 'default'
        if self._state == self.HOVER:
            return 'hover'
        return 'normal'

    def bind_to_frame(self, frame):
        self._frame = frame
        rx, ry, rw, rh = self._rect
        self._v_scrollbar = D2DScrollBar(
            (rx + rw - SCROLLBAR_WIDTH, ry + 2,
             SCROLLBAR_WIDTH, rh - 4),
            scroll_pos=0, scroll_max=0, page_size=1,
            orientation=D2DScrollBar.VERTICAL,
            on_scroll=self._on_v_scroll)
        self._update_scrollbar()

    def _sync_scrollbar_rect(self):
        if self._v_scrollbar is None:
            return
        rx, ry, rw, rh = self._rect
        self._v_scrollbar._rect = (
            rx + rw - SCROLLBAR_WIDTH, ry + 2,
            SCROLLBAR_WIDTH, rh - 4)
        self._update_scrollbar()

    def set_rect(self, rect):
        super().set_rect(rect)
        self._sync_scrollbar_rect()

    def _on_v_scroll(self, pos):
        self._scroll_y = pos
        return True

    def set_focus(self, focused):
        if self._focused == focused:
            return
        self._focused = focused

    def hit_test(self, pt):
        if not super().hit_test(pt):
            return False
        if self._v_scrollbar and self._v_scrollbar.hit_test(pt):
            return False
        return True

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._v_scrollbar and self._v_scrollbar.hit_test(pt):
            return self._v_scrollbar.on_mouse_down(pt)
        if not self.hit_test(pt):
            return False
        if self._frame:
            self._frame.set_focused_control(self)
        else:
            self.set_focus(True)
        idx = self._index_from_y(pt[1])
        if idx < 0:
            return True
        try:
            shift = wx.GetKeyState(wx.WXK_SHIFT)
            ctrl = wx.GetKeyState(wx.WXK_CONTROL)
        except Exception:
            shift = False
            ctrl = False
        if self._mode == self.SINGLE:
            self._selected = {idx}
            self._anchor_index = idx
        elif self._mode == self.MULTIPLE:
            if idx in self._selected:
                self._selected.discard(idx)
            else:
                self._selected.add(idx)
        elif self._mode == self.EXTENDED:
            if ctrl:
                if idx in self._selected:
                    self._selected.discard(idx)
                else:
                    self._selected.add(idx)
            elif shift and self._anchor_index >= 0:
                lo = min(self._anchor_index, idx)
                hi = max(self._anchor_index, idx)
                self._selected = set(range(lo, hi + 1))
            else:
                self._selected = {idx}
                self._anchor_index = idx
        if self._on_change:
            self._on_change(sorted(self._selected))
        return True

    def on_mouse_up(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._v_scrollbar and self._v_scrollbar._captured:
            return self._v_scrollbar.on_mouse_up(pt)
        return False

    def on_mouse_move(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._v_scrollbar and self._v_scrollbar._captured:
            return self._v_scrollbar.on_mouse_move(pt)
        if self._v_scrollbar and self._v_scrollbar.hit_test(pt):
            return self._v_scrollbar.on_mouse_move(pt)
        if not self.hit_test(pt):
            if self._hover_index >= 0:
                self._hover_index = -1
                return True
            return False
        idx = self._index_from_y(pt[1])
        changed = idx != self._hover_index
        self._hover_index = idx
        return changed

    def on_mouse_leave(self):
        changed = self._hover_index >= 0
        self._hover_index = -1
        if self._v_scrollbar:
            self._v_scrollbar.on_mouse_leave()
        return changed

    def on_mouse_wheel(self, pt, delta):
        if self._state == self.DISABLED:
            return False
        if not super().hit_test(pt):
            return False
        if self._v_scrollbar is None or self._v_scrollbar._scroll_max <= 0:
            return False
        lh = self._line_height()
        scroll_delta = -delta * lh
        new_pos = max(0, min(self._v_scrollbar._scroll_max,
                              self._scroll_y + scroll_delta))
        if new_pos != self._scroll_y:
            self._scroll_y = new_pos
            self._v_scrollbar.set_scroll_pos(self._scroll_y)
            return True
        return False

    def on_double_click(self, pt):
        if self._state == self.DISABLED:
            return False
        idx = self._index_from_y(pt[1])
        if idx >= 0 and self._on_double_click:
            self._on_double_click(idx)
            return True
        return False

    def on_key_down(self, key_code, modifiers):
        if self._state == self.DISABLED:
            return False
        if not self._items:
            return False
        ctrl = bool(modifiers & wx.MOD_CONTROL)
        shift = bool(modifiers & wx.MOD_SHIFT)
        changed = False
        if key_code == wx.WXK_UP:
            cur = self.selected_index
            new_idx = max(0, (cur if cur >= 0 else 0) - 1)
            if self._mode == self.SINGLE:
                self._selected = {new_idx}
            elif self._mode == self.EXTENDED and shift and self._anchor_index >= 0:
                lo = min(self._anchor_index, new_idx)
                hi = max(self._anchor_index, new_idx)
                self._selected = set(range(lo, hi + 1))
            else:
                self._selected = {new_idx}
                self._anchor_index = new_idx
            self._ensure_visible(new_idx)
            changed = True
        elif key_code == wx.WXK_DOWN:
            cur = self.selected_index
            new_idx = min(len(self._items) - 1, (cur if cur >= 0 else 0) + 1)
            if self._mode == self.SINGLE:
                self._selected = {new_idx}
            elif self._mode == self.EXTENDED and shift and self._anchor_index >= 0:
                lo = min(self._anchor_index, new_idx)
                hi = max(self._anchor_index, new_idx)
                self._selected = set(range(lo, hi + 1))
            else:
                self._selected = {new_idx}
                self._anchor_index = new_idx
            self._ensure_visible(new_idx)
            changed = True
        elif key_code == wx.WXK_HOME:
            if self._mode == self.SINGLE:
                self._selected = {0}
            elif self._mode == self.EXTENDED and shift and self._anchor_index >= 0:
                self._selected = set(range(0, self._anchor_index + 1))
            else:
                self._selected = {0}
                self._anchor_index = 0
            self._ensure_visible(0)
            changed = True
        elif key_code == wx.WXK_END:
            last = len(self._items) - 1
            if self._mode == self.SINGLE:
                self._selected = {last}
            elif self._mode == self.EXTENDED and shift and self._anchor_index >= 0:
                self._selected = set(range(self._anchor_index, last + 1))
            else:
                self._selected = {last}
                self._anchor_index = last
            self._ensure_visible(last)
            changed = True
        elif key_code == wx.WXK_SPACE:
            if self._mode != self.SINGLE:
                cur = self.selected_index
                if cur >= 0:
                    if cur in self._selected:
                        self._selected.discard(cur)
                    else:
                        self._selected.add(cur)
                    changed = True
        elif key_code == ord('A') and ctrl:
            if self._mode != self.SINGLE:
                self._selected = set(range(len(self._items)))
                changed = True
        if changed and self._on_change:
            self._on_change(sorted(self._selected))
        return changed

    def on_char(self, char_code):
        return False

    def tick_caret(self):
        return False

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt
        dw_factory = ctx.dw_factory
        text_fmt = self._get_text_fmt(dw_factory)
        lh = self._line_height(dw_factory)

        border_state = self._border_state()
        draw_ctrl_border(rt, (rx, ry, rw, rh), state=border_state)

        cx, cy, cw, ch = self._content_rect()
        if cw <= 0 or ch <= 0:
            return

        rt.PushAxisAlignedClip(float(cx), float(cy),
                               float(cx + cw), float(cy + ch))

        bg_color = LISTBOX_COLORS['disabled']['bg'] if self._state == self.DISABLED else LISTBOX_COLORS['normal']['bg']
        bg_brush = get_brush(rt, *bg_color)
        rt.FillRectangle(float(cx), float(cy),
                         float(cx + cw), float(cy + ch), bg_brush)

        first_visible = max(0, int(self._scroll_y // lh))
        last_visible = min(len(self._items), first_visible + int(ch // lh) + 2)

        for i in range(first_visible, last_visible):
            ix, iy, iw, ih = self._item_rect(i, dw_factory)
            if iy + ih < cy or iy > cy + ch:
                continue

            is_sel = i in self._selected
            is_hover = i == self._hover_index and not is_sel

            if is_sel:
                if self._focused:
                    sel_colors = LISTBOX_COLORS['selected']
                else:
                    sel_colors = LISTBOX_COLORS['selected_no_focus']
                sel_brush = get_brush(rt, *sel_colors['item_bg'])
                rt.FillRectangle(float(ix), float(iy),
                                 float(ix + iw), float(iy + ih), sel_brush)
                text_color = sel_colors['item_text']
            elif is_hover:
                hover_brush = get_brush(rt, *LISTBOX_COLORS['hover']['item_bg'])
                rt.FillRectangle(float(ix), float(iy),
                                 float(ix + iw), float(iy + ih), hover_brush)
                text_color = LISTBOX_COLORS['hover']['item_text']
            else:
                if self._state == self.DISABLED:
                    text_color = LISTBOX_COLORS['disabled']['item_text']
                else:
                    text_color = LISTBOX_COLORS['normal']['item_text']

            text = self._items[i]
            if text and text_fmt:
                text_fmt.SetTextAlignment(pyd2d.TEXT_ALIGNMENT.LEADING)
                text_brush = get_brush(rt, *text_color)
                rt.DrawText(text, text_fmt,
                            float(ix + ITEM_PAD_X), float(iy),
                            float(ix + iw - ITEM_PAD_X), float(iy + ih),
                            text_brush)

        rt.PopAxisAlignedClip()

        if self._v_scrollbar:
            self._v_scrollbar.draw(ctx, client_rect)


class SkinAwareListBox(D2DListBox):
    """皮肤化列表框 — 使用 CtrlBorder 边框 + 皮肤化 ScrollBar。"""

    def __init__(self, rect, skin_context, items=None, selected=None,
                 mode=0, on_change=None, on_double_click=None,
                 subcat='ListBox'):
        super().__init__(rect, items=items, selected=selected, mode=mode,
                         on_change=on_change, on_double_click=on_double_click)
        self._ctx = skin_context
        self._subcat = subcat
        self._dwrite_text_fmt_cached = None

    def _get_text_fmt_cached(self, dw_factory=None):
        if self._dwrite_text_fmt_cached is not None:
            return self._dwrite_text_fmt_cached
        self._dwrite_text_fmt_cached = self._ctx.get_text_format(
            self._subcat, dw_factory=dw_factory,
            alignment=pyd2d.TEXT_ALIGNMENT.LEADING,
            para_alignment=pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return self._dwrite_text_fmt_cached

    def _get_text_color(self, state_idx):
        return self._ctx.get_text_color(self._subcat, state_idx)

    def bind_to_frame(self, frame):
        self._frame = frame
        rx, ry, rw, rh = self._rect
        self._v_scrollbar = SkinAwareScrollBar(
            (rx + rw - SCROLLBAR_WIDTH, ry + 2,
             SCROLLBAR_WIDTH, rh - 4),
            self._ctx,
            scroll_pos=0, scroll_max=0, page_size=1,
            orientation=D2DScrollBar.VERTICAL,
            on_scroll=self._on_v_scroll)
        self._update_scrollbar()

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt
        dw_factory = ctx.dw_factory
        text_fmt = self._get_text_fmt_cached(dw_factory)
        lh = self._line_height(dw_factory)

        border_state = self._border_state()
        draw_ctrl_border(rt, (rx, ry, rw, rh), state=border_state,
                         skin_context=self._ctx)

        cx, cy, cw, ch = self._content_rect()
        if cw <= 0 or ch <= 0:
            return

        rt.PushAxisAlignedClip(float(cx), float(cy),
                               float(cx + cw), float(cy + ch))

        bg_color = LISTBOX_COLORS['disabled']['bg'] if self._state == self.DISABLED else LISTBOX_COLORS['normal']['bg']
        bg_brush = get_brush(rt, *bg_color)
        rt.FillRectangle(float(cx), float(cy),
                         float(cx + cw), float(cy + ch), bg_brush)

        first_visible = max(0, int(self._scroll_y // lh))
        last_visible = min(len(self._items), first_visible + int(ch // lh) + 2)

        for i in range(first_visible, last_visible):
            ix, iy, iw, ih = self._item_rect(i, dw_factory)
            if iy + ih < cy or iy > cy + ch:
                continue

            is_sel = i in self._selected
            is_hover = i == self._hover_index and not is_sel

            if is_sel:
                if self._focused:
                    sel_colors = LISTBOX_COLORS['selected']
                else:
                    sel_colors = LISTBOX_COLORS['selected_no_focus']
                sel_brush = get_brush(rt, *sel_colors['item_bg'])
                rt.FillRectangle(float(ix), float(iy),
                                 float(ix + iw), float(iy + ih), sel_brush)
                text_color = self._get_text_color(2) if self._focused else self._get_text_color(3)
            elif is_hover:
                hover_brush = get_brush(rt, *LISTBOX_COLORS['hover']['item_bg'])
                rt.FillRectangle(float(ix), float(iy),
                                 float(ix + iw), float(iy + ih), hover_brush)
                text_color = self._get_text_color(1)
            else:
                text_color = self._get_text_color(0)

            text = self._items[i]
            if text and text_fmt:
                text_fmt.SetTextAlignment(pyd2d.TEXT_ALIGNMENT.LEADING)
                d2d_draw_text(rt, dw_factory, text, text_fmt, text_color,
                              float(ix + ITEM_PAD_X), float(iy),
                              float(iw - ITEM_PAD_X * 2), float(ih))

        rt.PopAxisAlignedClip()

        if self._v_scrollbar:
            self._v_scrollbar.draw(ctx, client_rect)
