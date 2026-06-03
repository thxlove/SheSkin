"""D2D 交互控件 — D2DCheckbox / SkinAwareCheckbox。"""
import pyd2d
from ..layout import CONTROL_SLOTS
from .base_control import SheControl
from ..brush_cache import get_brush
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP, \
    PT_TO_DIP, CHECKBOX_BOX_SIZE, CHECKBOX_TEXT_OFFSET, \
    CHECKBOX_BOX_LEFT_PAD, CHECKBOX_CHECK_INSET, CHECKBOX_TEXT_PADDING_RIGHT, \
    CHECKBOX_COLORS


class D2DCheckbox(SheControl):
    """D2D 自绘复选框 — 无 HWND，纯 D2D 渲染 + 鼠标 hit-test。

    用法：
        cb = D2DCheckbox((10, 10, 160, 24), "Enable feature", on_toggle=lambda v: print(v))
        frame.add_client_draw(cb.draw)
        frame.register_d2d_control(cb)
    """

    BOX_SIZE = CHECKBOX_BOX_SIZE
    TEXT_OFFSET = CHECKBOX_TEXT_OFFSET

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

    def __init__(self, rect, text, checked=False, on_toggle=None, is_thirdstate=False):
        super().__init__(rect, text)
        self._checked = bool(checked)
        self._is_thirdstate = bool(is_thirdstate)
        self._on_toggle = on_toggle
        self._layout_params = (None, 0.0, 0.0)

    def _on_activate(self):
        if self._is_thirdstate:
            self._is_thirdstate = False
            self._checked = False
        else:
            self._checked = not self._checked
        if self._on_toggle:
            self._on_toggle(self._checked)

    @property
    def checked(self):
        return self._checked

    def set_checked(self, checked):
        self._checked = bool(checked)
        self._is_thirdstate = False

    @property
    def is_thirdstate(self):
        return self._is_thirdstate

    def set_thirdstate(self, third):
        self._is_thirdstate = bool(third)

    def set_on_toggle(self, callback):
        self._on_toggle = callback

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        box_left = float(rx) + CHECKBOX_BOX_LEFT_PAD
        box_top = float(ry) + (rh - self.BOX_SIZE) / 2.0

        state_names = {
            self.NORMAL: 'normal', self.HOVER: 'hover',
            self.PRESSED: 'pressed', self.DISABLED: 'disabled',
        }
        c = CHECKBOX_COLORS[state_names[self._state]]

        rt = ctx.rt
        box_bg = get_brush(rt, *c['box_bg'])
        box_border = get_brush(rt, *c['box_border'])
        check_color = c['check']
        text_color = c['text']

        box_r = box_left + float(self.BOX_SIZE)
        box_b = box_top + float(self.BOX_SIZE)

        rt.FillRectangle(box_left, box_top, box_r, box_b, box_bg)
        rt.DrawRectangle(box_left, box_top, box_r, box_b, box_border, 1.0)

        if self._checked:
            check_brush = get_brush(rt, *check_color)
            inset = CHECKBOX_CHECK_INSET
            margin = box_left + inset
            mid_y = box_top + float(self.BOX_SIZE) / 2.0
            bot_y = box_b - inset
            right_x = box_r - inset * 0.5

            rt.DrawLine(margin, mid_y, margin + 3.5, bot_y, check_brush, 2.0)
            rt.DrawLine(margin + 3.5, bot_y, right_x, box_top + inset + 1.0, check_brush, 2.0)
        elif self._is_thirdstate:
            third_brush = get_brush(rt, *check_color)
            inset = CHECKBOX_CHECK_INSET
            margin = box_left + inset
            dash_y = box_top + float(self.BOX_SIZE) / 2.0
            dash_r = box_r - inset

            rt.DrawLine(margin, dash_y, dash_r, dash_y, third_brush, 2.0)

        if self._text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            text_x = box_r + self.TEXT_OFFSET
            pad_r = CHECKBOX_TEXT_PADDING_RIGHT
            text_w = max(1.0, float(rx + rw) - text_x - float(pad_r))
            layout_key = (rw, rh)
            if self._text_layout is None or self._layout_params != layout_key:
                self._text_layout = ctx.dw_factory.CreateTextLayout(
                    self._text, text_fmt, text_w, float(rh))
                self._text_layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                self._layout_params = layout_key
            layout = self._text_layout
            metrics = layout.GetMetrics()
            ty = float(ry) + max(0.0, (rh - metrics.height) / 2.0)
            text_brush = get_brush(rt, *text_color)
            ctx.rt.PushAxisAlignedClip(
                float(rx), float(ry), float(rx + rw), float(ry + rh))
            try:
                rt.DrawTextLayout(text_x, ty, layout, text_brush)
            finally:
                ctx.rt.PopAxisAlignedClip()


class SkinAwareCheckbox(D2DCheckbox):
    _STATE_NAMES = {0: 'normal', 1: 'hover', 2: 'pressed', 3: 'disabled'}

    def __init__(self, rect, text, skin_context, subcat_name='CheckBox',
                 slots_unchecked=None, slots_checked=None,
                 slots_third=None, checked=False, on_toggle=None,
                 is_thirdstate=False):
        if slots_unchecked is None:
            slots_unchecked = CONTROL_SLOTS['CheckBox']['unchecked']
        if slots_checked is None:
            slots_checked = CONTROL_SLOTS['CheckBox']['checked']
        if slots_third is None:
            slots_third = CONTROL_SLOTS['CheckBox']['third']
        super().__init__(rect, text, checked, on_toggle, is_thirdstate=is_thirdstate)
        self._ctx = skin_context
        self._subcat = subcat_name
        self._slots_unchecked = slots_unchecked
        self._slots_checked = slots_checked
        self._slots_third = slots_third
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
        state_name = self._STATE_NAMES.get(self._state, 'normal')
        if self._is_thirdstate:
            slots = self._slots_third
        elif self._checked:
            slots = self._slots_checked
        else:
            slots = self._slots_unchecked
        slot = slots[state_name]

        rt = ctx.rt
        block = self._ctx.get_block(slot)
        if block is not None and block.bg_width > 0 and block.bg_height > 0:
            box_w = block.bg_width
            box_h = block.bg_height
            box_left = rx + CHECKBOX_BOX_LEFT_PAD
            box_top = ry + (rh - box_h) // 2

            from ..d2d_render import d2d_draw_block
            d2d_draw_block(rt, self._ctx.skin_img, block,
                          (box_left, box_top, box_w, box_h),
                          wic_factory=ctx.wic_factory,
                          d2d_cache=self._ctx.cache)

            text_x = box_left + box_w + self.TEXT_OFFSET
        else:
            box_w = self.BOX_SIZE
            box_h = self.BOX_SIZE
            box_left = rx + CHECKBOX_BOX_LEFT_PAD
            box_top = ry + (rh - box_h) // 2

            box_bg = get_brush(rt, 0.96, 0.96, 0.98, 1.0)
            box_border = get_brush(rt, 0.55, 0.55, 0.58, 1.0)
            rt.FillRectangle(
                float(box_left), float(box_top),
                float(box_left + box_w), float(box_top + box_h), box_bg)
            rt.DrawRectangle(
                float(box_left), float(box_top),
                float(box_left + box_w), float(box_top + box_h), box_border, 1.0)

            if self._checked:
                check_brush = get_brush(rt, 0.0, 0.47, 0.84, 1.0)
                inset = CHECKBOX_CHECK_INSET
                margin = float(box_left) + inset
                mid_y = float(box_top) + float(box_h) / 2.0
                bot_y = float(box_top + box_h) - inset
                right_x = float(box_left + box_w) - inset * 0.5

                rt.DrawLine(margin, mid_y, margin + 3.5, bot_y, check_brush, 2.0)
                rt.DrawLine(margin + 3.5, bot_y, right_x, float(box_top) + inset + 1.0, check_brush, 2.0)
            elif self._is_thirdstate:
                third_brush = get_brush(rt, 0.0, 0.47, 0.84, 1.0)
                inset = CHECKBOX_CHECK_INSET
                margin = float(box_left) + inset
                dash_y = float(box_top) + float(box_h) / 2.0
                dash_r = float(box_left + box_w) - inset

                rt.DrawLine(margin, dash_y, dash_r, dash_y, third_brush, 2.0)

            text_x = float(box_left + box_w) + self.TEXT_OFFSET

        if self._text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            pad_r = CHECKBOX_TEXT_PADDING_RIGHT
            text_w = max(1.0, float(rx + rw) - text_x - float(pad_r))
            layout_key = (rw, rh)
            if self._text_layout is None or self._layout_params != layout_key:
                self._text_layout = ctx.dw_factory.CreateTextLayout(
                    self._text, text_fmt, text_w, float(rh))
                self._text_layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                self._layout_params = layout_key
            layout = self._text_layout
            metrics = layout.GetMetrics()
            ty = float(ry) + max(0.0, (rh - metrics.height) / 2.0)

            color = self._ctx.get_text_color(self._subcat, self._state)
            if len(color) == 3:
                color = (color[0], color[1], color[2], 255)
            text_brush = get_brush(rt,
                color[0] / 255.0, color[1] / 255.0,
                color[2] / 255.0, color[3] / 255.0)

            ctx.rt.PushAxisAlignedClip(
                float(rx), float(ry), float(rx + rw), float(ry + rh))
            try:
                rt.DrawTextLayout(float(text_x), ty, layout, text_brush)
            finally:
                ctx.rt.PopAxisAlignedClip()