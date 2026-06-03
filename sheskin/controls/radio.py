"""D2D 交互控件 — D2DRadioButton / SkinAwareRadioButton。"""
import math
import pyd2d
from ..layout import CONTROL_SLOTS
from .base_control import SheControl
from ..brush_cache import get_brush
from ..config import \
    DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP, PT_TO_DIP, \
    RADIO_BOX_SIZE, RADIO_TEXT_OFFSET, RADIO_BOX_LEFT_PAD, \
    RADIO_DOT_INSET, RADIO_TEXT_PADDING_RIGHT, RADIO_COLORS


class RadioGroup:
    def __init__(self):
        self._radios = []

    def add(self, radio):
        self._radios.append(radio)
        radio._group = self

    def _select(self, sender):
        for r in self._radios:
            if r is not sender and r._checked:
                r._checked = False
                r._dirty = True

    def get_selected(self):
        for r in self._radios:
            if r._checked:
                return r
        return None


class D2DRadioButton(SheControl):
    BOX_SIZE = RADIO_BOX_SIZE

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

    def __init__(self, rect, text, checked=False, on_toggle=None):
        super().__init__(rect, text)
        self._checked = bool(checked)
        self._on_toggle = on_toggle
        self._group = None
        self._layout_params = (None, 0.0, 0.0)

    @property
    def checked(self):
        return self._checked

    def set_checked(self, c):
        self._checked = bool(c)

    def _on_activate(self):
        if self._group is not None:
            self._group._select(self)
        self._checked = True
        if self._on_toggle:
            self._on_toggle(self._checked)

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect

        box_size = self.BOX_SIZE
        box_left = float(rx) + RADIO_BOX_LEFT_PAD
        box_top = float(ry) + max(0.0, (float(rh) - box_size) / 2.0)
        box_r = box_left + box_size
        box_b = box_top + box_size

        state_names = {
            self.NORMAL: 'normal', self.HOVER: 'hover',
            self.PRESSED: 'pressed', self.DISABLED: 'disabled',
        }
        c = RADIO_COLORS[state_names[self._state]]
        text_color = c['text']
        circle_bg = c['circle_bg']
        circle_border = c['circle_border']

        rt = ctx.rt

        bg_brush = get_brush(rt, *circle_bg)
        border_brush = get_brush(rt, *circle_border)

        cx = box_left + box_size / 2.0
        cy = box_top + box_size / 2.0
        radius = box_size / 2.0

        rt.FillEllipse(cx - radius, cy - radius, radius, radius, bg_brush)
        rt.DrawEllipse(cx - radius, cy - radius, radius, radius, border_brush, 1.5)

        if self._checked:
            dot_color = c['dot']
            dot_brush = get_brush(rt, *dot_color)
            dot_r = box_size / 2.0 - RADIO_DOT_INSET
            rt.FillEllipse(cx - dot_r, cy - dot_r, dot_r, dot_r, dot_brush)

        if self._text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            text_x = float(box_left + box_size) + RADIO_TEXT_OFFSET
            text_w = max(1.0, float(rx + rw) - text_x - RADIO_TEXT_PADDING_RIGHT)
            text_h = float(rh)
            layout_key = (rw, rh)
            if self._text_layout is None or self._layout_params != layout_key:
                self._text_layout = ctx.dw_factory.CreateTextLayout(
                    self._text, text_fmt, text_w, text_h)
                self._text_layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                self._layout_params = layout_key
            layout = self._text_layout
            metrics = layout.GetMetrics()
            ty = float(ry) + max(0.0, (text_h - metrics.height) / 2.0)
            text_brush = get_brush(rt, *text_color)

            rt.PushAxisAlignedClip(
                float(rx), float(ry), float(rx + rw), float(ry + rh))
            try:
                rt.DrawTextLayout(text_x, ty, layout, text_brush)
            finally:
                rt.PopAxisAlignedClip()


class SkinAwareRadioButton(D2DRadioButton):

    def __init__(self, rect, text, skin_context,
                 checked=False, on_toggle=None,
                 subcat_name='RadioButton',
                 slots_unchecked=None, slots_checked=None):
        super().__init__(rect, text, checked=checked, on_toggle=on_toggle)
        self._ctx = skin_context
        self._subcat = subcat_name
        self._dwrite_text_fmt_cached = None
        self._slots_unc = (
            slots_unchecked
            if slots_unchecked is not None
            else CONTROL_SLOTS.get(subcat_name, {}).get('unchecked', {})
        )
        self._slots_chk = (
            slots_checked
            if slots_checked is not None
            else CONTROL_SLOTS.get(subcat_name, {}).get('checked', {})
        )

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

        state_names = ['normal', 'hover', 'pressed', 'disabled']
        state_idx = self._state if self._state < len(state_names) else 0

        slots = self._slots_chk if self._checked else self._slots_unc
        slot = slots.get(state_names[state_idx])

        rt = ctx.rt
        block = self._ctx.get_block(slot) if slot is not None else None

        if block is not None and block.bg_width > 0 and block.bg_height > 0:
            box_w = block.bg_width
            box_h = block.bg_height
            box_left = float(rx) + RADIO_BOX_LEFT_PAD
            box_top = float(ry) + max(0.0, (float(rh) - box_h) / 2.0)

            from ..d2d_render import d2d_draw_block
            d2d_draw_block(rt, self._ctx.skin_img, block,
                          (box_left, box_top, box_w, box_h),
                          wic_factory=ctx.wic_factory,
                          d2d_cache=self._ctx.cache)

            box_size = box_w
        else:
            box_size = self.BOX_SIZE
            box_left = float(rx) + RADIO_BOX_LEFT_PAD
            box_top = float(ry) + max(0.0, (float(rh) - box_size) / 2.0)
            D2DRadioButton.draw(self, ctx, client_rect)
            return

        if self._text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            text_x = float(box_left + box_size) + RADIO_TEXT_OFFSET
            text_w = max(1.0, float(rx + rw) - text_x - RADIO_TEXT_PADDING_RIGHT)
            text_h = float(rh)
            layout_key = (rw, rh)
            if self._text_layout is None or self._layout_params != layout_key:
                self._text_layout = ctx.dw_factory.CreateTextLayout(
                    self._text, text_fmt, text_w, text_h)
                self._text_layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                self._layout_params = layout_key
            layout = self._text_layout
            metrics = layout.GetMetrics()
            ty = float(ry) + max(0.0, (text_h - metrics.height) / 2.0)

            color = self._ctx.get_text_color(self._subcat, state_idx)
            if len(color) == 3:
                color = (color[0], color[1], color[2], 255)
            text_brush = get_brush(ctx.rt,
                color[0] / 255.0, color[1] / 255.0,
                color[2] / 255.0, color[3] / 255.0)

            rt = ctx.rt
            rt.PushAxisAlignedClip(
                float(rx), float(ry), float(rx + rw), float(ry + rh))
            try:
                rt.DrawTextLayout(text_x, ty, layout, text_brush)
            finally:
                rt.PopAxisAlignedClip()