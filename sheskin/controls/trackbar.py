"""D2D 控件 — D2DTrackBar / SkinAwareTrackBar。"""
import math
from .base_control import SheControl
from ..brush_cache import get_brush
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP

TRACKBAR_THUMB_SIZE = 18
TRACKBAR_TRACK_HEIGHT = 4
TRACKBAR_TICK_HEIGHT = 4
TRACKBAR_MIN_THUMB_HALF = 9

TRACKBAR_COLORS = {
    'normal': {
        'track_bg': (0.80, 0.80, 0.83, 1.0),
        'track_fill': (0.0, 0.47, 0.84, 1.0),
        'thumb_bg': (0.96, 0.96, 0.98, 1.0),
        'thumb_border': (0.55, 0.55, 0.58, 1.0),
        'tick': (0.65, 0.65, 0.68, 1.0),
    },
    'hover': {
        'track_bg': (0.80, 0.80, 0.83, 1.0),
        'track_fill': (0.0, 0.47, 0.84, 1.0),
        'thumb_bg': (0.88, 0.94, 0.98, 1.0),
        'thumb_border': (0.18, 0.56, 0.92, 1.0),
        'tick': (0.65, 0.65, 0.68, 1.0),
    },
    'pressed': {
        'track_bg': (0.80, 0.80, 0.83, 1.0),
        'track_fill': (0.0, 0.47, 0.84, 1.0),
        'thumb_bg': (0.82, 0.88, 0.94, 1.0),
        'thumb_border': (0.11, 0.46, 0.76, 1.0),
        'tick': (0.65, 0.65, 0.68, 1.0),
    },
    'disabled': {
        'track_bg': (0.88, 0.88, 0.90, 1.0),
        'track_fill': (0.65, 0.65, 0.68, 1.0),
        'thumb_bg': (0.85, 0.85, 0.88, 1.0),
        'thumb_border': (0.70, 0.70, 0.73, 1.0),
        'tick': (0.78, 0.78, 0.80, 1.0),
    },
}


class D2DTrackBar(SheControl):
    HORIZONTAL = 0
    VERTICAL = 1

    def __init__(self, rect, value=0, min_value=0, max_value=100,
                 step=1, page_step=10, orientation=0,
                 show_ticks=False, tick_count=0,
                 resolution=1, on_change=None):
        super().__init__(rect, "")
        self._min = min_value
        self._max = max_value
        self._resolution = max(0, resolution)
        self._value = self._snap(max(self._min, min(self._max, value)))
        self._step = max(1, step)
        self._page_step = max(1, page_step)
        self._orientation = orientation
        self._show_ticks = show_ticks
        self._tick_count = tick_count
        self._on_change = on_change
        self._thumb_state = self.NORMAL
        self._dragging = False
        self._drag_origin = None

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
    def page_step(self):
        return self._page_step

    @property
    def orientation(self):
        return self._orientation

    @property
    def resolution(self):
        return self._resolution

    def _snap(self, value):
        if self._resolution <= 0:
            return value
        snapped = round(value / self._resolution) * self._resolution
        if self._resolution >= 1:
            return round(snapped)
        decimals = max(0, -int(math.floor(math.log10(abs(self._resolution)))))
        return round(snapped, decimals)

    def set_value(self, value):
        clamped = self._snap(max(self._min, min(self._max, value)))
        changed = clamped != self._value
        self._value = clamped
        if changed and self._on_change:
            self._on_change(self._value)
        return changed

    def set_range(self, min_value, max_value):
        self._min = min_value
        self._max = max_value
        self._value = max(self._min, min(self._max, self._value))

    def set_on_change(self, callback):
        self._on_change = callback

    def _get_thumb_rect(self):
        rx, ry, rw, rh = self._rect
        thumb_sz = float(TRACKBAR_THUMB_SIZE)
        track_h = float(TRACKBAR_TRACK_HEIGHT)
        if self._orientation == self.HORIZONTAL:
            track_y = float(ry) + (float(rh) - track_h) * 0.5
            range_w = float(rw) - thumb_sz
            if self._max > self._min:
                ratio = (self._value - self._min) / float(self._max - self._min)
            else:
                ratio = 0.0
            thumb_x = float(rx) + ratio * range_w
            thumb_y = track_y + track_h * 0.5 - thumb_sz * 0.5
            return (thumb_x, thumb_y, thumb_sz, thumb_sz)
        else:
            track_x = float(rx) + (float(rw) - track_h) * 0.5
            range_h = float(rh) - thumb_sz
            if self._max > self._min:
                ratio = (self._value - self._min) / float(self._max - self._min)
            else:
                ratio = 0.0
            thumb_y = float(ry) + (1.0 - ratio) * range_h
            thumb_x = track_x + track_h * 0.5 - thumb_sz * 0.5
            return (thumb_x, thumb_y, thumb_sz, thumb_sz)

    def _hit_thumb(self, pt):
        tx, ty, tw, th = self._get_thumb_rect()
        px, py = float(pt[0]), float(pt[1])
        return tx <= px <= tx + tw and ty <= py <= ty + th

    def _hit_track(self, pt):
        rx, ry, rw, rh = self._rect
        px, py = float(pt[0]), float(pt[1])
        return rx <= px <= rx + rw and ry <= py <= ry + rh

    def _pos_to_value(self, pt):
        rx, ry, rw, rh = self._rect
        thumb_sz = float(TRACKBAR_THUMB_SIZE)
        if self._orientation == self.HORIZONTAL:
            range_w = float(rw) - thumb_sz
            if range_w <= 0:
                return self._min
            offset = float(pt[0]) - float(rx) - thumb_sz * 0.5
            ratio = max(0.0, min(1.0, offset / range_w))
        else:
            range_h = float(rh) - thumb_sz
            if range_h <= 0:
                return self._min
            offset = float(pt[1]) - float(ry) - thumb_sz * 0.5
            ratio = max(0.0, min(1.0, 1.0 - offset / range_h))
        return self._snap(self._min + ratio * (self._max - self._min))

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._hit_thumb(pt):
            self._dragging = True
            self._thumb_state = self.PRESSED
            self._captured = True
            self._drag_origin = pt
            return True
        if self._hit_track(pt):
            new_val = self._pos_to_value(pt)
            self.set_value(new_val)
            self._dragging = True
            self._thumb_state = self.PRESSED
            self._captured = True
            self._drag_origin = pt
            return True
        return False

    def on_mouse_up(self, pt):
        if self._state == self.DISABLED:
            return False
        if not self._captured:
            return False
        was_dragging = self._dragging
        self._dragging = False
        self._captured = False
        self._drag_origin = None
        old_thumb = self._thumb_state
        if self._hit_thumb(pt) or self._hit_track(pt):
            self._thumb_state = self.HOVER
        else:
            self._thumb_state = self.NORMAL
        return was_dragging or old_thumb != self._thumb_state

    def on_mouse_move(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._dragging:
            new_val = self._pos_to_value(pt)
            self.set_value(new_val)
            return True
        old_thumb = self._thumb_state
        if self._hit_thumb(pt):
            self._thumb_state = self.HOVER
        else:
            self._thumb_state = self.NORMAL
        return old_thumb != self._thumb_state

    def on_mouse_leave(self):
        if self._state == self.DISABLED:
            return False
        old_thumb = self._thumb_state
        self._thumb_state = self.NORMAL
        if self._dragging:
            self._dragging = False
            self._captured = False
            self._drag_origin = None
        return old_thumb != self.NORMAL

    def _on_activate(self):
        pass

    def _state_name(self):
        if self._state == self.DISABLED:
            return 'disabled'
        return {self.NORMAL: 'normal', self.HOVER: 'hover',
                self.PRESSED: 'pressed'}.get(self._thumb_state, 'normal')

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt

        state_name = self._state_name()
        c = TRACKBAR_COLORS[state_name]

        track_h = float(TRACKBAR_TRACK_HEIGHT)
        thumb_sz = float(TRACKBAR_THUMB_SIZE)

        if self._orientation == self.HORIZONTAL:
            self._draw_horizontal(rt, rx, ry, rw, rh, c, track_h, thumb_sz)
        else:
            self._draw_vertical(rt, rx, ry, rw, rh, c, track_h, thumb_sz)

    def _draw_horizontal(self, rt, rx, ry, rw, rh, c, track_h, thumb_sz):
        track_y = float(ry) + (float(rh) - track_h) * 0.5
        track_bg_brush = get_brush(rt, *c['track_bg'])
        rt.FillRectangle(float(rx), track_y, float(rx + rw), track_y + track_h, track_bg_brush)

        if self._max > self._min:
            ratio = (self._value - self._min) / float(self._max - self._min)
        else:
            ratio = 0.0
        fill_end = float(rx) + ratio * float(rw)
        if fill_end > float(rx):
            fill_brush = get_brush(rt, *c['track_fill'])
            rt.FillRectangle(float(rx), track_y, fill_end, track_y + track_h, fill_brush)

        if self._show_ticks and self._tick_count > 1:
            tick_brush = get_brush(rt, *c['tick'])
            for i in range(self._tick_count):
                tick_ratio = i / float(self._tick_count - 1)
                tick_x = float(rx) + tick_ratio * float(rw)
                rt.DrawLine(tick_x, track_y + track_h, tick_x,
                            track_y + track_h + float(TRACKBAR_TICK_HEIGHT),
                            tick_brush, 1.0)

        tx, ty, tw, th = self._get_thumb_rect()
        thumb_bg = get_brush(rt, *c['thumb_bg'])
        thumb_border = get_brush(rt, *c['thumb_border'])
        r = thumb_sz * 0.25
        rt.FillRoundedRectangle(tx, ty, tx + tw, ty + th, r, r, thumb_bg)
        rt.DrawRoundedRectangle(tx, ty, tx + tw, ty + th, r, r, thumb_border, 1.0)

    def _draw_vertical(self, rt, rx, ry, rw, rh, c, track_h, thumb_sz):
        track_x = float(rx) + (float(rw) - track_h) * 0.5
        track_bg_brush = get_brush(rt, *c['track_bg'])
        rt.FillRectangle(track_x, float(ry), track_x + track_h, float(ry + rh), track_bg_brush)

        if self._max > self._min:
            ratio = (self._value - self._min) / float(self._max - self._min)
        else:
            ratio = 0.0
        fill_start = float(ry + rh) - ratio * float(rh)
        if fill_start < float(ry + rh):
            fill_brush = get_brush(rt, *c['track_fill'])
            rt.FillRectangle(track_x, fill_start, track_x + track_h, float(ry + rh), fill_brush)

        if self._show_ticks and self._tick_count > 1:
            tick_brush = get_brush(rt, *c['tick'])
            for i in range(self._tick_count):
                tick_ratio = i / float(self._tick_count - 1)
                tick_y = float(ry + rh) - tick_ratio * float(rh)
                rt.DrawLine(track_x + track_h, tick_y,
                            track_x + track_h + float(TRACKBAR_TICK_HEIGHT), tick_y,
                            tick_brush, 1.0)

        tx, ty, tw, th = self._get_thumb_rect()
        thumb_bg = get_brush(rt, *c['thumb_bg'])
        thumb_border = get_brush(rt, *c['thumb_border'])
        r = thumb_sz * 0.25
        rt.FillRoundedRectangle(tx, ty, tx + tw, ty + th, r, r, thumb_bg)
        rt.DrawRoundedRectangle(tx, ty, tx + tw, ty + th, r, r, thumb_border, 1.0)


class SkinAwareTrackBar(D2DTrackBar):
    def __init__(self, rect, skin_context, value=0, min_value=0,
                 max_value=100, step=1, page_step=10, orientation=0,
                 show_ticks=False, tick_count=0,
                 resolution=1, on_change=None, subcat='TrackBar'):
        super().__init__(rect, value=value, min_value=min_value,
                         max_value=max_value, step=step,
                         page_step=page_step, orientation=orientation,
                         show_ticks=show_ticks, tick_count=tick_count,
                         resolution=resolution, on_change=on_change)
        self._ctx = skin_context
        self._subcat = subcat
        from ..layout import CONTROL_SLOTS
        defaults = CONTROL_SLOTS.get(self._subcat, {})
        if self._orientation == self.HORIZONTAL:
            self._thumb_slots = defaults.get('h_square', {})
            self._track_slots = defaults.get('h_track', {})
        else:
            self._thumb_slots = defaults.get('v_square', {})
            self._track_slots = defaults.get('v_track', {})

    def draw(self, ctx, client_rect):
        state_name = self._state_name()

        thumb_slot = self._thumb_slots.get(state_name,
                                           self._thumb_slots.get('normal'))
        track_slot = self._track_slots.get(state_name,
                                           self._track_slots.get('normal'))

        thumb_block = self._ctx.get_block(thumb_slot) if thumb_slot is not None else None
        track_block = self._ctx.get_block(track_slot) if track_slot is not None else None

        has_thumb = (thumb_block is not None
                     and thumb_block.bg_width > 0
                     and thumb_block.bg_height > 0)
        has_track = (track_block is not None
                     and track_block.bg_width > 0
                     and track_block.bg_height > 0)

        if not has_thumb or not has_track:
            D2DTrackBar.draw(self, ctx, client_rect)
            return

        rx, ry, rw, rh = self._rect
        rt = ctx.rt
        from ..d2d_render import d2d_draw_block

        thumb_sz = float(TRACKBAR_THUMB_SIZE)
        track_h = float(TRACKBAR_TRACK_HEIGHT)

        if self._orientation == self.HORIZONTAL:
            track_y = float(ry) + (float(rh) - track_h) * 0.5
            d2d_draw_block(rt, self._ctx.skin_img, track_block,
                           (rx, int(track_y), rw, int(track_h)),
                           wic_factory=ctx.wic_factory,
                           d2d_cache=self._ctx.cache)

            if self._show_ticks and self._tick_count > 1:
                c = TRACKBAR_COLORS[self._state_name()]
                tick_brush = get_brush(rt, *c['tick'])
                for i in range(self._tick_count):
                    tick_ratio = i / float(self._tick_count - 1)
                    tick_x = float(rx) + tick_ratio * float(rw)
                    rt.DrawLine(tick_x, track_y + track_h, tick_x,
                                track_y + track_h + float(TRACKBAR_TICK_HEIGHT),
                                tick_brush, 1.0)

            tx, ty, tw, th = self._get_thumb_rect()
            d2d_draw_block(rt, self._ctx.skin_img, thumb_block,
                           (int(tx), int(ty), int(tw), int(th)),
                           wic_factory=ctx.wic_factory,
                           d2d_cache=self._ctx.cache)
        else:
            track_x = float(rx) + (float(rw) - track_h) * 0.5
            d2d_draw_block(rt, self._ctx.skin_img, track_block,
                           (int(track_x), ry, int(track_h), rh),
                           wic_factory=ctx.wic_factory,
                           d2d_cache=self._ctx.cache)

            if self._show_ticks and self._tick_count > 1:
                c = TRACKBAR_COLORS[self._state_name()]
                tick_brush = get_brush(rt, *c['tick'])
                for i in range(self._tick_count):
                    tick_ratio = i / float(self._tick_count - 1)
                    tick_y = float(ry + rh) - tick_ratio * float(rh)
                    rt.DrawLine(track_x + track_h, tick_y,
                                track_x + track_h + float(TRACKBAR_TICK_HEIGHT), tick_y,
                                tick_brush, 1.0)

            tx, ty, tw, th = self._get_thumb_rect()
            d2d_draw_block(rt, self._ctx.skin_img, thumb_block,
                           (int(tx), int(ty), int(tw), int(th)),
                           wic_factory=ctx.wic_factory,
                           d2d_cache=self._ctx.cache)
