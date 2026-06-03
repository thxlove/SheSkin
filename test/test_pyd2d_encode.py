"""
pyd2d WIC Encoder 测试 (TDD)
PNG/BMP 编码 + 回读验证
"""

import unittest
import ctypes
import os
import pyd2d

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory()])

@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestWICEncode(unittest.TestCase):
    """WIC SaveBitmap — 编码 + 回读验证"""

    @classmethod
    def setUpClass(cls):
        cls.wic = pyd2d.GetWICFactory()
        cls.factory = pyd2d.GetD2DFactory()
        cls.test_png = os.path.join(os.path.dirname(__file__), '..', '_test_output.png')
        cls.test_bmp = os.path.join(os.path.dirname(__file__), '..', '_test_output.bmp')

    def setUp(self):
        self._cleanup()

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        for f in [self.test_png, self.test_bmp]:
            try:
                os.unlink(f)
            except OSError:
                pass

    def _create_test_bitmap(self, w=64, h=48):
        wic_bmp = self.wic.CreateBitmap(w, h)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        red = rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 1.0)
        rt.FillRectangle(8, 8, 32, 32, red)
        blue = rt.CreateSolidColorBrush(0.0, 0.0, 1.0, 1.0)
        rt.FillRectangle(32, 24, 56, 40, blue)
        rt.EndDraw()
        return wic_bmp

    def _load_and_verify(self, filename, w, h):
        decoder = self.wic.CreateDecoderFromFilename(filename)
        frame = decoder.GetFrame(0)
        converter = self.wic.CreateFormatConverter()
        converter.Initialize(frame)

        wic_bmp = self.wic.CreateBitmap(w, h)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)
        d2d_bmp = rt.CreateBitmapFromWicBitmap(converter)
        rt.BeginDraw()
        rt.DrawBitmap(d2d_bmp, 0, 0, w, h, srcRect=(0, 0, w, h))
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, w, h)
        addr, size = lock.GetDataPointer()
        pixels = bytes((ctypes.c_ubyte * size).from_address(addr))
        return pixels

    def _pixel_at(self, pixels, stride, px, py):
        idx = (py * stride + px) * 4
        return pixels[idx + 2], pixels[idx + 1], pixels[idx + 0]

    def test_save_png_roundtrip(self):
        """SaveBitmap → PNG → 回读 → 验证像素"""
        wic_bmp = self._create_test_bitmap(64, 48)

        self.wic.SaveBitmap(wic_bmp, self.test_png)

        self.assertTrue(os.path.isfile(self.test_png),
                        f"PNG file not created at {self.test_png}")
        self.assertGreater(os.path.getsize(self.test_png), 0,
                           "PNG file is empty")

        pixels = self._load_and_verify(self.test_png, 64, 48)

        r, g, b = self._pixel_at(pixels, 64, 4, 4)
        self.assertTrue(r < 10 and g < 10 and b < 10,
                        f"Top-left corner should be transparent, got ({r},{g},{b})")

        r, g, b = self._pixel_at(pixels, 64, 16, 20)
        self.assertTrue(r > 200 and g < 30 and b < 30,
                        f"Red region should be RED, got ({r},{g},{b})")

        r, g, b = self._pixel_at(pixels, 64, 40, 32)
        self.assertTrue(r < 30 and g < 30 and b > 200,
                        f"Blue region should be BLUE, got ({r},{g},{b})")

    def test_save_bmp_roundtrip(self):
        """SaveBitmap → BMP → 回读 → 验证像素"""
        wic_bmp = self._create_test_bitmap(64, 48)

        self.wic.SaveBitmap(wic_bmp, self.test_bmp)

        self.assertTrue(os.path.isfile(self.test_bmp))
        self.assertGreater(os.path.getsize(self.test_bmp), 0)

        pixels = self._load_and_verify(self.test_bmp, 64, 48)

        r, g, b = self._pixel_at(pixels, 64, 16, 20)
        self.assertTrue(r > 200 and g < 30,
                        f"Red region should be RED in BMP, got ({r},{g},{b})")

    def test_save_png_alpha_preserved(self):
        """PNG 保存透明区域 → 回读仍为透明"""
        wic_bmp = self._create_test_bitmap(64, 48)

        self.wic.SaveBitmap(wic_bmp, self.test_png)

        pixels = self._load_and_verify(self.test_png, 64, 48)

        idx = (4 * 64 + 4) * 4
        a = pixels[idx + 3]
        self.assertLess(a, 10,
                        f"Transparent area alpha should be near 0, got {a}")


if __name__ == '__main__':
    unittest.main(verbosity=2)