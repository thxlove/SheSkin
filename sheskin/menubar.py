import wx
import pyd2d
from .brush_cache import get_brush
from .layout import CONTROL_SLOTS, DEFAULTS
from .block import is_block_empty
from .d2d_render import (d2d_draw_block, _wx_colour_to_rgba)
from .config import DEFAULT_FONT_FAMILY, PT_TO_DIP, \
    MENUBAR_LEFT_PAD, MENUBAR_ITEM_PAD, MENUBAR_TEXT_X_OFFSET


class SheMenuBar:
    def __init__(self, skin):
        self.skin = skin
        self._items = []
        self._hover_idx = -1
        self._pressed_idx = -1
        self._last_clicked_idx = -1
        self._active_menu_idx = -1  # 当前展开下拉菜单的 menubar 项索引
        self._dropdown = None       # 当前下拉菜单实例
        self._rect = wx.Rect(0, 0, 0, 0)
        self._item_rects = []
        self._font = None
        self._text_color = None
        self._d2d_text_fmt = None
        self._d2d_fmt_key = None
        self._d2d_layouts_key = None
        self._d2d_item_layouts = []
        self._frame = None          # 关联的 SheLayeredFrame

    def set_items(self, items):
        """设置菜单栏项。items 可以是:
        - 纯文本字符串列表（向后兼容）
        - MenuItemData 列表（支持子菜单）
        """
        self._items = list(items)
        self._item_rects = []
        self._d2d_layouts_key = None
        self._d2d_item_layouts = []

    def set_frame(self, frame):
        """关联 SheLayeredFrame，用于弹出下拉菜单。"""
        self._frame = frame

    def get_preferred_height(self):
        return self.skin.get_menu_bar_height()

    def set_rect(self, rect):
        self._rect = wx.Rect(*rect) if isinstance(rect, (list, tuple)) else rect

    def _item_text(self, idx):
        """获取第 idx 项的显示文本。"""
        item = self._items[idx]
        if isinstance(item, str):
            return item
        return getattr(item, 'text', '')

    def _item_submenu(self, idx):
        """获取第 idx 项的子菜单列表，无则返回 None。"""
        item = self._items[idx]
        if isinstance(item, str):
            return None
        submenu = getattr(item, 'submenu', None)
        if submenu and len(submenu) > 0:
            return submenu
        return None

    def _item_has_submenu(self, idx):
        return self._item_submenu(idx) is not None

    def _ensure_font(self):
        if self._font is not None:
            return
        props = self.skin.get_props('MenuBar')
        font_info = props.get('font')
        if font_info and isinstance(font_info, dict):
            font_size = max(6, -font_info.get('height', DEFAULTS['font_height']))
        else:
            font_size = max(6, -DEFAULTS['font_height'])
        self._font = wx.Font(font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_NORMAL)
        tc = props.get('text_color_n')
        self._text_color = tc if tc else wx.Colour(0, 0, 0)

        font_info = props.get('font')
        font_name = DEFAULT_FONT_FAMILY
        if font_info and isinstance(font_info, dict) and font_info.get('name'):
            font_name = font_info['name']
        self._font_name = font_name
        self._font_size = font_size
        self._d2d_fmt_key = None
        self._d2d_text_fmt = None
        self._d2d_layouts_key = None
        self._d2d_item_layouts = []

    def draw_d2d(self, ctx):
        x, y, w, h = self._rect
        if w <= 0 or h <= 0:
            return
        self._ensure_font()

        rt = ctx.rt
        d2d_cache = ctx.d2d_cache
        dw_factory = ctx.dw_factory

        bg_b = self.skin.get_block(CONTROL_SLOTS['MenuBar']['bg']['normal'])
        if not is_block_empty(bg_b):
            d2d_draw_block(rt, self.skin.skin_img, bg_b, (x, y, w, h),
                          d2d_cache=d2d_cache)

        text_color = _wx_colour_to_rgba(self._text_color) if self._text_color else (0, 0, 0, 255)
        d2d_font_size = float(self._font_size) * PT_TO_DIP
        fmt_key = (self._font_name, d2d_font_size)
        if self._d2d_fmt_key != fmt_key:
            self._d2d_text_fmt = dw_factory.CreateTextFormat(
                self._font_name, d2d_font_size,
                pyd2d.FONT_WEIGHT.NORMAL,
                pyd2d.FONT_STYLE.NORMAL,
                pyd2d.FONT_STRETCH.NORMAL)
            self._d2d_text_fmt.SetParagraphAlignment(pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
            self._d2d_fmt_key = fmt_key
            self._d2d_layouts_key = None
            self._d2d_item_layouts = []
        text_fmt = self._d2d_text_fmt

        texts = [self._item_text(i) for i in range(len(self._items))]
        layouts_key = (tuple(texts), w, h)
        if self._d2d_layouts_key != layouts_key:
            self._d2d_item_layouts = []
            for text in texts:
                measure = dw_factory.CreateTextLayout(text, text_fmt, float(w), float(h))
                tw = measure.GetMetrics().width
                item_w = int(tw + MENUBAR_ITEM_PAD)
                render = dw_factory.CreateTextLayout(text, text_fmt, float(tw + 4), float(h))
                self._d2d_item_layouts.append((measure, render, item_w))
            self._d2d_layouts_key = layouts_key

        brush = get_brush(rt,
            text_color[0] / 255.0, text_color[1] / 255.0,
            text_color[2] / 255.0, text_color[3] / 255.0)

        self._item_rects = []
        item_x = x + MENUBAR_LEFT_PAD

        for i in range(len(self._items)):
            measure, render, item_w = self._d2d_item_layouts[i]
            self._item_rects.append((item_x, item_w))
            is_active = (i == self._active_menu_idx)
            is_hover = (i == self._hover_idx)
            is_pressed = (i == self._pressed_idx)
            if is_active or is_hover or is_pressed:
                if is_active or is_pressed:
                    state_name = 'pressed'
                else:
                    state_name = 'hover'
                item_b = self.skin.get_block(CONTROL_SLOTS['MenuBar']['item'][state_name])
                if not is_block_empty(item_b):
                    d2d_draw_block(rt, self.skin.skin_img, item_b,
                                  (item_x, y, item_w, h),
                                  d2d_cache=d2d_cache)
            rt.DrawTextLayout(float(item_x + MENUBAR_TEXT_X_OFFSET), float(y), render, brush)
            item_x += item_w

    def hit_test(self, pos):
        px, py = pos
        x, y, w, h = self._rect
        if not (x <= px <= x + w and y <= py <= y + h):
            return -1
        for i, (ix, iw) in enumerate(self._item_rects):
            if ix <= px <= ix + iw:
                return i
        return -1

    @property
    def last_clicked_idx(self):
        return self._last_clicked_idx

    def _rect_hit_test(self, pt):
        px, py = pt
        x, y, w, h = self._rect
        return x <= px <= x + w and y <= py <= y + h

    def on_mouse_down(self, pt):
        self._pressed_idx = self.hit_test(pt)
        return self._pressed_idx >= 0

    def on_mouse_up(self, pt):
        idx = self.hit_test(pt)
        was_pressed = self._pressed_idx >= 0
        clicked = was_pressed and idx == self._pressed_idx
        self._last_clicked_idx = idx if clicked else -1
        self._pressed_idx = -1
        self._hover_idx = idx

        # 点击 menubar 项时弹出下拉菜单
        if clicked and idx >= 0:
            self._toggle_dropdown(idx)

        return was_pressed or (self._hover_idx != -1)

    def on_mouse_move(self, pt):
        idx = self.hit_test(pt)
        changed = idx != self._hover_idx
        self._hover_idx = idx

        # 如果已有下拉菜单打开，hover 到其他项时切换下拉菜单
        if self._active_menu_idx >= 0 and idx >= 0 and idx != self._active_menu_idx:
            if self._item_has_submenu(idx):
                self._show_dropdown(idx)
            else:
                self._close_dropdown()

        return changed

    def on_mouse_leave(self):
        changed = self._hover_idx != -1 or self._pressed_idx >= 0
        self._hover_idx = -1
        self._pressed_idx = -1
        return changed

    # ---- 下拉菜单 ----

    def _toggle_dropdown(self, idx):
        """点击 menubar 项：切换下拉菜单。"""
        if self._active_menu_idx == idx:
            self._close_dropdown()
        elif self._item_has_submenu(idx):
            self._show_dropdown(idx)
        else:
            self._close_dropdown()

    def _show_dropdown(self, idx):
        """在第 idx 项下方弹出下拉菜单。"""
        self._close_dropdown()
        if not self._item_has_submenu(idx):
            return
        if not self._frame:
            return

        self._active_menu_idx = idx

        # 计算下拉菜单弹出位置：menubar 项的左下角
        if idx < len(self._item_rects):
            item_x, item_w = self._item_rects[idx]
            bar_x, bar_y, bar_w, bar_h = self._rect
            screen_pos = self._frame.ClientToScreen((item_x, bar_y + bar_h))
        else:
            screen_pos = wx.GetMousePosition()
            screen_pos = (screen_pos.x, screen_pos.y)

        submenu = self._item_submenu(idx)
        self._dropdown = self._frame.popup_menu(submenu, screen_pos=screen_pos)

        # 监听下拉菜单关闭，清理状态
        if self._dropdown:
            orig_on_close = self._dropdown._on_close
            def _on_dropdown_close(orig=orig_on_close):
                self._active_menu_idx = -1
                self._dropdown = None
                if self._frame:
                    self._frame._dirty = True
                    self._frame._do_composite()
                if orig:
                    orig()
            self._dropdown._on_close = _on_dropdown_close

    def _close_dropdown(self):
        """关闭当前下拉菜单。"""
        if self._dropdown is not None:
            try:
                self._dropdown.dismiss()
            except Exception:
                pass
            self._dropdown = None
        self._active_menu_idx = -1

    def close_dropdown(self):
        """外部调用关闭下拉菜单。"""
        self._close_dropdown()
