"""D2DRadioButton / SkinAwareRadioButton 测试。"""
import unittest
import wx
import pyd2d
from sheskin.controls import D2DRadioButton
from sheskin.draw_context import DrawContext

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


class TestD2DRadioButton(unittest.TestCase):
    """D2DRadioButton 状态机测试。"""

    def test_init_defaults(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Option")
        self.assertEqual(rb.text, "Option")
        self.assertEqual(rb.checked, False)
        self.assertEqual(rb._state, D2DRadioButton.NORMAL)
        self.assertEqual(rb.rect, (10, 10, 120, 24))

    def test_init_checked(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Option", checked=True)
        self.assertTrue(rb.checked)

    def test_click_selects(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Option")
        rb.on_mouse_down((20, 20))
        self.assertEqual(rb._state, D2DRadioButton.PRESSED)
        self.assertFalse(rb.checked)

        rb.on_mouse_up((20, 20))
        self.assertEqual(rb._state, D2DRadioButton.HOVER)
        self.assertTrue(rb.checked)

    def test_click_stays_checked(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Option", checked=True)
        rb.on_mouse_down((20, 20))
        rb.on_mouse_up((20, 20))
        self.assertTrue(rb.checked)

    def test_callback_on_toggle(self):
        calls = []
        rb = D2DRadioButton((10, 10, 120, 24), "Option",
                            on_toggle=lambda v: calls.append(v))
        rb.on_mouse_down((20, 20))
        rb.on_mouse_up((20, 20))
        self.assertEqual(calls, [True])

        rb.on_mouse_down((20, 20))
        rb.on_mouse_up((20, 20))
        self.assertEqual(calls, [True, True])

    def test_setters(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Old")
        rb.set_rect((20, 20, 200, 30))
        self.assertEqual(rb.rect, (20, 20, 200, 30))

        rb.set_text("New")
        self.assertEqual(rb.text, "New")

        rb.set_checked(True)
        self.assertTrue(rb.checked)
        rb.set_checked(False)
        self.assertFalse(rb.checked)

    def test_disabled_no_toggle(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Disabled")
        rb._state = D2DRadioButton.DISABLED
        self.assertFalse(rb.on_mouse_down((20, 20)))
        self.assertEqual(rb._state, D2DRadioButton.DISABLED)
        self.assertFalse(rb.checked)

        self.assertFalse(rb.on_mouse_up((20, 20)))
        self.assertFalse(rb.checked)

    def test_hover_state(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Hover")
        rb.on_mouse_move((20, 20))
        self.assertEqual(rb._state, D2DRadioButton.HOVER)

        rb.on_mouse_leave()
        self.assertEqual(rb._state, D2DRadioButton.NORMAL)

    def test_mouse_leave(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Leave")
        rb._state = D2DRadioButton.NORMAL
        self.assertFalse(rb.on_mouse_leave())
        self.assertEqual(rb._state, D2DRadioButton.NORMAL)

    def test_mouse_leave_pressed(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Captured")
        rb._state = D2DRadioButton.PRESSED
        rb._captured = True
        self.assertTrue(rb.on_mouse_leave())
        self.assertEqual(rb._state, D2DRadioButton.NORMAL)
        self.assertFalse(rb._captured)

    def test_disabled_checked_stays(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Checked", checked=True)
        rb._state = D2DRadioButton.DISABLED
        self.assertTrue(rb.checked)

    def test_mouse_down_outside_ignored(self):
        rb = D2DRadioButton((10, 10, 120, 24), "Far")
        result = rb.on_mouse_down((500, 500))
        self.assertFalse(result)
        self.assertEqual(rb._state, D2DRadioButton.NORMAL)


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestD2DRadioButtonDraw(unittest.TestCase):

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

    def test_draw_unchecked(self):
        ctx = self._make_ctx()
        rb = D2DRadioButton((10, 10, 200, 30), "Unchecked")
        ctx.rt.BeginDraw()
        rb.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_checked(self):
        ctx = self._make_ctx()
        rb = D2DRadioButton((10, 10, 200, 30), "Checked", checked=True)
        ctx.rt.BeginDraw()
        rb.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_disabled_unchecked(self):
        ctx = self._make_ctx()
        rb = D2DRadioButton((10, 10, 200, 30), "Disabled")
        rb._state = D2DRadioButton.DISABLED
        ctx.rt.BeginDraw()
        rb.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_disabled_checked(self):
        ctx = self._make_ctx()
        rb = D2DRadioButton((10, 10, 200, 30), "Disabled", checked=True)
        rb._state = D2DRadioButton.DISABLED
        ctx.rt.BeginDraw()
        rb.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_all_states(self):
        ctx = self._make_ctx()
        for checked_val in (False, True):
            for state_val in (0, 1, 2, 3):
                rb = D2DRadioButton((10, 10, 200, 30),
                                    f"State {state_val} checked {checked_val}",
                                    checked=checked_val)
                rb._state = state_val
                ctx.rt.BeginDraw()
                rb.draw(ctx, (0, 0, 300, 60))
                ctx.rt.EndDraw()


if __name__ == '__main__':
    unittest.main()