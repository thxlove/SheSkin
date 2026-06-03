"""D2D 交互控件 — D2DBitmapButton / SkinAwareBitmapButton。

图形按钮，支持纯图标、图标+文字两种模式。
图标渲染复用 ToolBar 的 _wx_image_to_d2d_bitmap + DrawBitmap 方案。
"""
import wx
import pyd2d
from .base_control import SheControl
from .toolbar import _icon_to_image, _make_grey_image
from ..brush_cache import get_brush
from ..d2d_render import _wx_image_to_d2d_bitmap
from ..layout import CONTROL_SLOTS
from ..config import (
    DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP, PT_TO_DIP,
    BUTTON_COLORS, BUTTON_TEXT_PADDING_X, BUTTON_TEXT_PADDING_Y,
)

# 布局模式
ICON_ONLY = 0
ICON_ABOVE_TEXT = 1
ICON_LEFT_TEXT = 2

BITMAPBTN_ICON_SIZE = 16
BITMAPBTN_ICON_TEXT_GAP = 4
BITMAPBTN_ICON_PAD = 4

# 图标按钮颜色（比普通按钮更淡，适合工具面板）
BITMAPBTN_COLORS = {
    'normal': {
        'bg': (0.94, 0.94, 0.96, 1.0),
        'fg': (0.15, 0.15, 0.18, 1.0),
        'border': (0.72, 0.72, 0.76, 1.0),
    },
    'hover': {
        'bg': (0.85, 0.88, 0.95, 1.0),
        'fg': (0.10, 0.10, 0.14, 1.0),
        'border': (0.60, 0.65, 0.78, 1.0),
    },
    'pressed': {
        'bg': (0.78, 0.80, 0.88, 1.0),
        'fg': (0.08, 0.08, 0.12, 1.0),
        'border': (0.55, 0.58, 0.70, 1.0),
    },
    'disabled': {
        'bg': (0.93, 0.93, 0.94, 1.0),
        'fg': (0.55, 0.55, 0.58, 1.0),
        'border': (0.82, 0.82, 0.84, 1.0),
    },
}


class D2DBitmapButton(SheControl):
    """D2D 自绘图形按钮 — 支持图标 + 可选文字。

    用法：
        btn = D2DBitmapButton((10, 10, 80, 36), icon=wx.Bitmap(img), text="Open",
                               on_click=lambda: print("clicked"))
        frame.add_client_draw(btn.draw)
        frame.register_d2d_control(btn)
    """
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
        return cls._dwrite_text_fmt

    def __init__(self, rect, icon=None, text='', layout_mode=ICON_LEFT_TEXT,
                 on_click=None):
        super().__init__(rect, text)
        self._icon_img = _icon_to_image(icon)
        self._layout_mode = layout_mode
        self._on_click = on_click
        self._icon_cache = {}
        self._grey_icon_cache = {}
        self._text_layout = None
        self._layout_dim = (0, 0)

    def _on_activate(self):
        if self._on_click:
            self._on_click()

    def set_on_click(self, callback):
        self._on_click = callback

    def set_icon(self, icon):
        self._icon_img = _icon_to_image(icon)
        self._icon_cache.clear()
        self._grey_icon_cache.clear()

    def set_layout_mode(self, mode):
        self._layout_mode = mode

    def _get_d2d_icon(self, rt, wic_factory, grey=False):
        if self._icon_img is None:
            return None
        cache = self._grey_icon_cache if grey else self._icon_cache
        key = id(self._icon_img)
        if key in cache:
            return cache[key]
        src = _make_grey_image(self._icon_img) if grey else self._icon_img
        d2d_bmp = _wx_image_to_d2d_bitmap(rt, src, wic_factory)
        cache[key] = d2d_bmp
        return d2d_bmp

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect

        state_names = {
            self.NORMAL: 'normal', self.HOVER: 'hover',
            self.PRESSED: 'pressed', self.DISABLED: 'disabled',
        }
        state_name = state_names[self._state]
        colors = BITMAPBTN_COLORS[state_name]

        rt = ctx.rt
        bg_brush = get_brush(rt, *colors['bg'])
        border_brush = get_brush(rt, *colors['border'])
        text_brush = get_brush(rt, *colors['fg'])

        rt.FillRectangle(
            float(rx), float(ry), float(rx + rw), float(ry + rh), bg_brush)
        rt.DrawRectangle(
            float(rx) + 0.5, float(ry) + 0.5,
            float(rx + rw) - 0.5, float(ry + rh) - 0.5,
            border_brush, 1.0)

        is_disabled = self._state == self.DISABLED
        self._draw_content(ctx, rx, ry, rw, rh, text_brush, is_disabled)

    def _draw_content(self, ctx, rx, ry, rw, rh, text_brush, is_disabled):
        rt = ctx.rt
        has_icon = self._icon_img is not None
        has_text = bool(self._text)

        if not has_icon and not has_text:
            return

        icon_size = BITMAPBTN_ICON_SIZE
        pad = BITMAPBTN_ICON_PAD
        gap = BITMAPBTN_ICON_TEXT_GAP

        if self._layout_mode == ICON_ONLY:
            self._draw_icon_centered(rt, ctx.wic_factory, rx, ry, rw, rh,
                                      icon_size, is_disabled)
        elif self._layout_mode == ICON_ABOVE_TEXT:
            self._draw_icon_above_text(ctx, rx, ry, rw, rh, icon_size, pad,
                                        gap, text_brush, has_icon, has_text,
                                        is_disabled)
        else:  # ICON_LEFT_TEXT
            self._draw_icon_left_text(ctx, rx, ry, rw, rh, icon_size, pad,
                                       gap, text_brush, has_icon, has_text,
                                       is_disabled)

    def _draw_icon_centered(self, rt, wic_factory, rx, ry, rw, rh,
                             icon_size, is_disabled):
        d2d_bmp = self._get_d2d_icon(rt, wic_factory, grey=is_disabled)
        if d2d_bmp is None:
            return
        img_w = self._icon_img.GetWidth()
        img_h = self._icon_img.GetHeight()
        ix = float(rx) + (float(rw) - icon_size) / 2.0
        iy = float(ry) + (float(rh) - icon_size) / 2.0
        rt.DrawBitmap(d2d_bmp,
                      ix, iy, ix + icon_size, iy + icon_size,
                      srcRect=(0.0, 0.0, float(img_w), float(img_h)))

    def _draw_icon_left_text(self, ctx, rx, ry, rw, rh, icon_size, pad, gap,
                              text_brush, has_icon, has_text, is_disabled):
        rt = ctx.rt
        content_w = 0.0
        icon_w = 0.0
        text_w = 0.0

        if has_icon:
            icon_w = float(icon_size)
            content_w += icon_w
        if has_icon and has_text:
            content_w += gap
        if has_text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            avail_w = max(1.0, float(rw) - 2.0 * pad - (icon_w + gap if has_icon else 0))
            measure = ctx.dw_factory.CreateTextLayout(
                self._text, text_fmt, avail_w, float(rh))
            text_w = measure.GetMetrics().width
            content_w += text_w

        cx = float(rx) + (float(rw) - content_w) / 2.0

        if has_icon:
            d2d_bmp = self._get_d2d_icon(rt, ctx.wic_factory, grey=is_disabled)
            if d2d_bmp is not None:
                img_w = self._icon_img.GetWidth()
                img_h = self._icon_img.GetHeight()
                iy = float(ry) + (float(rh) - icon_size) / 2.0
                rt.DrawBitmap(d2d_bmp,
                              cx, iy, cx + icon_size, iy + icon_size,
                              srcRect=(0.0, 0.0, float(img_w), float(img_h)))
            cx += icon_w
            if has_text:
                cx += gap

        if has_text:
            self._draw_text_layout(ctx, rx, ry, rw, rh, cx, text_brush, text_w)

    def _draw_icon_above_text(self, ctx, rx, ry, rw, rh, icon_size, pad, gap,
                               text_brush, has_icon, has_text, is_disabled):
        rt = ctx.rt
        content_h = 0.0

        if has_icon:
            content_h += icon_size
        if has_icon and has_text:
            content_h += gap
        if has_text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            avail_w = max(1.0, float(rw) - 2.0 * pad)
            avail_h = max(1.0, float(rh) - icon_size - gap - 2.0 * pad)
            measure = ctx.dw_factory.CreateTextLayout(
                self._text, text_fmt, avail_w, avail_h)
            text_h = measure.GetMetrics().height
            content_h += text_h

        cy = float(ry) + (float(rh) - content_h) / 2.0

        if has_icon:
            d2d_bmp = self._get_d2d_icon(rt, ctx.wic_factory, grey=is_disabled)
            if d2d_bmp is not None:
                img_w = self._icon_img.GetWidth()
                img_h = self._icon_img.GetHeight()
                ix = float(rx) + (float(rw) - icon_size) / 2.0
                rt.DrawBitmap(d2d_bmp,
                              ix, cy, ix + icon_size, cy + icon_size,
                              srcRect=(0.0, 0.0, float(img_w), float(img_h)))
            cy += icon_size
            if has_text:
                cy += gap

        if has_text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            avail_w = max(1.0, float(rw) - 2.0 * pad)
            avail_h = max(1.0, float(rh) - cy + float(ry) - pad)
            layout = ctx.dw_factory.CreateTextLayout(
                self._text, text_fmt, avail_w, max(1.0, avail_h))
            layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
            metrics = layout.GetMetrics()
            tx = float(rx) + (float(rw) - metrics.width) / 2.0
            rt.DrawTextLayout(tx, cy, layout, text_brush)

    def _draw_text_layout(self, ctx, rx, ry, rw, rh, tx, text_brush, text_w):
        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
        pad_y = BUTTON_TEXT_PADDING_Y
        text_h = max(1.0, float(rh) - 2.0 * pad_y)
        layout = ctx.dw_factory.CreateTextLayout(
            self._text, text_fmt, max(1.0, text_w), text_h)
        layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
        metrics = layout.GetMetrics()
        ty = float(ry) + pad_y + max(0.0, (text_h - metrics.height) / 2.0)
        ctx.rt.PushAxisAlignedClip(
            float(rx), float(ry), float(rx + rw), float(ry + rh))
        try:
            ctx.rt.DrawTextLayout(float(tx), float(ty), layout, text_brush)
        finally:
            ctx.rt.PopAxisAlignedClip()


class SkinAwareBitmapButton(D2DBitmapButton):
    """皮肤化图形按钮 — 有皮肤时用皮肤渲染，无皮肤时 fallback 到 D2DBitmapButton。"""

    _STATE_NAMES = {0: 'normal', 1: 'hover', 2: 'pressed', 3: 'disabled'}

    def __init__(self, rect, skin_context, icon=None, text='',
                 layout_mode=ICON_LEFT_TEXT, subcat_name='PushButton',
                 slots=None, on_click=None):
        if slots is None:
            slots = CONTROL_SLOTS.get('PushButton', {}).get('button', {})
        super().__init__(rect, icon=icon, text=text, layout_mode=layout_mode,
                         on_click=on_click)
        self._ctx = skin_context
        self._subcat = subcat_name
        self._slots = slots
        self._dwrite_text_fmt_cached = None

    def _get_text_fmt_cached(self, dw_factory=None):
        if self._dwrite_text_fmt_cached is not None:
            return self._dwrite_text_fmt_cached

        font_info = self._ctx.get_font_info(self._subcat)
        if font_info:
            font_name = font_info.get('face_name', DEFAULT_FONT_FAMILY)
            font_size = float(abs(font_info.get('height', 9))) * PT_TO_DIP
            font_weight = font_info.get('weight', pyd2d.FONT_WEIGHT.NORMAL)
            font_style = pyd2d.FONT_STYLE.ITALIC if font_info.get('italic') else pyd2d.FONT_STYLE.NORMAL
        else:
            font_name = DEFAULT_FONT_FAMILY
            font_size = DEFAULT_FONT_SIZE_DIP
            font_weight = pyd2d.FONT_WEIGHT.NORMAL
            font_style = pyd2d.FONT_STYLE.NORMAL

        if dw_factory is None:
            dw_factory = pyd2d.GetDWriteFactory()
        self._dwrite_text_fmt_cached = dw_factory.CreateTextFormat(
            font_name, font_size, weight=font_weight, style=font_style,
            stretch=pyd2d.FONT_STRETCH.NORMAL)
        return self._dwrite_text_fmt_cached

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        state_name = self._STATE_NAMES.get(self._state, 'normal')
        slot = self._slots.get(state_name)

        rt = ctx.rt

        # 尝试皮肤渲染
        if slot is not None:
            block = self._ctx.get_block(slot)
            if block is not None and block.bg_width > 0 and block.bg_height > 0:
                from ..d2d_render import d2d_draw_block
                d2d_draw_block(rt, self._ctx.skin_img, block,
                              (rx, ry, rw, rh),
                              wic_factory=ctx.wic_factory,
                              d2d_cache=self._ctx.cache)

                # 皮肤按钮上绘制图标和文字
                is_disabled = self._state == self.DISABLED
                color = self._ctx.get_text_color(self._subcat, self._state)
                if len(color) == 3:
                    color = (color[0], color[1], color[2], 255)
                text_brush = get_brush(rt,
                    color[0] / 255.0, color[1] / 255.0,
                    color[2] / 255.0, color[3] / 255.0)
                self._draw_content(ctx, rx, ry, rw, rh, text_brush, is_disabled)
                return

        # 无皮肤 fallback
        self._draw_fallback(ctx, rx, ry, rw, rh)

    def _draw_fallback(self, ctx, rx, ry, rw, rh):
        D2DBitmapButton.draw(self, ctx, (rx, ry, rw, rh))
