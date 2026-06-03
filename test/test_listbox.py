"""单元测试 — D2DListBox / SkinAwareListBox。"""
import pytest
import wx
from sheskin.controls.listbox import D2DListBox, SkinAwareListBox, LISTBOX_COLORS


class TestD2DListBoxInit:
    def test_defaults(self):
        lb = D2DListBox((10, 20, 200, 150))
        assert lb.items == []
        assert lb.selected_indices == []
        assert lb.selected_index == -1
        assert lb.selected_item is None
        assert lb.mode == D2DListBox.SINGLE

    def test_with_items(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"])
        assert lb.items == ["A", "B", "C"]
        assert lb.selected_index == -1

    def test_with_selected(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={1})
        assert lb.selected_index == 1
        assert lb.selected_item == "B"

    def test_mode_multiple(self):
        lb = D2DListBox((0, 0, 200, 150), mode=D2DListBox.MULTIPLE)
        assert lb.mode == D2DListBox.MULTIPLE

    def test_mode_extended(self):
        lb = D2DListBox((0, 0, 200, 150), mode=D2DListBox.EXTENDED)
        assert lb.mode == D2DListBox.EXTENDED


class TestD2DListBoxItems:
    def test_set_items(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B"])
        lb.set_items(["X", "Y", "Z"])
        assert lb.items == ["X", "Y", "Z"]
        assert lb.selected_indices == []

    def test_add_item(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A"])
        lb.add_item("B")
        assert lb.items == ["A", "B"]

    def test_insert_item(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "C"])
        lb.insert_item(1, "B")
        assert lb.items == ["A", "B", "C"]

    def test_insert_item_shifts_selection(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={1, 2})
        lb.insert_item(1, "X")
        assert lb.selected_indices == [2, 3]

    def test_remove_item(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"])
        lb.remove_item(1)
        assert lb.items == ["A", "C"]

    def test_remove_item_shifts_selection(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={2})
        lb.remove_item(0)
        assert lb.selected_indices == [1]

    def test_remove_selected_item(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={1})
        lb.remove_item(1)
        assert lb.selected_indices == []

    def test_clear(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B"], selected={0})
        lb.clear()
        assert lb.items == []
        assert lb.selected_indices == []


class TestD2DListBoxSelection:
    def test_select(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"])
        lb.select(1)
        assert lb.is_selected(1)

    def test_deselect(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={1})
        lb.deselect(1)
        assert not lb.is_selected(1)

    def test_select_all(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"],
                        mode=D2DListBox.MULTIPLE)
        lb.select_all()
        assert lb.selected_indices == [0, 1, 2]

    def test_select_all_single_mode_noop(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"],
                        mode=D2DListBox.SINGLE)
        lb.select_all()
        assert lb.selected_indices == []

    def test_deselect_all(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={0, 2})
        lb.deselect_all()
        assert lb.selected_indices == []


class TestD2DListBoxMouse:
    def test_click_selects_single(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"])
        lb._line_height = lambda dw=None: 20
        lb._index_from_y = lambda py, dw=None: 1
        lb.on_mouse_down((10, 30))
        assert lb.selected_index == 1

    def test_click_triggers_on_change(self):
        changes = []
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"],
                        on_change=lambda sel: changes.append(sel))
        lb._index_from_y = lambda py, dw=None: 0
        lb.on_mouse_down((10, 10))
        assert len(changes) == 1
        assert changes[0] == [0]

    def test_disabled_no_click(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B"])
        lb._state = D2DListBox.DISABLED
        result = lb.on_mouse_down((10, 10))
        assert result is False

    def test_double_click(self):
        dbl = []
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"],
                        on_double_click=lambda idx: dbl.append(idx))
        lb._index_from_y = lambda py, dw=None: 2
        lb.on_double_click((10, 50))
        assert dbl == [2]


class TestD2DListBoxKeyboard:
    def test_key_down_moves_selection(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={0})
        lb.on_key_down(wx.WXK_DOWN, 0)
        assert lb.selected_index == 1

    def test_key_up_moves_selection(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={2})
        lb.on_key_down(wx.WXK_UP, 0)
        assert lb.selected_index == 1

    def test_key_home(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={2})
        lb.on_key_down(wx.WXK_HOME, 0)
        assert lb.selected_index == 0

    def test_key_end(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"], selected={0})
        lb.on_key_down(wx.WXK_END, 0)
        assert lb.selected_index == 2

    def test_ctrl_a_selects_all_extended(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"],
                        mode=D2DListBox.EXTENDED)
        lb.on_key_down(ord('A'), wx.MOD_CONTROL)
        assert lb.selected_indices == [0, 1, 2]

    def test_ctrl_a_noop_single(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"],
                        mode=D2DListBox.SINGLE)
        lb.on_key_down(ord('A'), wx.MOD_CONTROL)
        assert lb.selected_indices == []

    def test_disabled_no_key(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B"])
        lb._state = D2DListBox.DISABLED
        assert lb.on_key_down(wx.WXK_DOWN, 0) is False

    def test_empty_no_key(self):
        lb = D2DListBox((0, 0, 200, 150))
        assert lb.on_key_down(wx.WXK_DOWN, 0) is False


class TestD2DListBoxFocus:
    def test_set_focus(self):
        lb = D2DListBox((0, 0, 200, 150))
        lb.set_focus(True)
        assert lb.focused is True

    def test_lose_focus(self):
        lb = D2DListBox((0, 0, 200, 150))
        lb.set_focus(True)
        lb.set_focus(False)
        assert lb.focused is False

    def test_border_state_focused(self):
        lb = D2DListBox((0, 0, 200, 150))
        lb.set_focus(True)
        assert lb._border_state() == 'default'

    def test_border_state_hover(self):
        lb = D2DListBox((0, 0, 200, 150))
        lb._state = D2DListBox.HOVER
        assert lb._border_state() == 'hover'

    def test_border_state_disabled(self):
        lb = D2DListBox((0, 0, 200, 150))
        lb._state = D2DListBox.DISABLED
        assert lb._border_state() == 'disabled'


class TestD2DListBoxHitTest:
    def test_inside(self):
        lb = D2DListBox((10, 20, 200, 150))
        assert lb.hit_test((50, 50)) is True

    def test_outside(self):
        lb = D2DListBox((10, 20, 200, 150))
        assert lb.hit_test((5, 5)) is False


class TestD2DListBoxExtendedSelection:
    def test_single_click_selects(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C", "D"],
                        mode=D2DListBox.EXTENDED)
        lb._index_from_y = lambda py, dw=None: 0
        lb.on_mouse_down((10, 10))
        assert lb.selected_indices == [0]
        lb._index_from_y = lambda py, dw=None: 3
        lb.on_mouse_down((10, 80))
        assert lb.selected_indices == [3]

    def test_second_click_replaces(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"],
                        mode=D2DListBox.EXTENDED, selected={0})
        lb._index_from_y = lambda py, dw=None: 2
        lb.on_mouse_down((10, 60))
        assert lb.selected_indices == [2]


class TestD2DListBoxMultipleSelection:
    def test_toggle_on_click(self):
        lb = D2DListBox((0, 0, 200, 150), items=["A", "B", "C"],
                        mode=D2DListBox.MULTIPLE)
        lb._index_from_y = lambda py, dw=None: 1
        lb.on_mouse_down((10, 30))
        assert lb.is_selected(1)
        lb.on_mouse_down((10, 30))
        assert not lb.is_selected(1)
