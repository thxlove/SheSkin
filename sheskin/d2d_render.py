"""D2D 渲染辅助函数 — 供 frame/titlebar/menubar 共享使用。"""

import ctypes
from collections import OrderedDict

import numpy as np
import wx

import pyd2d
from .block import is_block_empty, block_from_raw
from .brush_cache import get_brush
from .bitmap import apply_color_key

class D2DBlockCache:
    """D2D Bitmap 预缓存 — 皮肤块一次转换，帧渲染零拷贝。

    d2d_draw_block 每帧需要 wx.Image → D2D Bitmap 转换，
    同一 block 的源图固定不变（bg/fg 区域 + color_key），
    缓存 D2D Bitmap 后只需 rt.DrawBitmap() — 零 CPU 开销。

    LRU 淘汰：超过 MAX_SIZE 条目时淘汰最久未使用的条目。
    """

    MAX_SIZE = 128

    def __init__(self):
        self._bg = OrderedDict()
        self._fg = OrderedDict()

    def clear(self):
        self._bg.clear()
        self._fg.clear()

    def _evict_if_needed(self, cache):
        while len(cache) > self.MAX_SIZE:
            cache.popitem(last=False)

    def get_bg(self, rt, skin_img, block, wic_factory=None):
        key = (block.bg_left, block.bg_top, block.bg_width,
               block.bg_height, block.bg_color_key)
        if key in self._bg:
            self._bg.move_to_end(key)
            return self._bg[key]
        sub = skin_img.GetSubImage(wx.Rect(
            int(block.bg_left), int(block.bg_top),
            int(block.bg_width), int(block.bg_height)))
        sub = _prep_image(sub, block.bg_color_key)
        d2d_bmp = _wx_image_to_d2d_bitmap(rt, sub, wic_factory)
        self._bg[key] = d2d_bmp
        self._evict_if_needed(self._bg)
        return d2d_bmp

    def get_fg(self, rt, skin_img, block, wic_factory=None):
        key = (block.fg_left, block.fg_top, block.fg_width,
               block.fg_height, block.fg_color_key)
        if key in self._fg:
            self._fg.move_to_end(key)
            return self._fg[key]
        sub = skin_img.GetSubImage(wx.Rect(
            int(block.fg_left), int(block.fg_top),
            int(block.fg_width), int(block.fg_height)))
        sub = _prep_image(sub, block.fg_color_key)
        d2d_bmp = _wx_image_to_d2d_bitmap(rt, sub, wic_factory)
        self._fg[key] = d2d_bmp
        self._evict_if_needed(self._fg)
        return d2d_bmp


def _wx_image_to_d2d_bitmap(rt, img, wic_factory=None):
    """wx.Image -> ID2D1Bitmap（premultiplied BGRA）。"""
    if wic_factory is None:
        wic_factory = pyd2d.GetWICFactory()

    img_w, img_h = img.GetWidth(), img.GetHeight()

    rgb = np.frombuffer(img.GetData(), dtype=np.uint8).reshape(img_h, img_w, 3)
    if img.HasAlpha():
        alpha = np.frombuffer(img.GetAlpha(), dtype=np.uint8).reshape(img_h, img_w)
    else:
        alpha = np.full((img_h, img_w), 255, dtype=np.uint8)

    a = alpha.astype(np.float32) / 255.0
    bgra = np.zeros((img_h, img_w, 4), dtype=np.uint8)
    bgra[:, :, 0] = (rgb[:, :, 2].astype(np.float32) * a).astype(np.uint8)
    bgra[:, :, 1] = (rgb[:, :, 1].astype(np.float32) * a).astype(np.uint8)
    bgra[:, :, 2] = (rgb[:, :, 0].astype(np.float32) * a).astype(np.uint8)
    bgra[:, :, 3] = alpha

    bgra_bytes = bgra.tobytes()

    wic_bmp = wic_factory.CreateBitmap(img_w, img_h)
    lock = wic_bmp.Lock(0, 0, img_w, img_h)
    addr, cb_size = lock.GetDataPointer()
    pixels = (ctypes.c_ubyte * cb_size).from_address(addr)
    ctypes.memmove(pixels, bgra_bytes, cb_size)
    del lock

    return rt.CreateBitmapFromWicBitmap(wic_bmp)


def _calc_fg_position(fg_w, fg_h, bg_rect, alignment, offset_x, offset_y):
    bx, by, bw, bh = bg_rect
    fx, fy = bx, by
    if alignment == 0:
        fx = bx + (bw - fg_w) // 2
        fy = by + (bh - fg_h) // 2
    elif alignment == 1:
        fx = bx
        fy = by + (bh - fg_h) // 2
    elif alignment == 2:
        fx = bx + bw - fg_w
        fy = by + (bh - fg_h) // 2
    elif alignment == 3:
        fx = bx + (bw - fg_w) // 2
        fy = by
    elif alignment == 4:
        fx = bx + (bw - fg_w) // 2
        fy = by + bh - fg_h
    fx += offset_x
    fy += offset_y
    return int(fx), int(fy)


def d2d_draw_block(rt, skin_img, block, rect, wic_factory=None, d2d_cache=None):
    if isinstance(block, (list, tuple)):
        block = block_from_raw(block)
    if is_block_empty(block):
        return

    rx, ry, rw, rh = rect
    margins = [block.margin_left, block.margin_top,
               block.margin_right, block.margin_bottom]

    has_fg = block.fg_width > 0 and block.fg_height > 0

    if block.bg_width > 0 and block.bg_height > 0:
        if d2d_cache is not None:
            d2d_bmp = d2d_cache.get_bg(rt, skin_img, block, wic_factory)
            pyd2d.nine_patch_draw(rt, d2d_bmp,
                                  (rx, ry, rw, rh), margins, block.draw_flags)
        else:
            sub = skin_img.GetSubImage(wx.Rect(
                int(block.bg_left), int(block.bg_top),
                int(block.bg_width), int(block.bg_height)))
            sub = _prep_image(sub, block.bg_color_key)
            d2d_bmp = _wx_image_to_d2d_bitmap(rt, sub, wic_factory)
            pyd2d.nine_patch_draw(rt, d2d_bmp,
                                  (rx, ry, rw, rh), margins, block.draw_flags)

    if not has_fg:
        return

    if block.fg_width > 0 and block.fg_height > 0:
        fg_w = block.fg_width
        fg_h = block.fg_height
        inner_x = rx + margins[0]
        inner_y = ry + margins[1]
        inner_w = max(0, rw - margins[0] - margins[2])
        inner_h = max(0, rh - margins[1] - margins[3])

        if block.bg_width > 0 and inner_w > 0 and inner_h > 0:
            fg_x, fg_y = _calc_fg_position(
                fg_w, fg_h,
                (inner_x, inner_y, inner_w, inner_h),
                block.alignment, block.offset_x, block.offset_y)
        else:
            fg_x = rx
            fg_y = ry

        if d2d_cache is not None:
            d2d_bmp = d2d_cache.get_fg(rt, skin_img, block, wic_factory)
            rt.DrawBitmap(d2d_bmp,
                         float(fg_x), float(fg_y),
                         float(fg_x + fg_w), float(fg_y + fg_h),
                         srcRect=(0.0, 0.0, float(fg_w), float(fg_h)))
        else:
            fg_sub = skin_img.GetSubImage(wx.Rect(
                int(block.fg_left), int(block.fg_top),
                int(block.fg_width), int(block.fg_height)))
            fg_sub = _prep_image(fg_sub, block.fg_color_key)
            d2d_bmp = _wx_image_to_d2d_bitmap(rt, fg_sub, wic_factory)
            rt.DrawBitmap(d2d_bmp,
                         float(fg_x), float(fg_y),
                         float(fg_x + fg_w), float(fg_y + fg_h),
                         srcRect=(0.0, 0.0, float(fg_w), float(fg_h)))


def _prep_image(img, ck):
    """颜色键透明预处理。"""
    if ck and ck != 0xFFFFFFFF:
        return apply_color_key(img, ck)
    return img


def d2d_draw_text(rt, dw_factory, text, text_format, text_color,
                  x, y, w, h, alignment=None):
    """用 DWrite 绘制文本（包含排版）。"""

    brush = get_brush(rt,
        text_color[0] / 255.0,
        text_color[1] / 255.0,
        text_color[2] / 255.0,
        text_color[3] / 255.0 if len(text_color) > 3 else 1.0)

    if alignment:
        try:
            layout = dw_factory.CreateTextLayout(text, text_format, float(w), float(h))
            layout.SetTextAlignment(alignment)
            rt.DrawTextLayout(layout, float(x), float(y), brush)
        except Exception:
            rt.DrawText(text, text_format, float(x), float(y),
                       float(x + w), float(y + h), brush)
    else:
        rt.DrawText(text, text_format, float(x), float(y),
                   float(x + w), float(y + h), brush)


def _wx_colour_to_rgba(colour):
    """wx.Colour -> (r, g, b, a) tuple 0-255。"""
    if hasattr(colour, 'Red'):
        return (colour.Red(), colour.Green(), colour.Blue(), colour.Alpha())
    return (colour[0], colour[1], colour[2],
            colour[3] if len(colour) > 3 else 255)