"""pyd2d 图片加载集成测试:
PNG File → WIC Decoder → FormatConverter(PBGRA) → D2D Bitmap → Draw → Pixel Verify"""
import pyd2d
import ctypes
import ctypes.wintypes as wintypes
import unittest
import os

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory()])

TEST_PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'archive', 'temp_images', 'test_image.png')

HWND = wintypes.HWND
HDC = wintypes.HDC
HINSTANCE = wintypes.HINSTANCE
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
LPWSTR = ctypes.c_wchar_p
LPVOID = ctypes.c_void_p

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]

class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", wintypes.BYTE),
        ("BlendFlags", wintypes.BYTE),
        ("SourceConstantAlpha", wintypes.BYTE),
        ("AlphaFormat", wintypes.BYTE),
    ]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER)]

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT), ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int), ("hInstance", HINSTANCE),
        ("hIcon", wintypes.HICON), ("hCursor", wintypes.HICON),
        ("hbrBackground", wintypes.HBRUSH), ("lpszMenuName", LPWSTR),
        ("lpszClassName", LPWSTR), ("hIconSm", wintypes.HICON),
    ]

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

user32.DefWindowProcW.argtypes = [HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes.c_longlong
gdi32.CreateCompatibleDC.restype = HDC
gdi32.CreateCompatibleDC.argtypes = [HDC]
gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.CreateDIBSection.argtypes = [HDC, ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p, wintypes.HANDLE, wintypes.DWORD]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.SelectObject.argtypes = [HDC, wintypes.HGDIOBJ]
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = [HDC]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
user32.GetDC.restype = HDC
user32.GetDC.argtypes = [HWND]
user32.ReleaseDC.restype = ctypes.c_int
user32.ReleaseDC.argtypes = [HWND, HDC]
user32.UpdateLayeredWindow.restype = wintypes.BOOL
user32.UpdateLayeredWindow.argtypes = [HWND, HDC, ctypes.c_void_p, ctypes.c_void_p, HDC, ctypes.c_void_p, wintypes.COLORREF, ctypes.c_void_p, wintypes.DWORD]
user32.RegisterClassExW.argtypes = [ctypes.c_void_p]
user32.RegisterClassExW.restype = wintypes.ATOM
user32.CreateWindowExW.restype = HWND
user32.CreateWindowExW.argtypes = [wintypes.DWORD, LPWSTR, LPWSTR, wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, HWND, wintypes.HMENU, HINSTANCE, LPVOID]
user32.ShowWindow.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [HWND, ctypes.c_int]
user32.UpdateWindow.restype = wintypes.BOOL
user32.UpdateWindow.argtypes = [HWND]
user32.DestroyWindow.restype = wintypes.BOOL
user32.DestroyWindow.argtypes = [HWND]
user32.UnregisterClassW.restype = wintypes.BOOL
user32.UnregisterClassW.argtypes = [LPWSTR, HINSTANCE]
user32.LoadCursorW.restype = wintypes.HICON
user32.PostQuitMessage.restype = None
user32.PostQuitMessage.argtypes = [ctypes.c_int]
kernel32.GetModuleHandleW.restype = HINSTANCE
kernel32.GetModuleHandleW.argtypes = [LPWSTR]

WIDTH, HEIGHT = 64, 64
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_OVERLAPPEDWINDOW = 0x00CF0000
WM_DESTROY = 0x0002
DIB_RGB_COLORS = 0
SW_SHOW = 5

@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestImageLoading(unittest.TestCase):
    """WIC Decoder + FormatConverter → CreateBitmapFromWicBitmap"""

    @classmethod
    def setUpClass(cls):
        cls.wic = pyd2d.GetWICFactory()
        cls.factory = pyd2d.GetD2DFactory()

    def test_decode_png_basic(self):
        decoder = self.wic.CreateDecoderFromFilename(TEST_PNG)
        self.assertIsNotNone(decoder)
        self.assertIsInstance(decoder, pyd2d.WICBitmapDecoder)
        print("  [PASS] CreateDecoderFromFilename → WICBitmapDecoder")

    def test_get_frame(self):
        decoder = self.wic.CreateDecoderFromFilename(TEST_PNG)
        frame = decoder.GetFrame(0)
        self.assertIsNotNone(frame)
        self.assertIsInstance(frame, pyd2d.WICBitmapFrameDecode)
        print("  [PASS] GetFrame(0) → WICBitmapFrameDecode")

    def test_format_converter(self):
        decoder = self.wic.CreateDecoderFromFilename(TEST_PNG)
        frame = decoder.GetFrame(0)
        converter = self.wic.CreateFormatConverter()
        self.assertIsNotNone(converter)
        self.assertIsInstance(converter, pyd2d.WICFormatConverter)
        converter.Initialize(frame)
        print("  [PASS] CreateFormatConverter → Initialize(PBGRA)")

    def test_full_pipeline_to_d2d_bitmap(self):
        decoder = self.wic.CreateDecoderFromFilename(TEST_PNG)
        frame = decoder.GetFrame(0)
        converter = self.wic.CreateFormatConverter()
        converter.Initialize(frame)

        wic_bmp = self.wic.CreateBitmap(32, 32)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        d2d_bitmap = rt.CreateBitmapFromWicBitmap(converter)
        self.assertIsNotNone(d2d_bitmap)
        print("  [PASS] CreateBitmapFromWicBitmap(converter) → D2D Bitmap")

        rt.BeginDraw()
        rt.Clear(0, 0, 0, 0)
        rt.DrawBitmap(d2d_bitmap, 0, 0, 32, 32)
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, 32, 32)
        addr, size = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * size).from_address(addr)

        idx_left = (16 * 32 + 8) * 4
        r_left = pixels[idx_left + 2]
        g_left = pixels[idx_left + 1]
        b_left = pixels[idx_left + 0]
        a_left = pixels[idx_left + 3]

        idx_right = (16 * 32 + 24) * 4
        r_right = pixels[idx_right + 2]
        g_right = pixels[idx_right + 1]
        b_right = pixels[idx_right + 0]
        a_right = pixels[idx_right + 3]

        self.assertAlmostEqual(r_left / 255.0, 1.0, delta=0.05)
        self.assertAlmostEqual(g_left / 255.0, 0.0, delta=0.05)
        self.assertAlmostEqual(b_left / 255.0, 0.0, delta=0.05)

        self.assertAlmostEqual(r_right / 255.0, 0.0, delta=0.05)
        self.assertAlmostEqual(g_right / 255.0, 0.0, delta=0.05)
        self.assertAlmostEqual(b_right / 255.0, 1.0, delta=0.05)

        print(f"  [PASS] Full pipeline: PNG → WIC → D2D → DrawBitmap")
        print(f"    Left (8,16)  → RGBA({r_left},{g_left},{b_left},{a_left}) = RED")
        print(f"    Right (24,16) → RGBA({r_right},{g_right},{b_right},{a_right}) = BLUE")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestImageToDCULW(unittest.TestCase):
    """PNG → WIC → D2D DC RT → ULW: 完整皮肤渲染管线"""

    _wndproc_cb = None

    @classmethod
    def setUpClass(cls):
        cls.hwnd = None
        cls.hinst = kernel32.GetModuleHandleW(None)

        def _wndproc(hwnd, msg, wparam, lparam):
            if msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        cls._wndproc_cb = WNDPROC(_wndproc)
        wndclass = WNDCLASSEXW()
        wndclass.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wndclass.style = 0
        wndclass.lpfnWndProc = cls._wndproc_cb
        wndclass.hInstance = cls.hinst
        wndclass.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(32512))
        wndclass.hbrBackground = ctypes.c_void_p(6)
        wndclass.lpszClassName = "pyd2d_img_test"
        user32.RegisterClassExW(ctypes.byref(wndclass))
        cls.hwnd = user32.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TOPMOST, "pyd2d_img_test", "Test",
            WS_OVERLAPPEDWINDOW, 100, 100, WIDTH, HEIGHT,
            None, None, cls.hinst, None)
        user32.ShowWindow(cls.hwnd, SW_SHOW)
        user32.UpdateWindow(cls.hwnd)
        cls.wic = pyd2d.GetWICFactory()
        cls.factory = pyd2d.GetD2DFactory()

    @classmethod
    def tearDownClass(cls):
        if cls.hwnd:
            user32.DestroyWindow(cls.hwnd)
            cls.hwnd = None
        user32.UnregisterClassW("pyd2d_img_test", cls.hinst)
        cls._wndproc_cb = None

    def _create_dib_section(self, hdc, width, height):
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

    def test_load_png_render_to_ulw(self):
        decoder = self.wic.CreateDecoderFromFilename(TEST_PNG)
        frame = decoder.GetFrame(0)
        converter = self.wic.CreateFormatConverter()
        converter.Initialize(frame)

        hdc_screen = user32.GetDC(None)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp, pBits = self._create_dib_section(hdc_mem, WIDTH, HEIGHT)
        old_bmp = gdi32.SelectObject(hdc_mem, hbmp)

        dc_rt = self.factory.CreateDCRenderTarget(
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)
        dc_rt.BindDC(hdc_mem, 0, 0, WIDTH, HEIGHT)

        dc_rt.BeginDraw()
        dc_rt.Clear(0.0, 0.0, 0.0, 0.0)
        d2d_bitmap = dc_rt.CreateBitmapFromWicBitmap(converter)
        dc_rt.DrawBitmap(d2d_bitmap, 0, 0, WIDTH, HEIGHT)
        dc_rt.EndDraw()

        sz = SIZE(WIDTH, HEIGHT)
        pt_dst = POINT(200, 200)
        pt_src = POINT(0, 0)
        bf = BLENDFUNCTION()
        bf.BlendOp = 0
        bf.BlendFlags = 0
        bf.SourceConstantAlpha = 255
        bf.AlphaFormat = 1

        user32.UpdateLayeredWindow.argtypes = [HWND, HDC, ctypes.c_void_p, ctypes.c_void_p, HDC, ctypes.c_void_p, wintypes.COLORREF, ctypes.c_void_p, wintypes.DWORD]
        user32.UpdateLayeredWindow(
            self.hwnd, None, ctypes.byref(pt_dst), ctypes.byref(sz),
            hdc_mem, ctypes.byref(pt_src), 0, ctypes.byref(bf), 2)

        pixels = (ctypes.c_ubyte * (WIDTH * HEIGHT * 4)).from_address(pBits.value)
        idx_left = (32 * WIDTH + 8) * 4
        r_left = pixels[idx_left + 2]
        idx_right = (32 * WIDTH + 56) * 4
        b_right = pixels[idx_right + 0]

        self.assertAlmostEqual(r_left / 255.0, 1.0, delta=0.05)
        self.assertAlmostEqual(b_right / 255.0, 1.0, delta=0.05)

        print(f"  [PASS] PNG → WIC → DC RT → DrawBitmap → ULW → pixel verify")
        print(f"    Left pixel  → R={r_left} (RED)")
        print(f"    Right pixel → B={b_right} (BLUE)")

        gdi32.SelectObject(hdc_mem, old_bmp)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)


if __name__ == "__main__":
    print("=" * 60)
    print("pyd2d 图片加载集成测试")
    print("=" * 60)
    print()
    print("--- TestImageLoading ---")
    unittest.main(argv=["", "TestImageLoading"], exit=False)
    print()
    print("--- TestImageToDCULW ---")
    unittest.main(argv=["", "TestImageToDCULW"], exit=False)
    print()
    print("=" * 60)
    print("全部测试完成")