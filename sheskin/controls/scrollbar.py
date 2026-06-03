"""D2D 控件 — D2DScrollBar / SkinAwareScrollBar。"""
import math
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush

SCROLLBAR_BTN_SIZE = 16
SCROLLBAR_MIN_THUMB = 18

SCROLLBAR_COLORS = {
    'normal': {
        'btn_bg': (0.88, 0.88, 0.90, 1.0),
        'btn_fg': (0.30, 0.30, 0.33, 1.0),
        'btn_border': (0.70, 0.70, 0.73, 1.0),
        'track_bg': (0.92, 0.92, 0.94, 1.0),
        'thumb_bg': (0.82, 0.82, 0.85, 1.0),
        'thumb_border': (0.65, 0.65, 0.68, 1.0),
    },
    'hover': {
        'btn_bg': (0.82, 0.82, 0.85, 1.0),
        'btn_fg': (0.15, 0.15, 0.18, 1.0),
        'btn_border': (0.55, 0.55, 0.58, 1.0),
        'track_bg': (0.92, 0.92, 0.94, 1.0),
        'thumb_bg': (0.75, 0.80, 0.88, 1.0),
        'thumb_border': (0.45, 0.55, 0.70, 1.0),
    },
    'pressed': {
        'btn_bg': (0.75, 0.75, 0.78, 1.0),
        'btn_fg': (0.05, 0.05, 0.07, 1.0),
        'btn_border': (0.50, 0.50, 0.53, 1.0),
        'track_bg': (0.92, 0.92, 0.94, 1.0),
        'thumb_bg': (0.65, 0.72, 0.82, 1.0),
        'thumb_border': (0.35, 0.45, 0.60, 1.0),
    },
    'disabled': {
        'btn_bg': (0.92, 0.92, 0.93, 1.0),
        'btn_fg': (0.60, 0.60, 0.62, 1.0),
        'btn_border': (0.78, 0.78, 0.80, 1.0),
        'track_bg': (0.93, 0.93, 0.94, 1.0),
        'thumb_bg': (0.88, 0.88, 0.90, 1.0),
        'thumb_border': (0.78, 0.78, 0.80, 1.0),
    },
}


class D2DScrollBar(SheControl):
    VERTICAL = 0
    HORIZONTAL = 1

    BTN1 = 0
    BTN2 = 1
    TRACK = 2
    THUMB = 3

    def __init__(self, rect, scroll_pos=0, scroll_max=100, page_size=10,
                 orientation=0, resolution=1, on_scroll=None):
        super().__init__(rect, "")
        self._scroll_max = max(0, scroll_max)
        self._page_size = max(1, page_size)
        self._resolution = max(0, resolution)
        self._scroll_pos = self._snap(max(0, min(self._scroll_max, scroll_pos)))
        self._orientation = orientation
        self._on_scroll = on_scroll
        self._btn1_state = self.NORMAL
        self._btn2_state = self.NORMAL
        self._thumb_state = self.NORMAL
        self._track_pressed = False
        self._dragging = False
        self._drag_origin = None
        self._drag_start_pos = 0
        self._captured_part = None

    @property
    def scroll_pos(self):
        return self._scroll_pos

    @property
    def scroll_max(self):
        return self._scroll_max

    @property
    def page_size(self):
        return self._page_size

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

    def set_scroll_pos(self, pos):
        clamped = self._snap(max(0, min(self._scroll_max, pos)))
        changed = clamped != self._scroll_pos
        self._scroll_pos = clamped
        if changed and self._on_scroll:
            self._on_scroll(self._scroll_pos)
        return changed

    def set_scroll_info(self, scroll_pos=None, scroll_max=None, page_size=None):
        if scroll_max is not None:
            self._scroll_max = max(0, scroll_max)
        if page_size is not None:
            self._page_size = max(1, page_size)
        if scroll_pos is not None:
            self._scroll_pos = max(0, min(self._scroll_max, scroll_pos))
        else:
            self._scroll_pos = max(0, min(self._scroll_max, self._scroll_pos))

    def set_on_scroll(self, callback):
        self._on_scroll = callback

    def _get_btn_size(self):
        return float(SCROLLBAR_BTN_SIZE)

    def _get_thumb_size(self):
        total = self._scroll_max + self._page_size
        if total <= 0 or self._page_size <= 0:
            return float(SCROLLBAR_MIN_THUMB)
        rx, ry, rw, rh = self._rect
        btn = self._get_btn_size()
        if self._orientation == self.VERTICAL:
            track_len = float(rh) - btn * 2
        else:
            track_len = float(rw) - btn * 2
        if track_len <= 0:
            return float(SCROLLBAR_MIN_THUMB)
        ratio = self._page_size / total
        thumb = max(float(SCROLLBAR_MIN_THUMB), track_len * ratio)
        return min(thumb, track_len)

    def _get_part_rects(self):
        rx, ry, rw, rh = self._rect
        btn = self._get_btn_size()
        thumb_sz = self._get_thumb_size()
        if self._orientation == self.VERTICAL:
            btn1 = (float(rx), float(ry), float(rw), btn)
            btn2 = (float(rx), float(ry + rh) - btn, float(rw), btn)
            track_top = float(ry) + btn
            track_bottom = float(ry + rh) - btn
            track_len = track_bottom - track_top
            if self._scroll_max > 0:
                ratio = self._scroll_pos / float(self._scroll_max)
            else:
                ratio = 0.0
            thumb_range = track_len - thumb_sz
            thumb_y = track_top + ratio * thumb_range
            thumb = (float(rx), thumb_y, float(rw), thumb_sz)
            track = (float(rx), track_top, float(rw), track_len)
            return {self.BTN1: btn1, self.BTN2: btn2,
                    self.TRACK: track, self.THUMB: thumb}
        else:
            btn1 = (float(rx), float(ry), btn, float(rh))
            btn2 = (float(rx + rw) - btn, float(ry), btn, float(rh))
            track_left = float(rx) + btn
            track_right = float(rx + rw) - btn
            track_len = track_right - track_left
            if self._scroll_max > 0:
                ratio = self._scroll_pos / float(self._scroll_max)
            else:
                ratio = 0.0
            thumb_range = track_len - thumb_sz
            thumb_x = track_left + ratio * thumb_range
            thumb = (thumb_x, float(ry), thumb_sz, float(rh))
            track = (track_left, float(ry), track_len, float(rh))
            return {self.BTN1: btn1, self.BTN2: btn2,
                    self.TRACK: track, self.THUMB: thumb}

    def _hit_test(self, pt):
        px, py = float(pt[0]), float(pt[1])
        rects = self._get_part_rects()
        for part in (self.THUMB, self.BTN1, self.BTN2, self.TRACK):
            rx, ry, rw, rh = rects[part]
            if rx <= px <= rx + rw and ry <= py <= ry + rh:
                return part
        return None

    def _pos_to_scroll(self, pt):
        rects = self._get_part_rects()
        thumb_sz = self._get_thumb_size()
        if self._orientation == self.VERTICAL:
            _, _, _, track_len = rects[self.TRACK]
        else:
            _, _, track_len, _ = rects[self.TRACK]
        if track_len <= thumb_sz or self._scroll_max <= 0:
            return self._scroll_pos
        thumb_range = track_len - thumb_sz
        if self._orientation == self.VERTICAL:
            track_top = rects[self.TRACK][1]
            offset = float(pt[1]) - track_top - thumb_sz * 0.5
        else:
            track_left = rects[self.TRACK][0]
            offset = float(pt[0]) - track_left - thumb_sz * 0.5
        ratio = max(0.0, min(1.0, offset / thumb_range))
        return self._snap(ratio * self._scroll_max)

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        part = self._hit_test(pt)
        if part is None:
            return False
        if part == self.BTN1:
            self._btn1_state = self.PRESSED
            self._captured_part = self.BTN1
            self._captured = True
            self.set_scroll_pos(self._scroll_pos - 1)
            return True
        if part == self.BTN2:
            self._btn2_state = self.PRESSED
            self._captured_part = self.BTN2
            self._captured = True
            self.set_scroll_pos(self._scroll_pos + 1)
            return True
        if part == self.THUMB:
            self._thumb_state = self.PRESSED
            self._dragging = True
            self._drag_origin = pt
            self._drag_start_pos = self._scroll_pos
            self._captured = True
            self._captured_part = self.THUMB
            return True
        if part == self.TRACK:
            self._track_pressed = True
            self._captured = True
            self._captured_part = self.TRACK
            new_pos = self._pos_to_scroll(pt)
            if new_pos < self._scroll_pos:
                self.set_scroll_pos(self._scroll_pos - self._page_size)
            else:
                self.set_scroll_pos(self._scroll_pos + self._page_size)
            return True
        return False

    def on_mouse_up(self, pt):
        if self._state == self.DISABLED:
            return False
        if not self._captured:
            return False
        old_btn1 = self._btn1_state
        old_btn2 = self._btn2_state
        old_thumb = self._thumb_state
        was_dragging = self._dragging
        was_track = self._track_pressed
        self._btn1_state = self.NORMAL
        self._btn2_state = self.NORMAL
        self._thumb_state = self.NORMAL
        self._track_pressed = False
        self._dragging = False
        self._captured = False
        self._captured_part = None
        self._drag_origin = None
        part = self._hit_test(pt)
        if part == self.BTN1:
            self._btn1_state = self.HOVER
        elif part == self.BTN2:
            self._btn2_state = self.HOVER
        elif part == self.THUMB:
            self._thumb_state = self.HOVER
        return (old_btn1 != self._btn1_state
                or old_btn2 != self._btn2_state
                or old_thumb != self._thumb_state
                or was_dragging or was_track)

    def on_mouse_move(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._dragging:
            new_pos = self._pos_to_scroll(pt)
            self.set_scroll_pos(new_pos)
            return True
        old_btn1 = self._btn1_state
        old_btn2 = self._btn2_state
        old_thumb = self._thumb_state
        part = self._hit_test(pt)
        self._btn1_state = self.HOVER if part == self.BTN1 else self.NORMAL
        self._btn2_state = self.HOVER if part == self.BTN2 else self.NORMAL
        self._thumb_state = self.HOVER if part == self.THUMB else self.NORMAL
        return (old_btn1 != self._btn1_state
                or old_btn2 != self._btn2_state
                or old_thumb != self._thumb_state)

    def on_mouse_leave(self):
        if self._state == self.DISABLED:
            return False
        old_btn1 = self._btn1_state
        old_btn2 = self._btn2_state
        old_thumb = self._thumb_state
        self._btn1_state = self.NORMAL
        self._btn2_state = self.NORMAL
        self._thumb_state = self.NORMAL
        self._track_pressed = False
        if self._dragging:
            self._dragging = False
            self._captured = False
            self._captured_part = None
            self._drag_origin = None
        return (old_btn1 != self.NORMAL
                or old_btn2 != self.NORMAL
                or old_thumb != self.NORMAL)

    def _on_activate(self):
        pass

    def _state_for(self, part_state):
        if self._state == self.DISABLED:
            return 'disabled'
        return {self.NORMAL: 'normal', self.HOVER: 'hover',
                self.PRESSED: 'pressed'}.get(part_state, 'normal')

    def _draw_arrow(self, rt, bx, by, bw, bh, direction, brush):
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
        try:
            factory = pyd2d.GetD2DFactory()
            geo = factory.CreatePathGeometry()
            sink = geo.Open()
            sink.SetFillMode(pyd2d.FILL_MODE.ALTERNATE)
            sink.BeginFigure(x0, y0)
            sink.AddLine(x1, y1)
            sink.AddLine(x2, y2)
            sink.EndFigure(1)
            sink.Close()
            rt.FillGeometry(geo, brush)
        except Exception:
            pass

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt
        rects = self._get_part_rects()

        c_track = SCROLLBAR_COLORS[self._state_for(self.NORMAL)]
        c_btn1 = SCROLLBAR_COLORS[self._state_for(self._btn1_state)]
        c_btn2 = SCROLLBAR_COLORS[self._state_for(self._btn2_state)]
        c_thumb = SCROLLBAR_COLORS[self._state_for(self._thumb_state)]

        track_bg = get_brush(rt, *c_track['track_bg'])
        _, _, tw, th = rects[self.TRACK]
        tx, ty = rects[self.TRACK][0], rects[self.TRACK][1]
        rt.FillRectangle(tx, ty, tx + tw, ty + th, track_bg)

        for part, state, colors, direction in [
            (self.BTN1, self._btn1_state, c_btn1,
             'up' if self._orientation == self.VERTICAL else 'left'),
            (self.BTN2, self._btn2_state, c_btn2,
             'down' if self._orientation == self.VERTICAL else 'right'),
        ]:
            bx, by, bw, bh = rects[part]
            bg = get_brush(rt, *colors['btn_bg'])
            border = get_brush(rt, *colors['btn_border'])
            fg = get_brush(rt, *colors['btn_fg'])
            rt.FillRectangle(bx, by, bx + bw, by + bh, bg)
            rt.DrawRectangle(bx, by, bx + bw, by + bh, border, 1.0)
            self._draw_arrow(rt, bx, by, bw, bh, direction, fg)

        tx, ty, tw, th = rects[self.THUMB]
        thumb_bg = get_brush(rt, *c_thumb['thumb_bg'])
        thumb_border = get_brush(rt, *c_thumb['thumb_border'])
        r = min(tw, th) * 0.2
        rt.FillRoundedRectangle(tx, ty, tx + tw, ty + th, r, r, thumb_bg)
        rt.DrawRoundedRectangle(tx, ty, tx + tw, ty + th, r, r, thumb_border, 1.0)


class SkinAwareScrollBar(D2DScrollBar):
    def __init__(self, rect, skin_context, scroll_pos=0, scroll_max=100,
                 page_size=10, orientation=0, on_scroll=None,
                 subcat='ScrollBar'):
        super().__init__(rect, scroll_pos=scroll_pos, scroll_max=scroll_max,
                         page_size=page_size, orientation=orientation,
                         on_scroll=on_scroll)
        self._ctx = skin_context
        self._subcat = subcat
        from ..layout import CONTROL_SLOTS
        defaults = CONTROL_SLOTS.get(self._subcat, {})
        if self._orientation == self.VERTICAL:
            self._btn1_slots = defaults.get('v_top', {})
            self._btn2_slots = defaults.get('v_bottom', {})
            self._track_slots = defaults.get('v_track', {})
            self._thumb_slots = defaults.get('v_thumb', {})
        else:
            self._btn1_slots = defaults.get('h_left', {})
            self._btn2_slots = defaults.get('h_right', {})
            self._track_slots = defaults.get('h_track', {})
            self._thumb_slots = defaults.get('h_thumb', {})

    def _get_skin_block(self, slots, state_name):
        slot_num = slots.get(state_name, slots.get('normal'))
        if slot_num is None:
            return None
        return self._ctx.get_block(slot_num)

    def draw(self, ctx, client_rect):
        btn1_state = self._state_for(self._btn1_state)
        btn2_state = self._state_for(self._btn2_state)
        thumb_state = self._state_for(self._thumb_state)
        track_state = self._state_for(self.PRESSED if self._track_pressed else self.NORMAL)

        btn1_block = self._get_skin_block(self._btn1_slots, btn1_state)
        btn2_block = self._get_skin_block(self._btn2_slots, btn2_state)
        track_block = self._get_skin_block(self._track_slots, track_state)
        thumb_block = self._get_skin_block(self._thumb_slots, thumb_state)

        has_all = all(b is not None and b.bg_width > 0 and b.bg_height > 0
                      for b in [btn1_block, btn2_block, track_block, thumb_block])

        if not has_all:
            D2DScrollBar.draw(self, ctx, client_rect)
            return

        rt = ctx.rt
        from ..d2d_render import d2d_draw_block
        rects = self._get_part_rects()

        bx, by, bw, bh = rects[self.TRACK]
        d2d_draw_block(rt, self._ctx.skin_img, track_block,
                       (int(bx), int(by), int(bw), int(bh)),
                       wic_factory=ctx.wic_factory,
                       d2d_cache=self._ctx.cache)

        for part, block in [(self.BTN1, btn1_block), (self.BTN2, btn2_block)]:
            bx, by, bw, bh = rects[part]
            d2d_draw_block(rt, self._ctx.skin_img, block,
                           (int(bx), int(by), int(bw), int(bh)),
                           wic_factory=ctx.wic_factory,
                           d2d_cache=self._ctx.cache)

        bx, by, bw, bh = rects[self.THUMB]
        d2d_draw_block(rt, self._ctx.skin_img, thumb_block,
                       (int(bx), int(by), int(bw), int(bh)),
                       wic_factory=ctx.wic_factory,
                       d2d_cache=self._ctx.cache)
