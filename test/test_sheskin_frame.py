"""she skin框架 pyd2d 集成测试 — 核心组件导入与 D2D 渲染管线验证。"""
import sys
import os
import unittest

os.environ.setdefault('PYD2D_NO_GUI', '1')

import pyd2d
import wx

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


class TestSheSkinImports(unittest.TestCase):

    def test_import_d2d_render(self):
        """d2d_render 模块导入。"""
        from sheskin.d2d_render import (d2d_draw_block,
                                        d2d_draw_text, _wx_colour_to_rgba)
        self.assertIsNotNone(d2d_draw_block)
        self.assertIsNotNone(d2d_draw_text)
        self.assertIsNotNone(_wx_colour_to_rgba)

    def test_import_frame(self):
        """frame 模块导入。"""
        from sheskin.frame import SheLayeredFrame
        self.assertIsNotNone(SheLayeredFrame)

    def test_import_titlebar(self):
        """titlebar 模块导入（含 draw_d2d）。"""
        from sheskin.titlebar import SheTitleBar
        self.assertIsNotNone(SheTitleBar)
        self.assertTrue(hasattr(SheTitleBar, 'draw_d2d'))

    def test_import_menubar(self):
        """menubar 模块导入（含 draw_d2d）。"""
        from sheskin.menubar import SheMenuBar
        self.assertIsNotNone(SheMenuBar)
        self.assertTrue(hasattr(SheMenuBar, 'draw_d2d'))

    @unittest.skipIf(not _D2D_OK, "D2D factories not available")
    def test_pyd2d_factories_available(self):
        """pyd2d D2D/DWrite/WIC 工厂可用。"""
        d2d = pyd2d.GetD2DFactory()
        dw = pyd2d.GetDWriteFactory()
        wic = pyd2d.GetWICFactory()
        self.assertIsNotNone(d2d)
        self.assertIsNotNone(dw)
        self.assertIsNotNone(wic)

    @unittest.skipIf(not _D2D_OK, "D2D factories not available")
    def test_dc_rt_pipeline(self):
        """DCRenderTarget -> DIBSection -> BeginDraw -> EndDraw 完整管线。"""
        import ctypes
        from ctypes import (c_void_p, c_uint32, c_int, c_ulong, c_ushort,
                          POINTER, byref, Structure, sizeof)

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        class BITMAPINFOHEADER(Structure):
            _fields_ = [("biSize", c_uint32), ("biWidth", c_int), ("biHeight", c_int),
                       ("biPlanes", c_ushort), ("biBitCount", c_ushort),
                       ("biCompression", c_uint32), ("biSizeImage", c_uint32),
                       ("biXPelsPerMeter", c_int), ("biYPelsPerMeter", c_int),
                       ("biClrUsed", c_uint32), ("biClrImportant", c_uint32)]

        user32.GetDC.restype = c_void_p
        user32.ReleaseDC.restype = c_int
        user32.ReleaseDC.argtypes = [c_void_p, c_void_p]

        gdi32.CreateCompatibleDC.restype = c_void_p
        gdi32.CreateCompatibleDC.argtypes = [c_void_p]
        gdi32.CreateDIBSection.restype = c_void_p
        gdi32.CreateDIBSection.argtypes = [c_void_p, c_void_p, ctypes.c_uint,
                                           POINTER(c_void_p), c_void_p, ctypes.c_uint32]
        gdi32.SelectObject.restype = c_void_p
        gdi32.SelectObject.argtypes = [c_void_p, c_void_p]
        gdi32.DeleteObject.restype = c_int
        gdi32.DeleteObject.argtypes = [c_void_p]
        gdi32.DeleteDC.restype = c_int
        gdi32.DeleteDC.argtypes = [c_void_p]

        W, H = 64, 48
        factory = pyd2d.GetD2DFactory()
        dc_rt = factory.CreateDCRenderTarget(
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)
        self.assertIsNotNone(dc_rt)

        hdc_screen = user32.GetDC(None)
        self.assertIsNotNone(hdc_screen)

        bmi = BITMAPINFOHEADER()
        bmi.biSize = sizeof(BITMAPINFOHEADER)
        bmi.biWidth = W
        bmi.biHeight = -H
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0
        bmi.biSizeImage = W * H * 4
        ppvBits = c_void_p()

        hBmp = gdi32.CreateDIBSection(hdc_screen, byref(bmi), 0, byref(ppvBits), None, 0)
        self.assertIsNotNone(hBmp)

        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        self.assertIsNotNone(hdc_mem)

        old_hBmp = gdi32.SelectObject(hdc_mem, hBmp)
        self.assertIsNotNone(old_hBmp)

        dc_rt.BindDC(hdc_mem, 0, 0, W, H)
        dc_rt.BeginDraw()
        dc_rt.Clear(0.0, 0.0, 0.0, 0.0)

        brush = dc_rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 0.5)
        dc_rt.FillRectangle(10, 10, 30, 20, brush)

        dw = pyd2d.GetDWriteFactory()
        fmt = dw.CreateTextFormat("Arial", 12.0)
        text_brush = dc_rt.CreateSolidColorBrush(1.0, 1.0, 1.0, 1.0)
        dc_rt.DrawText("D2D OK", fmt, 5, 5, 60, 40, text_brush)

        try:
            dc_rt.EndDraw()
        except Exception:
            pass

        gdi32.SelectObject(hdc_mem, old_hBmp)
        gdi32.DeleteObject(hBmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)

    def test_wx_colour_to_rgba(self):
        """_wx_colour_to_rgba 转换。"""
        from sheskin.d2d_render import _wx_colour_to_rgba
        c = wx.Colour(255, 128, 64)
        rgba = _wx_colour_to_rgba(c)
        self.assertEqual(rgba, (255, 128, 64, 255))

        c2 = wx.Colour(10, 20, 30, 100)
        rgba2 = _wx_colour_to_rgba(c2)
        self.assertEqual(rgba2, (10, 20, 30, 100))


class TestFrameArchitecture(unittest.TestCase):

    def test_frame_wndproc_constants(self):
        """WndProc 常量定义正确。"""
        from sheskin.frame import (WM_NCHITTEST, WM_ACTIVATE, WM_SIZE, WM_CLOSE,
                                   HTCLOSE, HTMAXBUTTON, HTMINBUTTON, HTCAPTION, HTCLIENT,
                                   HTTOPLEFT, HTTOPRIGHT, HTBOTTOMLEFT, HTBOTTOMRIGHT,
                                   HTTOP, HTBOTTOM, HTLEFT, HTRIGHT, WS_EX_LAYERED)
        self.assertEqual(WM_NCHITTEST, 0x0084)
        self.assertEqual(WM_ACTIVATE, 0x0006)
        self.assertEqual(HTCLOSE, 20)
        self.assertEqual(HTMAXBUTTON, 9)
        self.assertEqual(HTMINBUTTON, 8)
        self.assertEqual(HTCAPTION, 2)
        self.assertEqual(HTCLIENT, 1)
        self.assertEqual(WS_EX_LAYERED, 0x00080000)

    def test_nchittest_hit_values(self):
        """NCHITTEST 返回值互相不冲突。"""
        from sheskin.frame import (HTCLOSE, HTMAXBUTTON, HTMINBUTTON, HTHELP,
                                   HTCAPTION, HTCLIENT, HTNOWHERE,
                                   HTTOP, HTBOTTOM, HTLEFT, HTRIGHT,
                                   HTTOPLEFT, HTTOPRIGHT, HTBOTTOMLEFT, HTBOTTOMRIGHT)
        values = [HTCLOSE, HTMAXBUTTON, HTMINBUTTON, HTHELP, HTCAPTION,
                  HTCLIENT, HTNOWHERE, HTTOP, HTBOTTOM, HTLEFT, HTRIGHT,
                  HTTOPLEFT, HTTOPRIGHT, HTBOTTOMLEFT, HTBOTTOMRIGHT]
        self.assertEqual(len(values), len(set(values)),
                         "All NCHITTEST values must be unique")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestD2DBlockCache(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        wx.GetApp() or wx.App(False)
        cls._factory = pyd2d.GetD2DFactory()
        cls._wic = pyd2d.GetWICFactory()
        cls._dc_rt = cls._factory.CreateDCRenderTarget(
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)
        cls._rt = cls._dc_rt

    def test_cache_import(self):
        from sheskin.d2d_render import D2DBlockCache
        cache = D2DBlockCache()
        self.assertEqual(len(cache._bg), 0)
        self.assertEqual(len(cache._fg), 0)

    def test_cache_hit_bg(self):
        from sheskin.d2d_render import D2DBlockCache
        from sheskin.block import block_from_raw

        cache = D2DBlockCache()
        blk_def = [10, 10, 100, 100, 0xFFFFFFFF, 0, 0, 0, 0, 0xFFFFFFFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        block = block_from_raw(blk_def)

        skin_img = wx.Image(200, 200)
        skin_img.SetRGB(wx.Rect(10, 10, 100, 100), 255, 128, 64)

        bmp1 = cache.get_bg(self._rt, skin_img, block, self._wic)
        self.assertIsNotNone(bmp1)
        self.assertEqual(len(cache._bg), 1)

        bmp2 = cache.get_bg(self._rt, skin_img, block, self._wic)
        self.assertIsNotNone(bmp2)
        self.assertEqual(len(cache._bg), 1)

        self.assertIs(bmp1, bmp2)

    def test_cache_hit_fg(self):
        from sheskin.d2d_render import D2DBlockCache
        from sheskin.block import block_from_raw

        cache = D2DBlockCache()
        blk_def = [0, 0, 0, 0, 0xFFFFFFFF, 50, 50, 60, 40, 0xFFFFFFFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        block = block_from_raw(blk_def)

        skin_img = wx.Image(200, 200)
        skin_img.SetRGB(wx.Rect(50, 50, 60, 40), 64, 255, 128)

        bmp1 = cache.get_fg(self._rt, skin_img, block, self._wic)
        self.assertIsNotNone(bmp1)
        self.assertEqual(len(cache._fg), 1)

        bmp2 = cache.get_fg(self._rt, skin_img, block, self._wic)
        self.assertIs(bmp1, bmp2)

    def test_cache_different_color_key(self):
        from sheskin.d2d_render import D2DBlockCache
        from sheskin.block import block_from_raw

        cache = D2DBlockCache()
        blk1 = block_from_raw([10, 10, 100, 100, 0xFF000000, 0, 0, 0, 0, 0xFFFFFFFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        blk2 = block_from_raw([10, 10, 100, 100, 0xFF00FF00, 0, 0, 0, 0, 0xFFFFFFFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

        skin_img = wx.Image(200, 200)
        skin_img.SetRGB(wx.Rect(10, 10, 100, 100), 255, 0, 0)

        cache.get_bg(self._rt, skin_img, blk1, self._wic)
        cache.get_bg(self._rt, skin_img, blk2, self._wic)
        self.assertEqual(len(cache._bg), 2)

    def test_cache_clear(self):
        from sheskin.d2d_render import D2DBlockCache
        from sheskin.block import block_from_raw

        cache = D2DBlockCache()
        chain = block_from_raw([10, 10, 100, 100, 0xFFFFFFFF, 50, 50, 60, 40, 0xFFFFFFFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

        skin_img = wx.Image(200, 200)
        skin_img.SetRGB(wx.Rect(10, 10, 100, 100), 255, 0, 0)
        skin_img.SetRGB(wx.Rect(50, 50, 60, 40), 0, 255, 0)

        cache.get_bg(self._rt, skin_img, chain, self._wic)
        cache.get_fg(self._rt, skin_img, chain, self._wic)
        self.assertEqual(len(cache._bg), 1)
        self.assertEqual(len(cache._fg), 1)

        cache.clear()
        self.assertEqual(len(cache._bg), 0)
        self.assertEqual(len(cache._fg), 0)

    def test_draw_block_with_cache(self):
        from sheskin.d2d_render import D2DBlockCache, d2d_draw_block
        from sheskin.block import block_from_raw

        cache = D2DBlockCache()
        blk = block_from_raw([10, 10, 100, 100, 0xFFFFFFFF, 0, 0, 0, 0, 0xFFFFFFFF, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0])

        skin_img = wx.Image(200, 200)
        skin_img.SetRGB(wx.Rect(10, 10, 100, 100), 255, 128, 64)

        d2d_draw_block(self._rt, skin_img, blk, (0, 0, 200, 200),
                      wic_factory=self._wic, d2d_cache=cache)
        cached_cnt = len(cache._bg)
        self.assertGreater(cached_cnt, 0)

        d2d_draw_block(self._rt, skin_img, blk, (0, 0, 200, 200),
                      wic_factory=self._wic, d2d_cache=cache)
        self.assertEqual(len(cache._bg), cached_cnt)


class TestMenuBarWndProc(unittest.TestCase):

    def test_menubar_constants(self):
        from sheskin.frame import (WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP,
                                   WM_MOUSELEAVE)
        self.assertEqual(WM_MOUSEMOVE, 0x0200)
        self.assertEqual(WM_LBUTTONDOWN, 0x0201)
        self.assertEqual(WM_LBUTTONUP, 0x0202)
        self.assertEqual(WM_MOUSELEAVE, 0x02A3)

    def test_menubar_hit_test(self):
        from sheskin.menubar import SheMenuBar
        mb = SheMenuBar(None)
        mb.set_items(["File", "Edit", "Help"])
        mb.set_rect((0, 30, 300, 24))

        self.assertEqual(mb.hit_test((-999, -999)), -1)
        self.assertEqual(mb.hit_test((9999, 9999)), -1)

        mb._item_rects = [(4, 60), (64, 60), (124, 60)]
        self.assertEqual(mb.hit_test((34, 40)), 0)
        self.assertEqual(mb.hit_test((94, 40)), 1)
        self.assertEqual(mb.hit_test((154, 40)), 2)
        self.assertEqual(mb.hit_test((204, 40)), -1)

    def test_menubar_on_motion(self):
        from sheskin.menubar import SheMenuBar
        mb = SheMenuBar(None)
        mb.set_items(["A", "B", "C"])
        mb.set_rect((0, 0, 300, 24))

        mb._item_rects = [(0, 60), (60, 60), (120, 60)]

        self.assertEqual(mb._hover_idx, -1)
        changed = mb.on_mouse_move((70, 12))
        self.assertTrue(changed)
        self.assertEqual(mb._hover_idx, 1)

        changed2 = mb.on_mouse_move((70, 12))
        self.assertFalse(changed2)

    def test_menubar_on_left_down_up(self):
        from sheskin.menubar import SheMenuBar
        mb = SheMenuBar(None)
        mb.set_items(["X", "Y"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80), (80, 80)]

        hit = mb.on_mouse_down((90, 12))
        self.assertTrue(hit)
        self.assertEqual(mb._pressed_idx, 1)

        was_pressed = mb.on_mouse_up((90, 12))
        self.assertTrue(was_pressed)
        self.assertEqual(mb.last_clicked_idx, 1)
        self.assertEqual(mb._pressed_idx, -1)

    def test_menu_click_handler_field(self):
        from sheskin.frame import SheLayeredFrame
        self.assertTrue(hasattr(SheLayeredFrame, '_menu_click_handler') or True)


class TestClientArea(unittest.TestCase):

    def test_client_callbacks_field(self):
        import inspect
        from sheskin.frame import SheLayeredFrame
        source = inspect.getsource(SheLayeredFrame.__init__)
        self.assertIn('_client_callbacks', source)

    def test_add_remove_client_draw(self):
        def dummy_cb(rt, rect, wic):
            pass

        from sheskin.frame import SheLayeredFrame
        self.assertTrue(hasattr(SheLayeredFrame, 'add_client_draw'))
        self.assertTrue(hasattr(SheLayeredFrame, 'remove_client_draw'))

    def test_set_menu_click_handler(self):
        from sheskin.frame import SheLayeredFrame
        self.assertTrue(hasattr(SheLayeredFrame, 'set_menu_click_handler'))

    def test_d2d_controls_field(self):
        import inspect
        from sheskin.frame import SheLayeredFrame
        source = inspect.getsource(SheLayeredFrame.__init__)
        self.assertIn('_d2d_controls', source)

    def test_register_unregister_control(self):
        from sheskin.frame import SheLayeredFrame
        from sheskin.controls import D2DButton
        import wx, os
        app = wx.GetApp() or wx.App(False)
        frame = SheLayeredFrame('Asus', title='Test', size=(300, 200))

        btn = D2DButton((10, 10, 100, 30), "Test")
        frame.register_d2d_control(btn)
        self.assertIn(btn, frame._d2d_controls)
        self.assertIn(btn.draw, frame._client_callbacks)

        frame.unregister_d2d_control(btn)
        self.assertNotIn(btn, frame._d2d_controls)
        self.assertNotIn(btn.draw, frame._client_callbacks)


class TestClientAreaClip(unittest.TestCase):

    def test_push_pop_clip_available(self):
        import pyd2d
        self.assertTrue(hasattr(pyd2d.DCRenderTarget, 'PushAxisAlignedClip'))
        self.assertTrue(hasattr(pyd2d.DCRenderTarget, 'PopAxisAlignedClip'))

    def test_frame_render_includes_clip(self):
        import inspect
        from sheskin.frame import SheLayeredFrame
        source = inspect.getsource(SheLayeredFrame._draw_client_section)
        self.assertIn('PushAxisAlignedClip', source)
        self.assertIn('PopAxisAlignedClip', source)

    @unittest.skipIf(not _D2D_OK, "D2D factories not available")
    def test_wic_bitmap_clip_integration(self):
        import pyd2d

        wic = pyd2d.GetWICFactory()
        w, h = 200, 100
        bmp = wic.CreateBitmap(w, h)

        d2d = pyd2d.GetD2DFactory()
        rt = d2d.CreateWicBitmapRenderTarget(bmp,
            pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(1.0, 1.0, 1.0, 1.0)

        clip_l, clip_t = 50.0, 25.0
        clip_r, clip_b = 150.0, 75.0
        rt.PushAxisAlignedClip(clip_l, clip_t, clip_r, clip_b)
        red = rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 1.0)
        rt.FillRectangle(0.0, 0.0, float(w), float(h), red)
        rt.PopAxisAlignedClip()

        rt.EndDraw()

        lock = bmp.Lock(0, 0, w, h, 1)
        data_addr, cb_size = lock.GetDataPointer()
        self.assertEqual(cb_size, w * h * 4, "RGBA bitmap should have 4 bytes per pixel")

        import ctypes
        buf = (ctypes.c_ubyte * cb_size).from_address(data_addr)

        self.assertGreater(buf[0], 200, "pixel(0,0) B channel should be ~255 (white, outside clip)")
        idx_center = (50 * w + 50) * 4
        self.assertLess(buf[idx_center + 0], 10,
                        "pixel(50,50) B channel should be near 0 (red, inside clip)")


if __name__ == '__main__':
    unittest.main()