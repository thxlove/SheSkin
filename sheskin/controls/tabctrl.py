"""D2D 控件 — D2DTabCtrl / SkinAwareTabCtrl。"""
import pyd2d
from .base_control import SheControl
from .layout import D2DVBox
from ..brush_cache import get_brush
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP

TABCTRL_MIN_TAB_WIDTH = 40
TABCTRL_TAB_PAD_X = 8
TABCTRL_TAB_PAD_Y = 4
TABCTRL_BTN_MIN_HEIGHT = 24
TABCTRL_PAGE_MARGIN = 10
TABCTRL_PAGE_SPACING = 6

TABCTRL_COLORS = {
    'normal': {
        'btn_bg': (0.85, 0.85, 0.88, 1.0),
        'btn_border': (0.70, 0.70, 0.73, 1.0),
        'btn_text': (0.20, 0.20, 0.22, 1.0),
        'body_bg': (0.94, 0.94, 0.97, 1.0),
        'body_border': (0.70, 0.70, 0.73, 1.0),
    },
    'hover': {
        'btn_bg': (0.88, 0.88, 0.91, 1.0),
        'btn_border': (0.65, 0.65, 0.68, 1.0),
        'btn_text': (0.10, 0.10, 0.12, 1.0),
    },
    'pressed': {
        'btn_bg': (0.92, 0.92, 0.95, 1.0),
        'btn_border': (0.60, 0.60, 0.63, 1.0),
        'btn_text': (0.05, 0.05, 0.08, 1.0),
    },
    'disabled': {
        'btn_bg': (0.88, 0.88, 0.90, 1.0),
        'btn_border': (0.78, 0.78, 0.80, 1.0),
        'btn_text': (0.60, 0.60, 0.63, 1.0),
        'body_bg': (0.92, 0.92, 0.95, 1.0),
        'body_border': (0.78, 0.78, 0.80, 1.0),
    },
}


class D2DTabCtrl(SheControl):
    TOP = 0
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3

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

    def __init__(self, rect, orientation=0, on_change=None, default_page=None):
        super().__init__(rect, "")
        self._orientation = orientation
        self._on_change = on_change
        self._pages = []
        self._page_vboxes = []
        self._selected = -1
        self._hovered = -1
        self._pressed_tab = -1
        self._captured = False
        self._tab_layouts = []
        self._default_page = default_page
        self._page_visibility_stale = False
        self._layout_precise = False

    @property
    def orientation(self):
        return self._orientation

    @property
    def page_count(self):
        return len(self._pages)

    @property
    def selected(self):
        return self._selected

    def add_page(self, title, disabled=False, controls=None):
        self._pages.append({'title': title, 'disabled': disabled})
        vbox = D2DVBox(controls or [], spacing=TABCTRL_PAGE_SPACING, margin=TABCTRL_PAGE_MARGIN)
        self._page_vboxes.append(vbox)
        if self._selected < 0:
            default = self._default_page if self._default_page is not None else 0
            if default == len(self._pages) - 1:
                self._selected = default
                self._page_visibility_stale = True
        self._tab_layouts = []
        return len(self._pages) - 1

    def select_page(self, index):
        if 0 <= index < len(self._pages) and index != self._selected:
            old = self._selected
            self._selected = index
            self._apply_page_visibility(index)
            if self._on_change:
                self._on_change(index, old)

    def set_page_controls(self, index, controls):
        if 0 <= index < len(self._page_vboxes):
            self._page_vboxes[index] = D2DVBox(
                controls or [], spacing=TABCTRL_PAGE_SPACING, margin=TABCTRL_PAGE_MARGIN)
            self._page_visibility_stale = True

    @property
    def body_rect(self):
        self._ensure_layout()
        return self._body_rect

    @property
    def all_controls(self):
        result = [self]
        for vbox in self._page_vboxes:
            result.extend(vbox._walk_controls())
        return result

    def _apply_page_visibility(self, page_index):
        for i, vbox in enumerate(self._page_vboxes):
            for c in vbox._walk_controls():
                visible = (i == page_index)
                c._visible = visible
                if not visible and getattr(c, '_focused', False):
                    c.set_focus(False)
                    frame = getattr(c, '_frame', None)
                    if frame and getattr(frame, '_focused_ctrl', None) is c:
                        frame._focused_ctrl = None

    def _flush_page_visibility(self):
        if self._page_visibility_stale:
            self._page_visibility_stale = False
            self._apply_page_visibility(self._selected)

    def _layout_page_vboxes(self):
        if self._selected < 0 or not self._tab_layouts:
            return
        bx, by, bw, bh = self._body_rect
        for i, vbox in enumerate(self._page_vboxes):
            if i == self._selected:
                vbox.layout((bx, by, bw, bh))
            else:
                for c in vbox._walk_controls():
                    c._visible = False

    def get_selected(self):
        return self._selected

    def _is_horizontal(self):
        return self._orientation in (self.TOP, self.BOTTOM)

    def _get_btn_size(self):
        if self._is_horizontal():
            return (TABCTRL_MIN_TAB_WIDTH, 24)
        return (24, TABCTRL_MIN_TAB_WIDTH)

    def _measure_text(self, dw_factory, text):
        fmt = self._get_text_fmt(dw_factory=dw_factory)
        layout = dw_factory.CreateTextLayout(text, fmt, 500.0, 100.0)
        return float(layout.GetMetrics().width)

    def _ensure_layout(self, dw_factory=None):
        if self._tab_layouts and len(self._tab_layouts) == len(self._pages):
            if dw_factory is not None and not self._layout_precise:
                self._layout_tabs(dw_factory)
            return
        self._layout_tabs(dw_factory)

    def _estimate_text_width(self, text):
        return max(TABCTRL_MIN_TAB_WIDTH, len(text) * 10 + 8)

    def _layout_tabs(self, dw_factory):
        if not self._pages:
            self._tab_layouts = []
            self._layout_precise = False
            return

        rx, ry, rw, rh = self._rect
        rxf, ryf, rwf, rhf = float(rx), float(ry), float(rw), float(rh)
        pad_x = float(TABCTRL_TAB_PAD_X)
        pad_y = float(TABCTRL_TAB_PAD_Y)
        min_w = float(TABCTRL_MIN_TAB_WIDTH)

        if dw_factory is not None:
            self._layout_precise = True
            try:
                btn_h = self._get_btn_natural_height() if hasattr(self, '_get_btn_natural_height') else float(TABCTRL_BTN_MIN_HEIGHT)
            except Exception:
                btn_h = float(TABCTRL_BTN_MIN_HEIGHT)
            btn_h = max(btn_h, float(TABCTRL_BTN_MIN_HEIGHT))
            measures = []
            for page in self._pages:
                tw = max(min_w, self._measure_text(dw_factory, page['title']) + pad_x * 2)
                measures.append(tw)
        else:
            self._layout_precise = False
            btn_h = float(TABCTRL_BTN_MIN_HEIGHT)
            measures = [max(min_w, len(p['title']) * 10.0 + pad_x * 2) for p in self._pages]

        if self._is_horizontal():
            cur_x = rxf
            self._tab_layouts = []
            for i, page in enumerate(self._pages):
                bw = float(measures[i])
                self._tab_layouts.append((cur_x, ryf, bw, btn_h))
                cur_x += bw
            self._body_rect = (rxf, ryf + btn_h, rwf, rhf - btn_h)
        else:
            btn_w = btn_h
            cur_y = ryf
            self._tab_layouts = []
            for i, page in enumerate(self._pages):
                bh = float(measures[i])
                self._tab_layouts.append((rxf, cur_y, btn_w, bh))
                cur_y += bh
            self._body_rect = (rxf + btn_w, ryf, rwf - btn_w, rhf)

    def _get_state_name(self, tab_index):
        if tab_index >= len(self._pages):
            return 'normal'
        if self._pages[tab_index].get('disabled'):
            return 'disabled'
        if self._captured and tab_index == self._pressed_tab:
            return 'pressed'
        if tab_index == self._selected:
            return 'pressed'
        if tab_index == self._hovered:
            return 'hover'
        return 'normal'

    def _hit_tab(self, pt):
        self._ensure_layout()
        if not self._tab_layouts:
            return -1
        px, py = float(pt[0]), float(pt[1])
        for i, (bx, by, bw, bh) in enumerate(self._tab_layouts):
            if bx <= px <= bx + bw and by <= py <= by + bh:
                return i
        return -1

    def hit_test(self, pt):
        return self._hit_tab(pt) >= 0

    def on_mouse_down(self, pt):
        tab = self._hit_tab(pt)
        if tab < 0 or self._pages[tab].get('disabled'):
            return False
        self._captured = True
        self._pressed_tab = tab
        return True

    def on_mouse_up(self, pt):
        if not self._captured:
            return False
        self._captured = False
        old_pressed = self._pressed_tab
        self._pressed_tab = -1
        tab = self._hit_tab(pt)
        if tab >= 0 and tab == old_pressed and not self._pages[tab].get('disabled'):
            if tab != self._selected:
                self.select_page(tab)
            return True
        return old_pressed >= 0

    def on_mouse_move(self, pt):
        if not self._pages:
            return False
        tab = self._hit_tab(pt)
        if self._captured:
            return False
        old = self._hovered
        if tab >= 0:
            if self._pages[tab].get('disabled'):
                self._hovered = -1
            else:
                self._hovered = tab
        else:
            self._hovered = -1
        return old != self._hovered

    def on_mouse_leave(self):
        self._captured = False
        self._pressed_tab = -1
        old = self._hovered
        self._hovered = -1
        return old >= 0

    def _on_activate(self):
        pass

    def draw(self, ctx, client_rect):
        self._flush_page_visibility()
        rx, ry, rw, rh = self._rect
        rt = ctx.rt

        self._ensure_layout(ctx.dw_factory)
        self._layout_page_vboxes()

        if self._state == self.DISABLED:
            c = TABCTRL_COLORS['disabled']
        else:
            c = TABCTRL_COLORS['normal']

        bx, by, bw, bh = self._body_rect
        body_bg = get_brush(rt, *c.get('body_bg', c['btn_bg']))
        rt.FillRectangle(bx, by, bx + bw, by + bh, body_bg)
        body_border = get_brush(rt, *c.get('body_border', c['btn_border']))
        rt.DrawRectangle(bx, by, bx + bw, by + bh, body_border, 1.0)

        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
        for i, (tx, ty, tw, th) in enumerate(self._tab_layouts):
            state_name = self._get_state_name(i)
            tab_colors = TABCTRL_COLORS.get(state_name, TABCTRL_COLORS['normal'])

            tab_bg = get_brush(rt, *tab_colors['btn_bg'])
            tab_border = get_brush(rt, *tab_colors['btn_border'])
            text_color = tab_colors['btn_text']

            rt.FillRectangle(tx, ty, tx + tw, ty + th, tab_bg)
            rt.DrawRectangle(tx, ty, tx + tw, ty + th, tab_border, 1.0)

            text = self._pages[i]['title']
            text_brush = get_brush(rt, *text_color)
            rt.DrawText(text, text_fmt,
                        tx + TABCTRL_TAB_PAD_X, ty + TABCTRL_TAB_PAD_Y,
                        tx + tw - TABCTRL_TAB_PAD_X, ty + th, text_brush)


class SkinAwareTabCtrl(D2DTabCtrl):
    ORIENT_KEY_MAP = {
        D2DTabCtrl.TOP: ('top_btn', 'top_body'),
        D2DTabCtrl.BOTTOM: ('bottom_btn', 'bottom_body'),
        D2DTabCtrl.LEFT: ('left_btn', 'left_body'),
        D2DTabCtrl.RIGHT: ('right_btn', 'right_body'),
    }

    _dwrite_text_fmt = None

    @classmethod
    def _get_text_fmt(cls, dw_factory=None, skin_ctx=None):
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

    def __init__(self, rect, skin_context, orientation=0, on_change=None,
                 subcat='TabCtrl', default_page=None):
        super().__init__(rect, orientation=orientation, on_change=on_change,
                         default_page=default_page)
        self._ctx = skin_context
        self._subcat = subcat
        from ..layout import CONTROL_SLOTS
        self._slots = CONTROL_SLOTS.get(self._subcat, {})

    @property
    def skin_context(self):
        return self._ctx

    def _get_btn_key(self):
        return self.ORIENT_KEY_MAP.get(self._orientation, ('top_btn', 'top_body'))[0]

    def _get_body_key(self):
        return self.ORIENT_KEY_MAP.get(self._orientation, ('top_btn', 'top_body'))[1]

    def _has_skin_blocks(self):
        btn_key = self._get_btn_key()
        body_key = self._get_body_key()
        if btn_key not in self._slots or body_key not in self._slots:
            return False
        return True

    def _get_btn_state_slot(self, state_name):
        if state_name == 'hover':
            state_name = 'default'
        btn_key = self._get_btn_key()
        slot_dict = self._slots.get(btn_key)
        if slot_dict and state_name in slot_dict:
            return slot_dict[state_name]
        disabled_key = btn_key + '_disabled'
        disabled_dict = self._slots.get(disabled_key, {})
        if state_name in disabled_dict:
            return disabled_dict[state_name]
        return None

    def _measure_text(self, dw_factory, text):
        fmt = self._ctx.get_text_format(self._subcat, dw_factory=dw_factory, no_wrap=True)
        layout = dw_factory.CreateTextLayout(text, fmt, 500.0, 100.0)
        return float(layout.GetMetrics().width)

    def _get_btn_natural_height(self):
        btn_key = self._get_btn_key()
        slot_dict = self._slots.get(btn_key, {})
        for state_name in ('normal', 'default', 'pressed'):
            slot = slot_dict.get(state_name)
            if slot is not None:
                block = self._ctx.get_block(slot)
                if block.bg_height > 0:
                    return float(block.bg_height)
        return 13.0

    def _get_btn_margin_x(self):
        btn_key = self._get_btn_key()
        slot_dict = self._slots.get(btn_key, {})
        for state_name in ('normal', 'default', 'pressed'):
            slot = slot_dict.get(state_name)
            if slot is not None:
                block = self._ctx.get_block(slot)
                return float(block.margin_left + block.margin_right)
        return 0.0

    def _get_btn_margin_y(self):
        btn_key = self._get_btn_key()
        slot_dict = self._slots.get(btn_key, {})
        for state_name in ('normal', 'default', 'pressed'):
            slot = slot_dict.get(state_name)
            if slot is not None:
                block = self._ctx.get_block(slot)
                return float(block.margin_top + block.margin_bottom)
        return 0.0

    def _layout_tabs(self, dw_factory):
        if not self._pages:
            self._tab_layouts = []
            self._layout_precise = False
            return

        rx, ry, rw, rh = self._rect
        rxf, ryf, rwf, rhf = float(rx), float(ry), float(rw), float(rh)
        min_w = float(TABCTRL_MIN_TAB_WIDTH)
        pad_x = max(float(TABCTRL_TAB_PAD_X), self._get_btn_margin_x())
        pad_y = max(float(TABCTRL_TAB_PAD_Y), self._get_btn_margin_y())

        btn_h = self._get_btn_natural_height()
        btn_h = max(btn_h, float(TABCTRL_BTN_MIN_HEIGHT))

        if dw_factory is not None:
            self._layout_precise = True
            measures = []
            for page in self._pages:
                tw = max(min_w, self._measure_text(dw_factory, page['title']) + pad_x * 2)
                measures.append(tw)
        else:
            self._layout_precise = False
            measures = [max(min_w, len(p['title']) * 10.0 + pad_x * 2) for p in self._pages]

        if self._is_horizontal():
            cur_x = rxf
            self._tab_layouts = []
            for i, page in enumerate(self._pages):
                bw = float(measures[i])
                self._tab_layouts.append((cur_x, ryf, bw, btn_h))
                cur_x += bw
            self._body_rect = (rxf, ryf + btn_h, rwf, rhf - btn_h)
        else:
            btn_w = btn_h
            cur_y = ryf
            self._tab_layouts = []
            for i, page in enumerate(self._pages):
                bh = float(measures[i])
                self._tab_layouts.append((rxf, cur_y, btn_w, bh))
                cur_y += bh
            self._body_rect = (rxf + btn_w, ryf, rwf - btn_w, rhf)

    def draw(self, ctx, client_rect):
        self._flush_page_visibility()
        rx, ry, rw, rh = self._rect

        if not self._has_skin_blocks():
            D2DTabCtrl.draw(self, ctx, client_rect)
            return

        body_key = self._get_body_key()
        body_slots = self._slots.get(body_key, {})

        if self._state == self.DISABLED:
            body_state = 'disabled'
        else:
            body_state = 'normal'

        body_slot = body_slots.get(body_state)
        body_block = (self._ctx.get_block(body_slot)
                      if body_slot is not None else None)

        has_skin = (body_block is not None
                    and body_block.bg_width > 0
                    and body_block.bg_height > 0)

        if not has_skin:
            D2DTabCtrl.draw(self, ctx, client_rect)
            return

        self._ensure_layout(ctx.dw_factory)
        self._layout_page_vboxes()

        rt = ctx.rt
        from ..d2d_render import d2d_draw_block

        bx, by, bw, bh = self._body_rect
        d2d_draw_block(rt, self._ctx.skin_img, body_block,
                       (int(bx), int(by), int(bw), int(bh)),
                       wic_factory=ctx.wic_factory,
                       d2d_cache=self._ctx.cache)

        text_fmt = self._ctx.get_text_format(self._subcat, dw_factory=ctx.dw_factory, no_wrap=True)
        for i, (tx, ty, tw, th) in enumerate(self._tab_layouts):
            state_name = self._get_state_name(i)
            slot = self._get_btn_state_slot(state_name)
            if slot is not None:
                btn_block = self._ctx.get_block(slot)
                if btn_block.bg_width > 0 and btn_block.bg_height > 0:
                    d2d_draw_block(rt, self._ctx.skin_img, btn_block,
                                   (int(tx), int(ty), int(tw), int(th)),
                                   wic_factory=ctx.wic_factory,
                                   d2d_cache=self._ctx.cache)

            text = self._pages[i]['title']
            text_state = self.NORMAL
            if self._pages[i].get('disabled'):
                text_state = self.DISABLED
            elif i == self._selected:
                text_state = self.PRESSED
            elif i == self._hovered:
                text_state = self.HOVER
            text_color = self._ctx.get_text_color(self._subcat, text_state)
            from ..d2d_render import d2d_draw_text
            d2d_draw_text(rt, ctx.dw_factory, text, text_fmt, text_color,
                          tx, ty, tw, th)