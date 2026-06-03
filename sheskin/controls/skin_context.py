import wx
import pyd2d
from ..block import block_from_raw, is_block_empty
from ..d2d_render import d2d_draw_block, d2d_draw_text, D2DBlockCache
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP


class SkinContext:
    def __init__(self, skin, d2d_cache=None):
        self.skin = skin
        self.skin_img = skin.skin_img if skin._loaded else None
        self._props = {}
        self._d2d_cache = d2d_cache or D2DBlockCache()

    @property
    def cache(self):
        return self._d2d_cache

    def get_block(self, slot):
        return self.skin.get_block(slot)

    def get_text_color(self, subcat_name, state_idx):
        if state_idx in self._props.get((subcat_name, 'text_color'), {}):
            return self._props[(subcat_name, 'text_color')][state_idx]

        props = self.skin.get_props(subcat_name)
        color_keys = {
            0: 'text_color_n',
            1: 'text_color_h',
            2: 'text_color_s',
            3: 'text_color_d',
        }
        key = color_keys.get(state_idx, 'text_color_n')

        if key in props and isinstance(props[key], wx.Colour):
            c = props[key]
            color = (c.Red(), c.Green(), c.Blue(), c.Alpha())
        else:
            color = (0, 0, 0, 255)

        self._props.setdefault((subcat_name, 'text_color'), {})[state_idx] = color
        return color

    def get_font_height(self, subcat_name):
        cache_key = (subcat_name, 'font_height')
        if cache_key in self._props:
            return self._props[cache_key]

        font_info = self.get_font_info(subcat_name)
        val = font_info.get('height', -9) if font_info else -9
        self._props[cache_key] = val
        return val

    def get_font_info(self, subcat_name):
        cache_key = (subcat_name, 'font_info')
        if cache_key in self._props:
            return self._props[cache_key]
        props = self.skin.get_props(subcat_name)
        font_info = props.get('font')
        if not isinstance(font_info, dict):
            font_info = None
        self._props[cache_key] = font_info
        return font_info

    def get_text_offset(self, subcat_name):
        cache_key = (subcat_name, 'text_offset')
        if cache_key in self._props:
            return self._props[cache_key]
        props = self.skin.get_props(subcat_name)
        ox = props.get('text_offset_s_x', 0)
        oy = props.get('text_offset_s_y', 0)
        offset = (ox, oy)
        self._props[cache_key] = offset
        return offset

    def get_text_format(self, subcat_name, dw_factory=None,
                        alignment=pyd2d.TEXT_ALIGNMENT.CENTER,
                        para_alignment=pyd2d.PARAGRAPH_ALIGNMENT.CENTER,
                        no_wrap=False):
        cache_key = (subcat_name, 'text_format', no_wrap)
        if cache_key in self._props:
            return self._props[cache_key]
        if dw_factory is None:
            dw_factory = pyd2d.GetDWriteFactory()
        font_info = self.get_font_info(subcat_name)
        if font_info:
            face = font_info.get('face_name', DEFAULT_FONT_FAMILY)
            height = font_info.get('height', -9) * -1.0
            weight = font_info.get('weight', pyd2d.FONT_WEIGHT.NORMAL)
            italic = font_info.get('italic', False)
        else:
            face = DEFAULT_FONT_FAMILY
            height = DEFAULT_FONT_SIZE_DIP
            weight = pyd2d.FONT_WEIGHT.NORMAL
            italic = False
        fmt = dw_factory.CreateTextFormat(
            face, float(height),
            weight=weight,
            style=pyd2d.FONT_STYLE.ITALIC if italic else pyd2d.FONT_STYLE.NORMAL,
            stretch=pyd2d.FONT_STRETCH.NORMAL)
        fmt.SetTextAlignment(alignment)
        fmt.SetParagraphAlignment(para_alignment)
        if no_wrap:
            fmt.SetWordWrapping(pyd2d.WORD_WRAPPING.NO_WRAP)
        self._props[cache_key] = fmt
        return fmt

    def draw_control_block(self, rt, slot, rect, wic_factory=None):
        block = self.get_block(slot)
        if is_block_empty(block):
            return False
        d2d_draw_block(rt, self.skin_img, block, rect,
                      wic_factory=wic_factory,
                      d2d_cache=self._d2d_cache)
        return True

    def draw_control_text(self, rt, dw_factory, text, text_format,
                          subcat_name, state_idx, x, y, w, h):
        color = self.get_text_color(subcat_name, state_idx)
        d2d_draw_text(rt, dw_factory, text, text_format, color, x, y, w, h)