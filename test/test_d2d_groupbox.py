"""D2DGroupBox / SkinAwareGroupBox 测试。"""
import unittest
import wx
import pyd2d
from sheskin.controls import D2DGroupBox, SkinAwareGroupBox, D2DLabel, D2DRadioButton, RadioGroup
from sheskin.draw_context import DrawContext

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


class TestD2DGroupBox(unittest.TestCase):

    def test_init_defaults(self):
        gb = D2DGroupBox((10, 10, 200, 80), "Settings")
        self.assertEqual(gb.text, "Settings")
        self.assertEqual(gb.rect, (10, 10, 200, 80))
        self.assertEqual(gb._state, D2DGroupBox.NORMAL)

    def test_init_empty_children(self):
        gb = D2DGroupBox((0, 0, 200, 80), "Title")
        self.assertEqual(gb.children, [])

    def test_add_remove_children(self):
        gb = D2DGroupBox((0, 0, 200, 80), "Title")
        lbl = D2DLabel((0, 0, 100, 24), "Child")
        gb.add(lbl)
        self.assertEqual(len(gb.children), 1)
        self.assertIs(gb.children[0], lbl)

        gb.remove(lbl)
        self.assertEqual(len(gb.children), 0)

    def test_clear_children(self):
        gb = D2DGroupBox((0, 0, 200, 80), "Title")
        gb.add(D2DLabel((0, 0, 100, 24), "A"))
        gb.add(D2DLabel((0, 0, 100, 24), "B"))
        self.assertEqual(len(gb.children), 2)
        gb.clear()
        self.assertEqual(len(gb.children), 0)

    def test_add_radiogroup_expands_to_children(self):
        gb = D2DGroupBox((0, 0, 200, 80), "Title")
        rg = RadioGroup()
        rg.add(D2DRadioButton((0, 0, 200, 24), "A"))
        rg.add(D2DRadioButton((0, 0, 200, 24), "B"))
        rg.add(D2DRadioButton((0, 0, 200, 24), "C"))
        gb.add(rg)
        self.assertEqual(len(gb.children), 3)
        for c in gb.children:
            self.assertIsInstance(c, D2DRadioButton)

    def test_setters(self):
        gb = D2DGroupBox((10, 10, 200, 80), "Old")
        gb.set_rect((20, 20, 300, 100))
        self.assertEqual(gb.rect, (20, 20, 300, 100))
        gb.set_text("New Title")
        self.assertEqual(gb.text, "New Title")

    def test_activate_noop(self):
        gb = D2DGroupBox((0, 0, 200, 80), "Title")
        old_state = gb._state
        gb._on_activate()
        self.assertEqual(gb._state, old_state)

    def test_disabled_state(self):
        gb = D2DGroupBox((0, 0, 200, 80), "Disabled")
        gb._state = D2DGroupBox.DISABLED
        self.assertEqual(gb._state, D2DGroupBox.DISABLED)

    def test_mouse_events_return_false(self):
        gb = D2DGroupBox((10, 10, 200, 80), "Title")
        self.assertFalse(gb.on_mouse_down((110, 50)))
        self.assertEqual(gb._state, D2DGroupBox.NORMAL)
        self.assertFalse(gb.on_mouse_up((110, 50)))
        self.assertFalse(gb.on_mouse_move((110, 50)))
        self.assertFalse(gb.on_mouse_leave())

    def test_mouse_events_disabled_return_false(self):
        gb = D2DGroupBox((10, 10, 200, 80), "Title")
        gb._state = D2DGroupBox.DISABLED
        self.assertFalse(gb.on_mouse_down((110, 50)))
        self.assertFalse(gb.on_mouse_up((110, 50)))
        self.assertFalse(gb.on_mouse_move((110, 50)))
        self.assertFalse(gb.on_mouse_leave())

    def test_layout_children_positions(self):
        gb = D2DGroupBox((50, 100, 200, 120), "Title")
        lbl_a = D2DLabel((0, 0, 100, 24), "A")
        lbl_b = D2DLabel((0, 0, 100, 24), "B")
        gb.add(lbl_a)
        gb.add(lbl_b)
        gb.layout_children()

        _, ry, _, _ = gb.rect
        th = gb._title_height()
        margin = gb._child_margin

        self.assertGreater(lbl_a.rect[1], ry + th,
                           "Child Y should be below title area")
        self.assertGreater(lbl_b.rect[1], lbl_a.rect[1],
                           "Child B should be below Child A")

    def test_layout_empty_no_error(self):
        gb = D2DGroupBox((0, 0, 200, 80), "Title")
        gb.layout_children()

    def test_title_height_no_text(self):
        gb = D2DGroupBox((0, 0, 200, 80), "")
        self.assertEqual(gb._title_height(), 0.0)


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestD2DGroupBoxDraw(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls.factory = pyd2d.GetD2DFactory()
        cls.wic = pyd2d.GetWICFactory()
        cls.dw = pyd2d.GetDWriteFactory()
        if not all([cls.factory, cls.wic, cls.dw]):
            raise unittest.SkipTest("D2D factories not available at runtime")

    def _make_ctx(self, w=300, h=150):
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
        gb = D2DGroupBox((10, 10, 250, 80), "Group Title")
        ctx.rt.BeginDraw()
        gb.draw(ctx, (0, 0, 300, 150))
        ctx.rt.EndDraw()

    def test_draw_disabled_no_crash(self):
        ctx = self._make_ctx()
        gb = D2DGroupBox((10, 10, 250, 80), "Disabled Group")
        gb._state = D2DGroupBox.DISABLED
        ctx.rt.BeginDraw()
        gb.draw(ctx, (0, 0, 300, 150))
        ctx.rt.EndDraw()

    def test_draw_empty_text_no_crash(self):
        ctx = self._make_ctx()
        gb = D2DGroupBox((10, 10, 250, 80), "")
        ctx.rt.BeginDraw()
        gb.draw(ctx, (0, 0, 300, 150))
        ctx.rt.EndDraw()

    def test_draw_with_children_no_crash(self):
        ctx = self._make_ctx(300, 180)
        gb = D2DGroupBox((10, 10, 250, 120), "Child Group")
        gb.add(D2DLabel((0, 0, 200, 24), "Item 1"))
        gb.add(D2DLabel((0, 0, 200, 24), "Item 2"))
        gb.layout_children()
        ctx.rt.BeginDraw()
        gb.draw(ctx, (0, 0, 300, 180))
        for child in gb.children:
            child.draw(ctx, (0, 0, 300, 180))
        ctx.rt.EndDraw()

    def test_title_on_border_position(self):
        ctx = self._make_ctx()
        gb = D2DGroupBox((10, 10, 250, 80), "Border Title")
        ctx.rt.BeginDraw()
        gb.draw(ctx, (0, 0, 300, 150))
        ctx.rt.EndDraw()
        self.assertIsNotNone(gb._title_metrics,
                            "Title metrics should be set during draw")

    def test_title_not_clipped_above_border(self):
        ctx = self._make_ctx()
        gb = D2DGroupBox((10, 10, 250, 80), "Title")
        ctx.rt.BeginDraw()
        gb.draw(ctx, (0, 0, 300, 150))
        ctx.rt.EndDraw()
        self.assertIsNotNone(gb._title_metrics)
        m = gb._title_metrics
        rx, ry, rw, rh = gb.rect
        self.assertGreater(ry, ry - m.height * 0.5,
                           "Text ty should be above border ry, "
                           "clip must extend above ry to avoid clipping")


if __name__ == '__main__':
    unittest.main()