"""D2DCheckbox 测试 — 状态机 + D2D 渲染无异常。"""
import unittest
import wx
import pyd2d
from sheskin.controls import D2DCheckbox
from sheskin.draw_context import DrawContext

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


class TestD2DCheckbox(unittest.TestCase):
    """D2DCheckbox 状态机测试。"""

    def test_init_defaults(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option")
        self.assertEqual(cb.text, "Option")
        self.assertEqual(cb.checked, False)
        self.assertEqual(cb._state, D2DCheckbox.NORMAL)
        self.assertEqual(cb.rect, (10, 10, 120, 24))

    def test_init_checked(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option", checked=True)
        self.assertTrue(cb.checked)

    def test_toggle_on_mouse_up(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option")
        cb.on_mouse_down((20, 20))
        self.assertEqual(cb._state, D2DCheckbox.PRESSED)
        self.assertFalse(cb.checked)

        cb.on_mouse_up((20, 20))
        self.assertEqual(cb._state, D2DCheckbox.HOVER)
        self.assertTrue(cb.checked)

    def test_toggle_back(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option", checked=True)
        cb.on_mouse_down((20, 20))
        cb.on_mouse_up((20, 20))
        self.assertFalse(cb.checked)

    def test_callback_on_toggle(self):
        calls = []
        cb = D2DCheckbox((10, 10, 120, 24), "Option",
                         on_toggle=lambda v: calls.append(v))
        cb.on_mouse_down((20, 20))
        cb.on_mouse_up((20, 20))
        self.assertEqual(calls, [True])

        cb.on_mouse_down((20, 20))
        cb.on_mouse_up((20, 20))
        self.assertEqual(calls, [True, False])

    def test_disabled_no_toggle(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option", checked=False)
        cb._state = D2DCheckbox.DISABLED
        self.assertFalse(cb.on_mouse_down((20, 20)))
        self.assertFalse(cb.on_mouse_up((20, 20)))
        self.assertFalse(cb.checked)

    def test_disabled_checked_stays(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option", checked=True)
        cb._state = D2DCheckbox.DISABLED
        cb.on_mouse_down((20, 20))
        cb.on_mouse_up((20, 20))
        self.assertTrue(cb.checked)

    def test_hover_state(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option")
        cb.on_mouse_move((20, 20))
        self.assertEqual(cb._state, D2DCheckbox.HOVER)

    def test_mouse_leave(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option")
        cb.on_mouse_move((20, 20))
        self.assertEqual(cb._state, D2DCheckbox.HOVER)
        cb.on_mouse_leave()
        self.assertEqual(cb._state, D2DCheckbox.NORMAL)

    def test_mouse_leave_pressed(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option")
        cb.on_mouse_down((20, 20))
        self.assertEqual(cb._state, D2DCheckbox.PRESSED)
        cb.on_mouse_leave()
        self.assertEqual(cb._state, D2DCheckbox.NORMAL)

    def test_mouse_down_outside_ignored(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option")
        self.assertFalse(cb.on_mouse_down((200, 200)))
        self.assertEqual(cb._state, D2DCheckbox.NORMAL)

    def test_setters(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option")
        cb.set_rect((5, 5, 100, 30))
        self.assertEqual(cb.rect, (5, 5, 100, 30))
        cb.set_text("Changed")
        self.assertEqual(cb.text, "Changed")
        cb.set_checked(True)
        self.assertTrue(cb.checked)

        toggled = []
        cb.set_on_toggle(lambda v: toggled.append(v))
        cb._on_toggle(True)
        self.assertEqual(toggled, [True])

    def test_init_thirdstate(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option", is_thirdstate=True)
        self.assertTrue(cb.is_thirdstate)
        self.assertFalse(cb.checked)

    def test_set_thirdstate(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option")
        self.assertFalse(cb.is_thirdstate)
        cb.set_thirdstate(True)
        self.assertTrue(cb.is_thirdstate)
        cb.set_thirdstate(False)
        self.assertFalse(cb.is_thirdstate)

    def test_set_checked_clears_thirdstate(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option", is_thirdstate=True)
        self.assertTrue(cb.is_thirdstate)
        cb.set_checked(True)
        self.assertTrue(cb.checked)
        self.assertFalse(cb.is_thirdstate)

    def test_thirdstate_click_clears(self):
        cb = D2DCheckbox((10, 10, 120, 24), "Option", is_thirdstate=True)
        cb.on_mouse_down((20, 20))
        cb.on_mouse_up((20, 20))
        self.assertFalse(cb.is_thirdstate)
        self.assertFalse(cb.checked)


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestD2DCheckboxDraw(unittest.TestCase):
    """验证 D2DCheckbox.draw 不抛异常。"""

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
        cb = D2DCheckbox((10, 10, 200, 30), "Unchecked")
        ctx.rt.BeginDraw()
        cb.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_checked(self):
        ctx = self._make_ctx()
        cb = D2DCheckbox((10, 10, 200, 30), "Checked", checked=True)
        ctx.rt.BeginDraw()
        cb.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_disabled_unchecked(self):
        ctx = self._make_ctx()
        cb = D2DCheckbox((10, 10, 200, 30), "Disabled")
        cb._state = D2DCheckbox.DISABLED
        ctx.rt.BeginDraw()
        cb.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_disabled_checked(self):
        ctx = self._make_ctx()
        cb = D2DCheckbox((10, 10, 200, 30), "Disabled", checked=True)
        cb._state = D2DCheckbox.DISABLED
        ctx.rt.BeginDraw()
        cb.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()

    def test_draw_all_states(self):
        ctx = self._make_ctx(200, 200)
        cb = D2DCheckbox((10, 10, 180, 30), "State Test")
        for third in (False, True):
            for checked in (False, True):
                for state in (D2DCheckbox.NORMAL, D2DCheckbox.HOVER,
                              D2DCheckbox.PRESSED, D2DCheckbox.DISABLED):
                    cb._state = state
                    cb._checked = checked
                    cb._is_thirdstate = third and not checked
                    ctx.rt.BeginDraw()
                    cb.draw(ctx, (0, 0, 200, 200))
                    ctx.rt.EndDraw()

    def test_draw_thirdstate(self):
        ctx = self._make_ctx()
        cb = D2DCheckbox((10, 10, 200, 30), "Indeterminate", is_thirdstate=True)
        ctx.rt.BeginDraw()
        cb.draw(ctx, (0, 0, 300, 60))
        ctx.rt.EndDraw()


if __name__ == '__main__':
    unittest.main()