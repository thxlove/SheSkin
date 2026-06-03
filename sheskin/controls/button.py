"""D2D 交互控件 — D2DButton / SkinAwareButton。"""
import pyd2d
from ..layout import CONTROL_SLOTS
from .base_control import SheControl
from ..brush_cache import get_brush
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP, \
    PT_TO_DIP, BUTTON_COLORS, BUTTON_TEXT_PADDING_X, BUTTON_TEXT_PADDING_Y


class D2DButton(SheControl):
    """D2D 自绘按钮 — 无 HWND，纯 D2D 渲染 + 鼠标 hit-test。

    用法：
        btn = D2DButton((10, 10, 120, 36), "Click Me", on_click=lambda: print("clicked"))
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

    def __init__(self, rect, text, on_click=None):
        super().__init__(rect, text)
        self._on_click = on_click
        self._layout_dim = (0, 0)

    def _on_activate(self):
        if self._on_click:
            self._on_click()

    def set_on_click(self, callback):
        self._on_click = callback

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect

        state_names = {
            self.NORMAL: 'normal', self.HOVER: 'hover',
            self.PRESSED: 'pressed', self.DISABLED: 'disabled',
        }
        state_name = state_names[self._state]
        colors = BUTTON_COLORS[state_name]

        rt = ctx.rt
        bg_brush = get_brush(rt, *colors['bg'])
        border_brush = get_brush(rt, *colors['border'])
        text_brush = get_brush(rt, *colors['fg'])

        rt.FillRectangle(
            float(rx), float(ry), float(rx + rw), float(ry + rh), bg_brush)
        rt.DrawRectangle(
            float(rx), float(ry), float(rx + rw), float(ry + rh), border_brush, 1.0)

        if self._text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            rw, rh = self._rect[2], self._rect[3]
            pad_x, pad_y = BUTTON_TEXT_PADDING_X, BUTTON_TEXT_PADDING_Y
            text_w = max(1.0, float(rw) - 2.0 * pad_x)
            text_h = max(1.0, float(rh) - 2.0 * pad_y)
            if self._text_layout is None or self._layout_dim != (rw, rh):
                self._text_layout = ctx.dw_factory.CreateTextLayout(
                    self._text, text_fmt, text_w, text_h)
                self._text_layout.SetTrimming(
                    pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                self._layout_dim = (rw, rh)
            layout = self._text_layout
            metrics = layout.GetMetrics()
            tx = float(rx) + float(pad_x) + max(0.0, (text_w - metrics.width) / 2.0)
            ty = float(ry) + float(pad_y) + max(0.0, (text_h - metrics.height) / 2.0)
            ctx.rt.PushAxisAlignedClip(
                float(rx), float(ry), float(rx + rw), float(ry + rh))
            try:
                rt.DrawTextLayout(tx, ty, layout, text_brush)
            finally:
                ctx.rt.PopAxisAlignedClip()


class SkinAwareButton(D2DButton):
    _STATE_NAMES = {0: 'normal', 1: 'hover', 2: 'pressed', 3: 'disabled'}

    def __init__(self, rect, text, skin_context, subcat_name='PushButton',
                 slots=None, on_click=None):
        if slots is None:
            slots = CONTROL_SLOTS['PushButton']['button']
        super().__init__(rect, text, on_click)
        self._ctx = skin_context
        self._subcat = subcat_name
        self._slots = slots
        self._text_brushes = {}
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
        slot = self._slots[state_name]

        rt = ctx.rt
        block = self._ctx.get_block(slot)
        if block is not None and block.bg_width > 0 and block.bg_height > 0:
            from ..d2d_render import d2d_draw_block
            d2d_draw_block(rt, self._ctx.skin_img, block,
                          (rx, ry, rw, rh),
                          wic_factory=ctx.wic_factory,
                          d2d_cache=self._ctx.cache)
        else:
            self._draw_fallback(ctx, rx, ry, rw, rh)

        if self._text:
            color = self._ctx.get_text_color(
                self._subcat, self._state)
            if len(color) == 3:
                color = (color[0], color[1], color[2], 255)

            text_brush = get_brush(rt,
                color[0] / 255.0, color[1] / 255.0,
                color[2] / 255.0, color[3] / 255.0)

            text_fmt = self._get_text_fmt_cached(dw_factory=ctx.dw_factory)
            pad_x, pad_y = BUTTON_TEXT_PADDING_X, BUTTON_TEXT_PADDING_Y
            text_w = max(1.0, float(rw) - 2.0 * pad_x)
            text_h = max(1.0, float(rh) - 2.0 * pad_y)
            if self._text_layout is None or self._layout_dim != (rw, rh):
                self._text_layout = ctx.dw_factory.CreateTextLayout(
                    self._text, text_fmt, text_w, text_h)
                self._text_layout.SetTrimming(
                    pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                self._layout_dim = (rw, rh)
            layout = self._text_layout
            metrics = layout.GetMetrics()
            tx = float(rx) + float(pad_x) + max(0.0, (text_w - metrics.width) / 2.0)
            ty = float(ry) + float(pad_y) + max(0.0, (text_h - metrics.height) / 2.0)
            if self._state == self.PRESSED:
                ox, oy = self._ctx.get_text_offset(self._subcat)
                tx += float(ox)
                ty += float(oy)
            ctx.rt.PushAxisAlignedClip(
                float(rx), float(ry), float(rx + rw), float(ry + rh))
            try:
                rt.DrawTextLayout(tx, ty, layout, text_brush)
            finally:
                ctx.rt.PopAxisAlignedClip()

    def _draw_fallback(self, ctx, rx, ry, rw, rh):
        super().draw(ctx, (rx, ry, rw, rh))