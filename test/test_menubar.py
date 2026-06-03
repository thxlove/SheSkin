"""SheMenuBar 单元测试 — 项目管理、hit_test、鼠标交互、状态。"""
import unittest
from unittest.mock import MagicMock, patch
from sheskin.menubar import SheMenuBar


class TestSheMenuBarInit(unittest.TestCase):

    def test_init_defaults(self):
        mb = SheMenuBar(None)
        self.assertEqual(mb._items, [])
        self.assertEqual(mb._hover_idx, -1)
        self.assertEqual(mb._pressed_idx, -1)
        self.assertEqual(mb._last_clicked_idx, -1)

    def test_init_rect(self):
        mb = SheMenuBar(None)
        self.assertEqual(mb._rect.GetWidth(), 0)
        self.assertEqual(mb._rect.GetHeight(), 0)


class TestSheMenuBarSetItems(unittest.TestCase):

    def test_set_items(self):
        mb = SheMenuBar(None)
        mb.set_items(["File", "Edit", "Help"])
        self.assertEqual(mb._items, ["File", "Edit", "Help"])

    def test_set_items_clears_layouts(self):
        mb = SheMenuBar(None)
        mb.set_items(["A"])
        mb._d2d_item_layouts = [MagicMock()]
        mb.set_items(["B", "C"])
        self.assertEqual(mb._d2d_item_layouts, [])

    def test_set_items_empty(self):
        mb = SheMenuBar(None)
        mb.set_items(["A"])
        mb.set_items([])
        self.assertEqual(mb._items, [])


class TestSheMenuBarSetRect(unittest.TestCase):

    def test_set_rect_from_tuple(self):
        mb = SheMenuBar(None)
        mb.set_rect((10, 20, 300, 24))
        self.assertEqual(mb._rect.x, 10)
        self.assertEqual(mb._rect.y, 20)
        self.assertEqual(mb._rect.width, 300)
        self.assertEqual(mb._rect.height, 24)

    def test_set_rect_from_wx_rect(self):
        import wx
        mb = SheMenuBar(None)
        mb.set_rect(wx.Rect(5, 10, 200, 24))
        self.assertEqual(mb._rect.x, 5)


class TestSheMenuBarHitTest(unittest.TestCase):

    def test_hit_inside_item(self):
        mb = SheMenuBar(None)
        mb.set_items(["File", "Edit"])
        mb.set_rect((0, 0, 300, 24))
        mb._item_rects = [(4, 60), (64, 60)]
        self.assertEqual(mb.hit_test((34, 12)), 0)
        self.assertEqual(mb.hit_test((94, 12)), 1)

    def test_hit_outside_items(self):
        mb = SheMenuBar(None)
        mb.set_items(["File", "Edit"])
        mb.set_rect((0, 0, 300, 24))
        mb._item_rects = [(4, 60), (64, 60)]
        self.assertEqual(mb.hit_test((200, 12)), -1)

    def test_hit_outside_rect(self):
        mb = SheMenuBar(None)
        mb.set_rect((0, 0, 300, 24))
        self.assertEqual(mb.hit_test((-10, -10)), -1)
        self.assertEqual(mb.hit_test((400, 400)), -1)

    def test_hit_empty_items(self):
        mb = SheMenuBar(None)
        mb.set_rect((0, 0, 300, 24))
        mb._item_rects = []
        self.assertEqual(mb.hit_test((50, 12)), -1)


class TestSheMenuBarMouseDown(unittest.TestCase):

    def test_mouse_down_on_item(self):
        mb = SheMenuBar(None)
        mb.set_items(["A", "B"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80), (80, 80)]
        result = mb.on_mouse_down((40, 12))
        self.assertTrue(result)
        self.assertEqual(mb._pressed_idx, 0)

    def test_mouse_down_miss(self):
        mb = SheMenuBar(None)
        mb.set_items(["A"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80)]
        result = mb.on_mouse_down((200, 12))
        self.assertFalse(result)
        self.assertEqual(mb._pressed_idx, -1)


class TestSheMenuBarMouseUp(unittest.TestCase):

    def test_mouse_up_click_same_item(self):
        mb = SheMenuBar(None)
        mb.set_items(["A", "B"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80), (80, 80)]
        mb.on_mouse_down((40, 12))
        result = mb.on_mouse_up((40, 12))
        self.assertTrue(result)
        self.assertEqual(mb.last_clicked_idx, 0)
        self.assertEqual(mb._pressed_idx, -1)
        self.assertEqual(mb._hover_idx, 0)

    def test_mouse_up_different_item(self):
        mb = SheMenuBar(None)
        mb.set_items(["A", "B"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80), (80, 80)]
        mb.on_mouse_down((40, 12))
        result = mb.on_mouse_up((120, 12))
        self.assertTrue(result)
        self.assertEqual(mb.last_clicked_idx, -1)
        self.assertEqual(mb._hover_idx, 1)

    def test_mouse_up_no_pressed(self):
        mb = SheMenuBar(None)
        mb.set_items(["A"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80)]
        result = mb.on_mouse_up((40, 12))
        self.assertTrue(result)
        self.assertEqual(mb.last_clicked_idx, -1)


class TestSheMenuBarMouseMove(unittest.TestCase):

    def test_mouse_move_hover(self):
        mb = SheMenuBar(None)
        mb.set_items(["A", "B"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80), (80, 80)]
        result = mb.on_mouse_move((40, 12))
        self.assertTrue(result)
        self.assertEqual(mb._hover_idx, 0)

    def test_mouse_move_same_no_change(self):
        mb = SheMenuBar(None)
        mb.set_items(["A"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80)]
        mb.on_mouse_move((40, 12))
        result = mb.on_mouse_move((40, 12))
        self.assertFalse(result)

    def test_mouse_move_to_different_item(self):
        mb = SheMenuBar(None)
        mb.set_items(["A", "B"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80), (80, 80)]
        mb.on_mouse_move((40, 12))
        result = mb.on_mouse_move((120, 12))
        self.assertTrue(result)
        self.assertEqual(mb._hover_idx, 1)

    def test_mouse_move_outside(self):
        mb = SheMenuBar(None)
        mb.set_items(["A"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80)]
        mb.on_mouse_move((40, 12))
        result = mb.on_mouse_move((200, 12))
        self.assertTrue(result)
        self.assertEqual(mb._hover_idx, -1)


class TestSheMenuBarMouseLeave(unittest.TestCase):

    def test_mouse_leave_from_hover(self):
        mb = SheMenuBar(None)
        mb.set_items(["A"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80)]
        mb.on_mouse_move((40, 12))
        result = mb.on_mouse_leave()
        self.assertTrue(result)
        self.assertEqual(mb._hover_idx, -1)
        self.assertEqual(mb._pressed_idx, -1)

    def test_mouse_leave_from_pressed(self):
        mb = SheMenuBar(None)
        mb.set_items(["A"])
        mb.set_rect((0, 0, 200, 24))
        mb._item_rects = [(0, 80)]
        mb.on_mouse_down((40, 12))
        result = mb.on_mouse_leave()
        self.assertTrue(result)
        self.assertEqual(mb._pressed_idx, -1)

    def test_mouse_leave_no_state(self):
        mb = SheMenuBar(None)
        result = mb.on_mouse_leave()
        self.assertFalse(result)


class TestSheMenuBarRectHitTest(unittest.TestCase):

    def test_inside_rect(self):
        mb = SheMenuBar(None)
        mb.set_rect((0, 0, 300, 24))
        self.assertTrue(mb._rect_hit_test((50, 12)))

    def test_outside_rect(self):
        mb = SheMenuBar(None)
        mb.set_rect((0, 0, 300, 24))
        self.assertFalse(mb._rect_hit_test((-10, 12)))
        self.assertFalse(mb._rect_hit_test((400, 12)))


class TestSheMenuBarLastClicked(unittest.TestCase):

    def test_last_clicked_initially(self):
        mb = SheMenuBar(None)
        self.assertEqual(mb.last_clicked_idx, -1)

    def test_last_clicked_after_click(self):
        mb = SheMenuBar(None)
        mb.set_items(["A", "B", "C"])
        mb.set_rect((0, 0, 300, 24))
        mb._item_rects = [(0, 80), (80, 80), (160, 80)]
        mb.on_mouse_down((120, 12))
        mb.on_mouse_up((120, 12))
        self.assertEqual(mb.last_clicked_idx, 1)


if __name__ == '__main__':
    unittest.main()
