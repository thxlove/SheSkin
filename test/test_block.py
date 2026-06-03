"""BlockData / block_from_raw / is_block_empty 单元测试。"""
import unittest
from sheskin.block import BlockData, block_from_raw, is_block_empty


class TestBlockData(unittest.TestCase):

    def test_namedtuple_fields(self):
        b = BlockData(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
        self.assertEqual(b.bg_left, 1)
        self.assertEqual(b.bg_top, 2)
        self.assertEqual(b.bg_width, 3)
        self.assertEqual(b.bg_height, 4)
        self.assertEqual(b.bg_color_key, 5)
        self.assertEqual(b.fg_left, 6)
        self.assertEqual(b.fg_top, 7)
        self.assertEqual(b.fg_width, 8)
        self.assertEqual(b.fg_height, 9)
        self.assertEqual(b.fg_color_key, 10)
        self.assertEqual(b.margin_left, 11)
        self.assertEqual(b.margin_top, 12)
        self.assertEqual(b.margin_right, 13)
        self.assertEqual(b.margin_bottom, 14)
        self.assertEqual(b.draw_flags, 15)
        self.assertEqual(b.alignment, 16)
        self.assertEqual(b.offset_x, 17)
        self.assertEqual(b.offset_y, 18)

    def test_all_zeros(self):
        b = BlockData(*([0] * 18))
        self.assertEqual(b.bg_width, 0)
        self.assertEqual(b.fg_width, 0)

    def test_immutable(self):
        b = BlockData(*([0] * 18))
        with self.assertRaises(AttributeError):
            b.bg_width = 100


class TestBlockFromRaw(unittest.TestCase):

    def test_valid_raw(self):
        raw = [10, 20, 100, 50, 0xFF, 30, 40, 60, 30, 0xFF,
               5, 5, 5, 5, 0, 0, 0, 0]
        b = block_from_raw(raw)
        self.assertEqual(b.bg_left, 10)
        self.assertEqual(b.bg_top, 20)
        self.assertEqual(b.bg_width, 100)
        self.assertEqual(b.bg_height, 50)
        self.assertEqual(b.fg_left, 30)
        self.assertEqual(b.fg_width, 60)

    def test_none_raw(self):
        b = block_from_raw(None)
        self.assertEqual(b.bg_width, 0)
        self.assertEqual(b.fg_width, 0)

    def test_empty_raw(self):
        b = block_from_raw([])
        self.assertEqual(b.bg_width, 0)

    def test_short_raw_returns_zeros(self):
        b = block_from_raw([1, 2, 3])
        self.assertEqual(b.bg_width, 0)
        self.assertEqual(b.fg_width, 0)

    def test_extra_fields_ignored(self):
        raw = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        b = block_from_raw(raw)
        self.assertEqual(b.offset_y, 18)

    def test_exactly_18_fields(self):
        raw = list(range(18))
        b = block_from_raw(raw)
        self.assertEqual(b.bg_left, 0)
        self.assertEqual(b.offset_y, 17)


class TestIsBlockEmpty(unittest.TestCase):

    def test_none_is_empty(self):
        self.assertTrue(is_block_empty(None))

    def test_all_zeros_is_empty(self):
        b = BlockData(*([0] * 18))
        self.assertTrue(is_block_empty(b))

    def test_bg_nonzero_not_empty(self):
        b = BlockData(0, 0, 100, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.assertFalse(is_block_empty(b))

    def test_fg_nonzero_not_empty(self):
        b = BlockData(0, 0, 0, 0, 0, 0, 0, 60, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.assertFalse(is_block_empty(b))

    def test_both_nonzero_not_empty(self):
        b = BlockData(10, 20, 100, 50, 0, 30, 40, 60, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.assertFalse(is_block_empty(b))

    def test_only_margins_not_empty_for_list(self):
        raw = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 0, 0, 0, 0]
        self.assertFalse(is_block_empty(raw))

    def test_all_zero_list_is_empty(self):
        self.assertTrue(is_block_empty([0] * 18))

    def test_nonzero_in_list_not_empty(self):
        raw = [0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.assertFalse(is_block_empty(raw))


if __name__ == '__main__':
    unittest.main()
