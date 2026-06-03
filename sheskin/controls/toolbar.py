import wx
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush
from ..d2d_render import _wx_image_to_d2d_bitmap
from ..config import (
    DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
)

TOOLBAR_HEIGHT = 30
TOOLBAR_BTN_PAD_X = 6
TOOLBAR_BTN_PAD_Y = 2
TOOLBAR_SEP_WIDTH = 2
TOOLBAR_SEP_HEIGHT = 20
TOOLBAR_BTN_MIN_WIDTH = 28
TOOLBAR_ICON_SIZE = 16
TOOLBAR_ICON_TEXT_GAP = 3

TOOLBAR_COLORS = {
    'normal': {
        'bg': (0.92, 0.92, 0.94, 1.0),
        'btn_bg': (0.92, 0.92, 0.94, 1.0),
        'btn_border': None,
        'btn_text': (0.15, 0.15, 0.18, 1.0),
        'hover_bg': (0.85, 0.88, 0.95, 1.0),
        'hover_border': (0.60, 0.65, 0.78, 1.0),
        'pressed_bg': (0.78, 0.80, 0.88, 1.0),
        'pressed_border': (0.55, 0.58, 0.70, 1.0),
        'sep': (0.65, 0.65, 0.68, 1.0),
    },
    'disabled': {
        'bg': (0.93, 0.93, 0.94, 1.0),
        'btn_bg': (0.93, 0.93, 0.94, 1.0),
        'btn_border': None,
        'btn_text': (0.55, 0.55, 0.58, 1.0),
        'sep': (0.78, 0.78, 0.80, 1.0),
    },
}


def _icon_to_image(icon):
    if icon is None:
        return None
    if isinstance(icon, wx.Image):
        return icon
    if isinstance(icon, wx.Bitmap):
        return icon.ConvertToImage()
    return None


def _make_grey_image(img):
    if img is None:
        return None
    w, h = img.GetWidth(), img.GetHeight()
    if w <= 0 or h <= 0:
        return img
    grey = wx.Image(w, h)
    data = img.GetData()
    alpha = img.GetAlpha() if img.HasAlpha() else bytearray([255] * w * h)
    out = bytearray(len(data))
    for i in range(w * h):
        r, g, b = data[i * 3], data[i * 3 + 1], data[i * 3 + 2]
        a = alpha[i]
        lum = int(0.299 * r + 0.587 * g + 0.114 * b)
        lum = int(lum * 0.6 + 128 * 0.4)
        out[i * 3] = lum
        out[i * 3 + 1] = lum
        out[i * 3 + 2] = lum
    grey.SetData(bytes(out))
    grey.SetAlpha(bytes(alpha))
    return grey


class D2DToolBar(SheControl):
    HORIZONTAL = 0
    VERTICAL = 1

    _dwrite_text_fmt = None

    @classmethod
    def _get_text_fmt(cls, dw_factory=None):
        if cls._dwrite_text_fmt is None:
            if dw_factory is None:
                dw_factory = pyd2d.GetDWriteFactory()
            cls._dwrite_text_fmt = dw_factory.CreateTextFormat(
                DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
                weight=pyd2d.FONT_WEIGHT.NORMAL,
                style=pyd2d.FONT_STYLE.NORMAL,
                stretch=pyd2d.FONT_STRETCH.NORMAL)
            cls._dwrite_text_fmt.SetParagraphAlignment(
                pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return cls._dwrite_text_fmt

    def __init__(self, rect, orientation=0, on_click=None):
        super().__init__(rect, "")
        self._orientation = orientation
        self._on_click = on_click
        self._items = []
        self._item_layouts = []
        self._hovered = -1
        self._pressed = -1
        self._captured = False
        self._layout_dirty = True
        self._icon_cache = {}
        self._grey_icon_cache = {}

    @property
    def items(self):
        return self._items

    def set_rect(self, rect):
        old = self._rect
        super().set_rect(rect)
        if old != rect:
            self._layout_dirty = True

    def add_button(self, text='', icon=None, disabled=False, data=None):
        icon_img = _icon_to_image(icon)
        self._items.append({
            'type': 'button', 'text': text,
            'icon': icon_img, 'disabled': disabled, 'data': data,
        })
        self._layout_dirty = True
        return len(self._items) - 1

    def add_separator(self):
        self._items.append({'type': 'separator'})
        self._layout_dirty = True
        return len(self._items) - 1

    def set_button_disabled(self, index, disabled=True):
        if 0 <= index < len(self._items) and self._items[index]['type'] == 'button':
            if self._items[index]['disabled'] != disabled:
                self._items[index]['disabled'] = disabled
                self._layout_dirty = True
                return True
        return False

    def _is_horizontal(self):
        return self._orientation == self.HORIZONTAL

    def _ensure_layout(self, dw_factory=None):
        if not self._layout_dirty and self._item_layouts:
            return
        rx, ry, rw, rh = self._rect
        text_fmt = self._get_text_fmt(dw_factory=dw_factory)
        layouts = []

        if self._is_horizontal():
            cur_x = float(rx)
            for item in self._items:
                if item['type'] == 'separator':
                    layouts.append((cur_x, float(ry), float(TOOLBAR_SEP_WIDTH), float(rh), 'separator'))
                    cur_x += TOOLBAR_SEP_WIDTH
                else:
                    tw = 0.0
                    has_icon = item.get('icon') is not None
                    has_text = bool(item.get('text'))

                    if has_icon:
                        tw += TOOLBAR_ICON_SIZE
                    if has_icon and has_text:
                        tw += TOOLBAR_ICON_TEXT_GAP
                    if has_text:
                        if dw_factory:
                            measure = dw_factory.CreateTextLayout(
                                item['text'], text_fmt, float(rw), float(rh))
                            tw += measure.GetMetrics().width
                        else:
                            tw += len(item['text']) * 8.0

                    tw = max(tw + 2 * TOOLBAR_BTN_PAD_X, float(TOOLBAR_BTN_MIN_WIDTH))
                    layouts.append((cur_x, float(ry), tw, float(rh), 'button'))
                    cur_x += tw
        else:
            cur_y = float(ry)
            for item in self._items:
                if item['type'] == 'separator':
                    layouts.append((float(rx), cur_y, float(rw), float(TOOLBAR_SEP_WIDTH), 'separator'))
                    cur_y += TOOLBAR_SEP_WIDTH
                else:
                    th = 0.0
                    has_icon = item.get('icon') is not None
                    has_text = bool(item.get('text'))

                    if has_icon:
                        th += TOOLBAR_ICON_SIZE
                    if has_icon and has_text:
                        th += TOOLBAR_ICON_TEXT_GAP
                    if has_text:
                        if dw_factory:
                            measure = dw_factory.CreateTextLayout(
                                item['text'], text_fmt, float(rw), float(rh))
                            th += measure.GetMetrics().height
                        else:
                            th += 14.0

                    th = max(th + 2 * TOOLBAR_BTN_PAD_Y, float(TOOLBAR_BTN_MIN_WIDTH))
                    layouts.append((float(rx), cur_y, float(rw), th, 'button'))
                    cur_y += th

        self._item_layouts = layouts
        self._layout_dirty = False

    def _hit_test(self, pt):
        px, py = pt
        for i, (x, y, w, h, kind) in enumerate(self._item_layouts):
            if kind == 'button' and x <= px <= x + w and y <= py <= y + h:
                return i
        return -1

    def on_mouse_down(self, pt):
        idx = self._hit_test(pt)
        if idx < 0:
            return False
        item = self._items[idx]
        if item['type'] != 'button' or item.get('disabled'):
            return False
        self._captured = True
        self._pressed = idx
        return True

    def on_mouse_up(self, pt):
        if not self._captured:
            return False
        idx = self._hit_test(pt)
        was_pressed = self._pressed >= 0
        if was_pressed and idx == self._pressed:
            item = self._items[idx]
            if self._on_click and not item.get('disabled'):
                self._on_click(idx, item.get('data'))
        self._captured = False
        self._pressed = -1
        self._hovered = idx
        return True

    def on_mouse_move(self, pt):
        idx = self._hit_test(pt)
        if self._captured:
            return False
        changed = idx != self._hovered
        self._hovered = idx
        return changed

    def on_mouse_leave(self):
        changed = self._hovered >= 0 or self._pressed >= 0
        self._hovered = -1
        self._pressed = -1
        self._captured = False
        return changed

    def _on_activate(self):
        pass

    def _get_btn_state(self, index):
        item = self._items[index]
        if item.get('disabled'):
            return 'disabled'
        if self._captured and index == self._pressed:
            return 'pressed'
        if index == self._pressed:
            return 'pressed'
        if index == self._hovered:
            return 'hover'
        return 'normal'

    def _get_d2d_icon(self, rt, icon_img, wic_factory, grey=False):
        if icon_img is None:
            return None
        cache = self._grey_icon_cache if grey else self._icon_cache
        key = id(icon_img)
        if key in cache:
            return cache[key]
        src = _make_grey_image(icon_img) if grey else icon_img
        d2d_bmp = _wx_image_to_d2d_bitmap(rt, src, wic_factory)
        cache[key] = d2d_bmp
        return d2d_bmp

    def _draw_icon_and_text(self, rt, dw_factory, wic_factory, item, x, y, w, h,
                             text_fmt, text_color_tuple, is_disabled=False):
        has_icon = item.get('icon') is not None
        has_text = bool(item.get('text'))
        icon_img = item.get('icon')

        if self._is_horizontal():
            content_w = 0.0
            icon_w = 0.0
            text_w = 0.0
            if has_icon:
                icon_w = float(TOOLBAR_ICON_SIZE)
                content_w += icon_w
            if has_icon and has_text:
                content_w += TOOLBAR_ICON_TEXT_GAP
            if has_text:
                if dw_factory:
                    measure = dw_factory.CreateTextLayout(
                        item['text'], text_fmt, float(w), float(h))
                    text_w = measure.GetMetrics().width
                else:
                    text_w = len(item['text']) * 8.0
                content_w += text_w

            cx = x + (w - content_w) / 2.0
            if has_icon:
                d2d_bmp = self._get_d2d_icon(rt, icon_img, wic_factory, grey=is_disabled)
                if d2d_bmp is not None:
                    img_w = icon_img.GetWidth()
                    img_h = icon_img.GetHeight()
                    iy = y + (h - TOOLBAR_ICON_SIZE) / 2.0
                    rt.DrawBitmap(d2d_bmp,
                                  float(cx), float(iy),
                                  float(cx + TOOLBAR_ICON_SIZE),
                                  float(iy + TOOLBAR_ICON_SIZE),
                                  srcRect=(0.0, 0.0, float(img_w), float(img_h)))
                cx += icon_w
                if has_text:
                    cx += TOOLBAR_ICON_TEXT_GAP

            if has_text:
                text_brush = get_brush(rt, *text_color_tuple)
                avail_h = max(1.0, h - 2 * TOOLBAR_BTN_PAD_Y)
                layout = dw_factory.CreateTextLayout(
                    item['text'], text_fmt, max(1.0, text_w), avail_h)
                layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                metrics = layout.GetMetrics()
                ty = y + (h - metrics.height) / 2.0
                rt.DrawTextLayout(float(cx), float(ty), layout, text_brush)
        else:
            content_h = 0.0
            if has_icon:
                content_h += TOOLBAR_ICON_SIZE
            if has_icon and has_text:
                content_h += TOOLBAR_ICON_TEXT_GAP
            if has_text:
                if dw_factory:
                    measure = dw_factory.CreateTextLayout(
                        item['text'], text_fmt, float(w), float(h))
                    content_h += measure.GetMetrics().height
                else:
                    content_h += 14.0

            cy = y + (h - content_h) / 2.0
            if has_icon:
                d2d_bmp = self._get_d2d_icon(rt, icon_img, wic_factory, grey=is_disabled)
                if d2d_bmp is not None:
                    img_w = icon_img.GetWidth()
                    img_h = icon_img.GetHeight()
                    ix = x + (w - TOOLBAR_ICON_SIZE) / 2.0
                    rt.DrawBitmap(d2d_bmp,
                                  float(ix), float(cy),
                                  float(ix + TOOLBAR_ICON_SIZE),
                                  float(cy + TOOLBAR_ICON_SIZE),
                                  srcRect=(0.0, 0.0, float(img_w), float(img_h)))
                cy += TOOLBAR_ICON_SIZE
                if has_text:
                    cy += TOOLBAR_ICON_TEXT_GAP

            if has_text:
                text_brush = get_brush(rt, *text_color_tuple)
                avail_w = max(1.0, w - 2 * TOOLBAR_BTN_PAD_X)
                avail_h = max(1.0, h - 2 * TOOLBAR_BTN_PAD_Y)
                layout = dw_factory.CreateTextLayout(
                    item['text'], text_fmt, avail_w, avail_h)
                layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                metrics = layout.GetMetrics()
                tx = x + (w - metrics.width) / 2.0
                rt.DrawTextLayout(float(tx), float(cy), layout, text_brush)

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt

        self._ensure_layout(ctx.dw_factory)

        c = TOOLBAR_COLORS.get('disabled' if self._state == self.DISABLED else 'normal',
                                TOOLBAR_COLORS['normal'])
        bg_brush = get_brush(rt, *c['bg'])
        rt.FillRectangle(float(rx), float(ry), float(rx + rw), float(ry + rh), bg_brush)

        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
        sep_brush = get_brush(rt, *c['sep'])

        for i, (x, y, w, h, kind) in enumerate(self._item_layouts):
            if kind == 'separator':
                if self._is_horizontal():
                    sx = x + (TOOLBAR_SEP_WIDTH - 1.0) / 2.0
                    rt.FillRectangle(sx, y + (h - TOOLBAR_SEP_HEIGHT) / 2.0,
                                     sx + 1.0, y + (h + TOOLBAR_SEP_HEIGHT) / 2.0,
                                     sep_brush)
                else:
                    sy = y + (TOOLBAR_SEP_WIDTH - 1.0) / 2.0
                    rt.FillRectangle(x + (w - TOOLBAR_SEP_HEIGHT) / 2.0, sy,
                                     x + (w + TOOLBAR_SEP_HEIGHT) / 2.0, sy + 1.0,
                                     sep_brush)
                continue

            state = self._get_btn_state(i)
            if state == 'hover':
                btn_bg = get_brush(rt, *c['hover_bg'])
                btn_border = get_brush(rt, *c['hover_border'])
                rt.FillRectangle(x, y, x + w, y + h, btn_bg)
                rt.DrawRectangle(x + 0.5, y + 0.5, x + w - 0.5, y + h - 0.5, btn_border, 1.0)
            elif state == 'pressed':
                btn_bg = get_brush(rt, *c['pressed_bg'])
                btn_border = get_brush(rt, *c['pressed_border'])
                rt.FillRectangle(x, y, x + w, y + h, btn_bg)
                rt.DrawRectangle(x + 0.5, y + 0.5, x + w - 0.5, y + h - 0.5, btn_border, 1.0)

            item = self._items[i]
            is_disabled = state == 'disabled'
            text_color = c['btn_text']
            self._draw_icon_and_text(rt, ctx.dw_factory, ctx.wic_factory,
                                     item, x, y, w, h,
                                     text_fmt, text_color, is_disabled)


class SkinAwareToolBar(D2DToolBar):
    _dwrite_text_fmt = None

    @classmethod
    def _get_text_fmt(cls, dw_factory=None, skin_ctx=None):
        if cls._dwrite_text_fmt is None:
            if dw_factory is None:
                dw_factory = pyd2d.GetDWriteFactory()
            if skin_ctx is not None:
                font_info = skin_ctx.get_font_info('ToolBar')
            else:
                font_info = None
            face = font_info.get('face_name', DEFAULT_FONT_FAMILY) if font_info else DEFAULT_FONT_FAMILY
            height = (font_info.get('height', -9) if font_info else -9) * -1.0
            weight = font_info.get('weight', pyd2d.FONT_WEIGHT.NORMAL) if font_info else pyd2d.FONT_WEIGHT.NORMAL
            italic = font_info.get('italic', False) if font_info else False
            cls._dwrite_text_fmt = dw_factory.CreateTextFormat(
                face, float(height),
                weight=weight,
                style=pyd2d.FONT_STYLE.ITALIC if italic else pyd2d.FONT_STYLE.NORMAL,
                stretch=pyd2d.FONT_STRETCH.NORMAL)
            cls._dwrite_text_fmt.SetParagraphAlignment(
                pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return cls._dwrite_text_fmt

    def __init__(self, rect, skin_context, orientation=0, on_click=None,
                 subcat='ToolBar'):
        super().__init__(rect, orientation=orientation, on_click=on_click)
        self._ctx = skin_context
        self._subcat = subcat
        from ..layout import CONTROL_SLOTS
        defaults = CONTROL_SLOTS.get(self._subcat, {})
        self._slots = defaults
        self._h_bg_slot = defaults.get('h_bg', {}).get('normal')
        self._v_bg_slot = defaults.get('v_bg', {}).get('normal')
        self._btn_slots = defaults.get('button', {})
        self._h_sep_slot = defaults.get('h_sep', {}).get('normal')
        self._v_sep_slot = defaults.get('v_sep', {}).get('normal')

    def _get_bg_slot(self):
        return self._h_bg_slot if self._is_horizontal() else self._v_bg_slot

    def _get_sep_slot(self):
        return self._h_sep_slot if self._is_horizontal() else self._v_sep_slot

    def _has_skin_blocks(self):
        bg_slot = self._get_bg_slot()
        bg_block = self._ctx.get_block(bg_slot) if bg_slot is not None else None
        has_bg = (bg_block is not None
                  and bg_block.bg_width > 0
                  and bg_block.bg_height > 0)
        has_btn = False
        for state in ('normal', 'default', 'pressed'):
            btn_slot = self._btn_slots.get(state)
            if btn_slot is not None:
                btn_block = self._ctx.get_block(btn_slot)
                if btn_block is not None and btn_block.bg_width > 0 and btn_block.bg_height > 0:
                    has_btn = True
                    break
        return has_bg and has_btn

    def _get_btn_state_slot(self, state_name):
        if state_name == 'hover':
            state_name = 'default'
        slot = self._btn_slots.get(state_name)
        if slot is not None:
            return slot
        if state_name == 'disabled':
            return self._btn_slots.get('normal')
        return None

    def _get_text_state(self, index):
        item = self._items[index]
        if item.get('disabled'):
            return self.DISABLED
        if self._captured and index == self._pressed:
            return self.PRESSED
        if index == self._pressed:
            return self.PRESSED
        if index == self._hovered:
            return self.HOVER
        return self.NORMAL

    def draw(self, ctx, client_rect):
        if not self._has_skin_blocks():
            D2DToolBar.draw(self, ctx, client_rect)
            return

        rx, ry, rw, rh = self._rect
        self._ensure_layout(ctx.dw_factory)

        rt = ctx.rt
        from ..d2d_render import d2d_draw_block, d2d_draw_text

        bg_slot = self._get_bg_slot()
        bg_block = self._ctx.get_block(bg_slot)
        if bg_block is not None and bg_block.bg_width > 0 and bg_block.bg_height > 0:
            d2d_draw_block(rt, self._ctx.skin_img, bg_block,
                           (int(rx), int(ry), int(rw), int(rh)),
                           wic_factory=ctx.wic_factory,
                           d2d_cache=self._ctx.cache)

        sep_slot = self._get_sep_slot()
        sep_block = self._ctx.get_block(sep_slot) if sep_slot is not None else None

        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory, skin_ctx=self._ctx)

        for i, (x, y, w, h, kind) in enumerate(self._item_layouts):
            if kind == 'separator':
                if sep_block is not None and sep_block.bg_width > 0 and sep_block.bg_height > 0:
                    d2d_draw_block(rt, self._ctx.skin_img, sep_block,
                                   (int(x), int(y), int(w), int(h)),
                                   wic_factory=ctx.wic_factory,
                                   d2d_cache=self._ctx.cache)
                else:
                    c = TOOLBAR_COLORS['normal']
                    sep_brush = get_brush(rt, *c['sep'])
                    if self._is_horizontal():
                        sx = x + (TOOLBAR_SEP_WIDTH - 1.0) / 2.0
                        rt.FillRectangle(sx, y + (h - TOOLBAR_SEP_HEIGHT) / 2.0,
                                         sx + 1.0, y + (h + TOOLBAR_SEP_HEIGHT) / 2.0,
                                         sep_brush)
                    else:
                        sy = y + (TOOLBAR_SEP_WIDTH - 1.0) / 2.0
                        rt.FillRectangle(x + (w - TOOLBAR_SEP_HEIGHT) / 2.0, sy,
                                         x + (w + TOOLBAR_SEP_HEIGHT) / 2.0, sy + 1.0,
                                         sep_brush)
                continue

            state = self._get_btn_state(i)
            slot = self._get_btn_state_slot(state)
            if slot is not None:
                btn_block = self._ctx.get_block(slot)
                if btn_block is not None and btn_block.bg_width > 0 and btn_block.bg_height > 0:
                    d2d_draw_block(rt, self._ctx.skin_img, btn_block,
                                   (int(x), int(y), int(w), int(h)),
                                   wic_factory=ctx.wic_factory,
                                   d2d_cache=self._ctx.cache)

            item = self._items[i]
            has_icon = item.get('icon') is not None
            has_text = bool(item.get('text'))

            if has_icon or has_text:
                is_disabled = state == 'disabled'
                text_state = self._get_text_state(i)
                text_color = self._ctx.get_text_color(self._subcat, text_state)
                self._draw_icon_and_text(rt, ctx.dw_factory, ctx.wic_factory,
                                         item, x, y, w, h,
                                         text_fmt, text_color, is_disabled)
