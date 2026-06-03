import struct
import wx
from .layout import CHANNEL_ORDER, FLIP_ROWS, CHANNEL_ORDERS_MAP


def extract_bitmap(data, bmp_info):
    offset = bmp_info['offset']
    w = bmp_info['width']
    h = bmp_info['height']
    bpp = bmp_info['bpp']

    bmp_header_size = struct.unpack_from('<I', data, offset)[0]
    comp = struct.unpack_from('<I', data, offset + 16)[0]
    row_size = ((w * bpp + 31) // 32) * 4

    if comp == 0:
        pixel_start = offset + bmp_header_size
        if offset + bmp_header_size + row_size * h + 4 == len(data):
            pixel_start += 4
    else:
        comp_size = struct.unpack_from('<I', data, offset + 20)[0]
        pixel_start = offset + bmp_header_size + comp_size

    img = wx.Image(w, h)
    img.InitAlpha()
    alpha = bytearray(w * h)
    rgb_data = bytearray(w * h * 3)
    r_idx, g_idx, b_idx = CHANNEL_ORDERS_MAP[CHANNEL_ORDER]

    for y in range(h):
        src_row = (h - 1 - y) if FLIP_ROWS else y
        row_off = pixel_start + src_row * row_size
        for x in range(w):
            if bpp == 24:
                pix_off = row_off + x * 3
                if pix_off + 2 < len(data):
                    byte0, byte1, byte2 = data[pix_off], data[pix_off + 1], data[pix_off + 2]
                else:
                    byte0 = byte1 = byte2 = 0
            elif bpp == 32:
                pix_off = row_off + x * 4
                if pix_off + 3 < len(data):
                    byte0, byte1, byte2 = data[pix_off], data[pix_off + 1], data[pix_off + 2]
                else:
                    byte0 = byte1 = byte2 = 0
            else:
                byte0 = byte1 = byte2 = 0

            idx = y * w + x
            arr = [byte0, byte1, byte2]
            rgb_data[idx * 3] = arr[r_idx]
            rgb_data[idx * 3 + 1] = arr[g_idx]
            rgb_data[idx * 3 + 2] = arr[b_idx]
            alpha[idx] = 255

    img.SetData(bytes(rgb_data))
    img.SetAlpha(bytes(alpha))
    return img


def apply_color_key(img, color_key):
    if color_key == 0:
        color_key = 0x00FF00FF
    from .layout import CK_AS_BGR
    if CK_AS_BGR:
        ck_r = (color_key >> 16) & 0xFF
        ck_g = (color_key >> 8) & 0xFF
        ck_b = color_key & 0xFF
    else:
        ck_r = color_key & 0xFF
        ck_g = (color_key >> 8) & 0xFF
        ck_b = (color_key >> 16) & 0xFF

    w, h = img.GetWidth(), img.GetHeight()
    if not img.HasAlpha():
        img.InitAlpha()
    data = bytearray(img.GetData())
    alpha = bytearray(img.GetAlpha())
    for i in range(w * h):
        off = i * 3
        if data[off] == ck_r and data[off + 1] == ck_g and data[off + 2] == ck_b:
            alpha[i] = 0
            data[off] = data[off + 1] = data[off + 2] = 0
    img.SetData(bytes(data))
    img.SetAlpha(bytes(alpha))
    return img


def clean_alpha(img, threshold=128):
    w, h = img.GetWidth(), img.GetHeight()
    if not img.HasAlpha():
        return img
    data = bytearray(img.GetData())
    alpha = bytearray(img.GetAlpha())
    for i in range(w * h):
        if alpha[i] < threshold:
            alpha[i] = 0
            off = i * 3
            data[off] = data[off + 1] = data[off + 2] = 0
        else:
            alpha[i] = 255
    img.SetData(bytes(data))
    img.SetAlpha(bytes(alpha))
    return img
