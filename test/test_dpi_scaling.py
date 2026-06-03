"""
隔离测试: DCRenderTarget 高 DPI + SetTransform 物理像素坐标正确性

第一性原理:
  DCRenderTarget(dpiX=144) -> D2D使用DIP空间
  DIBSection = WxH 物理像素 -> DIP范围 = W*(96/dpi), H*(96/dpi)
  我们的坐标是物理像素 -> 必须 SetTransform(Scale(96/dpi, 96/dpi)) 映射回DIP
  验证: 分别用 dpi=96(基线) 和 dpi=144+transform 绘制, 像素值应完全一致
"""
import ctypes
import pytest

import pyd2d

from sheskin.frame import _BITMAPINFOHEADER

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

user32.GetDC.argtypes = [ctypes.c_void_p]
user32.GetDC.restype = ctypes.c_void_p
user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
user32.ReleaseDC.restype = ctypes.c_int

gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
gdi32.CreateDIBSection.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
                                    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
gdi32.CreateDIBSection.restype = ctypes.c_void_p
gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
gdi32.SelectObject.restype = ctypes.c_void_p
gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
gdi32.DeleteObject.restype = ctypes.c_int
gdi32.DeleteDC.argtypes = [ctypes.c_void_p]
gdi32.DeleteDC.restype = ctypes.c_int


W, H = 200, 100


def _create_dibsection(w, h):
    hdc_screen = user32.GetDC(None)
    bmi = _BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    bmi.biSizeImage = w * h * 4

    ppv_bits = ctypes.c_void_p()
    hbmp = gdi32.CreateDIBSection(
        hdc_screen, ctypes.byref(bmi), 0, ctypes.byref(ppv_bits), None, 0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    old_bmp = gdi32.SelectObject(hdc_mem, hbmp)
    user32.ReleaseDC(None, hdc_screen)

    buf = (ctypes.c_ubyte * (w * h * 4)).from_address(ppv_bits.value)
    return hdc_mem, hbmp, old_bmp, buf


def _release_dibsection(hdc_mem, hbmp, old_bmp):
    if old_bmp:
        gdi32.SelectObject(hdc_mem, old_bmp)
    if hdc_mem:
        gdi32.DeleteDC(hdc_mem)
    if hbmp:
        gdi32.DeleteObject(hbmp)


def _make_rt(dpi_x, dpi_y, hdc_mem, w, h):
    factory = pyd2d.GetD2DFactory()
    rt = factory.CreateDCRenderTarget(
        rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
        pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
        alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
        dpiX=float(dpi_x), dpiY=float(dpi_y))
    rt.BindDC(hdc_mem, 0, 0, w, h)
    return rt


def _pixel(buf, x, y):
    offset = (y * W + x) * 4
    return (buf[offset + 2], buf[offset + 1], buf[offset + 0], buf[offset + 3])


def _is_white(px):
    """白色背景: RGB全部>=245"""
    return px[0] >= 245 and px[1] >= 245 and px[2] >= 245


def _is_red(px):
    """红色填充: R>=250 且 G,B<=20"""
    return px[0] >= 250 and px[1] <= 20 and px[2] <= 20


def _is_green(px):
    """绿色填充: G>=250 且 R,B<=20"""
    return px[1] >= 250 and px[0] <= 20 and px[2] <= 20


def _is_blue(px):
    """蓝色填充: B>=250 且 R,G<=20"""
    return px[2] >= 250 and px[0] <= 20 and px[1] <= 20


class TestDPIScaling:

    @staticmethod
    def _draw_rect(rt, x, y, w, h, r, g, b, a=1.0):
        brush = rt.CreateSolidColorBrush(r, g, b, a)
        rt.FillRectangle(x, y, x + w, y + h, brush)
        brush.Release()

    # ---- 基线: dpi=96 ----

    def test_baseline_dpi96(self):
        hdc_mem, hbmp, old_bmp, buf = _create_dibsection(W, H)
        try:
            rt = _make_rt(96, 96, hdc_mem, W, H)
            rt.BeginDraw()
            rt.Clear(1.0, 1.0, 1.0, 1.0)
            self._draw_rect(rt, 10, 10, 50, 30, 1.0, 0.0, 0.0)
            self._draw_rect(rt, 150, 70, 40, 20, 0.0, 1.0, 0.0)
            rt.EndDraw()

            # (10,10) = 红色矩形左上
            assert _is_red(_pixel(buf, 10, 10)), \
                f"dpi96 (10,10) expected red, got {_pixel(buf, 10, 10)}"
            # (9,9) = 左上外侧, 白色背景
            assert _is_white(_pixel(buf, 9, 9)), \
                f"dpi96 (9,9) expected white, got {_pixel(buf, 9, 9)}"
            # (59,39) = 红色右下
            assert _is_red(_pixel(buf, 59, 39)), \
                f"dpi96 (59,39) expected red, got {_pixel(buf, 59, 39)}"
            # (60,20) = 红色右边界, 白色
            assert _is_white(_pixel(buf, 60, 20)), \
                f"dpi96 (60,20) expected white, got {_pixel(buf, 60, 20)}"
            # (20,40) = 红色下边界, 白色
            assert _is_white(_pixel(buf, 20, 40)), \
                f"dpi96 (20,40) expected white, got {_pixel(buf, 20, 40)}"
            # 绿色矩形验证
            assert _is_green(_pixel(buf, 150, 70)), \
                f"dpi96 (150,70) expected green, got {_pixel(buf, 150, 70)}"
            assert _is_green(_pixel(buf, 189, 89)), \
                f"dpi96 (189,89) expected green, got {_pixel(buf, 189, 89)}"
            assert _is_white(_pixel(buf, 190, 80)), \
                f"dpi96 (190,80) expected white, got {_pixel(buf, 190, 80)}"
        finally:
            rt.Release()
            rt = None
            _release_dibsection(hdc_mem, hbmp, old_bmp)

    # ---- dpi=144 无 Transform → 坐标偏移 ----

    def test_dpi144_no_transform_shift(self):
        """dpi=144 无 Transform: 物理(10,10)为白, 物理(15,15)为红"""
        hdc_mem, hbmp, old_bmp, buf = _create_dibsection(W, H)
        try:
            rt = _make_rt(144, 144, hdc_mem, W, H)
            rt.BeginDraw()
            rt.Clear(1.0, 1.0, 1.0, 1.0)
            self._draw_rect(rt, 10, 10, 50, 30, 1.0, 0.0, 0.0)
            rt.EndDraw()

            # DIP(10) → 物理 10*1.5=15: (10,10)物理应为白
            assert _is_white(_pixel(buf, 10, 10)), \
                f"dpi144 no-transform (10,10) should be white, got {_pixel(buf, 10, 10)}"
            # 红色在物理(15,15)
            assert _is_red(_pixel(buf, 15, 15)), \
                f"dpi144 no-transform (15,15) should be red, got {_pixel(buf, 15, 15)}"
            # DIP(10+50, 10+30) = (60,40) → 物理 (90,60)
            # 红色右下角内部
            assert _is_red(_pixel(buf, 88, 58)), \
                f"dpi144 no-transform (88,58) should be red, got {_pixel(buf, 88, 58)}"
            # 右边界外 (90, 20) 白色
            assert _is_white(_pixel(buf, 90, 20)), \
                f"dpi144 no-transform (90,20) should be white, got {_pixel(buf, 90, 20)}"
        finally:
            rt.Release()
            rt = None
            _release_dibsection(hdc_mem, hbmp, old_bmp)

    # ---- dpi=144 + SetTransform → 与 dpi=96 像素级一致 ----

    def test_dpi144_with_transform_matches_baseline(self):
        hdc_mem, hbmp, old_bmp, buf = _create_dibsection(W, H)
        try:
            rt = _make_rt(144, 144, hdc_mem, W, H)
            rt.BeginDraw()
            rt.Clear(1.0, 1.0, 1.0, 1.0)

            rt.SetTransform(96.0 / 144.0, 0.0, 0.0, 96.0 / 144.0, 0.0, 0.0)

            self._draw_rect(rt, 10, 10, 50, 30, 1.0, 0.0, 0.0)
            self._draw_rect(rt, 150, 70, 40, 20, 0.0, 1.0, 0.0)
            rt.EndDraw()

            # 必须与 dpi=96 基线完全一致
            assert _is_red(_pixel(buf, 10, 10)), \
                f"dpi144+T (10,10) expected red, got {_pixel(buf, 10, 10)}"
            assert _is_white(_pixel(buf, 9, 9)), \
                f"dpi144+T (9,9) expected white, got {_pixel(buf, 9, 9)}"
            assert _is_red(_pixel(buf, 59, 39)), \
                f"dpi144+T (59,39) expected red, got {_pixel(buf, 59, 39)}"
            assert _is_white(_pixel(buf, 60, 20)), \
                f"dpi144+T (60,20) expected white, got {_pixel(buf, 60, 20)}"
            assert _is_white(_pixel(buf, 20, 40)), \
                f"dpi144+T (20,40) expected white, got {_pixel(buf, 20, 40)}"

            assert _is_green(_pixel(buf, 150, 70)), \
                f"dpi144+T (150,70) expected green, got {_pixel(buf, 150, 70)}"
            assert _is_green(_pixel(buf, 189, 89)), \
                f"dpi144+T (189,89) expected green, got {_pixel(buf, 189, 89)}"
            assert _is_white(_pixel(buf, 190, 80)), \
                f"dpi144+T (190,80) expected white, got {_pixel(buf, 190, 80)}"
        finally:
            rt.Release()
            rt = None
            _release_dibsection(hdc_mem, hbmp, old_bmp)

    # ---- dpi=120 (125%) + Transform ----

    def test_dpi120_transform(self):
        hdc_mem, hbmp, old_bmp, buf = _create_dibsection(W, H)
        try:
            rt = _make_rt(120, 120, hdc_mem, W, H)
            rt.BeginDraw()
            rt.Clear(1.0, 1.0, 1.0, 1.0)

            rt.SetTransform(96.0 / 120.0, 0.0, 0.0, 96.0 / 120.0, 0.0, 0.0)

            self._draw_rect(rt, 10, 10, 50, 30, 1.0, 0.0, 0.0)
            rt.EndDraw()

            assert _is_red(_pixel(buf, 10, 10)), \
                f"dpi120+T (10,10) expected red, got {_pixel(buf, 10, 10)}"
            assert _is_white(_pixel(buf, 9, 9)), \
                f"dpi120+T (9,9) expected white, got {_pixel(buf, 9, 9)}"
            assert _is_red(_pixel(buf, 59, 39)), \
                f"dpi120+T (59,39) expected red, got {_pixel(buf, 59, 39)}"
            assert _is_white(_pixel(buf, 60, 20)), \
                f"dpi120+T (60,20) expected white, got {_pixel(buf, 60, 20)}"
        finally:
            rt.Release()
            rt = None
            _release_dibsection(hdc_mem, hbmp, old_bmp)

    # ---- dpi=192 (200%) + Transform ----

    def test_dpi192_transform(self):
        hdc_mem, hbmp, old_bmp, buf = _create_dibsection(W, H)
        try:
            rt = _make_rt(192, 192, hdc_mem, W, H)
            rt.BeginDraw()
            rt.Clear(1.0, 1.0, 1.0, 1.0)

            rt.SetTransform(96.0 / 192.0, 0.0, 0.0, 96.0 / 192.0, 0.0, 0.0)

            self._draw_rect(rt, 10, 10, 50, 30, 1.0, 0.0, 0.0)
            rt.EndDraw()

            assert _is_red(_pixel(buf, 10, 10)), \
                f"dpi192+T (10,10) expected red, got {_pixel(buf, 10, 10)}"
            assert _is_white(_pixel(buf, 9, 9)), \
                f"dpi192+T (9,9) expected white, got {_pixel(buf, 9, 9)}"
            assert _is_red(_pixel(buf, 59, 39)), \
                f"dpi192+T (59,39) expected red, got {_pixel(buf, 59, 39)}"
            assert _is_white(_pixel(buf, 60, 20)), \
                f"dpi192+T (60,20) expected white, got {_pixel(buf, 60, 20)}"
        finally:
            rt.Release()
            rt = None
            _release_dibsection(hdc_mem, hbmp, old_bmp)

    # ---- 当前真实 DPI + Transform ----

    def test_native_dpi_with_transform(self):
        """使用真实系统 DPI + SetTransform, 坐标必须正确"""
        import ctypes
        user32_l = ctypes.windll.user32
        gdi32_l = ctypes.windll.gdi32
        hdc = user32_l.GetDC(None)
        dpi_x = gdi32_l.GetDeviceCaps(hdc, 88)
        dpi_y = gdi32_l.GetDeviceCaps(hdc, 90)
        user32_l.ReleaseDC(None, hdc)
        scale_x = 96.0 / max(dpi_x, 1)
        scale_y = 96.0 / max(dpi_y, 1)

        hdc_mem, hbmp, old_bmp, buf = _create_dibsection(W, H)
        try:
            rt = _make_rt(dpi_x, dpi_y, hdc_mem, W, H)
            rt.BeginDraw()
            rt.Clear(1.0, 1.0, 1.0, 1.0)

            rt.SetTransform(scale_x, 0.0, 0.0, scale_y, 0.0, 0.0)

            self._draw_rect(rt, 10, 10, 50, 30, 1.0, 0.0, 0.0)
            rt.EndDraw()

            assert _is_red(_pixel(buf, 10, 10)), \
                f"native DPI({dpi_x},{dpi_y})+T (10,10) expected red, got {_pixel(buf, 10, 10)}"
            assert _is_white(_pixel(buf, 9, 9)), \
                f"native DPI({dpi_x},{dpi_y})+T (9,9) expected white, got {_pixel(buf, 9, 9)}"
            assert _is_red(_pixel(buf, 59, 39)), \
                f"native DPI({dpi_x},{dpi_y})+T (59,39) expected red, got {_pixel(buf, 59, 39)}"
            assert _is_white(_pixel(buf, 60, 20)), \
                f"native DPI({dpi_x},{dpi_y})+T (60,20) expected white, got {_pixel(buf, 60, 20)}"
        finally:
            rt.Release()
            rt = None
            _release_dibsection(hdc_mem, hbmp, old_bmp)