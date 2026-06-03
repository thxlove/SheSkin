"""D2DComboBox 单元测试 — 初始化、属性、交互、hit_test。"""
import unittest
from unittest.mock import MagicMock
from sheskin.controls.combobox import (
    D2DComboBox, COMBO_DROPDOWN_BTN_WIDTH, COMBO_TEXT_PAD_X,
)


class TestD2DComboBoxInit(unittest.TestCase):

    def test_init_defaults(self):
        cb = D2DComboBox((0, 0, 200, 26))
        self.assertEqual(cb.rect, (0, 0, 200, 26))
        self.assertEqual(cb.items, [])
        self.assertEqual(cb.selected, -1)
        self.assertEqual(cb.selected_text, '')
        self.assertFalse(cb.dropped_down)

    def test_init_with_items(self):
        cb = D2DComboBox((0, 0, 200, 26), items=['A', 'B', 'C'])
        self.assertEqual(cb.items, ['A', 'B', 'C'])

    def test_init_with_selected(self):
        cb = D2DComboBox((0, 0, 200, 26), items=['A', 'B'], selected=1)
        self.assertEqual(cb.selected, 1)
        self.assertEqual(cb.selected_text, 'B')

    def test_init_selected_out_of_range(self):
        cb = D2DComboBox((0, 0, 200, 26), items=['A'], selected=5)
        self.assertEqual(cb.selected, 5)
        self.assertEqual(cb.selected_text, '')


class TestD2DComboBoxProperties(unittest.TestCase):

    def test_selected_text_valid(self):
        cb = D2DComboBox((0, 0, 200, 26), items=['X', 'Y'], selected=0)
        self.assertEqual(cb.selected_text, 'X')

    def test_selected_text_invalid(self):
        cb = D2DComboBox((0, 0, 200, 26), items=['X'], selected=-1)
        self.assertEqual(cb.selected_text, '')

    def test_set_items(self):
        cb = D2DComboBox((0, 0, 200, 26), items=['A'], selected=0)
        cb.set_items(['X', 'Y', 'Z'])
        self.assertEqual(cb.items, ['X', 'Y', 'Z'])
        self.assertEqual(cb.selected, -1)

    def test_items_returns_copy(self):
        cb = D2DComboBox((0, 0, 200, 26), items=['A', 'B'])
        items = cb.items
        items.append('C')
        self.assertEqual(cb.items, ['A', 'B'])


class TestD2DComboBoxHitTest(unittest.TestCase):

    def test_hit_inside(self):
        cb = D2DComboBox((10, 20, 200, 26))
        self.assertTrue(cb.hit_test((50, 30)))

    def test_hit_outside(self):
        cb = D2DComboBox((10, 20, 200, 26))
        self.assertFalse(cb.hit_test((5, 30)))

    def test_hit_btn_area(self):
        cb = D2DComboBox((10, 20, 200, 26))
        bx = 10 + 200 - COMBO_DROPDOWN_BTN_WIDTH
        self.assertTrue(cb._hit_btn((bx + 5, 30)))

    def test_hit_text_area(self):
        cb = D2DComboBox((10, 20, 200, 26))
        self.assertTrue(cb._hit_text_area((20, 30)))

    def test_hit_text_area_not_btn(self):
        cb = D2DComboBox((10, 20, 200, 26))
        bx = 10 + 200 - COMBO_DROPDOWN_BTN_WIDTH
        self.assertFalse(cb._hit_text_area((bx + 5, 30)))


class TestD2DComboBoxMouseEvents(unittest.TestCase):

    def test_mouse_down_on_text_area(self):
        cb = D2DComboBox((10, 20, 200, 26), items=['A', 'B'])
        result = cb.on_mouse_down((30, 33))
        self.assertTrue(result)
        self.assertTrue(cb._captured)

    def test_mouse_down_on_btn(self):
        cb = D2DComboBox((10, 20, 200, 26), items=['A', 'B'])
        bx = 10 + 200 - COMBO_DROPDOWN_BTN_WIDTH
        result = cb.on_mouse_down((bx + 5, 33))
        self.assertTrue(result)
        self.assertTrue(cb._captured)

    def test_mouse_down_disabled(self):
        cb = D2DComboBox((10, 20, 200, 26))
        cb._state = D2DComboBox.DISABLED
        result = cb.on_mouse_down((30, 33))
        self.assertFalse(result)

    def test_mouse_down_miss(self):
        cb = D2DComboBox((10, 20, 200, 26))
        result = cb.on_mouse_down((5, 5))
        self.assertFalse(result)

    def test_mouse_up_triggers_dropdown(self):
        cb = D2DComboBox((10, 20, 200, 26), items=['A', 'B'])
        cb.on_mouse_down((30, 33))
        cb._parent_wnd = None
        result = cb.on_mouse_up((30, 33))
        self.assertTrue(result)
        self.assertFalse(cb._captured)

    def test_mouse_up_disabled(self):
        cb = D2DComboBox((10, 20, 200, 26))
        cb._state = D2DComboBox.DISABLED
        result = cb.on_mouse_up((30, 33))
        self.assertFalse(result)

    def test_mouse_move_hover(self):
        cb = D2DComboBox((10, 20, 200, 26))
        result = cb.on_mouse_move((30, 33))
        self.assertTrue(result)
        self.assertEqual(cb._btn_state, D2DComboBox.HOVER)

    def test_mouse_move_leave(self):
        cb = D2DComboBox((10, 20, 200, 26))
        cb.on_mouse_move((30, 33))
        result = cb.on_mouse_move((5, 5))
        self.assertTrue(result)
        self.assertEqual(cb._btn_state, D2DComboBox.NORMAL)

    def test_mouse_move_same_no_change(self):
        cb = D2DComboBox((10, 20, 200, 26))
        cb.on_mouse_move((30, 33))
        result = cb.on_mouse_move((30, 33))
        self.assertFalse(result)

    def test_mouse_leave(self):
        cb = D2DComboBox((10, 20, 200, 26))
        cb.on_mouse_move((30, 33))
        result = cb.on_mouse_leave()
        self.assertTrue(result)
        self.assertEqual(cb._btn_state, D2DComboBox.NORMAL)

    def test_mouse_leave_no_hover(self):
        cb = D2DComboBox((10, 20, 200, 26))
        result = cb.on_mouse_leave()
        self.assertFalse(result)


class TestD2DComboBoxStateName(unittest.TestCase):

    def test_normal_state(self):
        cb = D2DComboBox((0, 0, 200, 26))
        self.assertEqual(cb._get_state_name(), 'normal')

    def test_hover_state(self):
        cb = D2DComboBox((0, 0, 200, 26))
        cb._btn_state = D2DComboBox.HOVER
        self.assertEqual(cb._get_state_name(), 'hover')

    def test_disabled_state(self):
        cb = D2DComboBox((0, 0, 200, 26))
        cb._state = D2DComboBox.DISABLED
        self.assertEqual(cb._get_state_name(), 'disabled')

    def test_dropped_down_pressed(self):
        cb = D2DComboBox((0, 0, 200, 26))
        cb._dropped_down = True
        self.assertEqual(cb._get_state_name(), 'pressed')


if __name__ == '__main__':
    unittest.main()
