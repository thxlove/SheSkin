"""Minimal standalone test for PushLayer + opacityBrush (BitmapBrush)."""
import ctypes
from ctypes import wintypes
import numpy as np
import wx
import pyd2d

# Ensure wx.App exists before using pyd2d factories
wx.GetApp() or wx.App(False)

W, H = 300, 200


class TestOpacityBrush:
    @classmethod
    def setup_class(cls):
        cls.d2d_factory = pyd2d.GetD2DFactory()
        cls.wic_factory = pyd2d.GetWICFactory()
        # Use WicBitmapRenderTarget instead of DCRenderTarget + DIB section
        # DCRenderTarget.BindDC does not reliably write to DIB sections
        wic_bmp = cls.wic_factory.CreateBitmap(W, H)
        cls.rt = cls.d2d_factory.CreateWicBitmapRenderTarget(
            wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)

    def _read_pixels(self):
        """Read pixels from the WIC bitmap render target."""
        # Re-create a fresh WIC bitmap + RT for each test to avoid state leakage
        wic_bmp = self.wic_factory.CreateBitmap(W, H)
        rt = self.d2d_factory.CreateWicBitmapRenderTarget(
            wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=96.0, dpiY=96.0)
        return rt, wic_bmp

    def _pixel_data(self, wic_bmp):
        lock = wic_bmp.Lock(0, 0, W, H, 2)  # WICBitmapLockRead
        addr, cb = lock.GetDataPointer()
        buf = (ctypes.c_ubyte * cb).from_address(addr)
        return np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 4)

    def test_no_opacity_brush(self):
        rt, wic_bmp = self._read_pixels()
        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        red = rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 1.0)
        rt.FillRectangle(0.0, 0.0, float(W), float(H), red)
        rt.EndDraw()

        data = self._pixel_data(wic_bmp)
        assert data[0, 0, 2] > 200, f"TL R channel should be ~255, got {data[0,0,2]}"
        assert data[H//2, W//2, 2] > 200, f"Center R channel should be ~255"
        assert data[H//2, W//2, 3] > 200, f"Center alpha should be ~255"

    def test_with_opacity_brush(self):
        rt, wic_bmp = self._read_pixels()

        mask = np.full((H, W), 255, dtype=np.uint8)
        mask[0:30, 0:20] = 0
        mask[0:30, W-20:W] = 0
        mask[H-30:H, 0:20] = 0
        mask[H-30:H, W-20:W] = 0

        a = mask.astype(np.float32) / 255.0
        bgra = np.zeros((H, W, 4), dtype=np.uint8)
        bgra[:, :, 0] = (mask.astype(np.float32) * a).astype(np.uint8)
        bgra[:, :, 1] = (mask.astype(np.float32) * a).astype(np.uint8)
        bgra[:, :, 2] = (mask.astype(np.float32) * a).astype(np.uint8)
        bgra[:, :, 3] = mask

        mask_bmp = self.wic_factory.CreateBitmap(W, H)
        lock = mask_bmp.Lock(0, 0, W, H)
        addr, cb_size = lock.GetDataPointer()
        pixel_view = (ctypes.c_ubyte * cb_size).from_address(addr)
        ctypes.memmove(pixel_view, bgra.tobytes(), cb_size)
        del lock

        d2d_bmp = rt.CreateBitmapFromWicBitmap(mask_bmp)
        alpha_brush = rt.CreateBitmapBrush(d2d_bmp)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        layer = rt.CreateLayer()
        rt.PushLayer(
            layer,
            contentLeft=0.0, contentTop=0.0,
            contentRight=float(W), contentBottom=float(H),
            opacityBrush=alpha_brush)
        red2 = rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 1.0)
        rt.FillRectangle(0.0, 0.0, float(W), float(H), red2)
        rt.PopLayer()
        rt.EndDraw()

        data2 = self._pixel_data(wic_bmp)
        # Corners should be transparent (masked out)
        assert data2[5, 5, 3] < 30, f"TL corner alpha should be ~0, got {data2[5,5,3]}"
        # Center should be opaque
        assert data2[H//2, W//2, 3] > 200, f"Center alpha should be ~255, got {data2[H//2,W//2,3]}"
        # Center should be red
        assert data2[H//2, W//2, 2] > 200, f"Center R channel should be ~255"

    def test_brush_samples_correctly(self):
        rt, wic_bmp = self._read_pixels()

        mask = np.full((H, W), 255, dtype=np.uint8)
        mask[0:30, 0:20] = 0
        mask[0:30, W-20:W] = 0
        mask[H-30:H, 0:20] = 0
        mask[H-30:H, W-20:W] = 0

        a = mask.astype(np.float32) / 255.0
        bgra = np.zeros((H, W, 4), dtype=np.uint8)
        bgra[:, :, 0] = (mask.astype(np.float32) * a).astype(np.uint8)
        bgra[:, :, 1] = (mask.astype(np.float32) * a).astype(np.uint8)
        bgra[:, :, 2] = (mask.astype(np.float32) * a).astype(np.uint8)
        bgra[:, :, 3] = mask

        mask_bmp = self.wic_factory.CreateBitmap(W, H)
        lock = mask_bmp.Lock(0, 0, W, H)
        addr, cb_size = lock.GetDataPointer()
        pixel_view = (ctypes.c_ubyte * cb_size).from_address(addr)
        ctypes.memmove(pixel_view, bgra.tobytes(), cb_size)
        del lock

        d2d_bmp = rt.CreateBitmapFromWicBitmap(mask_bmp)
        alpha_brush = rt.CreateBitmapBrush(d2d_bmp)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        green = rt.CreateSolidColorBrush(0.0, 1.0, 0.0, 1.0)
        rt.FillRectangle(50.0, 50.0, 250.0, 150.0, green)
        layer2 = rt.CreateLayer()
        rt.PushLayer(
            layer2,
            contentLeft=0.0, contentTop=0.0,
            contentRight=float(W), contentBottom=float(H),
            opacityBrush=alpha_brush)
        rt.FillRectangle(50.0, 50.0, 250.0, 150.0, green)
        rt.PopLayer()
        rt.EndDraw()

        data3 = self._pixel_data(wic_bmp)
        # Center should be green and visible
        assert data3[75, 75, 1] > 200, f"Center G channel should be ~255, got {data3[75,75,1]}"
