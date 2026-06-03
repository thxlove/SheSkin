"""D2D 布局辅助测试 — D2DLayout 基类 + D2DHBox + D2DVBox。"""
import unittest
from sheskin.controls.layout import (
    d2d_hbox, d2d_vbox, D2DLayout, D2DHBox, D2DVBox,
)


class _MockCtrl:
    def __init__(self, rect):
        self._rect = rect

    @property
    def rect(self):
        return self._rect

    def set_rect(self, rect):
        self._rect = rect


class TestD2DLayoutBase(unittest.TestCase):

    def test_init_defaults(self):
        box = D2DHBox()
        self.assertEqual(box.controls, [])
        self.assertEqual(box.spacing, 8)
        self.assertEqual(box.margin, 12)

    def test_init_with_controls(self):
        c1 = _MockCtrl((0, 0, 50, 20))
        c2 = _MockCtrl((0, 0, 60, 20))
        box = D2DHBox([c1, c2], spacing=4, margin=6)
        self.assertEqual(len(box.controls), 2)
        self.assertEqual(box.spacing, 4)
        self.assertEqual(box.margin, 6)

    def test_spacing_setter(self):
        box = D2DHBox()
        box.spacing = 20
        self.assertEqual(box.spacing, 20)

    def test_margin_setter(self):
        box = D2DHBox()
        box.margin = 30
        self.assertEqual(box.margin, 30)

    def test_add_control(self):
        box = D2DHBox()
        c = _MockCtrl((0, 0, 50, 20))
        box.add(c)
        self.assertEqual(len(box.controls), 1)

    def test_remove_control(self):
        box = D2DHBox()
        c = _MockCtrl((0, 0, 50, 20))
        box.add(c)
        box.remove(c)
        self.assertEqual(len(box.controls), 0)

    def test_clear_controls(self):
        box = D2DHBox()
        box.add(_MockCtrl((0, 0, 50, 20)))
        box.add(_MockCtrl((0, 0, 60, 20)))
        box.clear()
        self.assertEqual(len(box.controls), 0)

    def test_rect_without_layout(self):
        c1 = _MockCtrl((0, 0, 50, 20))
        c2 = _MockCtrl((0, 0, 60, 20))
        box = D2DHBox([c1, c2], spacing=8, margin=10)
        r = box.rect
        self.assertGreater(r[2], 0)
        self.assertGreater(r[3], 0)

    def test_set_rect_triggers_layout(self):
        c1 = _MockCtrl((0, 0, 50, 20))
        box = D2DHBox([c1], spacing=8, margin=10)
        box.set_rect((0, 0, 200, 100))
        self.assertEqual(box._last_container, (0, 0, 200, 100))
        self.assertEqual(c1.rect, (10, 10, 50, 20))

    def test_overhang_top_default(self):
        box = D2DHBox()
        self.assertEqual(box.overhang_top(), 0.0)

    def test_walk_controls_flat(self):
        c1 = _MockCtrl((0, 0, 50, 20))
        c2 = _MockCtrl((0, 0, 60, 20))
        box = D2DHBox([c1, c2])
        walked = list(box._walk_controls())
        self.assertEqual(len(walked), 2)
        self.assertIs(walked[0], c1)
        self.assertIs(walked[1], c2)

    def test_walk_controls_nested(self):
        c1 = _MockCtrl((0, 0, 50, 20))
        c2 = _MockCtrl((0, 0, 60, 20))
        inner = D2DVBox([c1, c2])
        c3 = _MockCtrl((0, 0, 70, 20))
        outer = D2DHBox([inner, c3])
        walked = list(outer._walk_controls())
        self.assertEqual(len(walked), 3)
        self.assertIs(walked[0], c1)
        self.assertIs(walked[1], c2)
        self.assertIs(walked[2], c3)


class TestD2DHBoxMeasureNatural(unittest.TestCase):

    def test_empty_natural_size(self):
        box = D2DHBox([], spacing=8, margin=10)
        r = box._measure_natural()
        self.assertEqual(r, (0, 0, 20, 20))

    def test_single_control_natural(self):
        c = _MockCtrl((0, 0, 100, 30))
        box = D2DHBox([c], spacing=8, margin=10)
        r = box._measure_natural()
        self.assertEqual(r[2], 100 + 20)
        self.assertEqual(r[3], 30 + 20)

    def test_two_controls_natural(self):
        c1 = _MockCtrl((0, 0, 80, 30))
        c2 = _MockCtrl((0, 0, 100, 40))
        box = D2DHBox([c1, c2], spacing=8, margin=10)
        r = box._measure_natural()
        self.assertEqual(r[2], 80 + 100 + 8 + 20)
        self.assertEqual(r[3], 40 + 20)


class TestD2DVBoxMeasureNatural(unittest.TestCase):

    def test_empty_natural_size(self):
        box = D2DVBox([], spacing=8, margin=10)
        r = box._measure_natural()
        self.assertEqual(r, (0, 0, 20, 20))

    def test_single_control_natural(self):
        c = _MockCtrl((0, 0, 100, 30))
        box = D2DVBox([c], spacing=8, margin=10)
        r = box._measure_natural()
        self.assertEqual(r[2], 100 + 20)
        self.assertEqual(r[3], 30 + 20)

    def test_two_controls_natural(self):
        c1 = _MockCtrl((0, 0, 120, 30))
        c2 = _MockCtrl((0, 0, 100, 40))
        box = D2DVBox([c1, c2], spacing=8, margin=10)
        r = box._measure_natural()
        self.assertEqual(r[2], 120 + 20)
        self.assertEqual(r[3], 30 + 40 + 8 + 20)


class TestD2DHBox(unittest.TestCase):

    def test_empty_controls(self):
        container = (0, 0, 400, 100)
        controls = []
        d2d_hbox(controls, container)
        self.assertEqual(len(controls), 0)

    def test_single_control_positioned(self):
        ctrl = _MockCtrl((999, 999, 100, 30))
        d2d_hbox([ctrl], (0, 0, 400, 100), margin=12)
        r = ctrl.rect
        self.assertEqual(r, (12, 12, 100, 30))

    def test_two_controls_horizontal(self):
        c1 = _MockCtrl((99, 99, 80, 30))
        c2 = _MockCtrl((99, 99, 100, 30))
        d2d_hbox([c1, c2], (0, 0, 400, 100), spacing=8, margin=10)

        self.assertEqual(c1.rect, (10, 10, 80, 30))
        self.assertEqual(c2.rect, (10 + 80 + 8, 10, 100, 30))

    def test_custom_margin_spacing(self):
        c1 = _MockCtrl((99, 99, 50, 30))
        c2 = _MockCtrl((99, 99, 60, 30))
        d2d_hbox([c1, c2], (0, 0, 400, 100), spacing=20, margin=5)

        self.assertEqual(c1.rect, (5, 5, 50, 30))
        self.assertEqual(c2.rect, (5 + 50 + 20, 5, 60, 30))

    def test_integration_with_button(self):
        from sheskin.controls import D2DButton
        btn1 = D2DButton((99, 99, 80, 30), "A")
        btn2 = D2DButton((99, 99, 100, 30), "B")
        d2d_hbox([btn1, btn2], (0, 0, 400, 100), spacing=10, margin=15)

        self.assertEqual(btn1.rect, (15, 15, 80, 30))
        self.assertEqual(btn2.rect, (15 + 80 + 10, 15, 100, 30))


class TestD2DVBox(unittest.TestCase):

    def test_empty_controls(self):
        controls = []
        d2d_vbox(controls, (0, 0, 200, 200))
        self.assertEqual(len(controls), 0)

    def test_single_control_positioned(self):
        ctrl = _MockCtrl((99, 99, 100, 30))
        d2d_vbox([ctrl], (0, 0, 200, 200), margin=12)
        self.assertEqual(ctrl.rect, (12, 12, 100, 30))

    def test_two_controls_vertical(self):
        c1 = _MockCtrl((99, 99, 120, 30))
        c2 = _MockCtrl((99, 99, 120, 40))
        d2d_vbox([c1, c2], (0, 0, 300, 200), spacing=10, margin=15)

        self.assertEqual(c1.rect, (15, 15, 120, 30))
        self.assertEqual(c2.rect, (15, 15 + 30 + 10, 120, 40))

    def test_integration_with_button(self):
        from sheskin.controls import D2DButton
        btn1 = D2DButton((99, 99, 140, 36), "X")
        btn2 = D2DButton((99, 99, 140, 36), "Y")
        d2d_vbox([btn1, btn2], (0, 0, 300, 200), spacing=8, margin=20)

        self.assertEqual(btn1.rect, (20, 20, 140, 36))
        self.assertEqual(btn2.rect, (20, 20 + 36 + 8, 140, 36))

    def test_overhang_top_in_vbox(self):
        class OverhangCtrl(_MockCtrl):
            def overhang_top(self):
                return 10.0

        c1 = OverhangCtrl((0, 0, 100, 30))
        c2 = _MockCtrl((0, 0, 100, 30))
        d2d_vbox([c1, c2], (0, 0, 200, 200), spacing=8, margin=10)
        self.assertEqual(c1.rect, (10, 20, 100, 30))
        self.assertEqual(c2.rect, (10, 58.0, 100, 30))


if __name__ == '__main__':
    unittest.main()