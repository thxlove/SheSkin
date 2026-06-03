"""Test pyd2d TODO 28: RenderTarget state management & transforms"""
import sys
import os
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pyd2d

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


def _make_rt():
    wic = pyd2d.GetWICFactory()
    d2d = pyd2d.GetD2DFactory()
    bmp = wic.CreateBitmap(200, 100)
    rt = d2d.CreateWicBitmapRenderTarget(
        bmp,
        rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
        pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
        alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
        dpiX=96.0, dpiY=96.0)
    return rt


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestTodo28(unittest.TestCase):

    def test_save_restore_supported(self):
        self.assertTrue(hasattr(pyd2d.RenderTarget, 'SaveDrawingState'))
        self.assertTrue(hasattr(pyd2d.RenderTarget, 'RestoreDrawingState'))
        self.assertTrue(hasattr(pyd2d.RenderTarget, 'SetTransform'))
        self.assertTrue(hasattr(pyd2d.RenderTarget, 'GetTransform'))
        self.assertTrue(hasattr(pyd2d.D2DFactory, 'CreateDrawingStateBlock'))

    def test_set_get_transform(self):
        rt = _make_rt()
        try:
            rt.BeginDraw()
            rt.SetTransform(1.0, 0.0, 0.0, 2.0, 10.0, 20.0)
            m = rt.GetTransform()
            self.assertAlmostEqual(m[0], 1.0, delta=0.001)
            self.assertAlmostEqual(m[3], 2.0, delta=0.001)
            self.assertAlmostEqual(m[4], 10.0, delta=0.001)
            self.assertAlmostEqual(m[5], 20.0, delta=0.001)
            rt.SetTransform(2.0, 0.5, 0.5, 1.0, 0.0, 0.0)
            m = rt.GetTransform()
            self.assertAlmostEqual(m[0], 2.0, delta=0.001)
            self.assertAlmostEqual(m[1], 0.5, delta=0.001)
        finally:
            rt.EndDraw()

    def test_create_drawing_state_block(self):
        factory = pyd2d.GetD2DFactory()
        block = factory.CreateDrawingStateBlock()
        self.assertIsNotNone(block)

    def test_save_restore_roundtrip(self):
        factory = pyd2d.GetD2DFactory()
        block = factory.CreateDrawingStateBlock()
        rt = _make_rt()
        try:
            rt.BeginDraw()
            rt.SetAntialiasMode(pyd2d.ANTIALIAS_MODE.ALIASED)
            rt.SetTransform(2.0, 0.0, 0.0, 1.0, 5.0, 10.0)
            rt.SaveDrawingState(block)
            rt.SetAntialiasMode(pyd2d.ANTIALIAS_MODE.PER_PRIMITIVE)
            rt.SetTransform(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
            rt.RestoreDrawingState(block)
            m = rt.GetTransform()
            self.assertAlmostEqual(m[0], 2.0, delta=0.001)
            self.assertAlmostEqual(m[4], 5.0, delta=0.001)
            self.assertAlmostEqual(m[5], 10.0, delta=0.001)
        finally:
            rt.EndDraw()

    def test_get_system_font_collection(self):
        dw = pyd2d.GetDWriteFactory()
        coll = dw.GetSystemFontCollection(False)
        self.assertIsNotNone(coll)
        count = coll.GetFontFamilyCount()
        self.assertGreater(count, 0)

    def test_enumerate_font_families(self):
        dw = pyd2d.GetDWriteFactory()
        coll = dw.GetSystemFontCollection(False)
        count = coll.GetFontFamilyCount()
        max_check = min(count, 5)
        for i in range(max_check):
            family = coll.GetFontFamily(i)
            self.assertIsNotNone(family)
            loc_names = family.GetFamilyNames()
            self.assertIsNotNone(loc_names)
            name = loc_names.GetString(0)
            self.assertGreater(len(name), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
