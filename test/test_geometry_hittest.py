"""测试 GeometryHitTester — 圆角窗体命中测试增强。"""
import unittest
import pyd2d
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from sheskin.geometry_hittest import create_rounded_rect_geometry, GeometryHitTester


class TestCreateRoundedRectGeometry(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._d2d_factory = pyd2d.GetD2DFactory()

    def test_rect_geometry_basic(self):
        geo = create_rounded_rect_geometry(
            self._d2d_factory, 0, 0, 100, 100, 0)
        self.assertTrue(geo.FillContainsPoint(50, 50))
        self.assertFalse(geo.FillContainsPoint(-1, 50))

    def test_rounded_rect_corners(self):
        geo = create_rounded_rect_geometry(
            self._d2d_factory, 0, 0, 200, 200, 10)
        self.assertTrue(geo.FillContainsPoint(100, 100))
        self.assertFalse(geo.FillContainsPoint(3, 3))
        self.assertFalse(geo.FillContainsPoint(197, 3))
        self.assertFalse(geo.FillContainsPoint(3, 197))
        self.assertFalse(geo.FillContainsPoint(197, 197))

    def test_rounded_rect_edges(self):
        geo = create_rounded_rect_geometry(
            self._d2d_factory, 0, 0, 200, 200, 10)
        self.assertTrue(geo.FillContainsPoint(100, 0))
        self.assertTrue(geo.FillContainsPoint(200, 100))
        self.assertTrue(geo.FillContainsPoint(100, 200))
        self.assertTrue(geo.FillContainsPoint(0, 100))

    def test_rounded_rect_bounds(self):
        geo = create_rounded_rect_geometry(
            self._d2d_factory, 0, 0, 200, 200, 10)
        l, t, r, b = geo.GetBounds()
        self.assertLessEqual(abs(l), 1.0)
        self.assertLessEqual(abs(t), 1.0)
        self.assertLessEqual(abs(r - 200), 1.0)
        self.assertLessEqual(abs(b - 200), 1.0)

    def test_area_with_and_without_rounding(self):
        geo_rect = create_rounded_rect_geometry(
            self._d2d_factory, 0, 0, 100, 100, 0)
        geo_rounded = create_rounded_rect_geometry(
            self._d2d_factory, 0, 0, 100, 100, 20)
        area_rect = geo_rect.ComputeArea()
        area_rounded = geo_rounded.ComputeArea()
        self.assertLess(area_rounded, area_rect)
        self.assertGreater(area_rounded, 0)


class TestGeometryHitTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._d2d_factory = pyd2d.GetD2DFactory()

    def test_rect_window_all_inside(self):
        tester = GeometryHitTester(self._d2d_factory)
        tester.init_window_shape(800, 600, 0, 4, 30, 4, 4)
        self.assertTrue(tester.hit_test(50, 50))
        self.assertTrue(tester.hit_test(400, 300))
        self.assertTrue(tester.hit_test(750, 550))

    def test_rect_window_corner_outside(self):
        tester = GeometryHitTester(self._d2d_factory)
        tester.init_window_shape(800, 600, 0, 4, 30, 4, 4)
        self.assertFalse(tester.hit_test(-1, 50))
        self.assertFalse(tester.hit_test(50, -1))
        self.assertFalse(tester.hit_test(801, 300))
        self.assertFalse(tester.hit_test(400, 601))

    def test_rounded_window_corner_transparency(self):
        tester = GeometryHitTester(self._d2d_factory)
        tester.init_window_shape(800, 600, 8, 4, 30, 4, 4)
        self.assertTrue(tester.hit_test(400, 300))
        self.assertFalse(tester.hit_test(2, 2))
        self.assertFalse(tester.hit_test(798, 2))
        self.assertFalse(tester.hit_test(2, 598))
        self.assertFalse(tester.hit_test(798, 598))

    def test_rounded_window_edge_inside(self):
        tester = GeometryHitTester(self._d2d_factory)
        tester.init_window_shape(800, 600, 8, 4, 30, 4, 4)
        self.assertTrue(tester.hit_test(400, 0))
        self.assertTrue(tester.hit_test(800, 300))
        self.assertTrue(tester.hit_test(400, 600))
        self.assertTrue(tester.hit_test(0, 300))

    def test_cache_reuse(self):
        tester = GeometryHitTester(self._d2d_factory)
        tester.init_window_shape(800, 600, 0, 4, 30, 4, 4)
        key_before = tester._geometry_cache_key
        tester.init_window_shape(800, 600, 0, 4, 30, 4, 4)
        self.assertEqual(tester._geometry_cache_key, key_before)

    def test_cache_invalidation(self):
        tester = GeometryHitTester(self._d2d_factory)
        tester.init_window_shape(800, 600, 0, 4, 30, 4, 4)
        key_before = tester._geometry_cache_key
        tester.init_window_shape(1024, 768, 0, 4, 30, 4, 4)
        self.assertNotEqual(tester._geometry_cache_key, key_before)

    def test_nchittest_corner_validation(self):
        """模拟 Frame._on_nchittest 转角穿透逻辑：
        圆角窗口的 4 个转角区域中，落在圆角外部的像素返回 HTNOWHERE，
        圆角内部的像素返回对应的 HT 转角值。
        """
        tester = GeometryHitTester(self._d2d_factory)
        radius = 8
        b_left, b_top, b_right, b_bottom = 12, 30, 12, 12
        tester.init_window_shape(800, 600, radius, b_left, b_top, b_right, b_bottom)

        def classify_corner(px, py):
            w, h = 800, 600
            if py < b_top and px < b_left:
                corner = 'HTTOPLEFT'
            elif py < b_top and px >= w - b_right:
                corner = 'HTTOPRIGHT'
            elif py >= h - b_bottom and px < b_left:
                corner = 'HTBOTTOMLEFT'
            elif py >= h - b_bottom and px >= w - b_right:
                corner = 'HTBOTTOMRIGHT'
            else:
                return None
            if tester.hit_test(px, py):
                return corner
            return 'HTNOWHERE'

        # 圆角外穿透 → HTNOWHERE
        self.assertEqual(classify_corner(2, 2), 'HTNOWHERE')
        self.assertEqual(classify_corner(798, 2), 'HTNOWHERE')
        self.assertEqual(classify_corner(2, 598), 'HTNOWHERE')
        self.assertEqual(classify_corner(798, 598), 'HTNOWHERE')

        # 圆角内边缘 → 正确的 HT 值
        self.assertEqual(classify_corner(6, 27), 'HTTOPLEFT')
        self.assertEqual(classify_corner(794, 27), 'HTTOPRIGHT')
        self.assertEqual(classify_corner(6, 593), 'HTBOTTOMLEFT')
        self.assertEqual(classify_corner(794, 593), 'HTBOTTOMRIGHT')

    def test_nchittest_corner_rect_window(self):
        """矩形窗口（radius=0）所有转角区域都返回对应 HT 值，不穿透。"""
        tester = GeometryHitTester(self._d2d_factory)
        b_left, b_top, b_right, b_bottom = 4, 30, 4, 4
        tester.init_window_shape(800, 600, 0, b_left, b_top, b_right, b_bottom)

        def classify_corner(px, py):
            w, h = 800, 600
            if py < b_top and px < b_left:
                corner = 'HTTOPLEFT'
            elif py < b_top and px >= w - b_right:
                corner = 'HTTOPRIGHT'
            elif py >= h - b_bottom and px < b_left:
                corner = 'HTBOTTOMLEFT'
            elif py >= h - b_bottom and px >= w - b_right:
                corner = 'HTBOTTOMRIGHT'
            else:
                return None
            if tester.hit_test(px, py):
                return corner
            return 'HTNOWHERE'

        # 矩形窗口所有转角像素都在 shape 内
        self.assertEqual(classify_corner(2, 2), 'HTTOPLEFT')
        self.assertEqual(classify_corner(798, 2), 'HTTOPRIGHT')
        self.assertEqual(classify_corner(2, 598), 'HTBOTTOMLEFT')
        self.assertEqual(classify_corner(798, 598), 'HTBOTTOMRIGHT')


if __name__ == '__main__':
    unittest.main()