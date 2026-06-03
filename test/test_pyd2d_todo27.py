import sys
import ctypes
import unittest
sys.path.insert(0, 'pyd2d-main')
import pyd2d

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


def _make_rt(width=200, height=100):
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
class TestTodo27(unittest.TestCase):

    def test_get_color(self):
        rt = _make_rt()
        brush = rt.CreateSolidColorBrush(0.1, 0.2, 0.3, 0.4)
        r, g, b, a = brush.GetColor()
        self.assertAlmostEqual(r, 0.1, delta=0.001)
        self.assertAlmostEqual(g, 0.2, delta=0.001)
        self.assertAlmostEqual(b, 0.3, delta=0.001)
        self.assertAlmostEqual(a, 0.4, delta=0.001)

    def test_get_cluster_metrics(self):
        dwfactory = pyd2d.GetDWriteFactory()
        fmt = dwfactory.CreateTextFormat('Segoe UI', 14)
        layout = dwfactory.CreateTextLayout('Hello World', fmt, 300, 50)
        metrics = layout.GetClusterMetrics()
        self.assertGreater(len(metrics), 0)
        self.assertEqual(len(metrics), 11)
        for i, cm in enumerate(metrics):
            self.assertGreater(cm.width, 0)
            self.assertGreater(cm.length, 0)
            self.assertTrue(hasattr(cm, 'canWrapLineAfter'))
            self.assertTrue(hasattr(cm, 'isWhitespace'))
            self.assertTrue(hasattr(cm, 'isNewline'))
            self.assertTrue(hasattr(cm, 'isSoftHyphen'))
            self.assertTrue(hasattr(cm, 'isRightToLeft'))
        self.assertTrue(metrics[5].isWhitespace)

    def test_get_line_metrics(self):
        dwfactory = pyd2d.GetDWriteFactory()
        fmt = dwfactory.CreateTextFormat('Segoe UI', 14)
        layout = dwfactory.CreateTextLayout('Line 1\nLine 2\nLine 3', fmt, 300, 200)
        metrics = layout.GetLineMetrics()
        self.assertGreater(len(metrics), 0)
        self.assertEqual(len(metrics), 3)
        for i, lm in enumerate(metrics):
            self.assertGreater(lm.length, 0)
            self.assertGreater(lm.height, 0)
            self.assertGreater(lm.baseline, 0)
            self.assertTrue(hasattr(lm, 'trailingWhitespaceLength'))
            self.assertTrue(hasattr(lm, 'newlineLength'))
            self.assertTrue(hasattr(lm, 'isTrimmed'))
        self.assertGreater(metrics[0].newlineLength, 0)

    def test_set_underline(self):
        dwfactory = pyd2d.GetDWriteFactory()
        fmt = dwfactory.CreateTextFormat('Segoe UI', 14)
        layout = dwfactory.CreateTextLayout('Hello World', fmt, 300, 50)
        layout.SetUnderline(True, 0, 5)
        layout.SetUnderline(False, 0, 5)

    def test_set_strikethrough(self):
        dwfactory = pyd2d.GetDWriteFactory()
        fmt = dwfactory.CreateTextFormat('Segoe UI', 14)
        layout = dwfactory.CreateTextLayout('Hello World', fmt, 300, 50)
        layout.SetStrikethrough(True, 0, 5)
        layout.SetStrikethrough(False, 0, 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
