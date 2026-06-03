"""
pyd2d 全功能集成测试
验证: WIC, 渐变画刷, 裁剪, 图层, WIC RT → DIBSection → UpdateLayeredWindow
"""
import ctypes
import ctypes.wintypes as wintypes
import time
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', "pyd2d-main", "src"))
import pyd2d

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory()])

WIDTH, HEIGHT = 320, 240

ULW_ALPHA = 0x00000002
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
COLOR_WINDOW = 5
SW_SHOW = 5
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

LPWSTR = ctypes.c_wchar_p
LPVOID = ctypes.c_void_p
HANDLE = wintypes.HANDLE
HDC = wintypes.HDC
HWND = wintypes.HWND
HINSTANCE = wintypes.HINSTANCE
HMODULE = wintypes.HMODULE
LONG_PTR = ctypes.c_longlong
UINT_PTR = ctypes.c_ulonglong
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

user32.DefWindowProcW.argtypes = [HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes.c_longlong
gdi32.CreateCompatibleDC.restype = HDC
gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.CreateDIBSection.argtypes = [HDC, ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p, wintypes.HANDLE, wintypes.DWORD]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.DeleteObject.restype = wintypes.BOOL
user32.GetDC.restype = HDC
user32.ReleaseDC.restype = ctypes.c_int
user32.UpdateLayeredWindow.restype = wintypes.BOOL


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
    ]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", wintypes.BYTE),
        ("BlendFlags", wintypes.BYTE),
        ("SourceConstantAlpha", wintypes.BYTE),
        ("AlphaFormat", wintypes.BYTE),
    ]


class SIZE(ctypes.Structure):
    _fields_ = [
        ("cx", ctypes.c_long),
        ("cy", ctypes.c_long),
    ]


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


def create_dib_section(hdc, width, height):
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    pBits = ctypes.c_void_p()
    hbmp = gdi32.CreateDIBSection(hdc, ctypes.byref(bmi), DIB_RGB_COLORS,
                                   ctypes.byref(pBits), None, 0)
    return hbmp, pBits


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestWICBitmap(unittest.TestCase):
    """WIC Bitmap 基础测试"""

    def test_create_wic_factory(self):
        wic_factory = pyd2d.GetWICFactory()
        self.assertIsNotNone(wic_factory)
        print("  [PASS] GetWICFactory()")

    def test_create_wic_bitmap(self):
        wic_factory = pyd2d.GetWICFactory()
        bmp = wic_factory.CreateBitmap(64, 64)
        self.assertIsNotNone(bmp)
        w, h = bmp.GetSize()
        self.assertEqual(w, 64)
        self.assertEqual(h, 64)
        print(f"  [PASS] CreateBitmap(64,64) → size=({w},{h})")

    def test_lock_wic_bitmap(self):
        wic_factory = pyd2d.GetWICFactory()
        bmp = wic_factory.CreateBitmap(32, 32)
        lock = bmp.Lock(0, 0, 32, 32, 1)
        data_ptr, data_size = lock.GetDataPointer()
        self.assertGreater(data_ptr, 0)
        self.assertEqual(data_size, 32 * 32 * 4)
        print(f"  [PASS] Lock+GetDataPointer → ptr=0x{data_ptr:X}, size={data_size}")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestWICRenderTarget(unittest.TestCase):
    """WIC Bitmap RenderTarget 测试"""

    def test_create_wic_render_target(self):
        factory = pyd2d.GetD2DFactory()
        wic_factory = pyd2d.GetWICFactory()
        wic_bmp = wic_factory.CreateBitmap(WIDTH, HEIGHT)
        rt = factory.CreateWicBitmapRenderTarget(
            wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)
        self.assertIsNotNone(rt)
        print("  [PASS] CreateWicBitmapRenderTarget")

    def test_wic_rt_begin_draw_clear(self):
        factory = pyd2d.GetD2DFactory()
        wic_factory = pyd2d.GetWICFactory()
        wic_bmp = wic_factory.CreateBitmap(WIDTH, HEIGHT)
        rt = factory.CreateWicBitmapRenderTarget(
            wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)
        rt.BeginDraw()
        rt.Clear(0.0, 0.3, 0.7, 1.0)
        rt.EndDraw()
        print(f"  [PASS] WIC RT BeginDraw->Clear->EndDraw")

    def test_wic_rt_fill_rect(self):
        factory = pyd2d.GetD2DFactory()
        wic_factory = pyd2d.GetWICFactory()
        wic_bmp = wic_factory.CreateBitmap(WIDTH, HEIGHT)
        rt = factory.CreateWicBitmapRenderTarget(
            wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)
        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        brush = rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 0.75)
        rt.FillRectangle(10, 10, 100, 80, brush)
        rt.EndDraw()

        lock = wic_bmp.Lock(15, 15, 1, 1, 1)
        data_ptr, _ = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * 4).from_address(data_ptr)
        print(f"  [PASS] WIC RT FillRectangle → pixel@(15,15)=RGBA({pixels[2]},{pixels[1]},{pixels[0]},{pixels[3]})")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestGradientBrushes(unittest.TestCase):
    """渐变画刷测试"""

    def test_linear_gradient_brush(self):
        factory = pyd2d.GetD2DFactory()
        wic_factory = pyd2d.GetWICFactory()
        wic_bmp = wic_factory.CreateBitmap(WIDTH, HEIGHT)
        rt = factory.CreateWicBitmapRenderTarget(
            wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)

        stops = rt.CreateGradientStopCollection([
            (0.0, 1.0, 0.0, 0.0, 1.0),
            (0.5, 0.0, 1.0, 0.0, 1.0),
            (1.0, 0.0, 0.0, 1.0, 1.0),
        ])

        brush = rt.CreateLinearGradientBrush(stops, 0, 0, WIDTH, HEIGHT)
        self.assertIsNotNone(brush)

        sx, sy = brush.GetStartPoint()
        ex, ey = brush.GetEndPoint()
        self.assertAlmostEqual(sx, 0.0)
        self.assertAlmostEqual(sy, 0.0)
        self.assertAlmostEqual(ex, WIDTH)
        self.assertAlmostEqual(ey, HEIGHT)

        rt.BeginDraw()
        rt.Clear(0, 0, 0, 0)
        rt.FillRectangle(0, 0, WIDTH, HEIGHT, brush)
        rt.EndDraw()

        lock = wic_bmp.Lock(10, 10, 1, 1, 1)
        data_ptr, _ = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * 4).from_address(data_ptr)
        print(f"  [PASS] LinearGradientBrush → pixel@(10,10)=RGBA({pixels[2]},{pixels[1]},{pixels[0]},{pixels[3]})")

    def test_radial_gradient_brush(self):
        factory = pyd2d.GetD2DFactory()
        wic_factory = pyd2d.GetWICFactory()
        wic_bmp = wic_factory.CreateBitmap(WIDTH, HEIGHT)
        rt = factory.CreateWicBitmapRenderTarget(
            wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)

        stops = rt.CreateGradientStopCollection([
            (0.0, 1.0, 1.0, 0.0, 1.0),
            (1.0, 1.0, 0.0, 0.0, 1.0),
        ])

        cx, cy = WIDTH / 2, HEIGHT / 2
        brush = rt.CreateRadialGradientBrush(stops, cx, cy, 0, 0, 160, 120)
        self.assertIsNotNone(brush)

        bcx, bcy = brush.GetCenter()
        self.assertAlmostEqual(bcx, cx)
        self.assertAlmostEqual(bcy, cy)

        rt.BeginDraw()
        rt.Clear(0, 0, 0, 0)
        rt.FillRectangle(0, 0, WIDTH, HEIGHT, brush)
        rt.EndDraw()

        lock = wic_bmp.Lock(int(cx), int(cy), 1, 1, 1)
        data_ptr, _ = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * 4).from_address(data_ptr)
        print(f"  [PASS] RadialGradientBrush → pixel@center=RGBA({pixels[2]},{pixels[1]},{pixels[0]},{pixels[3]})")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestClipping(unittest.TestCase):
    """裁剪测试"""

    def test_axis_aligned_clip(self):
        factory = pyd2d.GetD2DFactory()
        wic_factory = pyd2d.GetWICFactory()
        wic_bmp = wic_factory.CreateBitmap(WIDTH, HEIGHT)
        rt = factory.CreateWicBitmapRenderTarget(
            wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 1.0)

        rt.PushAxisAlignedClip(50, 50, 150, 150, 1)
        red_brush = rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 1.0)
        rt.FillRectangle(0, 0, WIDTH, HEIGHT, red_brush)
        rt.PopAxisAlignedClip()

        rt.EndDraw()

        lock_inside = wic_bmp.Lock(100, 100, 1, 1, 1)
        data_ptr, _ = lock_inside.GetDataPointer()
        pix_in = (ctypes.c_ubyte * 4).from_address(data_ptr)

        lock_outside = wic_bmp.Lock(30, 30, 1, 1, 1)
        data_ptr, _ = lock_outside.GetDataPointer()
        pix_out = (ctypes.c_ubyte * 4).from_address(data_ptr)

        self.assertEqual(pix_in[2], 255)
        self.assertEqual(pix_out[2], 0)
        print(f"  [PASS] PushAxisAlignedClip → inside=red({pix_in[2]}), outside=black({pix_out[2]})")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestLayers(unittest.TestCase):
    """图层测试"""

    def test_push_pop_layer(self):
        factory = pyd2d.GetD2DFactory()
        wic_factory = pyd2d.GetWICFactory()
        wic_bmp = wic_factory.CreateBitmap(WIDTH, HEIGHT)
        rt = factory.CreateWicBitmapRenderTarget(
            wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)

        layer = rt.CreateLayer()
        self.assertIsNotNone(layer)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 1.0)

        rt.PushLayer(layer, 0, 0, WIDTH, HEIGHT, opacity=0.5)
        red_brush = rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 1.0)
        rt.FillRectangle(0, 0, WIDTH, HEIGHT, red_brush)
        rt.PopLayer()

        rt.EndDraw()

        lock = wic_bmp.Lock(100, 100, 1, 1, 1)
        data_ptr, _ = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * 4).from_address(data_ptr)
        print(f"  [PASS] PushLayer(opacity=0.5) → pixel@(100,100)=RGBA({pixels[2]},{pixels[1]},{pixels[0]},{pixels[3]})")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestDCToULW(unittest.TestCase):
    """DC RenderTarget → DIBSection → UpdateLayeredWindow 全管线"""

    _wndproc_cb = None

    class WNDCLASSEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HICON),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", LPWSTR),
            ("lpszClassName", LPWSTR),
            ("hIconSm", wintypes.HICON),
        ]

    @classmethod
    def setUpClass(cls):
        cls.hwnd = None
        cls.hinst = kernel32.GetModuleHandleW(None)
        cls._wndproc_cb = WNDPROC(_wndproc)

        wndclass = cls.WNDCLASSEXW()
        wndclass.cbSize = ctypes.sizeof(cls.WNDCLASSEXW)
        wndclass.style = 0
        wndclass.lpfnWndProc = cls._wndproc_cb
        wndclass.hInstance = cls.hinst
        wndclass.hCursor = user32.LoadCursorW(None, 32512)
        wndclass.hbrBackground = ctypes.c_void_p(COLOR_WINDOW + 1)
        wndclass.lpszClassName = "pyd2d_test_window"

        user32.RegisterClassExW(ctypes.byref(wndclass))

        cls.hwnd = user32.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TOPMOST,
            "pyd2d_test_window",
            "Test",
            WS_OVERLAPPEDWINDOW,
            100, 100, WIDTH, HEIGHT,
            None, None, cls.hinst, None)
        user32.ShowWindow(cls.hwnd, SW_SHOW)
        user32.UpdateWindow(cls.hwnd)

    @classmethod
    def tearDownClass(cls):
        if cls.hwnd:
            user32.DestroyWindow(cls.hwnd)
            cls.hwnd = None
        user32.UnregisterClassW("pyd2d_test_window", cls.hinst)
        cls._wndproc_cb = None

    def test_dc_rt_to_ulw(self):
        hdc_screen = user32.GetDC(None)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp, pBits = create_dib_section(hdc_mem, WIDTH, HEIGHT)
        old_bmp = gdi32.SelectObject(hdc_mem, hbmp)

        factory = pyd2d.GetD2DFactory()
        dc_rt = factory.CreateDCRenderTarget(
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)
        dc_rt.BindDC(hdc_mem, 0, 0, WIDTH, HEIGHT)

        dc_rt.BeginDraw()
        dc_rt.Clear(0.0, 0.2, 0.8, 0.9)
        brush = dc_rt.CreateSolidColorBrush(1.0, 0.5, 0.0, 0.8)
        dc_rt.FillRectangle(20, 20, 80, 60, brush)
        dc_rt.EndDraw()

        sz = SIZE(WIDTH, HEIGHT)
        pt_dst = POINT(200, 200)
        pt_src = POINT(0, 0)
        bf = BLENDFUNCTION()
        bf.BlendOp = 0  # AC_SRC_OVER
        bf.BlendFlags = 0
        bf.SourceConstantAlpha = 255
        bf.AlphaFormat = 1  # AC_SRC_ALPHA

        _saved_restype = user32.UpdateLayeredWindow.restype
        _saved_argtypes = user32.UpdateLayeredWindow.argtypes
        user32.UpdateLayeredWindow.restype = wintypes.BOOL
        user32.UpdateLayeredWindow.argtypes = [
            HWND, HDC, ctypes.POINTER(POINT), ctypes.POINTER(SIZE),
            HDC, ctypes.POINTER(POINT), wintypes.COLORREF,
            ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD]

        result = user32.UpdateLayeredWindow(
            self.hwnd, None, None, ctypes.byref(sz), hdc_mem,
            ctypes.byref(pt_dst), 0, ctypes.byref(bf), ULW_ALPHA)

        user32.UpdateLayeredWindow.restype = _saved_restype
        user32.UpdateLayeredWindow.argtypes = _saved_argtypes
        self.assertTrue(result)

        pixels = (ctypes.c_ubyte * (WIDTH * HEIGHT * 4)).from_address(pBits.value)
        idx = (10 * WIDTH + 10) * 4
        b, g, r, a = pixels[idx], pixels[idx + 1], pixels[idx + 2], pixels[idx + 3]
        self.assertAlmostEqual(b / 255.0, 0.8 * 0.9, delta=0.05)
        print(f"  [PASS] DC RT → DIBSection → UpdateLayeredWindow → pixel@(10,10)=RGBA({r},{g},{b},{a})")

        gdi32.SelectObject(hdc_mem, old_bmp)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)


def _wndproc(hwnd, msg, wparam, lparam):
    if msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


if __name__ == "__main__":
    print("=" * 60)
    print("pyd2d 全功能集成测试")
    print("=" * 60)

    print()
    print("Part 1: WIC Bitmap 基础")
    unittest.main(argv=["", "TestWICBitmap"], exit=False)

    print()
    print("Part 2: WIC Bitmap RenderTarget")
    unittest.main(argv=["", "TestWICRenderTarget"], exit=False)

    print()
    print("Part 3: 渐变画刷")
    unittest.main(argv=["", "TestGradientBrushes"], exit=False)

    print()
    print("Part 4: 裁剪")
    unittest.main(argv=["", "TestClipping"], exit=False)

    print()
    print("Part 5: 图层")
    unittest.main(argv=["", "TestLayers"], exit=False)

    print()
    print("Part 6: DC RT → DIBSection → UpdateLayeredWindow")
    unittest.main(argv=["", "TestDCToULW"], exit=False)

    print()
    print("=" * 60)
    print("全部测试完成")