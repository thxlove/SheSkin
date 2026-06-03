"""D2D 控件 — D2DSpinCtrl / SkinAwareSpinCtrl。"""
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush
from ..config import (
    SPINCTRL_BTN_SIZE, SPINCTRL_TEXT_PAD,
    SPINCTRL_COLORS, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
)


class D2DSpinCtrl(SheControl):
    HORIZONTAL = 0
    VERTICAL = 1

    BTN_UP = 0
    BTN_DOWN = 1
    BTN_LEFT = 2
    BTN_RIGHT = 3

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
            cls._dwrite_text_fmt.SetTextAlignment(
                pyd2d.TEXT_ALIGNMENT.CENTER)
            cls._dwrite_text_fmt.SetParagraphAlignment(
                pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return cls._dwrite_text_fmt

    def __init__(self, rect, value=0, min_value=0, max_value=100, step=1,
                 orientation=1, on_change=None):
        super().__init__(rect, "")
        self._value = max(min_value, min(max_value, value))
        self._min = min_value
        self._max = max_value
        self._step = max(1, step)
        self._orientation = orientation
        self._on_change = on_change
        self._btn_increase_state = self.NORMAL
        self._btn_decrease_state = self.NORMAL
        self._captured = False
        self._captured_btn = None

    @property
    def value(self):
        return self._value

    @property
    def min_value(self):
        return self._min

    @property
    def max_value(self):
        return self._max

    @property
    def step(self):
        return self._step

    @property
    def orientation(self):
        return self._orientation

    def set_value(self, value):
        clamped = max(self._min, min(self._max, value))
        changed = clamped != self._value
        self._value = clamped
        self._text_layout = None
        if changed and self._on_change:
            self._on_change(self._value)
        return changed

    def set_range(self, min_value, max_value):
        self._min = min_value
        self._max = max_value
        self._value = max(self._min, min(self._max, self._value))
        self._text_layout = None

    def set_on_change(self, callback):
        self._on_change = callback

    def _get_button_rects(self):
        rx, ry, rw, rh = self._rect
        btn_sz = float(SPINCTRL_BTN_SIZE)
        if self._orientation == self.VERTICAL:
            half_h = float(rh) * 0.5
            btn_x = float(rx) + float(rw) - btn_sz
            return {
                self.BTN_UP: (btn_x, float(ry), btn_sz, half_h),
                self.BTN_DOWN: (btn_x, float(ry) + half_h, btn_sz, half_h),
            }
        else:
            return {
                self.BTN_LEFT: (float(rx), float(ry), btn_sz, float(rh)),
                self.BTN_RIGHT: (float(rx) + float(rw) - btn_sz,
                                 float(ry), btn_sz, float(rh)),
            }

    def _get_text_rect(self):
        rx, ry, rw, rh = self._rect
        rxf, ryf, rwf, rhf = float(rx), float(ry), float(rw), float(rh)
        btn_sz = float(SPINCTRL_BTN_SIZE)
        if self._orientation == self.VERTICAL:
            return (rxf + SPINCTRL_TEXT_PAD, ryf,
                    rwf - btn_sz - SPINCTRL_TEXT_PAD * 2, rhf)
        else:
            return (rxf + btn_sz + SPINCTRL_TEXT_PAD, ryf,
                    rwf - btn_sz * 2 - SPINCTRL_TEXT_PAD * 2, rhf)

    def _hit_button(self, pt):
        btn_rects = self._get_button_rects()
        px, py = float(pt[0]), float(pt[1])
        for btn_id, (bx, by, bw, bh) in btn_rects.items():
            if bx <= px <= bx + bw and by <= py <= by + bh:
                return btn_id
        return None

    def _increase_btn(self):
        if self._orientation == self.VERTICAL:
            return self.BTN_UP
        return self.BTN_RIGHT

    def _decrease_btn(self):
        if self._orientation == self.VERTICAL:
            return self.BTN_DOWN
        return self.BTN_LEFT

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        btn = self._hit_button(pt)
        if btn is None:
            return False
        self._captured = True
        self._captured_btn = btn
        if btn == self._increase_btn():
            self._btn_increase_state = self.PRESSED
            self.set_value(self._value + self._step)
        elif btn == self._decrease_btn():
            self._btn_decrease_state = self.PRESSED
            self.set_value(self._value - self._step)
        return True

    def on_mouse_up(self, pt):
        if self._state == self.DISABLED:
            return False
        if not self._captured:
            return False
        self._captured = False
        self._captured_btn = None
        old_inc = self._btn_increase_state
        old_dec = self._btn_decrease_state
        self._btn_increase_state = self.NORMAL
        self._btn_decrease_state = self.NORMAL
        return old_inc != self.NORMAL or old_dec != self.NORMAL

    def on_mouse_move(self, pt):
        if self._state == self.DISABLED:
            return False
        if not self._captured:
            btn = self._hit_button(pt)
            old_inc = self._btn_increase_state
            old_dec = self._btn_decrease_state
            inc = self._increase_btn()
            dec = self._decrease_btn()
            if btn == inc:
                self._btn_increase_state = self.HOVER
            else:
                self._btn_increase_state = self.NORMAL
            if btn == dec:
                self._btn_decrease_state = self.HOVER
            else:
                self._btn_decrease_state = self.NORMAL
            return (old_inc != self._btn_increase_state
                    or old_dec != self._btn_decrease_state)
        return False

    def on_mouse_leave(self):
        if self._state == self.DISABLED:
            return False
        old_inc = self._btn_increase_state
        old_dec = self._btn_decrease_state
        self._btn_increase_state = self.NORMAL
        self._btn_decrease_state = self.NORMAL
        if self._captured:
            self._captured = False
            self._captured_btn = None
        return old_inc != self.NORMAL or old_dec != self.NORMAL

    def _on_activate(self):
        pass

    def _draw_triangle(self, rt, bx, by, bw, bh, direction, brush):
        hw = bw * 0.3
        hh = bh * 0.35
        cx = bx + bw * 0.5
        cy = by + bh * 0.5
        if direction == 'up':
            x0, y0 = cx - hw, cy + hh * 0.5
            x1, y1 = cx, cy - hh * 0.5
            x2, y2 = cx + hw, cy + hh * 0.5
        elif direction == 'down':
            x0, y0 = cx - hw, cy - hh * 0.5
            x1, y1 = cx, cy + hh * 0.5
            x2, y2 = cx + hw, cy - hh * 0.5
        elif direction == 'left':
            x0, y0 = cx + hw * 0.5, cy - hh
            x1, y1 = cx - hw * 0.5, cy
            x2, y2 = cx + hw * 0.5, cy + hh
        else:
            x0, y0 = cx - hw * 0.5, cy - hh
            x1, y1 = cx + hw * 0.5, cy
            x2, y2 = cx - hw * 0.5, cy + hh
        rt.FillTriangle(x0, y0, x1, y1, x2, y2, brush)

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect

        if self._state == self.DISABLED:
            overall_state = 'disabled'
        else:
            overall_state = 'normal'

        c = SPINCTRL_COLORS[overall_state]
        rt = ctx.rt

        btn_rects = self._get_button_rects()
        inc_btn = self._increase_btn()
        dec_btn = self._decrease_btn()

        for btn_id, (bx, by, bw, bh) in btn_rects.items():
            if btn_id == inc_btn:
                btn_st = self._btn_increase_state
            else:
                btn_st = self._btn_decrease_state

            state_names = {
                self.NORMAL: 'normal', self.HOVER: 'hover',
                self.PRESSED: 'pressed', self.DISABLED: 'disabled',
            }
            colors = SPINCTRL_COLORS[state_names.get(btn_st, 'normal')]

            bg_brush = get_brush(rt, *colors['btn_bg'])
            border_brush = get_brush(rt, *colors['btn_border'])
            fg_brush = get_brush(rt, *colors['btn_fg'])

            rt.FillRectangle(bx, by, bx + bw, by + bh, bg_brush)
            rt.DrawRectangle(bx, by, bx + bw, by + bh, border_brush, 1.0)

            if btn_id in (self.BTN_UP, self.BTN_DOWN):
                direction = 'up' if btn_id == self.BTN_UP else 'down'
            else:
                direction = 'left' if btn_id == self.BTN_LEFT else 'right'
            self._draw_triangle(rt, bx, by, bw, bh, direction, fg_brush)

        tx, ty, tw, th = self._get_text_rect()
        value_str = str(self._value)
        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
        if self._text_layout is None:
            self._text_layout = ctx.dw_factory.CreateTextLayout(
                value_str, text_fmt, tw, th)
            self._text_layout.SetTrimming(
                pyd2d.TRIMMING_GRANULARITY.CHARACTER)
        text_brush = get_brush(rt, *c['text'])
        rt.DrawTextLayout(tx, ty, self._text_layout, text_brush)


class SkinAwareSpinCtrl(D2DSpinCtrl):
    def __init__(self, rect, skin_context, value=0, min_value=0,
                 max_value=100, step=1, orientation=1, on_change=None,
                 subcat='SpinCtrl'):
        super().__init__(rect, value=value, min_value=min_value,
                         max_value=max_value, step=step,
                         orientation=orientation, on_change=on_change)
        self._ctx = skin_context
        self._subcat = subcat
        from ..layout import CONTROL_SLOTS
        defaults = CONTROL_SLOTS.get(self._subcat, {})
        self._slots = {
            'v_top': defaults.get('v_top', {}),
            'v_bottom': defaults.get('v_bottom', {}),
            'h_left': defaults.get('h_left', {}),
            'h_right': defaults.get('h_right', {}),
        }

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect

        btn_rects = self._get_button_rects()
        inc_btn_id = self._increase_btn()
        dec_btn_id = self._decrease_btn()

        slot_map = {
            self.BTN_UP: 'v_top',
            self.BTN_DOWN: 'v_bottom',
            self.BTN_LEFT: 'h_left',
            self.BTN_RIGHT: 'h_right',
        }

        state_names = {
            self.NORMAL: 'normal', self.HOVER: 'default',
            self.PRESSED: 'pressed', self.DISABLED: 'disabled',
        }

        has_all_skin = True
        for btn_id in btn_rects:
            slot_key = slot_map.get(btn_id)
            if slot_key:
                slot_name = 'normal'
                if btn_id == inc_btn_id:
                    slot_name = state_names.get(
                        self._btn_increase_state, 'normal')
                elif btn_id == dec_btn_id:
                    slot_name = state_names.get(
                        self._btn_decrease_state, 'normal')
                slot_num = self._slots.get(slot_key, {}).get(slot_name)
                block = (self._ctx.get_block(slot_num)
                         if slot_num is not None else None)
                if block is None or block.bg_width <= 0 or block.bg_height <= 0:
                    has_all_skin = False
                    break

        if not has_all_skin:
            D2DSpinCtrl.draw(self, ctx, client_rect)
            return

        rt = ctx.rt
        from ..d2d_render import d2d_draw_block

        for btn_id, btn_rect in btn_rects.items():
            slot_key = slot_map.get(btn_id)
            if not slot_key:
                continue
            if btn_id == inc_btn_id:
                slot_name = state_names.get(
                    self._btn_increase_state, 'normal')
            else:
                slot_name = state_names.get(
                    self._btn_decrease_state, 'normal')
            slot_num = self._slots.get(slot_key, {}).get(slot_name)
            if slot_num is not None:
                block = self._ctx.get_block(slot_num)
                if block is not None and block.bg_width > 0:
                    bx, by, bw, bh = btn_rect
                    d2d_draw_block(rt, self._ctx.skin_img, block,
                                   (int(bx), int(by), int(bw), int(bh)),
                                   wic_factory=ctx.wic_factory,
                                   d2d_cache=self._ctx.cache)

        if self._state == self.DISABLED:
            overall_state = 'disabled'
        else:
            overall_state = 'normal'

        c = SPINCTRL_COLORS[overall_state]
        tx, ty, tw, th = self._get_text_rect()
        value_str = str(self._value)
        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
        if self._text_layout is None:
            self._text_layout = ctx.dw_factory.CreateTextLayout(
                value_str, text_fmt, tw, th)
            self._text_layout.SetTrimming(
                pyd2d.TRIMMING_GRANULARITY.CHARACTER)
        text_brush = get_brush(rt, *c['text'])
        rt.DrawTextLayout(tx, ty, self._text_layout, text_brush)