"""D2D 控件 — D2DGroupBox / SkinAwareGroupBox。"""
import pyd2d
from .base_control import SheControl
from .radio import RadioGroup
from ..brush_cache import get_brush
from ..config import (
    DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
    GROUPBOX_TITLE_PAD_X,
    GROUPBOX_BORDER_RADIUS, GROUPBOX_BORDER_WIDTH,
    GROUPBOX_COLORS,
)

GROUPBOX_CHILD_SPACING = 6
GROUPBOX_CHILD_MARGIN = 8


class D2DGroupBox(SheControl):
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

    def __init__(self, rect, text=""):
        super().__init__(rect, text)
        self._children = []
        self._child_spacing = GROUPBOX_CHILD_SPACING
        self._child_margin = GROUPBOX_CHILD_MARGIN
        self._layout_params = (None, 0.0, 0.0)
        self._title_metrics = None
        self._visible_value = True

    @property
    def _visible(self):
        return self._visible_value

    @_visible.setter
    def _visible(self, value):
        self._visible_value = value
        for child in getattr(self, '_children', []):
            child._visible = value

    @property
    def children(self):
        return list(self._children)

    def add(self, child):
        if isinstance(child, RadioGroup):
            for r in child._radios:
                self._children.append(r)
        else:
            self._children.append(child)

    def set_rect(self, rect):
        super().set_rect(rect)
        self.layout_children()

    def remove(self, child):
        self._children.remove(child)

    def clear(self):
        self._children.clear()

    def _title_height(self, ctx=None):
        if not self._text:
            return 0.0
        if self._title_metrics is not None:
            return self._title_metrics.height * 0.5
        return DEFAULT_FONT_SIZE_DIP * 0.5 + 2

    def overhang_top(self):
        if not self._text:
            return 0.0
        if self._title_metrics is not None:
            return self._title_metrics.height * 0.5 + 2.0
        return DEFAULT_FONT_SIZE_DIP * 0.5 + 2.0

    def layout_children(self, ctx=None):
        if not self._children:
            return
        rx, ry, rw, rh = self._rect
        th = self._title_height(ctx)
        client_x = rx + self._child_margin
        client_y = ry + th + self._child_margin
        client_w = max(1.0, rw - 2.0 * self._child_margin)
        client_h = max(1.0, rh - th - self._child_margin)

        y = float(client_y)
        for child in self._children:
            _, _, cw, ch = child.rect
            child.set_rect((int(client_x), int(y), int(client_w), ch))
            y += ch + self._child_spacing

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

        state_names = {self.NORMAL: 'normal', self.DISABLED: 'disabled'}
        c = GROUPBOX_COLORS[state_names.get(self._state, 'normal')]
        border_color = c['border']
        text_color = c['text']
        text_bg_color = c.get('text_bg', (0.92, 0.92, 0.95, 1.0))

        rt = ctx.rt
        border_brush = get_brush(rt, *border_color)

        r = GROUPBOX_BORDER_RADIUS
        rt.DrawRoundedRectangle(
            float(rx) + 0.5, float(ry) + 0.5,
            float(rx + rw) - 0.5, float(ry + rh) - 0.5,
            r, r, border_brush, GROUPBOX_BORDER_WIDTH)

        if self._text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            pad_x = GROUPBOX_TITLE_PAD_X
            text_w = max(1.0, float(rw) - 2.0 * pad_x)
            text_h = float(rh)
            layout_key = (rw, rh)
            if self._text_layout is None or self._layout_params != layout_key:
                self._text_layout = ctx.dw_factory.CreateTextLayout(
                    self._text, text_fmt, text_w, text_h)
                self._text_layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                self._layout_params = layout_key
            layout = self._text_layout
            metrics = layout.GetMetrics()
            self._title_metrics = metrics

            tx = float(rx) + pad_x
            ty = float(ry) - metrics.height * 0.5

            text_bg = get_brush(rt, *text_bg_color)
            bg_pad_x = 6.0
            bg_pad_y = 2.0
            bg_x = tx - bg_pad_x
            bg_y = ty - bg_pad_y
            bg_w = max(metrics.width + 2.0 * bg_pad_x, 1.0)
            bg_h = metrics.height + 2.0 * bg_pad_y
            rt.FillRectangle(
                float(bg_x), float(bg_y),
                float(bg_x + bg_w), float(bg_y + bg_h),
                text_bg)

            text_brush = get_brush(rt, *text_color)
            rt.PushAxisAlignedClip(
                float(rx), float(ry) - metrics.height, float(rx + rw), float(ry + rh))
            try:
                rt.DrawTextLayout(tx, ty, layout, text_brush)
            finally:
                rt.PopAxisAlignedClip()

    def register_children_to_frame(self, frame):
        for child in self._children:
            frame.register_d2d_control(child)


class SkinAwareGroupBox(D2DGroupBox):
    _dwrite_text_fmt_cached = None

    @classmethod
    def _invalidate_text_fmt_cache(cls):
        cls._dwrite_text_fmt_cached = None

    def __init__(self, rect, text, skin_context,
                 border_slots=None, text_bg_slots=None,
                 subcat='GroupBox'):
        super().__init__(rect, text)
        self._ctx = skin_context
        self._subcat = subcat
        from ..layout import CONTROL_SLOTS
        defaults = CONTROL_SLOTS.get(self._subcat, {})
        self._border_slots = border_slots if border_slots is not None else defaults.get('border_bg', {})
        self._text_bg_slots = text_bg_slots if text_bg_slots is not None else defaults.get('text_bg', {})
        self._dwrite_text_fmt_cached = None

    def _get_text_fmt(self, dw_factory=None):
        if self._dwrite_text_fmt_cached is not None:
            return self._dwrite_text_fmt_cached

        if dw_factory is None:
            dw_factory = pyd2d.GetDWriteFactory()

        font_info = self._ctx.get_font_info(self._subcat)
        if font_info:
            face_name = font_info.get('face_name', DEFAULT_FONT_FAMILY)
            height = font_info.get('height', 0)
            from ..config import PT_TO_DIP
            d2d_font_size = abs(height) / PT_TO_DIP if height else DEFAULT_FONT_SIZE_DIP
            weight = pyd2d.FONT_WEIGHT(font_info.get('weight', 400))
            italic = bool(font_info.get('italic', False))
        else:
            face_name = DEFAULT_FONT_FAMILY
            d2d_font_size = DEFAULT_FONT_SIZE_DIP
            weight = pyd2d.FONT_WEIGHT.NORMAL
            italic = False

        font_style = pyd2d.FONT_STYLE.ITALIC if italic else pyd2d.FONT_STYLE.NORMAL
        self._dwrite_text_fmt_cached = dw_factory.CreateTextFormat(
            face_name, d2d_font_size,
            weight=weight, style=font_style,
            stretch=pyd2d.FONT_STRETCH.NORMAL)
        return self._dwrite_text_fmt_cached

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        state_name = {self.NORMAL: 'normal', self.DISABLED: 'disabled'}.get(self._state, 'normal')

        border_slot = self._border_slots.get(state_name)
        text_bg_slot = self._text_bg_slots.get(state_name)

        rt = ctx.rt
        border_block = self._ctx.get_block(border_slot) if border_slot is not None else None
        text_bg_block = self._ctx.get_block(text_bg_slot) if text_bg_slot is not None else None

        has_border = (border_block is not None
                      and border_block.bg_width > 0
                      and border_block.bg_height > 0)

        if not has_border:
            D2DGroupBox.draw(self, ctx, client_rect)
        else:
            from ..d2d_render import d2d_draw_block
            d2d_draw_block(rt, self._ctx.skin_img, border_block,
                           (rx, ry, rw, rh),
                           wic_factory=ctx.wic_factory,
                           d2d_cache=self._ctx.cache)

            if self._text:
                text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
                title_pad = GROUPBOX_TITLE_PAD_X
                text_x = float(rx) + title_pad
                text_w = max(1.0, float(rx + rw) - text_x - title_pad)
                text_h = float(rh)

                use_tbg = (text_bg_block is not None
                           and text_bg_block.bg_width > 0
                           and text_bg_block.bg_height > 0)

                layout_key = (rw, rh)
                if self._text_layout is None or self._layout_params != layout_key:
                    self._text_layout = ctx.dw_factory.CreateTextLayout(
                        self._text, text_fmt, text_w, text_h)
                    self._text_layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                    self._layout_params = layout_key
                layout = self._text_layout
                metrics = layout.GetMetrics()
                self._title_metrics = metrics

                text_y = float(ry) - metrics.height * 0.5

                if use_tbg:
                    tbg_x = text_x - (title_pad // 2)
                    tbg_y = float(text_y) - 2.0
                    tbg_w = int(max(text_bg_block.bg_width, metrics.width + title_pad))
                    tbg_h = int(metrics.height + 4.0)
                    d2d_draw_block(rt, self._ctx.skin_img, text_bg_block,
                                   (int(tbg_x), int(tbg_y), tbg_w, tbg_h),
                                   wic_factory=ctx.wic_factory,
                                   d2d_cache=self._ctx.cache)
                else:
                    bg = GROUPBOX_COLORS[state_name].get('text_bg', (0.92, 0.92, 0.95, 1.0))
                    bg_brush = get_brush(rt, *bg)
                    bg_pad = 6.0
                    rt.FillRectangle(
                        float(text_x - bg_pad), float(text_y) - 2.0,
                        float(text_x + metrics.width + bg_pad), float(text_y) + metrics.height + 2.0,
                        bg_brush)

                text_color = self._ctx.get_text_color(self._subcat, 2 if state_name == 'normal' else 9)
                text_brush = get_brush(rt, *text_color)
                rt.PushAxisAlignedClip(
                    float(rx), float(ry) - metrics.height, float(rx + rw), float(ry + rh))
                try:
                    rt.DrawTextLayout(text_x, text_y, layout, text_brush)
                finally:
                    rt.PopAxisAlignedClip()