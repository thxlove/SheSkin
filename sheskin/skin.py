import os
import wx
from .skin_data import get_skin_data, _SKINS_DIR
from .block import block_from_raw, is_block_empty
from .layout import CONTROL_SLOTS
from .config import DEFAULT_TITLE_HEIGHT, DEFAULT_BORDER_WIDTH


class SheSkin:
    """从 skin_data 加载皮肤资源。"""

    def __init__(self, skin_name):
        self._skin_name = skin_name
        self._skin_data = None
        self.skin_img = None
        self._props_cache = {}
        self._block_cache = {}
        self._loaded = False

    def load(self):
        if self._loaded:
            return True

        self._skin_data = get_skin_data(self._skin_name)
        if self._skin_data is None:
            raise FileNotFoundError(f'皮肤不存在: {self._skin_name}')

        # Load bitmap from PNG
        bmp_info = self._skin_data['bitmap']
        png_file = bmp_info.get('png_file', f'{self._skin_name}.png')
        png_path = os.path.join(_SKINS_DIR, png_file)
        if os.path.exists(png_path):
            self.skin_img = wx.Image(png_path)

        self._loaded = True
        return True

    @property
    def name(self):
        return self._skin_name

    @property
    def bitmap_info(self):
        return self._skin_data.get('bitmap', {}) if self._skin_data else {}

    def get_block(self, slot):
        if slot in self._block_cache:
            return self._block_cache[slot]

        blocks = self._skin_data['blocks']
        raw = blocks.get(slot, [0] * 18)
        block = block_from_raw(raw)
        self._block_cache[slot] = block
        return block

    def get_props(self, subcat_name):
        if subcat_name in self._props_cache:
            return self._props_cache[subcat_name]

        props = {}
        raw_props = self._skin_data['properties'].get(subcat_name, {})
        for pname, pval in raw_props.items():
            if isinstance(pval, tuple):
                if pval and pval[0] == 'color':
                    props[pname] = wx.Colour(*pval[1])
                elif pval and pval[0] == 'font':
                    props[pname] = {
                        'height': pval[1],
                        'width': pval[2],
                        'weight': pval[3],
                        'italic': pval[4],
                        'face_name': pval[5],
                        'charset': pval[6],
                    }
                else:
                    props[pname] = pval
            else:
                props[pname] = pval

        if subcat_name == 'MenuBar':
            props.setdefault('height', 24)

        self._props_cache[subcat_name] = props
        return props

    def get_border_dims(self, window_type='NormalWindow', state_name='active'):
        layout = CONTROL_SLOTS.get(window_type)
        if not layout:
            return None

        top_b = self.get_block(layout['top'][state_name])
        left_b = self.get_block(layout['left'][state_name])
        right_b = self.get_block(layout['right'][state_name])
        bottom_b = self.get_block(layout['bottom'][state_name])

        title_h = top_b.bg_height if not is_block_empty(top_b) and top_b.bg_height > 0 else DEFAULT_TITLE_HEIGHT
        border_l = left_b.bg_width if not is_block_empty(left_b) and left_b.bg_width > 0 else DEFAULT_BORDER_WIDTH
        border_r = right_b.bg_width if not is_block_empty(right_b) and right_b.bg_width > 0 else DEFAULT_BORDER_WIDTH
        border_b = bottom_b.bg_height if not is_block_empty(bottom_b) and bottom_b.bg_height > 0 else DEFAULT_BORDER_WIDTH

        props = self.get_props(window_type)
        corner_radius = props.get('corner_radius', 0)

        return {
            'title_h': title_h,
            'border_left': border_l,
            'border_right': border_r,
            'border_bottom': border_b,
            'corner_radius': corner_radius,
        }

    def get_menu_bar_height(self):
        return self.get_props('MenuBar').get('height', 24)
