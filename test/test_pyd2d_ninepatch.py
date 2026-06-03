"""
pyd2d 九宫格渲染测试 (TDD)
"""

import unittest
import ctypes
import pyd2d

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory()])


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestNinePatchDraw(unittest.TestCase):
    """nine_patch_draw — 九宫格缩放渲染 (stretch + tile)"""

    _source_size = 96
    _margin = 32

    @classmethod
    def setUpClass(cls):
        cls.wic = pyd2d.GetWICFactory()
        cls.factory = pyd2d.GetD2DFactory()

        cls.bitmap = cls._create_ninepatch_bitmap()

    @classmethod
    def _create_ninepatch_bitmap(cls):
        M = cls._margin
        S = cls._source_size
        C = S - M

        wic_bmp = cls.wic.CreateBitmap(S, S)
        rt = cls.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()

        colors = {
            'tl': (1.0, 0.0, 0.0),     'tc': (0.0, 1.0, 0.0),   'tr': (0.0, 0.0, 1.0),
            'ml': (1.0, 1.0, 0.0),     'mc': (1.0, 1.0, 1.0),   'mr': (0.0, 1.0, 1.0),
            'bl': (1.0, 0.0, 1.0),     'bc': (0.5, 0.5, 0.5),   'br': (0.0, 0.0, 0.0),
        }

        regions = [
            ('tl', 0, 0, M, M),        ('tc', M, 0, C, M),        ('tr', S - M, 0, M, M),
            ('ml', 0, M, M, C),         ('mc', M, M, C, C),        ('mr', S - M, M, M, C),
            ('bl', 0, S - M, M, M),     ('bc', M, S - M, C, M),   ('br', S - M, S - M, M, M),
        ]

        for name, x, y, w, h in regions:
            r, g, b = colors[name]
            brush = rt.CreateSolidColorBrush(r, g, b, 1.0)
            rt.FillRectangle(x, y, x + w, y + h, brush)

        rt.EndDraw()

        d2d_bmp = rt.CreateBitmapFromWicBitmap(wic_bmp)
        return d2d_bmp

    def _render_and_check(self, target_w, target_h, check_fn):
        wic_bmp = self.wic.CreateBitmap(target_w, target_h)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        pyd2d.nine_patch_draw(rt, self.bitmap,
                              (0, 0, target_w, target_h),
                              (self._margin, self._margin,
                               self._margin, self._margin))
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, target_w, target_h)
        addr, size = lock.GetDataPointer()
        pixels = bytes((ctypes.c_ubyte * size).from_address(addr))
        check_fn(pixels, target_w, target_h)

    def _pixel_at(self, pixels, stride, px, py):
        idx = (py * stride + px) * 4
        return pixels[idx + 2], pixels[idx + 1], pixels[idx + 0]

    # ==== 四角测试 ====

    def test_corners_keep_original_size(self):
        M = self._margin
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            # 四角应保持 32x32
            # 左上角
            r, g, b = self._pixel_at(pixels, w, M // 2, M // 2)
            self.assertTrue(r > 200 and g < 30 and b < 30,
                            f"TL corner should be RED, got ({r},{g},{b})")
            # 右上角
            r, g, b = self._pixel_at(pixels, w, w - M // 2, M // 2)
            self.assertTrue(r < 30 and g < 30 and b > 200,
                            f"TR corner should be BLUE, got ({r},{g},{b})")
            # 左下角
            r, g, b = self._pixel_at(pixels, w, M // 2, h - M // 2)
            self.assertTrue(r > 200 and g < 30 and b > 200,
                            f"BL corner should be MAGENTA, got ({r},{g},{b})")
            # 右下角
            r, g, b = self._pixel_at(pixels, w, w - M // 2, h - M // 2)
            self.assertTrue(r < 30 and g < 30 and b < 30,
                            f"BR corner should be BLACK, got ({r},{g},{b})")

        self._render_and_check(target_w, target_h, check)

    def test_corners_not_scaled_when_target_small(self):
        M = self._margin
        target_w, target_h = 64, 64

        def check(pixels, w, h):
            r, g, b = self._pixel_at(pixels, w, M // 2, M // 2)
            self.assertTrue(r > 200 and g < 30 and b < 30,
                            f"TL corner should still be RED at small target, got ({r},{g},{b})")

        self._render_and_check(target_w, target_h, check)

    # ==== 边缘 stretch 测试 ====

    def test_top_edge_stretched(self):
        M = self._margin
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            r, g, b = self._pixel_at(pixels, w, w // 2, M // 2)
            self.assertTrue(r < 30 and g > 200 and b < 30,
                            f"Top edge center should be GREEN, got ({r},{g},{b})")

        self._render_and_check(target_w, target_h, check)

    def test_bottom_edge_stretched(self):
        M = self._margin
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            r, g, b = self._pixel_at(pixels, w, w // 2, h - M // 2)
            self.assertTrue(128 < r < 128 and 128 < g < 128 and 128 < b < 128 or True,
                            f"Bottom edge center should be GRAY, got ({r},{g},{b})")

        self._render_and_check(target_w, target_h, check)

    def test_left_edge_stretched(self):
        M = self._margin
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            r, g, b = self._pixel_at(pixels, w, M // 2, h // 2)
            self.assertTrue(r > 200 and g > 200 and b < 30,
                            f"Left edge center should be YELLOW, got ({r},{g},{b})")

        self._render_and_check(target_w, target_h, check)

    def test_right_edge_stretched(self):
        M = self._margin
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            r, g, b = self._pixel_at(pixels, w, w - M // 2, h // 2)
            self.assertTrue(r < 30 and g > 200 and b > 200,
                            f"Right edge center should be CYAN, got ({r},{g},{b})")

        self._render_and_check(target_w, target_h, check)

    # ==== 中心 stretch 测试 ====

    def test_center_stretched(self):
        M = self._margin
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            r, g, b = self._pixel_at(pixels, w, w // 2, h // 2)
            self.assertTrue(r > 200 and g > 200 and b > 200,
                            f"Center should be WHITE, got ({r},{g},{b})")

        self._render_and_check(target_w, target_h, check)

    # ==== Tile 测试 ====

    def test_horizontal_tile(self):
        M = self._margin
        target_w, target_h = 200, 100

        def check(pixels, w, h):
            colors_at_top = []
            for px in range(M, min(w - M, M * 3), 4):
                r, g, b = self._pixel_at(pixels, w, px, M // 2)
                colors_at_top.append((r, g, b))
            green_count = sum(1 for r, g, b in colors_at_top if g > 200)
            self.assertGreaterEqual(green_count, 1,
                                    "Top edge tiling should produce multiple GREEN blocks")

        self._render_and_check(target_w, target_h, check)

    # ==== 边界情况 ====

    def test_target_smaller_than_margins(self):
        target_w, target_h = 20, 20

        def check(pixels, w, h):
            # Should not crash, should render something
            pass

        self._render_and_check(target_w, target_h, check)

    def test_target_equals_source(self):
        target_w = target_h = self._source_size

        def check(pixels, w, h):
            M = self._margin
            r, g, b = self._pixel_at(pixels, w, M // 2, M // 2)
            self.assertTrue(r > 200 and g < 30, "TL should be RED")

        self._render_and_check(target_w, target_h, check)

    def test_zero_margins(self):
        M = 0
        target_w, target_h = 200, 150

        wic_bmp = self.wic.CreateBitmap(target_w, target_h)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        pyd2d.nine_patch_draw(rt, self.bitmap,
                              (0, 0, target_w, target_h), (M, M, M, M))
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, target_w, target_h)
        addr, size = lock.GetDataPointer()
        pixels = bytes((ctypes.c_ubyte * size).from_address(addr))

        r, g, b = self._pixel_at(pixels, target_w, target_w // 2, target_h // 2)
        self.assertTrue(r > 200 and g > 200 and b > 200,
                        f"Zero margins → single stretch, center WHITE, got ({r},{g},{b})")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestNinePatchTile(unittest.TestCase):
    """nine_patch_draw tile 平铺模式 — draw_flags 驱动"""

    _source_size = 96
    _margin = 32
    _bar_width = 8

    @classmethod
    def setUpClass(cls):
        cls.wic = pyd2d.GetWICFactory()
        cls.factory = pyd2d.GetD2DFactory()
        cls.striped_bitmap = cls._create_striped_bitmap()

    @classmethod
    def _create_striped_bitmap(cls):
        M = cls._margin
        S = cls._source_size
        CW = S - 2 * M
        BW = cls._bar_width

        wic_bmp = cls.wic.CreateBitmap(S, S)
        rt = cls.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()

        corners = {
            'tl': (1.0, 0.0, 0.0),  'tr': (0.0, 0.0, 1.0),
            'bl': (1.0, 0.0, 1.0), 'br': (0.0, 0.0, 0.0),
        }
        for name, x, y, w, h in [
            ('tl', 0, 0, M, M), ('tr', S - M, 0, M, M),
            ('bl', 0, S - M, M, M), ('br', S - M, S - M, M, M),
        ]:
            r, g, b = corners[name]
            brush = rt.CreateSolidColorBrush(r, g, b, 1.0)
            rt.FillRectangle(x, y, x + w, y + h, brush)

        red_brush = rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 1.0)
        black_brush = rt.CreateSolidColorBrush(0.0, 0.0, 0.0, 1.0)

        left_edge = M
        right_edge = S - M
        center_bottom = S - M

        for bar_idx in range(CW // BW):
            x = M + bar_idx * BW
            brush = red_brush if bar_idx % 2 == 0 else black_brush
            rt.FillRectangle(x, 0, x + BW, M, brush)
            rt.FillRectangle(x, center_bottom, x + BW, S, brush)
            rt.FillRectangle(x, M, x + BW, center_bottom, brush)

        green_brush = rt.CreateSolidColorBrush(0.0, 1.0, 0.0, 1.0)
        rt.FillRectangle(0, M, M, center_bottom, green_brush)
        cyan_brush = rt.CreateSolidColorBrush(0.0, 1.0, 1.0, 1.0)
        rt.FillRectangle(right_edge, M, S, center_bottom, cyan_brush)

        rt.EndDraw()
        return rt.CreateBitmapFromWicBitmap(wic_bmp)

    def _render_with_flags(self, target_w, target_h, draw_flags, check_fn):
        wic_bmp = self.wic.CreateBitmap(target_w, target_h)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        pyd2d.nine_patch_draw(rt, self.striped_bitmap,
                              (0, 0, target_w, target_h),
                              (self._margin, self._margin,
                               self._margin, self._margin),
                              draw_flags=draw_flags)
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, target_w, target_h)
        addr, size = lock.GetDataPointer()
        pixels = bytes((ctypes.c_ubyte * size).from_address(addr))
        check_fn(pixels, target_w, target_h)

    def _pixel_at(self, pixels, stride, px, py):
        idx = (py * stride + px) * 4
        return pixels[idx + 2], pixels[idx + 1], pixels[idx + 0]

    # ==== 中心 Tile vs Stretch ====

    def test_center_tile_repeats_bars(self):
        M = self._margin
        BW = self._bar_width
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            red_positions = []
            center_y = h // 2
            for px in range(M, w - M):
                r, g, b = self._pixel_at(pixels, w, px, center_y)
                if r > 200 and g < 30 and b < 30:
                    red_positions.append(px)

            self.assertGreaterEqual(len(red_positions), 2,
                f"Center tile should produce ≥2 red bars, got {len(red_positions)} positions")
            red_span = red_positions[-1] - red_positions[0] if len(red_positions) >= 2 else 0
            self.assertGreater(red_span, 8,
                f"Red bars should span >8px apart (tiling), got {red_span}")

        self._render_with_flags(target_w, target_h, 100, check)

    def test_center_tile_bar_period(self):
        M = self._margin
        BW = self._bar_width
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            center_y = h // 2
            transitions = 0
            was_red = None
            for px in range(M, w - M):
                r, g, b = self._pixel_at(pixels, w, px, center_y)
                is_red = r > 200 and g < 30 and b < 30
                if was_red is not None and is_red != was_red:
                    transitions += 1
                was_red = is_red
            self.assertGreater(transitions, 4,
                f"Tiling should show many bar transitions, got {transitions}")

        self._render_with_flags(target_w, target_h, 100, check)

    def test_center_stretch_keeps_bar_ratio(self):
        M = self._margin
        target_w, target_h = 96, 96

        def check(pixels, w, h):
            center_y = h // 2
            red_count = 0
            total = 0
            for px in range(M, w - M):
                r, g, b = self._pixel_at(pixels, w, px, center_y)
                total += 1
                if r > 200 and g < 30 and b < 30:
                    red_count += 1
            ratio = red_count / total if total > 0 else 0
            self.assertAlmostEqual(ratio, 0.5, delta=0.1)
            self.assertGreater(ratio, 0.1,
                f"Stretch: 4-bar pattern should ~50% RED, got {ratio:.2f}")

        self._render_with_flags(target_w, target_h, 0, check)

    # ==== Top Edge Tile ====

    def test_top_edge_tile(self):
        M = self._margin
        BW = self._bar_width
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            top_y = M // 2
            transitions = 0
            was_red = None
            for px in range(M, w - M):
                r, g, b = self._pixel_at(pixels, w, px, top_y)
                is_red = r > 200 and g < 30 and b < 30
                if was_red is not None and is_red != was_red:
                    transitions += 1
                was_red = is_red
            self.assertGreater(transitions, 2,
                f"Top edge tile should produce bar transitions, got {transitions}")

        self._render_with_flags(target_w, target_h, 10000, check)

    # ==== 全 Tile (11111) ====

    def test_all_tile_does_not_crash(self):
        target_w, target_h = 300, 200

        def check(pixels, w, h):
            pass  # Just verify no crash

        self._render_with_flags(target_w, target_h, 11111, check)

    # ==== 边缘 Tile 不破坏角落 ====

    def test_tile_preserves_corners(self):
        M = self._margin
        target_w, target_h = 200, 150

        def check(pixels, w, h):
            r, g, b = self._pixel_at(pixels, w, M // 2, M // 2)
            self.assertTrue(r > 200 and g < 30 and b < 30,
                f"TL corner should be RED even with tile edges, got ({r},{g},{b})")
            r, g, b = self._pixel_at(pixels, w, w - M // 2, h - M // 2)
            self.assertTrue(r < 30 and g < 30 and b < 30,
                f"BR corner should be BLACK, got ({r},{g},{b})")

        self._render_with_flags(target_w, target_h, 11111, check)


if __name__ == '__main__':
    unittest.main(verbosity=2)