import wx
import numpy as np
import ctypes

import pyd2d
from .brush_cache import get_brush
from .layout import CONTROL_SLOTS, DEFAULTS
from .block import is_block_empty
from .d2d_render import (d2d_draw_block, _wx_colour_to_rgba)
from .config import DEFAULT_FONT_FAMILY, PT_TO_DIP


class SheTitleBar:
    def __init__(self, skin, window_type='NormalWindow'):
        self.skin = skin
        self.window_type = window_type
        self._hover_btn = None
        self._pressed_btn = None
        self._d2d_text_fmt = None
        self._d2d_fmt_key = None
        self._d2d_title_layout = None
        self._d2d_title_layout_key = None

        self._ctx_rect = (0, 0, 0, 0)
        self._ctx_state = 'active'
        self._ctx_has_max = True
        self._ctx_has_min = True
        self._ctx_has_help = False
        self._ctx_is_maximized = False
        self._disabled_btns = set()

    def sync_context(self, rect, state_name, has_max, has_min, has_help, is_maximized=False):
        self._ctx_rect = rect
        self._ctx_state = state_name
        self._ctx_has_max = has_max
        self._ctx_has_min = has_min
        self._ctx_has_help = has_help
        self._ctx_is_maximized = is_maximized

    def _layout(self, rect, state_name, has_max, has_min, has_help, is_maximized=False):
        slots = CONTROL_SLOTS.get(self.window_type)
        if not slots:
            return None
        props = self.skin.get_props(slots['subcat'])
        dims = self.skin.get_border_dims(self.window_type, state_name)
        if not dims:
            return None

        rx, ry, rw, rh = rect
        title_h = dims['title_h']
        D = DEFAULTS
        btn_size = D['btn_size']
        btn_gap = D['btn_gap']

        close_slot = slots.get('close')
        if close_slot is None:
            return None

        close_b = self.skin.get_block(close_slot['normal'])
        close_w = close_b.bg_width if not is_block_empty(close_b) and close_b.bg_width > 0 else btn_size
        close_h = close_b.bg_height if not is_block_empty(close_b) and close_b.bg_height > 0 else btn_size

        cby = props.get('close_btn_y')
        btn_y = ry + cby if cby else ry + (title_h - close_h) // 2
        cbx = props.get('close_btn_x')
        close_x = rx + rw + cbx if cbx is not None else rx + rw - close_w - 2

        disabled = set()
        buttons = {'close': {'slots': close_slot, 'rect': (close_x, btn_y, close_w, close_h)}}
        next_x = close_x

        if slots.get('max') is not None or slots.get('restore') is not None:
            max_slot_key = 'restore' if is_maximized else 'max'
            max_slot = slots.get(max_slot_key)
            if max_slot is None:
                max_slot_key = 'max'
                max_slot = slots.get('max')
            if max_slot is not None:
                max_b = self.skin.get_block(max_slot['normal'])
                max_w = max_b.bg_width if not is_block_empty(max_b) and max_b.bg_width > 0 else btn_size
                max_h = max_b.bg_height if not is_block_empty(max_b) and max_b.bg_height > 0 else close_h
                mbx = props.get('max_btn_x')
                max_x = rx + rw + mbx if mbx is not None else next_x - max_w - btn_gap
                buttons['max'] = {'slots': max_slot, 'rect': (max_x, btn_y, max_w, max_h)}
                next_x = max_x
            if not has_max:
                disabled.add('max')

        if slots.get('min') is not None:
            min_slot = slots['min']
            min_b = self.skin.get_block(min_slot['normal'])
            min_w = min_b.bg_width if not is_block_empty(min_b) and min_b.bg_width > 0 else btn_size
            min_h = min_b.bg_height if not is_block_empty(min_b) and min_b.bg_height > 0 else close_h
            mnx = props.get('min_btn_x')
            min_x = rx + rw + mnx if mnx is not None else next_x - min_w - btn_gap
            buttons['min'] = {'slots': min_slot, 'rect': (min_x, btn_y, min_w, min_h)}
            next_x = min_x
            if not has_min:
                disabled.add('min')

        if has_help and slots.get('help') is not None:
            help_slot = slots['help']
            help_b = self.skin.get_block(help_slot['normal'])
            help_w = help_b.bg_width if not is_block_empty(help_b) and help_b.bg_width > 0 else btn_size
            help_h = help_b.bg_height if not is_block_empty(help_b) and help_b.bg_height > 0 else close_h
            hbx = props.get('help_btn_x')
            help_x = rx + rw + hbx if hbx is not None else next_x - help_w - btn_gap
            buttons['help'] = {'slots': help_slot, 'rect': (help_x, btn_y, help_w, help_h)}

        self._disabled_btns = disabled
        return {'buttons': buttons, 'title_h': title_h, 'props': props, 'dims': dims}

    def _btn_state_name(self, name):
        if name in self._disabled_btns:
            return 'disabled'
        if self._pressed_btn == name:
            return 'pressed'
        if self._hover_btn == name:
            return 'hover'
        return 'normal'

    def draw_d2d(self, ctx, rect, state_name='active', title='', icon=None,
                 has_icon=True, has_max=True, has_min=True, has_help=False,
                 is_maximized=False):
        info = self._layout(rect, state_name, has_max, has_min, has_help, is_maximized)
        if not info:
            return

        rt = ctx.rt
        dw_factory = ctx.dw_factory
        d2d_cache = ctx.d2d_cache
        wic_factory = ctx.wic_factory

        props, dims = info['props'], info['dims']
        title_h = info['title_h']
        rx, ry, rw, rh = rect
        D = DEFAULTS

        tc_key = 'text_color_n' if state_name == 'active' else 'text_color_d'
        tc = props.get(tc_key)
        if tc:
            text_color = _wx_colour_to_rgba(tc)
        else:
            text_color = tuple(D[tc_key])

        font_info = props.get('font')
        if font_info and isinstance(font_info, dict):
            font_size = max(6, -font_info.get('height', D['font_height']))
        else:
            font_size = max(6, -D['font_height'])

        font_name = DEFAULT_FONT_FAMILY
        if font_info and isinstance(font_info, dict) and font_info.get('name'):
            font_name = font_info['name']

        d2d_font_size = float(font_size) * PT_TO_DIP
        fmt_key = (font_name, d2d_font_size)
        if self._d2d_fmt_key != fmt_key:
            self._d2d_text_fmt = dw_factory.CreateTextFormat(font_name, d2d_font_size,
                                                      pyd2d.FONT_WEIGHT.NORMAL,
                                                      pyd2d.FONT_STYLE.NORMAL,
                                                      pyd2d.FONT_STRETCH.NORMAL)
            self._d2d_fmt_key = fmt_key
            self._d2d_title_layout_key = None
        text_fmt = self._d2d_text_fmt

        icon_w = props.get('icon_w') or D['icon_w']
        icon_h = props.get('icon_h') or D['icon_h']
        if has_icon:
            ix = rx + (props.get('icon_x') or D['icon_pad'])
            iy = ry + props.get('icon_y', (title_h - icon_h) // 2)
            if icon:
                _wx_icon_to_d2d_and_draw(rt, dw_factory, icon, ix, iy, icon_w, icon_h)
            auto_text_x = int(ix + icon_w + D['icon_text_gap'])
        else:
            auto_text_x = rx + dims['border_left'] + D['icon_pad']

        if title:
            text_fixed = props.get('text_fixed', 0)
            text_area1_x = props.get('text_area1_x', 0)
            text_area1_y = props.get('text_area1_y', 0)
            text_area2_x = props.get('text_area2_x', 0)
            text_align = props.get('text_align', 0)

            if text_fixed and text_area1_x:
                text_x = float(rx + text_area1_x)
            else:
                text_x = float(auto_text_x)

            if text_align and text_area2_x:
                if text_fixed:
                    area_w = text_area2_x - text_area1_x
                else:
                    area_w = (rx + text_area2_x) - text_x
                if area_w <= 0:
                    area_w = float(rw - (text_x - rx))
            else:
                area_w = float(rw - (text_x - rx))

            align_map = {
                0: pyd2d.TEXT_ALIGNMENT.LEADING,
                1: pyd2d.TEXT_ALIGNMENT.CENTER,
                2: pyd2d.TEXT_ALIGNMENT.TRAILING,
            }
            text_fmt.SetTextAlignment(align_map.get(text_align, pyd2d.TEXT_ALIGNMENT.LEADING))

            if text_fixed and text_area1_y:
                text_fmt.SetParagraphAlignment(pyd2d.PARAGRAPH_ALIGNMENT.NEAR)
                layout_h = float(title_h - text_area1_y)
                text_y = float(ry + text_area1_y)
            else:
                text_fmt.SetParagraphAlignment(pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
                layout_h = float(title_h)
                text_y = float(ry)

            layout_key = (
                title, area_w, layout_h,
                text_align, text_fixed, text_area1_y)

            if area_w > 0 and layout_h > 0:
                if self._d2d_title_layout_key != layout_key:
                    self._d2d_title_layout = dw_factory.CreateTextLayout(
                        title, text_fmt, float(area_w), layout_h)
                    self._d2d_title_layout_key = layout_key
                layout = self._d2d_title_layout

                brush = get_brush(rt,
                    text_color[0] / 255.0,
                    text_color[1] / 255.0,
                    text_color[2] / 255.0,
                    text_color[3] / 255.0 if len(text_color) > 3 else 1.0)
                rt.DrawTextLayout(text_x, text_y, layout, brush)

        for btn_name, btn_info in info['buttons'].items():
            state = self._btn_state_name(btn_name)
            slot = btn_info['slots'][state]
            block = self.skin.get_block(slot)
            d2d_draw_block(rt, self.skin.skin_img, block,
                          btn_info['rect'], d2d_cache=d2d_cache)

    def hit_test(self, pos, rect=None, state_name=None, has_max=None,
                 has_min=None, has_help=False, is_maximized=None):
        if rect is None:
            rect, state_name = self._ctx_rect, self._ctx_state
            has_max, has_min = self._ctx_has_max, self._ctx_has_min
            has_help = self._ctx_has_help
            is_maximized = self._ctx_is_maximized
        elif state_name is None:
            state_name = 'active'
        if has_max is None:
            has_max = True
        if has_min is None:
            has_min = True
        if is_maximized is None:
            is_maximized = False

        info = self._layout(rect, state_name, has_max, has_min, has_help, is_maximized)
        if not info:
            return None
        px, py = pos
        rx, ry = rect[0], rect[1]
        for btn_name, btn_info in info['buttons'].items():
            if btn_name in self._disabled_btns:
                continue
            bx, by, bw, bh = btn_info['rect']
            if bx <= px <= bx + bw and by <= py <= by + bh:
                return btn_name
        if ry <= py <= ry + info['title_h']:
            return 'titlebar'
        return None

    def get_nchittest_code(self, pt):
        """返回 WM_NCHITTEST 所需的 HT 代码名称。None 表示不在标题栏区域。"""
        return self.hit_test(pt)

    def set_hover(self, btn):
        self._hover_btn = btn

    def set_pressed(self, btn):
        self._pressed_btn = btn

    def reset_state(self):
        self._hover_btn = None
        self._pressed_btn = None

    def on_mouse_down(self, pt, rect=None, state_name=None, has_max=None,
                      has_min=None, has_help=False, is_maximized=None):
        if rect is None:
            rect = self._ctx_rect
            state_name = self._ctx_state
            has_max = self._ctx_has_max
            has_min = self._ctx_has_min
            has_help = self._ctx_has_help
            is_maximized = self._ctx_is_maximized
        elif state_name is None:
            state_name = 'active'
        if has_max is None:
            has_max = True
        if has_min is None:
            has_min = True
        if is_maximized is None:
            is_maximized = False

        btn = self.hit_test(pt, rect, state_name, has_max, has_min, has_help, is_maximized)
        if btn and btn != 'titlebar':
            self._pressed_btn = btn
            self._hover_btn = None
            return True
        return False

    def on_mouse_up(self, pt, rect=None, state_name=None, has_max=None,
                    has_min=None, has_help=False, is_maximized=None):
        if rect is None:
            rect = self._ctx_rect
            state_name = self._ctx_state
            has_max = self._ctx_has_max
            has_min = self._ctx_has_min
            has_help = self._ctx_has_help
            is_maximized = self._ctx_is_maximized
        elif state_name is None:
            state_name = 'active'
        if has_max is None:
            has_max = True
        if has_min is None:
            has_min = True

        had_pressed = self._pressed_btn is not None
        self._pressed_btn = None
        self._hover_btn = None
        return had_pressed

    def on_mouse_move(self, pt, rect=None, state_name=None, has_max=None,
                      has_min=None, has_help=False, is_maximized=None):
        if rect is None:
            rect = self._ctx_rect
            state_name = self._ctx_state
            has_max = self._ctx_has_max
            has_min = self._ctx_has_min
            has_help = self._ctx_has_help
            is_maximized = self._ctx_is_maximized
        elif state_name is None:
            state_name = 'active'
        if has_max is None:
            has_max = True
        if has_min is None:
            has_min = True
        if is_maximized is None:
            is_maximized = False

        btn = self.hit_test(pt, rect, state_name, has_max, has_min, has_help, is_maximized)
        old = self._hover_btn
        if btn and btn != 'titlebar':
            if btn != old:
                self._hover_btn = btn
                return True
            return False
        else:
            if self._hover_btn is not None:
                self._hover_btn = None
                return True
            return False

    def on_mouse_leave(self):
        had = self._hover_btn is not None
        self._hover_btn = None
        return had


def _wx_icon_to_d2d_and_draw(rt, dw_factory, icon, ix, iy, icon_w, icon_h):
    img = icon.ConvertToImage()
    img_w, img_h = img.GetWidth(), img.GetHeight()

    if img_w <= 0 or img_h <= 0:
        return

    from .d2d_render import _wx_image_to_d2d_bitmap
    wic_factory = pyd2d.GetWICFactory()
    d2d_bmp = _wx_image_to_d2d_bitmap(rt, img, wic_factory)

    rt.DrawBitmap(d2d_bmp,
                  float(ix), float(iy),
                  float(ix + icon_w), float(iy + icon_h),
                  srcRect=(0.0, 0.0, float(img_w), float(img_h)))
