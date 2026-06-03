"""
pyd2d TODO 26 单元测试: Flush, SetTextAntialiasMode, HitTestPoint,
HitTestTextPosition, CreateCompatibleRenderTarget, IsSupported, GetDpi
"""
import sys
import unittest
import pyd2d

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


def _make_rt(width=128, height=128):
    wic = pyd2d.GetWICFactory()
    d2d = pyd2d.GetD2DFactory()
    bmp = wic.CreateBitmap(width, height)
    rt = d2d.CreateWicBitmapRenderTarget(
        bmp,
        rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
        pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
        alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
        dpiX=96.0, dpiY=96.0)
    return rt


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestTodo26(unittest.TestCase):

    def test_flush(self):
        rt = _make_rt()
        rt.BeginDraw()
        rt.Clear(0.2, 0.3, 0.4, 1.0)
        rt.Flush()
        rt.EndDraw()

    def test_text_antialias_mode(self):
        rt = _make_rt()
        default = rt.GetTextAntialiasMode()
        modes = [
            pyd2d.TEXT_ANTIALIAS_MODE.DEFAULT,
            pyd2d.TEXT_ANTIALIAS_MODE.CLEARTYPE,
            pyd2d.TEXT_ANTIALIAS_MODE.GRAYSCALE,
            pyd2d.TEXT_ANTIALIAS_MODE.ALIASED,
        ]
        for mode in modes:
            rt.SetTextAntialiasMode(mode)
            actual = rt.GetTextAntialiasMode()
            self.assertEqual(actual, mode)
        rt.SetTextAntialiasMode(default)

    def test_get_dpi(self):
        rt = _make_rt()
        dpiX, dpiY = rt.GetDpi()
        self.assertGreaterEqual(dpiX, 72.0)
        self.assertGreaterEqual(dpiY, 72.0)

    def test_is_supported(self):
        rt = _make_rt()
        supported = rt.IsSupported(
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

    def test_hit_test_point(self):
        dwfactory = pyd2d.GetDWriteFactory()
        fmt = dwfactory.CreateTextFormat('Segoe UI', 14)
        layout = dwfactory.CreateTextLayout('Hello World', fmt, 200, 50)
        isTrailing, isInside, metrics = layout.HitTestPoint(30, 10)
        self.assertTrue(isInside)
        self.assertLess(metrics.textPosition, 11)
        isTrailing2, isInside2, _ = layout.HitTestPoint(250, 10)
        self.assertFalse(isInside2)

    def test_hit_test_text_position(self):
        dwfactory = pyd2d.GetDWriteFactory()
        fmt = dwfactory.CreateTextFormat('Segoe UI', 14)
        layout = dwfactory.CreateTextLayout('Hello', fmt, 200, 50)
        x, y, metrics = layout.HitTestTextPosition(0, False)
        x2, y2, _ = layout.HitTestTextPosition(5, False)
        self.assertGreater(x2, x)

    def test_compatible_render_target(self):
        rt = _make_rt(128, 128)
        crt = rt.CreateCompatibleRenderTarget(64, 48)
        self.assertIsNotNone(crt)
        crt.BeginDraw()
        crt.Clear(0.8, 0.2, 0.2, 1.0)
        crt.Flush()
        crt.EndDraw()


if __name__ == '__main__':
    unittest.main(verbosity=2)
