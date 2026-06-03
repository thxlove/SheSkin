"""D2D 控件 — D2DStatusBar / SkinAwareStatusBar。"""
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush
from ..config import (
    STATUSBAR_HEIGHT, STATUSBAR_ITEM_PAD_X, STATUSBAR_ITEM_PAD_Y,
    STATUSBAR_SEPARATOR_WIDTH, STATUSBAR_COLORS,
    DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
)


class D2DStatusBar(SheControl):
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

    def __init__(self, rect, items=None):
        super().__init__(rect, "")
        self._items = []
        if items:
            for item in items:
                if isinstance(item, str):
                    self._items.append({'text': item, 'width': None})
                else:
                    self._items.append(item)

    def add_item(self, text, width=None):
        self._items.append({'text': text, 'width': width})

    def set_items(self, items):
        self._items = []
        for item in items:
            if isinstance(item, str):
                self._items.append({'text': item, 'width': None})
            else:
                self._items.append(item)

    @property
    def items(self):
        return self._items

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

    def _layout_items(self, sep_width=None):
        if sep_width is None:
            sep_width = STATUSBAR_SEPARATOR_WIDTH
        rx, ry, rw, rh = self._rect
        if not self._items:
            return []

        auto_items = [(i, it) for i, it in enumerate(self._items)
                      if it.get('width') is None]
        fixed_width = sum(it.get('width', 0) for it in self._items
                          if it.get('width') is not None)
        sep_count = max(0, len(self._items) - 1)
        sep_total = sep_count * sep_width
        pad_total = 2 * STATUSBAR_ITEM_PAD_X

        available = float(rw) - float(fixed_width) - float(sep_total) - float(pad_total)
        auto_w = max(0.0, available / max(1, len(auto_items)))

        layouts = []
        cur_x = float(rx) + float(STATUSBAR_ITEM_PAD_X)
        for i, item in enumerate(self._items):
            w = float(item.get('width') or auto_w)
            layouts.append((cur_x, float(ry), w, float(rh)))
            cur_x += w
            if i < len(self._items) - 1:
                cur_x += float(sep_width)
        return layouts

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect

        state_name = {self.NORMAL: 'normal', self.DISABLED: 'disabled'}.get(
            self._state, 'normal')
        c = STATUSBAR_COLORS[state_name]
        rt = ctx.rt

        bg_brush = get_brush(rt, *c['bg'])
        rt.FillRectangle(
            float(rx), float(ry), float(rx + rw), float(ry + rh), bg_brush)

        item_layouts = self._layout_items()
        sep_brush = get_brush(rt, *c['separator'])
        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)

        for i, (ix, iy, iw, ih) in enumerate(item_layouts):
            item = self._items[i]
            item_bg_brush = get_brush(rt, *c['item_bg'])
            item_border_brush = get_brush(rt, *c['item_border'])
            rt.FillRectangle(ix, iy + 1.0, ix + iw, iy + ih - 1.0, item_bg_brush)
            rt.DrawRectangle(ix, iy + 1.0, ix + iw, iy + ih - 1.0,
                             item_border_brush, 1.0)

            if i < len(self._items) - 1:
                sx = ix + iw
                rt.FillRectangle(sx, iy + 4.0, sx + float(STATUSBAR_SEPARATOR_WIDTH),
                                 iy + ih - 4.0, sep_brush)

            text = item.get('text', '')
            if text:
                text_brush = get_brush(rt, *c['text'])
                text_w = max(1.0, iw - STATUSBAR_ITEM_PAD_X * 2)
                text_h = max(1.0, ih - STATUSBAR_ITEM_PAD_Y * 2)
                layout = ctx.dw_factory.CreateTextLayout(
                    text, text_fmt, text_w, text_h)
                layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                metrics = layout.GetMetrics()
                tx = ix + float(STATUSBAR_ITEM_PAD_X)
                ty = iy + (ih - metrics.height) / 2.0
                rt.DrawTextLayout(tx, ty, layout, text_brush)


class SkinAwareStatusBar(D2DStatusBar):
    def __init__(self, rect, skin_context, items=None, subcat='StatusBar'):
        super().__init__(rect, items=items)
        self._ctx = skin_context
        self._subcat = subcat
        from ..layout import CONTROL_SLOTS
        defaults = CONTROL_SLOTS.get(self._subcat, {})
        self._bg_slot = defaults.get('bg', {}).get('normal')
        self._item_slots = defaults.get('item', {})
        self._sep_slot = defaults.get('separator', {}).get('normal')
        self._sep_block = None
        self._sep_width = STATUSBAR_SEPARATOR_WIDTH
        self._sep_height = 0
        self._min_sep_draw_height = 0

    def _resolve_min_sep_height(self, ctx):
        """根据状态栏字体高度确定分割线最小绘制高度。"""
        if self._min_sep_draw_height > 0:
            return
        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
        if text_fmt is not None and ctx.dw_factory is not None:
            layout = ctx.dw_factory.CreateTextLayout("M", text_fmt, 100.0, 100.0)
            metrics = layout.GetMetrics()
            self._min_sep_draw_height = int(metrics.height - 1) if metrics else 0
        if self._min_sep_draw_height <= 0:
            self._min_sep_draw_height = int(DEFAULT_FONT_SIZE_DIP - 1)

    def _resolve_sep_dimensions(self):
        if self._sep_slot is not None:
            self._sep_block = self._ctx.get_block(self._sep_slot)
        else:
            self._sep_block = None
        if (self._sep_block is not None
                and self._sep_block.bg_width > 0
                and self._sep_block.bg_height > 0):
            self._sep_width = self._sep_block.bg_width
            # 九宫格截取后的实际绘制高度 = 目标高度 - margin_top - margin_bottom
            mt = self._sep_block.margin_top
            mb = self._sep_block.margin_bottom
            inner_h = self._sep_block.bg_height - mt - mb
            if 0 < inner_h < self._min_sep_draw_height:
                # 分割线太细，拉伸目标高度使中间区域达到最小高度
                self._sep_height = self._min_sep_draw_height + mt + mb
            else:
                self._sep_height = self._sep_block.bg_height
        else:
            self._sep_width = STATUSBAR_SEPARATOR_WIDTH
            self._sep_height = 0

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect

        bg_block = (self._ctx.get_block(self._bg_slot)
                    if self._bg_slot is not None else None)
        has_bg = (bg_block is not None
                  and bg_block.bg_width > 0
                  and bg_block.bg_height > 0)

        if not has_bg:
            D2DStatusBar.draw(self, ctx, client_rect)
            return

        rt = ctx.rt
        from ..d2d_render import d2d_draw_block

        self._resolve_min_sep_height(ctx)
        d2d_draw_block(rt, self._ctx.skin_img, bg_block,
                       (rx, ry, rw, rh),
                       wic_factory=ctx.wic_factory,
                       d2d_cache=self._ctx.cache)

        self._resolve_sep_dimensions()
        item_layouts = self._layout_items(self._sep_width)
        state_name = {self.NORMAL: 'normal', self.DISABLED: 'disabled'}.get(
            self._state, 'normal')

        has_sep = (self._sep_block is not None and self._sep_height > 0)

        c = STATUSBAR_COLORS[state_name]
        text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)

        for i, (ix, iy, iw, ih) in enumerate(item_layouts):
            item_slot = self._item_slots.get(state_name)
            item_block = (self._ctx.get_block(item_slot)
                          if item_slot is not None else None)
            if item_block is not None and item_block.bg_width > 0:
                d2d_draw_block(rt, self._ctx.skin_img, item_block,
                               (int(ix), int(iy), int(iw), int(ih)),
                               wic_factory=ctx.wic_factory,
                               d2d_cache=self._ctx.cache)

            if i < len(self._items) - 1:
                sx = ix + iw
                if has_sep:
                    sy = iy + (ih - self._sep_height) / 2.0
                    d2d_draw_block(rt, self._ctx.skin_img, self._sep_block,
                                   (int(sx), int(sy),
                                    int(self._sep_width), int(self._sep_height)),
                                   wic_factory=ctx.wic_factory,
                                   d2d_cache=self._ctx.cache)
                else:
                    sep_brush = get_brush(rt, *c['separator'])
                    rt.FillRectangle(
                        sx, iy + 4.0,
                        sx + float(STATUSBAR_SEPARATOR_WIDTH),
                        iy + ih - 4.0, sep_brush)

            text = self._items[i].get('text', '')
            if text:
                text_brush = get_brush(rt, *c['text'])
                text_w = max(1.0, iw - STATUSBAR_ITEM_PAD_X * 2)
                text_h = max(1.0, ih - STATUSBAR_ITEM_PAD_Y * 2)
                layout = ctx.dw_factory.CreateTextLayout(
                    text, text_fmt, text_w, text_h)
                layout.SetTrimming(pyd2d.TRIMMING_GRANULARITY.CHARACTER)
                metrics = layout.GetMetrics()
                tx = ix + float(STATUSBAR_ITEM_PAD_X)
                ty = iy + (ih - metrics.height) / 2.0
                rt.DrawTextLayout(tx, ty, layout, text_brush)