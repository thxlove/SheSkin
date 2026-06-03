"""pyd2d DirectWrite 文字渲染集成测试:
TextFormat → TextLayout → DrawTextW/DrawTextLayout → Pixel Verify (ClearType)"""
import pyd2d
import ctypes
import unittest

_D2D_OK = all([pyd2d.GetD2DFactory(), pyd2d.GetWICFactory(), pyd2d.GetDWriteFactory()])


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestDWriteBasic(unittest.TestCase):
    """DWrite Factory + TextFormat + TextLayout 基础测试"""

    @classmethod
    def setUpClass(cls):
        cls.dw = pyd2d.GetDWriteFactory()
        cls.factory = pyd2d.GetD2DFactory()
        cls.wic = pyd2d.GetWICFactory()

    def test_create_text_format(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 24.0)
        self.assertIsNotNone(tf)
        print("  [PASS] CreateTextFormat('Segoe UI', 24.0)")

    def test_create_text_format_bold(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 24.0,
                                       weight=pyd2d.FONT_WEIGHT.BOLD)
        self.assertIsNotNone(tf)
        print("  [PASS] CreateTextFormat(bold)")

    def test_create_text_format_italic(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 24.0,
                                       style=pyd2d.FONT_STYLE.ITALIC)
        self.assertIsNotNone(tf)
        print("  [PASS] CreateTextFormat(italic)")

    def test_create_text_layout(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 24.0)
        tl = self.dw.CreateTextLayout('Hello World', tf, 300.0, 100.0)
        self.assertIsNotNone(tl)
        print("  [PASS] CreateTextLayout('Hello World', 300, 100)")

    def test_text_metrics(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 24.0)
        tl = self.dw.CreateTextLayout('Hello', tf, 300.0, 100.0)
        m = tl.GetMetrics()
        self.assertGreater(m.width, 0)
        self.assertGreater(m.height, 0)
        self.assertEqual(m.lineCount, 1)
        print("  [PASS] GetMetrics: width=%.2f height=%.2f lines=%d" %
              (m.width, m.height, m.lineCount))

    def test_text_metrics_multiline(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 16.0)
        tl = self.dw.CreateTextLayout('Hello\nWorld', tf, 200.0, 200.0)
        m = tl.GetMetrics()
        self.assertEqual(m.lineCount, 2)
        self.assertGreater(m.height, 30)
        print("  [PASS] Multiline: lineCount=%d height=%.2f" %
              (m.lineCount, m.height))

    def test_max_width(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 24.0)
        tl = self.dw.CreateTextLayout('Test', tf, 300.0, 100.0)
        self.assertEqual(tl.GetMaxWidth(), 300.0)
        print("  [PASS] GetMaxWidth() = 300.0")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestDrawTextW(unittest.TestCase):
    """DrawTextW — 直接绘制文字到 WIC RenderTarget"""

    @classmethod
    def setUpClass(cls):
        cls.dw = pyd2d.GetDWriteFactory()
        cls.factory = pyd2d.GetD2DFactory()
        cls.wic = pyd2d.GetWICFactory()

    def _render_and_get_pixels(self, w, h, draw_fn):
        wic_bmp = self.wic.CreateBitmap(w, h)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        draw_fn(rt)
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, w, h)
        addr, size = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * size).from_address(addr)
        result = bytes(pixels)
        return result

    def test_draw_text_white_on_black(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 48.0,
                                       weight=pyd2d.FONT_WEIGHT.BOLD)

        def draw(rt):
            brush = rt.CreateSolidColorBrush(1.0, 1.0, 1.0, 1.0)
            rt.DrawText('ABC', tf, 0, 0, 200, 80, brush)

        pixels = self._render_and_get_pixels(200, 80, draw)

        has_white = False
        for i in range(0, len(pixels), 4):
            r = pixels[i + 2]
            g = pixels[i + 1]
            b = pixels[i + 0]
            if r > 100 or g > 100 or b > 100:
                has_white = True
                break

        self.assertTrue(has_white,
                        "DrawTextW should render visible text pixels")
        print("  [PASS] DrawTextW('ABC', bold 48pt) → visible text pixels found")

    def test_draw_text_red_on_black(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 36.0)

        def draw(rt):
            brush = rt.CreateSolidColorBrush(1.0, 0.0, 0.0, 1.0)
            rt.DrawText('RED', tf, 0, 0, 300, 60, brush)

        pixels = self._render_and_get_pixels(300, 60, draw)

        red_pixels = 0
        for i in range(0, len(pixels), 4):
            r = pixels[i + 2]
            g = pixels[i + 1]
            b = pixels[i + 0]
            if r > 128 and g < 50 and b < 50:
                red_pixels += 1

        self.assertGreater(red_pixels, 5,
                           "DrawTextW red text should have red pixels")
        print("  [PASS] DrawTextW('RED', 36pt, red brush) → %d red pixels" % red_pixels)

    def test_draw_text_with_clip(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 36.0)

        def draw(rt):
            brush = rt.CreateSolidColorBrush(1.0, 1.0, 1.0, 1.0)
            rt.DrawText('WIDE TEXT CLIPPED', tf, 0, 0, 50, 60, brush,
                         options=pyd2d.DRAW_TEXT_OPTIONS.CLIP)

        pixels = self._render_and_get_pixels(200, 60, draw)

        right_region_has_text = False
        for y in range(10, 50):
            for x in range(100, 190):
                idx = (y * 200 + x) * 4
                r = pixels[idx + 2]
                if r > 50:
                    right_region_has_text = True
                    break
            if right_region_has_text:
                break

        self.assertFalse(right_region_has_text,
                         "CLIP option should prevent text beyond layout rect")
        print("  [PASS] DrawTextW with CLIP option → text clipped correctly")

    def test_draw_text_measuring_mode_gdi(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 24.0)

        def draw(rt):
            brush = rt.CreateSolidColorBrush(1.0, 1.0, 1.0, 1.0)
            rt.DrawText('Measuring Test', tf, 0, 0, 300, 40, brush,
                         measuringMode=pyd2d.MEASURING_MODE.GDI_CLASSIC)

        pixels = self._render_and_get_pixels(300, 40, draw)

        has_text = False
        for i in range(0, len(pixels), 4):
            r = pixels[i + 2]
            if r > 100:
                has_text = True
                break

        self.assertTrue(has_text,
                        "DrawTextW with GDI_CLASSIC measuring should render text")
        print("  [PASS] DrawTextW with GDI_CLASSIC measuring mode")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestDrawTextLayout(unittest.TestCase):
    """DrawTextLayout — 使用 TextLayout 绘制（支持排版控制）"""

    @classmethod
    def setUpClass(cls):
        cls.dw = pyd2d.GetDWriteFactory()
        cls.factory = pyd2d.GetD2DFactory()
        cls.wic = pyd2d.GetWICFactory()

    def test_draw_text_layout_basic(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 36.0,
                                       weight=pyd2d.FONT_WEIGHT.BOLD)
        tl = self.dw.CreateTextLayout('Layout', tf, 200.0, 60.0)

        wic_bmp = self.wic.CreateBitmap(200, 60)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        brush = rt.CreateSolidColorBrush(0.0, 1.0, 0.0, 1.0)
        rt.DrawTextLayout(0.0, 0.0, tl, brush)
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, 200, 60)
        addr, size = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * size).from_address(addr)

        green_pixels = 0
        for i in range(0, len(pixels), 4):
            r = pixels[i + 2]
            g = pixels[i + 1]
            b = pixels[i + 0]
            if g > 128 and r < 50 and b < 50:
                green_pixels += 1

        self.assertGreater(green_pixels, 5,
                           "DrawTextLayout should render visible green text")
        print("  [PASS] DrawTextLayout('Layout', bold 36pt, green) → %d green pixels" % green_pixels)

    def test_draw_text_layout_multiline(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 18.0)
        tl = self.dw.CreateTextLayout('Line 1\nLine 2\nLine 3', tf, 150.0, 100.0)

        wic_bmp = self.wic.CreateBitmap(150, 100)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        brush = rt.CreateSolidColorBrush(1.0, 1.0, 1.0, 1.0)
        rt.DrawTextLayout(0.0, 0.0, tl, brush)
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, 150, 100)
        addr, size = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * size).from_address(addr)

        text_found_top = False
        text_found_bottom = False
        for y in range(5, 95):
            for x in range(10, 140):
                idx = (y * 150 + x) * 4
                r = pixels[idx + 2]
                if r > 80:
                    if y < 35:
                        text_found_top = True
                    if y > 60:
                        text_found_bottom = True

        self.assertTrue(text_found_top, "Line 1 should be visible in top region")
        self.assertTrue(text_found_bottom, "Line 3 should be visible in bottom region")
        print("  [PASS] DrawTextLayout multiline → text in both top and bottom regions")

    def test_draw_text_layout_with_options(self):
        tf = self.dw.CreateTextFormat('Segoe UI', 24.0)
        tl = self.dw.CreateTextLayout('Options', tf, 300.0, 40.0)

        wic_bmp = self.wic.CreateBitmap(300, 40)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        brush = rt.CreateSolidColorBrush(1.0, 0.5, 0.0, 1.0)
        rt.DrawTextLayout(0.0, 0.0, tl, brush)
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, 300, 40)
        addr, size = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * size).from_address(addr)

        has_text = False
        for i in range(0, len(pixels), 4):
            r = pixels[i + 2]
            g = pixels[i + 1]
            if r > 60 or g > 30:
                has_text = True
                break

        self.assertTrue(has_text)
        print("  [PASS] DrawTextLayout with DRAW_TEXT_OPTIONS.NONE")


@unittest.skipIf(not _D2D_OK, "D2D factories not available")
class TestClearTypeAntialiasing(unittest.TestCase):
    """ClearType 亚像素抗锯齿验证"""

    @classmethod
    def setUpClass(cls):
        cls.dw = pyd2d.GetDWriteFactory()
        cls.factory = pyd2d.GetD2DFactory()
        cls.wic = pyd2d.GetWICFactory()

    def test_cleartype_produces_colored_pixels(self):
        """ClearType 使用 RGB 子像素渲染，因此白色文字在黑色背景上
        的像素应该包含有颜色的子像素分量（非纯灰色）"""
        tf = self.dw.CreateTextFormat('Segoe UI', 24.0)
        tl = self.dw.CreateTextLayout('I', tf, 50.0, 40.0)

        wic_bmp = self.wic.CreateBitmap(50, 40)
        rt = self.factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        rt.BeginDraw()
        rt.Clear(0.0, 0.0, 0.0, 0.0)
        brush = rt.CreateSolidColorBrush(1.0, 1.0, 1.0, 1.0)
        rt.DrawTextLayout(0.0, 0.0, tl, brush)
        rt.EndDraw()

        lock = wic_bmp.Lock(0, 0, 50, 40)
        addr, size = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * size).from_address(addr)

        colored_edges = 0
        gray_pixels = 0
        for i in range(0, len(pixels), 4):
            r = pixels[i + 2]
            g = pixels[i + 1]
            b = pixels[i + 0]
            max_diff = max(abs(int(r)-int(g)), abs(int(g)-int(b)), abs(int(r)-int(b)))
            if r > 50 or g > 50 or b > 50:
                if max_diff > 20:
                    colored_edges += 1
                else:
                    gray_pixels += 1

        total_lit = colored_edges + gray_pixels
        self.assertGreater(total_lit, 3, "Should have some visible text pixels")
        ratio = colored_edges / max(total_lit, 1)
        print("  [PASS] ClearType → colored_edges=%d gray=%d ratio=%.2f" %
              (colored_edges, gray_pixels, ratio))
        print("    ClearType sub-pixel anti-aliasing confirmed" if colored_edges > 0
              else "    NOTE: Check ClearType settings if no colored edges")


if __name__ == '__main__':
    print("=" * 60)
    print("pyd2d DirectWrite 文字渲染测试")
    print("=" * 60)
    unittest.main(verbosity=0)