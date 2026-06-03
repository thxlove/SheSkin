"""SheControl / Spacer 单元测试 — 基类交互、状态机、hit_test、visible 机制。"""
import unittest
from unittest.mock import MagicMock
from sheskin.controls.base_control import SheControl, Spacer


class TestSheControlInit(unittest.TestCase):

    def test_init_defaults(self):
        c = SheControl((10, 20, 100, 30), "Hello")
        self.assertEqual(c.rect, (10, 20, 100, 30))
        self.assertEqual(c.text, "Hello")
        self.assertEqual(c._state, SheControl.NORMAL)
        self.assertFalse(c._captured)
        self.assertTrue(c._visible)
        self.assertIsNone(c._hit_geometry)

    def test_state_constants(self):
        self.assertEqual(SheControl.NORMAL, 0)
        self.assertEqual(SheControl.HOVER, 1)
        self.assertEqual(SheControl.PRESSED, 2)
        self.assertEqual(SheControl.DISABLED, 3)


class TestSheControlHitTest(unittest.TestCase):

    def test_inside_rect(self):
        c = SheControl((10, 20, 100, 30), "")
        self.assertTrue(c.hit_test((50, 35)))

    def test_on_edge(self):
        c = SheControl((10, 20, 100, 30), "")
        self.assertTrue(c.hit_test((10, 20)))
        self.assertTrue(c.hit_test((110, 50)))

    def test_outside_rect(self):
        c = SheControl((10, 20, 100, 30), "")
        self.assertFalse(c.hit_test((9, 20)))
        self.assertFalse(c.hit_test((10, 19)))
        self.assertFalse(c.hit_test((111, 20)))
        self.assertFalse(c.hit_test((10, 51)))

    def test_hit_with_geometry(self):
        c = SheControl((0, 0, 100, 100), "")
        geo = MagicMock()
        geo.FillContainsPoint.return_value = True
        c.set_hit_geometry(geo)
        self.assertTrue(c.hit_test((50, 50)))
        geo.FillContainsPoint.assert_called_once_with(50.0, 50.0)

    def test_hit_geometry_offset(self):
        c = SheControl((10, 20, 100, 100), "")
        geo = MagicMock()
        geo.FillContainsPoint.return_value = True
        c.set_hit_geometry(geo)
        c.hit_test((60, 70))
        geo.FillContainsPoint.assert_called_once_with(50.0, 50.0)


class TestSheControlMouseDown(unittest.TestCase):

    def test_mouse_down_inside(self):
        c = SheControl((0, 0, 100, 30), "")
        result = c.on_mouse_down((50, 15))
        self.assertTrue(result)
        self.assertEqual(c._state, SheControl.PRESSED)
        self.assertTrue(c._captured)

    def test_mouse_down_outside(self):
        c = SheControl((0, 0, 100, 30), "")
        result = c.on_mouse_down((200, 200))
        self.assertFalse(result)
        self.assertEqual(c._state, SheControl.NORMAL)

    def test_mouse_down_disabled(self):
        c = SheControl((0, 0, 100, 30), "")
        c._state = SheControl.DISABLED
        result = c.on_mouse_down((50, 15))
        self.assertFalse(result)
        self.assertEqual(c._state, SheControl.DISABLED)


class TestSheControlMouseUp(unittest.TestCase):

    def test_mouse_up_inside_activates(self):
        activated = []
        c = SheControl((0, 0, 100, 30), "")
        c._on_activate = lambda: activated.append(True)
        c.on_mouse_down((50, 15))
        result = c.on_mouse_up((50, 15))
        self.assertTrue(result)
        self.assertEqual(c._state, SheControl.HOVER)
        self.assertFalse(c._captured)
        self.assertEqual(activated, [True])

    def test_mouse_up_outside_cancels(self):
        activated = []
        c = SheControl((0, 0, 100, 30), "")
        c._on_activate = lambda: activated.append(True)
        c.on_mouse_down((50, 15))
        result = c.on_mouse_up((200, 200))
        self.assertTrue(result)
        self.assertEqual(c._state, SheControl.NORMAL)
        self.assertEqual(activated, [])

    def test_mouse_up_disabled(self):
        c = SheControl((0, 0, 100, 30), "")
        c._state = SheControl.DISABLED
        result = c.on_mouse_up((50, 15))
        self.assertFalse(result)


class TestSheControlMouseMove(unittest.TestCase):

    def test_move_inside_hover(self):
        c = SheControl((0, 0, 100, 30), "")
        result = c.on_mouse_move((50, 15))
        self.assertTrue(result)
        self.assertEqual(c._state, SheControl.HOVER)

    def test_move_outside_normal(self):
        c = SheControl((0, 0, 100, 30), "")
        c._state = SheControl.HOVER
        result = c.on_mouse_move((200, 200))
        self.assertTrue(result)
        self.assertEqual(c._state, SheControl.NORMAL)

    def test_move_same_state_no_change(self):
        c = SheControl((0, 0, 100, 30), "")
        c.on_mouse_move((50, 15))
        result = c.on_mouse_move((60, 15))
        self.assertFalse(result)

    def test_move_captured_inside(self):
        c = SheControl((0, 0, 100, 30), "")
        c.on_mouse_down((50, 15))
        c._state = SheControl.NORMAL
        result = c.on_mouse_move((50, 15))
        self.assertTrue(result)
        self.assertEqual(c._state, SheControl.PRESSED)

    def test_move_captured_outside_stays_pressed(self):
        c = SheControl((0, 0, 100, 30), "")
        c.on_mouse_down((50, 15))
        result = c.on_mouse_move((200, 200))
        self.assertFalse(result)
        self.assertEqual(c._state, SheControl.PRESSED)

    def test_move_disabled(self):
        c = SheControl((0, 0, 100, 30), "")
        c._state = SheControl.DISABLED
        result = c.on_mouse_move((50, 15))
        self.assertFalse(result)


class TestSheControlMouseLeave(unittest.TestCase):

    def test_leave_from_hover(self):
        c = SheControl((0, 0, 100, 30), "")
        c._state = SheControl.HOVER
        result = c.on_mouse_leave()
        self.assertTrue(result)
        self.assertEqual(c._state, SheControl.NORMAL)

    def test_leave_from_pressed(self):
        c = SheControl((0, 0, 100, 30), "")
        c.on_mouse_down((50, 15))
        result = c.on_mouse_leave()
        self.assertTrue(result)
        self.assertEqual(c._state, SheControl.NORMAL)
        self.assertFalse(c._captured)

    def test_leave_from_normal(self):
        c = SheControl((0, 0, 100, 30), "")
        result = c.on_mouse_leave()
        self.assertFalse(result)

    def test_leave_disabled(self):
        c = SheControl((0, 0, 100, 30), "")
        c._state = SheControl.DISABLED
        result = c.on_mouse_leave()
        self.assertFalse(result)


class TestSheControlSetters(unittest.TestCase):

    def test_set_rect(self):
        c = SheControl((0, 0, 100, 30), "")
        c.set_rect((10, 20, 200, 40))
        self.assertEqual(c.rect, (10, 20, 200, 40))
        self.assertIsNone(c._text_layout)

    def test_set_text(self):
        c = SheControl((0, 0, 100, 30), "Old")
        c.set_text("New")
        self.assertEqual(c.text, "New")
        self.assertIsNone(c._text_layout)

    def test_overhang_top_default(self):
        c = SheControl((0, 0, 100, 30), "")
        self.assertEqual(c.overhang_top(), 0.0)


class TestSheControlVisible(unittest.TestCase):

    def test_visible_by_default(self):
        c = SheControl((0, 0, 100, 30), "")
        self.assertTrue(c._visible)

    def test_draw_skipped_when_invisible(self):
        class VisibleControl(SheControl):
            draw_called = False
            def draw(self, ctx, client_rect):
                VisibleControl.draw_called = True

        c = VisibleControl((0, 0, 100, 30), "")
        c._visible = False
        c.draw(None, None)
        self.assertFalse(VisibleControl.draw_called)

    def test_draw_called_when_visible(self):
        class VisibleControl(SheControl):
            draw_called = False
            def draw(self, ctx, client_rect):
                VisibleControl.draw_called = True

        c = VisibleControl((0, 0, 100, 30), "")
        c._visible = True
        c.draw(None, None)
        self.assertTrue(VisibleControl.draw_called)


class TestSpacer(unittest.TestCase):

    def test_init_defaults(self):
        s = Spacer()
        self.assertEqual(s.rect, (0, 0, 0, 0))
        self.assertEqual(s._state, SheControl.DISABLED)

    def test_init_with_size(self):
        s = Spacer(100, 80)
        self.assertEqual(s.rect, (0, 0, 100, 80))

    def test_init_negative_clamps_to_zero(self):
        s = Spacer(-10, -5)
        self.assertEqual(s.rect, (0, 0, 0, 0))

    def test_no_mouse_interaction(self):
        s = Spacer(50, 20)
        self.assertFalse(s.on_mouse_down((10, 10)))
        self.assertFalse(s.on_mouse_up((10, 10)))
        self.assertFalse(s.on_mouse_move((10, 10)))
        self.assertFalse(s.on_mouse_leave())

    def test_draw_noop(self):
        s = Spacer(50, 20)
        s.draw(None, None)

    def test_is_shecontrol(self):
        s = Spacer()
        self.assertIsInstance(s, SheControl)


if __name__ == '__main__':
    unittest.main()
