"""D2D 控件 — D2DProgress / SkinAwareProgress。"""
from .base_control import SheControl
from ..brush_cache import get_brush
from ..config import (
    PROGRESS_BORDER_RADIUS, PROGRESS_BORDER_WIDTH,
    PROGRESS_COLORS,
)


class D2DProgress(SheControl):
    HORIZONTAL = 0
    VERTICAL = 1

    def __init__(self, rect, value=0, max_value=100, orientation=0):
        super().__init__(rect, "")
        self._value = max(0, min(max_value, value))
        self._max_value = max_value
        self._orientation = orientation

    @property
    def value(self):
        return self._value

    @property
    def max_value(self):
        return self._max_value

    def set_value(self, value):
        clamped = max(0, min(self._max_value, value))
        changed = clamped != self._value
        self._value = clamped
        self._text_layout = None
        return changed

    def set_range(self, value, max_value):
        changed = False
        if max_value != self._max_value:
            self._max_value = max_value
            changed = True
        clamped = max(0, min(self._max_value, value))
        if clamped != self._value:
            self._value = clamped
            changed = True
        if changed:
            self._text_layout = None
        return changed

    @property
    def orientation(self):
        return self._orientation

    def set_orientation(self, orientation):
        self._orientation = orientation

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

        state_name = {self.NORMAL: 'normal', self.DISABLED: 'disabled'}.get(
            self._state, 'normal')
        c = PROGRESS_COLORS[state_name]

        rt = ctx.rt
        r = PROGRESS_BORDER_RADIUS
        bw = PROGRESS_BORDER_WIDTH

        track_bg = get_brush(rt, *c['track_bg'])
        track_border = get_brush(rt, *c['track_border'])
        fill_brush = get_brush(rt, *c['fill'])

        if self._orientation == self.VERTICAL:
            self._draw_vertical(rt, rx, ry, rw, rh, r, bw,
                                track_bg, track_border, fill_brush)
        else:
            self._draw_horizontal(rt, rx, ry, rw, rh, r, bw,
                                  track_bg, track_border, fill_brush)

    def _draw_horizontal(self, rt, rx, ry, rw, rh, r, bw,
                         track_bg, track_border, fill_brush):
        frx = float(rx) + bw * 0.5
        fry = float(ry) + bw * 0.5
        frw = float(rw) - bw
        frh = float(rh) - bw

        rt.DrawRoundedRectangle(frx, fry, frx + frw, fry + frh,
                                r, r, track_border, bw)
        rt.FillRoundedRectangle(
            frx + bw, fry + bw,
            frx + frw - bw, fry + frh - bw,
            r, r, track_bg)

        ratio = self._value / max(1.0, float(self._max_value))
        fill_w = max(0.0, frw - 2.0 * bw - 2.0) * ratio
        if fill_w > 0:
            inset = 1.0
            fill_x = frx + bw + inset
            fill_y = fry + bw + inset
            fill_r = max(0.0, r - bw - inset)
            rt.FillRoundedRectangle(
                fill_x, fill_y,
                fill_x + fill_w, fry + frh - bw - inset,
                fill_r, fill_r, fill_brush)

    def _draw_vertical(self, rt, rx, ry, rw, rh, r, bw,
                       track_bg, track_border, fill_brush):
        frx = float(rx) + bw * 0.5
        fry = float(ry) + bw * 0.5
        frw = float(rw) - bw
        frh = float(rh) - bw

        rt.DrawRoundedRectangle(frx, fry, frx + frw, fry + frh,
                                r, r, track_border, bw)
        rt.FillRoundedRectangle(
            frx + bw, fry + bw,
            frx + frw - bw, fry + frh - bw,
            r, r, track_bg)

        ratio = self._value / max(1.0, float(self._max_value))
        fill_h = max(0.0, frh - 2.0 * bw - 2.0) * ratio
        if fill_h > 0:
            inset = 1.0
            fill_x = frx + bw + inset
            fill_y = fry + frh - bw - inset - fill_h
            fill_r = max(0.0, r - bw - inset)
            rt.FillRoundedRectangle(
                fill_x, fill_y,
                frx + frw - bw - inset, fry + frh - bw - inset,
                fill_r, fill_r, fill_brush)


class SkinAwareProgress(D2DProgress):
    def __init__(self, rect, skin_context,
                 value=0, max_value=100, orientation=0,
                 h_bg_slots=None, h_fg_slots=None,
                 v_bg_slots=None, v_fg_slots=None,
                 subcat='Progress'):
        super().__init__(rect, value=value, max_value=max_value,
                         orientation=orientation)
        self._ctx = skin_context
        self._subcat = subcat
        from ..layout import CONTROL_SLOTS
        defaults = CONTROL_SLOTS.get(self._subcat, {})
        self._h_bg_slots = h_bg_slots if h_bg_slots is not None else defaults.get('h_bg', {})
        self._h_fg_slots = h_fg_slots if h_fg_slots is not None else defaults.get('h_fg', {})
        self._v_bg_slots = v_bg_slots if v_bg_slots is not None else defaults.get('v_bg', {})
        self._v_fg_slots = v_fg_slots if v_fg_slots is not None else defaults.get('v_fg', {})

    def draw(self, ctx, client_rect):
        state_name = {self.NORMAL: 'normal', self.DISABLED: 'disabled'}.get(
            self._state, 'normal')

        if self._orientation == self.VERTICAL:
            bg_slot = self._v_bg_slots.get(state_name)
            fg_slot = self._v_fg_slots.get(state_name)
        else:
            bg_slot = self._h_bg_slots.get(state_name)
            fg_slot = self._h_fg_slots.get(state_name)

        bg_block = self._ctx.get_block(bg_slot) if bg_slot is not None else None
        fg_block = self._ctx.get_block(fg_slot) if fg_slot is not None else None

        has_bg = (bg_block is not None
                  and bg_block.bg_width > 0
                  and bg_block.bg_height > 0)
        has_fg = (fg_block is not None
                  and fg_block.bg_width > 0
                  and fg_block.bg_height > 0)

        if not has_bg or not has_fg:
            D2DProgress.draw(self, ctx, client_rect)
            return

        rx, ry, rw, rh = self._rect
        rt = ctx.rt

        from ..d2d_render import d2d_draw_block

        d2d_draw_block(rt, self._ctx.skin_img, bg_block,
                       (rx, ry, rw, rh),
                       wic_factory=ctx.wic_factory,
                       d2d_cache=self._ctx.cache)

        ratio = self._value / max(1.0, float(self._max_value))
        if ratio <= 0:
            return

        if self._orientation == self.VERTICAL:
            fill_h = int(max(1.0, float(rh - 6) * ratio))
            d2d_draw_block(rt, self._ctx.skin_img, fg_block,
                           (rx + 2, ry + 3, rw - 4, fill_h),
                           wic_factory=ctx.wic_factory,
                           d2d_cache=self._ctx.cache)
        else:
            fill_w = int(max(1.0, float(rw - 4) * ratio))
            d2d_draw_block(rt, self._ctx.skin_img, fg_block,
                           (rx + 2, ry + 3, fill_w, rh - 6),
                           wic_factory=ctx.wic_factory,
                           d2d_cache=self._ctx.cache)