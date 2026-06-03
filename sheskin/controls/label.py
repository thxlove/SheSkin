"""D2D 交互控件 — D2DLabel / SkinAwareLabel。"""
import pyd2d
from ..layout import CONTROL_SLOTS
from .base_control import SheControl
from ..brush_cache import get_brush
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP, \
    PT_TO_DIP, LABEL_TEXT_PADDING_X, LABEL_TEXT_PADDING_Y, \
    LABEL_COLORS


class D2DLabel(SheControl):

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

    def __init__(self, rect, text):
        super().__init__(rect, text)
        self._layout_params = (None, 0.0, 0.0)

    def on_mouse_down(self, pt):
        return False

    def on_mouse_up(self, pt):
        return False

    def on_mouse_move(self, pt):
        return False

    def on_mouse_leave(self):
        return False

    def _on_activate(self):
        pass

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect

        state_names = {
            self.NORMAL: 'normal', self.DISABLED: 'disabled',
        }
        c = LABEL_COLORS[state_names.get(self._state, 'normal')]
        text_color = c['text']

        if self._text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            pad_x, pad_y = LABEL_TEXT_PADDING_X, LABEL_TEXT_PADDING_Y
            text_w = max(1.0, float(rw) - 2.0 * pad_x)
            text_h = max(1.0, float(rh) - 2.0 * pad_y)
            layout_key = (rw, rh)
            if self._text_layout is None or self._layout_params != layout_key:
                self._text_layout = ctx.dw_factory.CreateTextLayout(
                    self._text, text_fmt, text_w, text_h)
                self._text_layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                self._layout_params = layout_key
            layout = self._text_layout
            metrics = layout.GetMetrics()
            tx = float(rx) + pad_x
            ty = float(ry) + pad_y + max(0.0, (text_h - metrics.height) / 2.0)
            text_brush = get_brush(ctx.rt, *text_color)

            ctx.rt.PushAxisAlignedClip(
                float(rx), float(ry), float(rx + rw), float(ry + rh))
            try:
                ctx.rt.DrawTextLayout(tx, ty, layout, text_brush)
            finally:
                ctx.rt.PopAxisAlignedClip()


class SkinAwareLabel(D2DLabel):

    def __init__(self, rect, text, skin_context, subcat_name='Label'):
        super().__init__(rect, text)
        self._ctx = skin_context
        self._subcat = subcat_name
        self._dwrite_text_fmt_cached = None

    def _get_text_fmt(self, dw_factory=None):
        if self._dwrite_text_fmt_cached is None:
            font_info = self._ctx.get_font_info(self._subcat)
            if font_info is None:
                if dw_factory is None:
                    dw_factory = pyd2d.GetDWriteFactory()
                self._dwrite_text_fmt_cached = dw_factory.CreateTextFormat(
                    DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
                    weight=pyd2d.FONT_WEIGHT.NORMAL,
                    style=pyd2d.FONT_STYLE.NORMAL,
                    stretch=pyd2d.FONT_STRETCH.NORMAL)
                return self._dwrite_text_fmt_cached

            from ..parse_font import _parse_font_dict
            face_name = font_info.get('face_name', DEFAULT_FONT_FAMILY)
            font_h = font_info.get('height', -9)
            d2d_font_size = float(abs(font_h)) * PT_TO_DIP
            weight_val = font_info.get('weight', 400)
            weight = _parse_font_dict.map_weight(weight_val)
            italic = font_info.get('italic', 0)
            font_style = pyd2d.FONT_STYLE.ITALIC if italic else pyd2d.FONT_STYLE.NORMAL

            if dw_factory is None:
                dw_factory = pyd2d.GetDWriteFactory()
            self._dwrite_text_fmt_cached = dw_factory.CreateTextFormat(
                face_name, d2d_font_size,
                weight=weight, style=font_style,
                stretch=pyd2d.FONT_STRETCH.NORMAL)
        return self._dwrite_text_fmt_cached

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect

        state_names = {
            self.NORMAL: 'normal', self.DISABLED: 'disabled',
        }
        state_name = state_names.get(self._state, 'normal')

        if self._text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            pad_x, pad_y = LABEL_TEXT_PADDING_X, LABEL_TEXT_PADDING_Y
            text_w = max(1.0, float(rw) - 2.0 * pad_x)
            text_h = max(1.0, float(rh) - 2.0 * pad_y)
            layout_key = (rw, rh)
            if self._text_layout is None or self._layout_params != layout_key:
                self._text_layout = ctx.dw_factory.CreateTextLayout(
                    self._text, text_fmt, text_w, text_h)
                self._text_layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                self._layout_params = layout_key
            layout = self._text_layout
            metrics = layout.GetMetrics()
            tx = float(rx) + pad_x
            ty = float(ry) + pad_y + max(0.0, (text_h - metrics.height) / 2.0)

            state_idx = 0 if self._state != self.DISABLED else self.DISABLED
            color = self._ctx.get_text_color(self._subcat, state_idx)
            if len(color) == 3:
                color = (color[0], color[1], color[2], 255)
            text_brush = get_brush(ctx.rt,
                color[0] / 255.0, color[1] / 255.0,
                color[2] / 255.0, color[3] / 255.0)

            ctx.rt.PushAxisAlignedClip(
                float(rx), float(ry), float(rx + rw), float(ry + rh))
            try:
                ctx.rt.DrawTextLayout(tx, ty, layout, text_brush)
            finally:
                ctx.rt.PopAxisAlignedClip()