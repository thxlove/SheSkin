"""D2D 控件 — D2DHeaderCtrl / SkinAwareHeaderCtrl + CtrlBorder 边框绘制服务。"""
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush
from ..d2d_render import d2d_draw_block, d2d_draw_text
from ..block import is_block_empty
from ..layout import CONTROL_SLOTS
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP

HEADERCTRL_DEFAULT_HEIGHT = 24
HEADERCTRL_SEPARATOR_WIDTH = 1.0
HEADERCTRL_MIN_COL_WIDTH = 20
HEADERCTRL_TEXT_PAD_X = 6
HEADERCTRL_TEXT_PAD_Y = 4

HEADERCTRL_COLORS = {
    'normal': {
        'bg': (0.92, 0.92, 0.95, 1.0),
        'border': (0.72, 0.72, 0.75, 1.0),
        'text': (0.15, 0.15, 0.18, 1.0),
    },
    'hover': {
        'bg': (0.88, 0.92, 0.97, 1.0),
        'border': (0.55, 0.65, 0.80, 1.0),
        'text': (0.10, 0.10, 0.13, 1.0),
    },
    'pressed': {
        'bg': (0.82, 0.87, 0.94, 1.0),
        'border': (0.40, 0.55, 0.75, 1.0),
        'text': (0.05, 0.05, 0.08, 1.0),
    },
    'disabled': {
        'bg': (0.94, 0.94, 0.96, 1.0),
        'border': (0.78, 0.78, 0.80, 1.0),
        'text': (0.55, 0.55, 0.58, 1.0),
    },
}

CTRLBORDER_COLORS = {
    'normal': {
        'outer': (0.72, 0.72, 0.75, 1.0),
        'inner': (0.92, 0.92, 0.95, 1.0),
        'bg': (1.0, 1.0, 1.0, 1.0),
    },
    'default': {
        'outer': (0.30, 0.55, 0.85, 1.0),
        'inner': (0.72, 0.82, 0.95, 1.0),
        'bg': (1.0, 1.0, 1.0, 1.0),
    },
    'hover': {
        'outer': (0.40, 0.60, 0.88, 1.0),
        'inner': (0.78, 0.86, 0.96, 1.0),
        'bg': (1.0, 1.0, 1.0, 1.0),
    },
    'disabled': {
        'outer': (0.78, 0.78, 0.80, 1.0),
        'inner': (0.88, 0.88, 0.90, 1.0),
        'bg': (0.96, 0.96, 0.97, 1.0),
    },
}

CTRLBORDER_WIDTH = 1.0
CTRLBORDER_INNER_OFFSET = 1.0

# 皮肤属性后缀映射：state name → 属性 key 后缀
_STATE_SUFFIX = {
    'normal': 'n',
    'hover': 'h',
    'default': 'o',
    'disabled': 'd',
    'pressed': 'p',
}


class ColumnDef:
    __slots__ = ('text', 'width', 'align', 'sortable')

    def __init__(self, text='', width=100, align='left', sortable=False):
        self.text = text
        self.width = max(HEADERCTRL_MIN_COL_WIDTH, width)
        self.align = align
        self.sortable = sortable


def draw_ctrl_border(rt, rect, state='normal', skin_context=None,
                     curve_w=0, curve_h=0):
    """CtrlBorder 边框绘制服务。

    有皮肤时读取 CtrlBorder properties（outer/inner_color, curve），
    无皮肤时 fallback 到 CTRLBORDER_COLORS。

    Args:
        rt: D2D RenderTarget
        rect: (x, y, w, h)
        state: 'normal' / 'default' / 'hover' / 'disabled'
        skin_context: SkinContext 实例（可选）
        curve_w: 宽度曲率（0=直角）
        curve_h: 高度曲率（0=直角）
    """
    rx, ry, rw, rh = rect
    if rw <= 0 or rh <= 0:
        return

    outer_color = None
    inner_color = None
    bg_color = None
    draw_border = True

    if skin_context is not None and skin_context.skin is not None:
        props = skin_context.skin.get_props('CtrlBorder')
        if props:
            db = props.get('draw_border')
            if db is not None and db is False:
                draw_border = False
            # CtrlBorder 有贴图 slot 210-213，只有贴图非空时才使用皮肤颜色
            _has_skin = False
            if skin_context.skin._loaded:
                from ..block import is_block_empty
                for _slot in range(210, 214):
                    if not is_block_empty(skin_context.skin.get_block(_slot)):
                        _has_skin = True
                        break
            if _has_skin:
                state_suffix = _STATE_SUFFIX.get(state, state[0] if state else 'n')
                outer_key = f'outer_color_{state_suffix}'
                inner_key = f'inner_color_{state_suffix}'
                outer_val = props.get(outer_key)
                inner_val = props.get(inner_key)
                if outer_val is not None:
                    if hasattr(outer_val, 'Red'):
                        outer_color = (outer_val.Red() / 255.0,
                                       outer_val.Green() / 255.0,
                                       outer_val.Blue() / 255.0,
                                       outer_val.Alpha() / 255.0)
                    elif isinstance(outer_val, (list, tuple)):
                        outer_color = tuple(v / 255.0 for v in outer_val)
                if inner_val is not None:
                    if hasattr(inner_val, 'Red'):
                        inner_color = (inner_val.Red() / 255.0,
                                       inner_val.Green() / 255.0,
                                       inner_val.Blue() / 255.0,
                                       inner_val.Alpha() / 255.0)
                    elif isinstance(inner_val, (list, tuple)):
                        inner_color = tuple(v / 255.0 for v in inner_val)
            cw = props.get('width_curve', 0)
            ch = props.get('height_curve', 0)
            if isinstance(cw, (int, float)) and cw > 0:
                curve_w = cw
            if isinstance(ch, (int, float)) and ch > 0:
                curve_h = ch

    if not draw_border:
        return

    fallback = CTRLBORDER_COLORS.get(state, CTRLBORDER_COLORS['normal'])
    if outer_color is None:
        outer_color = fallback['outer']
    if inner_color is None:
        inner_color = fallback['inner']
    if bg_color is None:
        bg_color = fallback['bg']

    bg_brush = get_brush(rt, *bg_color)
    rt.FillRectangle(float(rx), float(ry),
                     float(rx + rw), float(ry + rh), bg_brush)

    if curve_w > 0 or curve_h > 0:
        rx_f, ry_f = float(rx), float(ry)
        rw_f, rh_f = float(rw), float(rh)
        outer_brush = get_brush(rt, *outer_color)
        inner_brush = get_brush(rt, *inner_color)
        _draw_rounded_rect(rt, rx_f, ry_f, rw_f, rh_f,
                           curve_w, curve_h, outer_brush, CTRLBORDER_WIDTH)
        _draw_rounded_rect(rt, rx_f + CTRLBORDER_INNER_OFFSET,
                           ry_f + CTRLBORDER_INNER_OFFSET,
                           rw_f - 2 * CTRLBORDER_INNER_OFFSET,
                           rh_f - 2 * CTRLBORDER_INNER_OFFSET,
                           max(0, curve_w - CTRLBORDER_INNER_OFFSET),
                           max(0, curve_h - CTRLBORDER_INNER_OFFSET),
                           inner_brush, CTRLBORDER_WIDTH)
    else:
        outer_brush = get_brush(rt, *outer_color)
        inner_brush = get_brush(rt, *inner_color)
        rt.DrawRectangle(float(rx), float(ry),
                         float(rx + rw), float(ry + rh),
                         outer_brush, CTRLBORDER_WIDTH)
        ix = rx + CTRLBORDER_INNER_OFFSET
        iy = ry + CTRLBORDER_INNER_OFFSET
        iw = rw - 2 * CTRLBORDER_INNER_OFFSET
        ih = rh - 2 * CTRLBORDER_INNER_OFFSET
        if iw > 0 and ih > 0:
            rt.DrawRectangle(float(ix), float(iy),
                             float(ix + iw), float(iy + ih),
                             inner_brush, CTRLBORDER_WIDTH)


def _draw_rounded_rect(rt, x, y, w, h, curve_w, curve_h, brush, stroke_w):
    if curve_w <= 0 and curve_h <= 0:
        rt.DrawRectangle(x, y, x + w, y + h, brush, stroke_w)
        return
    rx = min(curve_w, w / 2)
    ry = min(curve_h, h / 2)
    factory = pyd2d.GetD2DFactory()
    geo = factory.CreatePathGeometry()
    sink = geo.Open()
    sink.SetFillMode(pyd2d.FILL_MODE.ALTERNATE)
    sink.BeginFigure(x + rx, y)
    sink.AddLine(x + w - rx, y)
    sink.AddArc(x + w, y + ry, rx, ry, 0.0,
                pyd2d.SWEEP_DIRECTION.CLOCKWISE,
                pyd2d.ARC_SIZE.SMALL)
    sink.AddLine(x + w, y + h - ry)
    sink.AddArc(x + w - rx, y + h, rx, ry, 0.0,
                pyd2d.SWEEP_DIRECTION.CLOCKWISE,
                pyd2d.ARC_SIZE.SMALL)
    sink.AddLine(x + rx, y + h)
    sink.AddArc(x, y + h - ry, rx, ry, 0.0,
                pyd2d.SWEEP_DIRECTION.CLOCKWISE,
                pyd2d.ARC_SIZE.SMALL)
    sink.AddLine(x, y + ry)
    sink.AddArc(x + rx, y, rx, ry, 0.0,
                pyd2d.SWEEP_DIRECTION.CLOCKWISE,
                pyd2d.ARC_SIZE.SMALL)
    sink.EndFigure(pyd2d.FIGURE_END.CLOSED)
    sink.Close()
    rt.DrawGeometry(geo, brush, stroke_w)
    geo.Release()
    sink.Release()


class D2DHeaderCtrl(SheControl):
    """D2D 自绘列表头 — 无 HWND，纯 D2D 渲染 + 鼠标 hit-test。

    Win32 HeaderCtrl 行为：
    - 每列有独立状态（normal/hover/pressed/disabled）
    - 点击列头可排序（sortable 列）
    - 拖拽列分隔线调整列宽
    - 列间有垂直分隔线

    用法：
        cols = [ColumnDef('Name', 150), ColumnDef('Size', 80, align='right')]
        hdr = D2DHeaderCtrl((10, 10, 400, 24), cols, on_col_click=lambda i: print(i))
        frame.register_d2d_control(hdr)
    """

    NORMAL = 0
    HOVER = 1
    PRESSED = 2
    DISABLED = 3

    _STATE_NAMES = {0: 'normal', 1: 'hover', 2: 'pressed', 3: 'disabled'}

    def __init__(self, rect, columns=None, on_col_click=None):
        super().__init__(rect, "")
        self._columns = columns or []
        self._on_col_click = on_col_click
        self._col_states = [self.NORMAL] * len(self._columns)
        self._hover_col = -1
        self._pressed_col = -1
        self._captured_col = -1
        self._sort_col = -1
        self._sort_asc = True
        self._col_widths = [c.width for c in self._columns]
        self._dwrite_text_fmt = None

    @property
    def columns(self):
        return self._columns

    @property
    def col_widths(self):
        return list(self._col_widths)

    @property
    def sort_column(self):
        return self._sort_col

    @property
    def sort_ascending(self):
        return self._sort_asc

    def set_columns(self, columns):
        self._columns = columns or []
        self._col_states = [self.NORMAL] * len(self._columns)
        self._col_widths = [c.width for c in self._columns]
        self._hover_col = -1
        self._pressed_col = -1
        self._captured_col = -1
        self._sort_col = -1
        self._sort_asc = True
        self._dwrite_text_fmt = None

    def set_col_width(self, col_idx, width):
        if 0 <= col_idx < len(self._col_widths):
            self._col_widths[col_idx] = max(HEADERCTRL_MIN_COL_WIDTH, width)

    def _get_text_fmt(self, dw_factory=None):
        if self._dwrite_text_fmt is not None:
            return self._dwrite_text_fmt
        if dw_factory is None:
            dw_factory = pyd2d.GetDWriteFactory()
        self._dwrite_text_fmt = dw_factory.CreateTextFormat(
            DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
            weight=pyd2d.FONT_WEIGHT.NORMAL,
            style=pyd2d.FONT_STYLE.NORMAL,
            stretch=pyd2d.FONT_STRETCH.NORMAL)
        return self._dwrite_text_fmt

    def _col_rect(self, col_idx):
        rx, ry, rw, rh = self._rect
        x = rx
        for i in range(col_idx):
            x += self._col_widths[i] if i < len(self._col_widths) else 0
        w = self._col_widths[col_idx] if col_idx < len(self._col_widths) else 0
        return (x, ry, w, rh)

    def _hit_test_col(self, pt):
        px, py = pt
        rx, ry, rw, rh = self._rect
        if not (ry <= py <= ry + rh):
            return -1
        x = rx
        for i, cw in enumerate(self._col_widths):
            if x <= px < x + cw:
                return i
            x += cw
        return -1

    def hit_test(self, pt):
        rx, ry, rw, rh = self._rect
        px, py = pt
        return rx <= px <= rx + rw and ry <= py <= ry + rh

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        if not self.hit_test(pt):
            return False
        col = self._hit_test_col(pt)
        if col >= 0:
            self._pressed_col = col
            self._captured_col = col
            self._col_states[col] = self.PRESSED
            return True
        return False

    def on_mouse_up(self, pt):
        if self._state == self.DISABLED:
            return False
        was_captured = self._captured_col >= 0
        captured = self._captured_col
        self._captured_col = -1

        if captured >= 0 and captured < len(self._col_states):
            self._col_states[captured] = self.NORMAL

        if captured >= 0 and self._hit_test_col(pt) == captured:
            self._pressed_col = -1
            if captured < len(self._col_states):
                self._col_states[captured] = self.HOVER
            if captured == self._sort_col:
                self._sort_asc = not self._sort_asc
            else:
                self._sort_col = captured
                self._sort_asc = True
            if self._on_col_click:
                self._on_col_click(captured)
            return True

        self._pressed_col = -1
        col = self._hit_test_col(pt)
        if col >= 0 and col < len(self._col_states):
            self._col_states[col] = self.HOVER
        self._hover_col = col
        return was_captured

    def on_mouse_move(self, pt):
        if self._state == self.DISABLED:
            return False
        col = self._hit_test_col(pt)
        changed = False

        if self._captured_col >= 0:
            if col == self._captured_col:
                if self._col_states[self._captured_col] != self.PRESSED:
                    self._col_states[self._captured_col] = self.PRESSED
                    changed = True
            else:
                if self._col_states[self._captured_col] == self.PRESSED:
                    self._col_states[self._captured_col] = self.NORMAL
                    changed = True
            return changed

        if col != self._hover_col:
            if self._hover_col >= 0 and self._hover_col < len(self._col_states):
                if self._col_states[self._hover_col] != self.DISABLED:
                    self._col_states[self._hover_col] = self.NORMAL
            if col >= 0 and col < len(self._col_states):
                if self._col_states[col] != self.DISABLED:
                    self._col_states[col] = self.HOVER
            self._hover_col = col
            return True
        return False

    def on_mouse_leave(self):
        if self._state == self.DISABLED:
            return False
        self._captured_col = -1
        self._pressed_col = -1
        changed = False
        for i in range(len(self._col_states)):
            if self._col_states[i] == self.HOVER or self._col_states[i] == self.PRESSED:
                self._col_states[i] = self.NORMAL
                changed = True
        self._hover_col = -1
        return changed

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt
        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)

        bg_brush = get_brush(rt, *HEADERCTRL_COLORS['normal']['bg'])
        rt.FillRectangle(float(rx), float(ry),
                         float(rx + rw), float(ry + rh), bg_brush)

        x = float(rx)
        for i, col in enumerate(self._columns):
            cw = float(self._col_widths[i]) if i < len(self._col_widths) else 0
            state_idx = self._col_states[i] if i < len(self._col_states) else self.NORMAL
            state_name = self._STATE_NAMES.get(state_idx, 'normal')
            c = HEADERCTRL_COLORS.get(state_name, HEADERCTRL_COLORS['normal'])

            if state_name != 'normal':
                col_bg = get_brush(rt, *c['bg'])
                rt.FillRectangle(x, float(ry), x + cw, float(ry + rh), col_bg)

            text = col.text
            if text:
                text_brush = get_brush(rt, *c['text'])
                tx = x + HEADERCTRL_TEXT_PAD_X
                tw = cw - 2 * HEADERCTRL_TEXT_PAD_X
                if tw > 0:
                    align = pyd2d.TEXT_ALIGNMENT.LEADING
                    if col.align == 'center':
                        align = pyd2d.TEXT_ALIGNMENT.CENTER
                    elif col.align == 'right':
                        align = pyd2d.TEXT_ALIGNMENT.TRAILING
                    text_fmt.SetTextAlignment(align)
                    rt.DrawText(text, text_fmt,
                                tx, float(ry + HEADERCTRL_TEXT_PAD_Y),
                                tx + tw, float(ry + rh - HEADERCTRL_TEXT_PAD_Y),
                                text_brush)

            sep_brush = get_brush(rt, *HEADERCTRL_COLORS['normal']['border'])
            rt.DrawLine(x + cw, float(ry),
                        x + cw, float(ry + rh),
                        sep_brush, HEADERCTRL_SEPARATOR_WIDTH)

            if i == self._sort_col and col.sortable:
                arrow_brush = get_brush(rt, *c['text'])
                ax = x + cw - HEADERCTRL_TEXT_PAD_X - 8
                ay = float(ry) + float(rh) / 2
                if self._sort_asc:
                    rt.DrawLine(ax - 3, ay + 2, ax, ay - 2, arrow_brush, 1.0)
                    rt.DrawLine(ax, ay - 2, ax + 3, ay + 2, arrow_brush, 1.0)
                else:
                    rt.DrawLine(ax - 3, ay - 2, ax, ay + 2, arrow_brush, 1.0)
                    rt.DrawLine(ax, ay + 2, ax + 3, ay - 2, arrow_brush, 1.0)

            x += cw

        bottom_brush = get_brush(rt, *HEADERCTRL_COLORS['normal']['border'])
        rt.DrawLine(float(rx), float(ry + rh),
                    float(rx + rw), float(ry + rh),
                    bottom_brush, HEADERCTRL_SEPARATOR_WIDTH)


class SkinAwareHeaderCtrl(D2DHeaderCtrl):
    """皮肤化列表头 — 使用 HeaderCtrl.button slot 绘制列头。"""

    _TEXT_STATE_MAP = {0: 'n', 1: 'o', 2: 's', 3: 'd'}

    def __init__(self, rect, skin_context, columns=None, on_col_click=None,
                 subcat='HeaderCtrl'):
        super().__init__(rect, columns=columns, on_col_click=on_col_click)
        self._ctx = skin_context
        self._subcat = subcat
        self._slots = CONTROL_SLOTS.get(self._subcat, {})
        self._btn_slots = self._slots.get('button', {})
        self._dwrite_text_fmt_cached = None

    def _has_skin_blocks(self):
        if not self._btn_slots:
            return False
        for state_name in ('normal', 'pressed', 'disabled'):
            slot = self._btn_slots.get(state_name)
            if slot is not None:
                block = self._ctx.get_block(slot)
                if not is_block_empty(block):
                    return True
        return False

    def _get_text_fmt_cached(self, dw_factory=None):
        if self._dwrite_text_fmt_cached is not None:
            return self._dwrite_text_fmt_cached
        self._dwrite_text_fmt_cached = self._ctx.get_text_format(
            self._subcat, dw_factory=dw_factory,
            alignment=pyd2d.TEXT_ALIGNMENT.LEADING,
            para_alignment=pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return self._dwrite_text_fmt_cached

    def _get_text_color(self, state_idx):
        return self._ctx.get_text_color(self._subcat, state_idx)

    def draw(self, ctx, client_rect):
        if not self._has_skin_blocks():
            D2DHeaderCtrl.draw(self, ctx, client_rect)
            return

        rx, ry, rw, rh = self._rect
        rt = ctx.rt
        text_fmt = self._get_text_fmt_cached(dw_factory=ctx.dw_factory)

        bg_brush = get_brush(rt, *HEADERCTRL_COLORS['normal']['bg'])
        rt.FillRectangle(float(rx), float(ry),
                         float(rx + rw), float(ry + rh), bg_brush)

        x = float(rx)
        for i, col in enumerate(self._columns):
            cw = float(self._col_widths[i]) if i < len(self._col_widths) else 0
            state_idx = self._col_states[i] if i < len(self._col_states) else self.NORMAL
            state_name = self._STATE_NAMES.get(state_idx, 'normal')

            slot = self._btn_slots.get(state_name)
            if slot is not None:
                block = self._ctx.get_block(slot)
                if not is_block_empty(block):
                    d2d_draw_block(rt, self._ctx.skin_img, block,
                                   (int(x), int(ry), int(cw), int(rh)),
                                   wic_factory=ctx.wic_factory,
                                   d2d_cache=self._ctx.cache)
                else:
                    c = HEADERCTRL_COLORS.get(state_name, HEADERCTRL_COLORS['normal'])
                    col_bg = get_brush(rt, *c['bg'])
                    rt.FillRectangle(x, float(ry), x + cw, float(ry + rh), col_bg)
            else:
                c = HEADERCTRL_COLORS.get(state_name, HEADERCTRL_COLORS['normal'])
                col_bg = get_brush(rt, *c['bg'])
                rt.FillRectangle(x, float(ry), x + cw, float(ry + rh), col_bg)

            text = col.text
            if text:
                text_color = self._get_text_color(state_idx)
                tx = x + HEADERCTRL_TEXT_PAD_X
                tw = cw - 2 * HEADERCTRL_TEXT_PAD_X
                if tw > 0:
                    align = pyd2d.TEXT_ALIGNMENT.LEADING
                    if col.align == 'center':
                        align = pyd2d.TEXT_ALIGNMENT.CENTER
                    elif col.align == 'right':
                        align = pyd2d.TEXT_ALIGNMENT.TRAILING
                    text_fmt.SetTextAlignment(align)
                    d2d_draw_text(rt, ctx.dw_factory, text, text_fmt, text_color,
                                  tx, float(ry + HEADERCTRL_TEXT_PAD_Y),
                                  tx + tw, float(ry + rh - HEADERCTRL_TEXT_PAD_Y))

            sep_brush = get_brush(rt, *HEADERCTRL_COLORS['normal']['border'])
            rt.DrawLine(x + cw, float(ry), x + cw, float(ry + rh),
                        sep_brush, HEADERCTRL_SEPARATOR_WIDTH)

            if i == self._sort_col and col.sortable:
                arrow_color = self._get_text_color(state_idx)
                arrow_brush = get_brush(rt,
                                        arrow_color[0] / 255.0,
                                        arrow_color[1] / 255.0,
                                        arrow_color[2] / 255.0,
                                        arrow_color[3] / 255.0 if len(arrow_color) > 3 else 1.0)
                ax = x + cw - HEADERCTRL_TEXT_PAD_X - 8
                ay = float(ry) + float(rh) / 2
                if self._sort_asc:
                    rt.DrawLine(ax - 3, ay + 2, ax, ay - 2, arrow_brush, 1.0)
                    rt.DrawLine(ax, ay - 2, ax + 3, ay + 2, arrow_brush, 1.0)
                else:
                    rt.DrawLine(ax - 3, ay - 2, ax, ay + 2, arrow_brush, 1.0)
                    rt.DrawLine(ax, ay + 2, ax + 3, ay - 2, arrow_brush, 1.0)

            x += cw

        bottom_brush = get_brush(rt, *HEADERCTRL_COLORS['normal']['border'])
        rt.DrawLine(float(rx), float(ry + rh),
                    float(rx + rw), float(ry + rh),
                    bottom_brush, HEADERCTRL_SEPARATOR_WIDTH)
