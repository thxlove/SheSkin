"""
pyd2d 改造后测试: DC RenderTarget -> DIBSection -> BindDC -> BeginDraw -> Render -> ULW
"""
import ctypes
from ctypes import (
    c_void_p, c_uint32, c_int, c_ulong, c_ushort, c_ubyte,
    POINTER, byref, Structure, cast, sizeof, WinDLL, WINFUNCTYPE,
)
import sys, struct, time, unittest
import pyd2d

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestDCRenderTarget(unittest.TestCase):

    def test_dc_rt_pipeline(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        gdi32 = ctypes.windll.gdi32

        user32.GetDC.restype = c_void_p
        user32.ReleaseDC.restype = c_int
        user32.ReleaseDC.argtypes = [c_void_p, c_void_p]
        gdi32.CreateCompatibleDC.restype = c_void_p
        gdi32.CreateCompatibleDC.argtypes = [c_void_p]
        gdi32.CreateDIBSection.restype = c_void_p
        gdi32.CreateDIBSection.argtypes = [c_void_p, c_void_p, c_uint32, POINTER(c_void_p), c_void_p, c_uint32]
        gdi32.SelectObject.restype = c_void_p
        gdi32.SelectObject.argtypes = [c_void_p, c_void_p]
        gdi32.DeleteObject.restype = c_int
        gdi32.DeleteObject.argtypes = [c_void_p]
        gdi32.DeleteDC.restype = c_int
        gdi32.DeleteDC.argtypes = [c_void_p]
        gdi32.GetDeviceCaps.restype = c_int
        gdi32.GetDeviceCaps.argtypes = [c_void_p, c_int]
        kernel32.GetModuleHandleW.restype = c_void_p

        class BITMAPINFOHEADER(Structure):
            _fields_ = [("biSize", c_uint32), ("biWidth", c_int), ("biHeight", c_int),
                        ("biPlanes", c_ushort), ("biBitCount", c_ushort),
                        ("biCompression", c_uint32), ("biSizeImage", c_uint32),
                        ("biXPelsPerMeter", c_int), ("biYPelsPerMeter", c_int),
                        ("biClrUsed", c_uint32), ("biClrImportant", c_uint32)]
        class BITMAPINFO(Structure):
            _fields_ = [("bmiHeader", BITMAPINFOHEADER)]

        WIDTH, HEIGHT = 400, 300

        try:
            pyd2d.InitializeCOM()
        except pyd2d.COMError:
            pass

        factory = pyd2d.GetD2DFactory()
        self.assertIsNotNone(factory)

        dc_rt = factory.CreateDCRenderTarget(
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)
        self.assertIsNotNone(dc_rt)

        hdc_screen = user32.GetDC(None)
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = WIDTH
        bmi.bmiHeader.biHeight = -HEIGHT
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0
        bmi.bmiHeader.biSizeImage = WIDTH * HEIGHT * 4
        ppvBits = c_void_p()
        hBmp = gdi32.CreateDIBSection(hdc_screen, byref(bmi), 0, byref(ppvBits), None, 0)
        self.assertTrue(hBmp)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        gdi32.SelectObject(hdc_mem, hBmp)

        dc_rt.BindDC(hdc_mem, 0, 0, WIDTH, HEIGHT)
        dc_rt.BeginDraw()
        dc_rt.Clear(0.0, 0.2, 0.8, 0.9)
        red_brush = dc_rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 0.75)
        dc_rt.FillRectangle(30, 30, 180, 140, red_brush)
        green_brush = dc_rt.CreateSolidColorBrush(0.0, 0.8, 0.2, 0.6)
        dc_rt.FillRectangle(200, 80, 370, 260, green_brush)
        dw = pyd2d.GetDWriteFactory()
        fmt = dw.CreateTextFormat("Arial", 24.0)
        text_brush = dc_rt.CreateSolidColorBrush(1.0, 1.0, 1.0, 1.0)
        dc_rt.DrawText("pyd2d DC RT!", fmt, 50, 120, 380, 200, text_brush)
        dc_rt.EndDraw()

        pixels = (c_ubyte * (WIDTH * HEIGHT * 4)).from_address(ppvBits.value)
        b, g, r, a = pixels[0], pixels[1], pixels[2], pixels[3]
        self.assertGreater(b, 150)
        self.assertLess(g, 80)
        self.assertLess(r, 30)

        red_brush.Release()
        green_brush.Release()
        text_brush.Release()
        dc_rt.Release()
        user32.ReleaseDC(None, hdc_screen)
        gdi32.DeleteDC(hdc_mem)
        gdi32.DeleteObject(hBmp)
        pyd2d.UninitializeCOM()


if __name__ == '__main__':
    unittest.main(verbosity=2)
