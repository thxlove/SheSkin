"""D2DLabel / SkinAwareLabel 测试。"""
import unittest
import wx
import pyd2d
from sheskin.controls import D2DLabel, SkinAwareLabel
from sheskin.draw_context import DrawContext

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


class TestD2DLabel(unittest.TestCase):

    def test_init_defaults(self):
        lbl = D2DLabel((10, 10, 200, 24), "Hello")
        self.assertEqual(lbl.text, "Hello")
        self.assertEqual(lbl.rect, (10, 10, 200, 24))
        self.assertEqual(lbl._state, D2DLabel.NORMAL)

    def test_setters(self):
        lbl = D2DLabel((10, 10, 120, 24), "Old")
        lbl.set_rect((20, 20, 200, 30))
        self.assertEqual(lbl.rect, (20, 20, 200, 30))

        lbl.set_text("New")
        self.assertEqual(lbl.text, "New")

    def test_activate_noop(self):
        lbl = D2DLabel((0, 0, 100, 24), "X")
        old_state = lbl._state
        old_text = lbl.text
        lbl._on_activate()
        self.assertEqual(lbl._state, old_state)
        self.assertEqual(lbl.text, old_text)

    def test_disabled_state(self):
        lbl = D2DLabel((0, 0, 100, 24), "Disabled")
        lbl._state = D2DLabel.DISABLED
        self.assertEqual(lbl._state, D2DLabel.DISABLED)

    def test_hover_and_pressed(self):
        lbl = D2DLabel((10, 10, 120, 24), "Hover")
        self.assertFalse(lbl.on_mouse_down((20, 20)))
        self.assertEqual(lbl._state, D2DLabel.NORMAL)

        self.assertFalse(lbl.on_mouse_move((20, 20)))
        self.assertEqual(lbl._state, D2DLabel.NORMAL)

        self.assertFalse(lbl.on_mouse_leave())
        self.assertEqual(lbl._state, D2DLabel.NORMAL)


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestD2DLabelDraw(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls.factory = pyd2d.GetD2DFactory()
        cls.wic = pyd2d.GetWICFactory()
        cls.dw = pyd2d.GetDWriteFactory()
        if not all([cls.factory, cls.wic, cls.dw]):
            raise unittest.SkipTest("D2D factories not available at runtime")

    def _make_ctx(self, w=300, h=60):
        wic_bmp = self.wic.CreateBitmap(w, h)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)
        return DrawContext(rt=rt, skin=None, wic_factory=self.wic,
                           dw_factory=self.dw)

    def test_draw_no_crash(self):
        ctx = self._make_ctx()
        lbl = D2DLabel((10, 10, 200, 30), "Test Label")
        ctx.rt.BeginDraw()
        lbl.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_disabled_no_crash(self):
        ctx = self._make_ctx()
        lbl = D2DLabel((10, 10, 200, 30), "Disabled Label")
        lbl._state = D2DLabel.DISABLED
        ctx.rt.BeginDraw()
        lbl.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_empty_text_no_crash(self):
        ctx = self._make_ctx()
        lbl = D2DLabel((10, 10, 200, 30), "")
        ctx.rt.BeginDraw()
        lbl.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_multiline_reinit_no_crash(self):
        ctx = self._make_ctx()
        lbl = D2DLabel((0, 0, 200, 50), "Line1\nLine2")
        ctx.rt.BeginDraw()
        lbl.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()


if __name__ == '__main__':
    unittest.main()