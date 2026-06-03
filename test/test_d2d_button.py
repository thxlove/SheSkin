"""D2DButton 交互控件测试 (TDD)。"""
import unittest
import wx
import pyd2d
from sheskin.controls import D2DButton
from sheskin.draw_context import DrawContext

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


class TestD2DButton(unittest.TestCase):

    def test_init_defaults(self):
        btn = D2DButton((10, 20, 100, 30), "OK")
        self.assertEqual(btn.rect, (10, 20, 100, 30))
        self.assertEqual(btn.text, "OK")
        self.assertEqual(btn._state, D2DButton.NORMAL)

    def test_hit_test_inside(self):
        btn = D2DButton((0, 0, 100, 40), "X")
        self.assertTrue(btn.hit_test((50, 20)))
        self.assertTrue(btn.hit_test((0, 0)))
        self.assertTrue(btn.hit_test((99, 39)))

    def test_hit_test_outside(self):
        btn = D2DButton((10, 10, 50, 20), "X")
        self.assertFalse(btn.hit_test((-1, 10)))
        self.assertFalse(btn.hit_test((10, -1)))
        self.assertFalse(btn.hit_test((61, 10)))
        self.assertFalse(btn.hit_test((10, 31)))

    def test_mouse_down_up_state(self):
        btn = D2DButton((10, 10, 100, 30), "X")
        self.assertEqual(btn._state, D2DButton.NORMAL)

        hit = btn.on_mouse_down((50, 20))
        self.assertTrue(hit)
        self.assertEqual(btn._state, D2DButton.PRESSED)

        hit = btn.on_mouse_up((50, 20))
        self.assertTrue(hit)
        self.assertEqual(btn._state, D2DButton.HOVER)

    def test_mouse_down_outside_ignored(self):
        btn = D2DButton((10, 10, 100, 30), "X")
        hit = btn.on_mouse_down((200, 200))
        self.assertFalse(hit)
        self.assertEqual(btn._state, D2DButton.NORMAL)

    def test_mouse_hover_state(self):
        btn = D2DButton((10, 10, 100, 30), "X")
        self.assertEqual(btn._state, D2DButton.NORMAL)

        changed = btn.on_mouse_move((50, 20))
        self.assertTrue(changed)
        self.assertEqual(btn._state, D2DButton.HOVER)

        changed = btn.on_mouse_move((50, 20))
        self.assertFalse(changed)

        changed = btn.on_mouse_move((200, 200))
        self.assertTrue(changed)
        self.assertEqual(btn._state, D2DButton.NORMAL)

    def test_mouse_leave(self):
        btn = D2DButton((10, 10, 100, 30), "X")
        btn.on_mouse_move((50, 20))
        self.assertEqual(btn._state, D2DButton.HOVER)

        changed = btn.on_mouse_leave()
        self.assertTrue(changed)
        self.assertEqual(btn._state, D2DButton.NORMAL)

        changed = btn.on_mouse_leave()
        self.assertFalse(changed)

    def test_click_callback(self):
        calls = []
        btn = D2DButton((10, 10, 100, 30), "X",
                        on_click=lambda: calls.append(1))

        btn.on_mouse_down((50, 20))
        btn.on_mouse_up((50, 20))
        self.assertEqual(len(calls), 1)

        btn.on_mouse_down((50, 20))
        btn.on_mouse_up((200, 200))
        self.assertEqual(len(calls), 1)

    def test_double_click_two_callbacks(self):
        calls = []
        btn = D2DButton((10, 10, 100, 30), "X",
                        on_click=lambda: calls.append(1))

        btn.on_mouse_down((50, 20))
        btn.on_mouse_up((50, 20))
        self.assertEqual(len(calls), 1)

        btn.on_mouse_down((50, 20))
        btn.on_mouse_up((50, 20))
        self.assertEqual(len(calls), 2)

    def test_disabled_ignores_events(self):
        btn = D2DButton((10, 10, 100, 30), "X",
                        on_click=lambda: None)
        btn._state = D2DButton.DISABLED

        self.assertFalse(btn.on_mouse_down((50, 20)))
        self.assertEqual(btn._state, D2DButton.DISABLED)

        self.assertFalse(btn.on_mouse_up((50, 20)))
        self.assertEqual(btn._state, D2DButton.DISABLED)

        self.assertFalse(btn.on_mouse_move((50, 20)))
        self.assertEqual(btn._state, D2DButton.DISABLED)

        self.assertFalse(btn.on_mouse_leave())
        self.assertEqual(btn._state, D2DButton.DISABLED)

    def test_setters(self):
        btn = D2DButton((10, 10, 100, 30), "Old")
        btn.set_rect((20, 20, 200, 50))
        self.assertEqual(btn.rect, (20, 20, 200, 50))

        btn.set_text("New")
        self.assertEqual(btn.text, "New")

        calls = []
        btn.set_on_click(lambda: calls.append(1))
        btn._state = D2DButton.NORMAL
        btn.on_mouse_down((100, 40))
        btn.on_mouse_up((100, 40))
        self.assertEqual(len(calls), 1)


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestD2DButtonDraw(unittest.TestCase):
    """验证 D2DButton.draw 不抛异常。"""

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls.factory = pyd2d.GetD2DFactory()
        cls.wic = pyd2d.GetWICFactory()
        cls.dw = pyd2d.GetDWriteFactory()
        if not all([cls.factory, cls.wic, cls.dw]):
            raise unittest.SkipTest("D2D factories not available at runtime")

    def _make_ctx(self, w=200, h=100):
        wic_bmp = self.wic.CreateBitmap(w, h)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)
        return DrawContext(rt=rt, skin=None, wic_factory=self.wic,
                           dw_factory=self.dw)

    def _make_rt(self, w=200, h=100):
        return self._make_ctx(w, h).rt

    def test_draw_normal_does_not_crash(self):
        ctx = self._make_ctx()
        rt = ctx.rt
        btn = D2DButton((0, 0, 100, 30), "OK")
        rt.BeginDraw()
        btn.draw(ctx, (0, 0, 200, 100))
        rt.EndDraw()

    def test_draw_all_states(self):
        ctx = self._make_ctx()
        rt = ctx.rt
        btn = D2DButton((10, 10, 120, 36), "States")

        for state in (D2DButton.NORMAL, D2DButton.HOVER,
                      D2DButton.PRESSED, D2DButton.DISABLED):
            btn._state = state
            rt.BeginDraw()
            btn.draw(ctx, (0, 0, 200, 100))
            rt.EndDraw()


if __name__ == '__main__':
    unittest.main()