from collections import namedtuple

BlockData = namedtuple('BlockData', [
    'bg_left', 'bg_top', 'bg_width', 'bg_height', 'bg_color_key',
    'fg_left', 'fg_top', 'fg_width', 'fg_height', 'fg_color_key',
    'margin_left', 'margin_top', 'margin_right', 'margin_bottom',
    'draw_flags', 'alignment', 'offset_x', 'offset_y',
])


def block_from_raw(raw):
    if not raw or len(raw) < 18:
        return BlockData(*([0] * 18))
    return BlockData(*raw[:18])


def is_block_empty(block):
    if block is None:
        return True
    if isinstance(block, BlockData):
        return (block.bg_width == 0 and block.bg_height == 0
                and block.fg_width == 0 and block.fg_height == 0)
    return not any(v != 0 for v in block)
