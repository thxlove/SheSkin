"""SkinAwareButton / SkinAwareCheckbox 皮肤化控件测试 (TDD)。"""
import os
import unittest
import wx
import pyd2d

from sheskin.skin import SheSkin
from sheskin.skin_data import get_skin_names
from sheskin.controls import (D2DButton, D2DCheckbox, D2DLabel, D2DRadioButton,
                               D2DGroupBox,
                               SkinAwareButton, SkinAwareCheckbox,
                               SkinAwareLabel, SkinAwareRadioButton,
                               SkinAwareGroupBox,
                               SkinContext,
                               D2DHBox, D2DVBox,
                               SkinAwareHBox, SkinAwareVBox)


def _find_skin():
    names = get_skin_names()
    if not names:
        return None
    for preferred in ('Asus', 'Q2008', 'Aero'):
        if preferred in names:
            return preferred
    return names[0]


class _MockSkinCtx:
    def __init__(self):
        self.skin_img = None
        self.skin = None
        self._fake_props = {}
        self._block_cache = {}

    @property
    def cache(self):
        from sheskin.d2d_render import D2DBlockCache
        return D2DBlockCache()

    def get_block(self, slot):
        return None

    def get_text_color(self, subcat, state_idx):
        return (0, 0, 0, 255)

    def get_font_height(self, subcat):
        return -9

    def get_font_info(self, subcat):
        return None


class TestSkinContext(unittest.TestCase):

    def test_mock_skin_context(self):
        ctx = _MockSkinCtx()
        self.assertIsNone(ctx.skin_img)
        self.assertIsNone(ctx.get_block(71))
        self.assertIsNotNone(ctx.cache)
        color = ctx.get_text_color('PushButton', 0)
        self.assertEqual(len(color), 4)

    def test_skin_context_with_real_skin(self):
        skin_name = _find_skin()
        if skin_name is None:
            self.skipTest("无皮肤文件")
        skin = SheSkin(skin_name)
        if not skin._loaded:
            self.skipTest("皮肤未加载")
        ctx = SkinContext(skin)
        self.assertIsNotNone(ctx.skin_img)
        self.assertIsNotNone(ctx.cache)
        block71 = ctx.get_block(71)
        if block71 is not None:
            self.assertGreater(block71.bg_width, 0)


class TestSkinAwareButton(unittest.TestCase):

    def test_inherits_d2dbutton(self):
        ctx = _MockSkinCtx()
        btn = SkinAwareButton((10, 10, 120, 36), "Test", ctx)
        self.assertIsInstance(btn, D2DButton)
        self.assertEqual(btn.text, "Test")
        self.assertEqual(btn.rect, (10, 10, 120, 36))

    def test_default_subcat(self):
        ctx = _MockSkinCtx()
        btn = SkinAwareButton((0, 0, 100, 30), "OK", ctx)
        self.assertEqual(btn._subcat, 'PushButton')
        self.assertIn('normal', btn._slots)
        self.assertEqual(btn._slots['normal'], 71)

    def test_state_propagation_from_parent(self):
        ctx = _MockSkinCtx()
        btn = SkinAwareButton((0, 0, 100, 30), "X", ctx)

        btn.on_mouse_down((50, 15))
        self.assertEqual(btn._state, D2DButton.PRESSED)

        btn.on_mouse_up((50, 15))
        self.assertEqual(btn._state, D2DButton.HOVER)

        btn.on_mouse_leave()
        self.assertEqual(btn._state, D2DButton.NORMAL)

    def test_click_callback(self):
        calls = []
        ctx = _MockSkinCtx()
        btn = SkinAwareButton((0, 0, 100, 30), "OK", ctx,
                              on_click=lambda: calls.append(1))

        btn.on_mouse_down((50, 15))
        btn.on_mouse_up((50, 15))
        self.assertEqual(len(calls), 1)

    def test_disabled_state(self):
        ctx = _MockSkinCtx()
        btn = SkinAwareButton((0, 0, 100, 30), "OK", ctx)
        btn._state = D2DButton.DISABLED

        self.assertFalse(btn.on_mouse_down((50, 15)))
        self.assertFalse(btn.on_mouse_up((50, 15)))
        self.assertFalse(btn.on_mouse_move((50, 15)))
        self.assertFalse(btn.on_mouse_leave())

    def test_setters(self):
        ctx = _MockSkinCtx()
        btn = SkinAwareButton((10, 10, 100, 30), "Old", ctx)
        btn.set_rect((20, 20, 200, 50))
        self.assertEqual(btn.rect, (20, 20, 200, 50))
        btn.set_text("New")
        self.assertEqual(btn.text, "New")

    def test_fallback_draw_no_crash(self):
        app = wx.GetApp() or wx.App(False)
        import pyd2d
        wic = pyd2d.GetWICFactory()
        factory = pyd2d.GetD2DFactory()
        if not wic or not factory:
            self.skipTest("D2D factories not available")
        wic_bmp = wic.CreateBitmap(200, 100)
        rt = factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        ctx = _MockSkinCtx()
        ctx.rt = rt
        ctx.wic_factory = wic
        ctx.dw_factory = pyd2d.GetDWriteFactory()
        ctx.d2d_cache = None
        btn = SkinAwareButton((0, 0, 100, 30), "OK", ctx)
        rt.BeginDraw()
        btn.draw(ctx, (0, 0, 200, 100))
        rt.EndDraw()

    def test_real_skin_button_slot_exists(self):
        skin_name = _find_skin()
        if skin_name is None:
            self.skipTest("无皮肤文件")
        skin = SheSkin(skin_name)
        if not skin._loaded:
            self.skipTest("皮肤未加载")
        ctx = SkinContext(skin)
        block71 = ctx.get_block(71)
        self.assertIsNotNone(block71)
        if block71 is not None:
            self.assertGreater(block71.bg_width, 0)
            self.assertGreater(block71.bg_height, 0)

    def test_real_skin_button_states(self):
        skin_name = _find_skin()
        if skin_name is None:
            self.skipTest("无皮肤文件")
        skin = SheSkin(skin_name)
        if not skin._loaded:
            self.skipTest("皮肤未加载")
        ctx = SkinContext(skin)

        for slot in (71, 72, 73, 74, 75):
            block = ctx.get_block(slot)
            self.assertIsNotNone(block, f"Slot {slot} is None")
            if block is not None:
                self.assertGreater(block.bg_width, 0,
                                   f"Slot {slot} bg_width <= 0")
                self.assertGreater(block.bg_height, 0,
                                   f"Slot {slot} bg_height <= 0")


class TestSkinAwareCheckbox(unittest.TestCase):

    def test_inherits_d2dcheckbox(self):
        ctx = _MockSkinCtx()
        cb = SkinAwareCheckbox((10, 10, 160, 24), "Option", ctx)
        self.assertIsInstance(cb, D2DCheckbox)
        self.assertEqual(cb.text, "Option")
        self.assertFalse(cb.checked)

    def test_default_slots(self):
        ctx = _MockSkinCtx()
        cb = SkinAwareCheckbox((0, 0, 120, 24), "X", ctx)
        self.assertEqual(cb._subcat, 'CheckBox')
        self.assertIn('normal', cb._slots_unchecked)
        self.assertEqual(cb._slots_unchecked['normal'], 76)
        self.assertIn('normal', cb._slots_checked)
        self.assertEqual(cb._slots_checked['normal'], 81)

    def test_toggle_state(self):
        ctx = _MockSkinCtx()
        cb = SkinAwareCheckbox((0, 0, 200, 24), "Toggle", ctx)

        self.assertFalse(cb.checked)
        cb.on_mouse_down((10, 12))
        cb.on_mouse_up((10, 12))
        self.assertTrue(cb.checked)

        cb.on_mouse_down((10, 12))
        cb.on_mouse_up((10, 12))
        self.assertFalse(cb.checked)

    def test_toggle_callback(self):
        values = []
        ctx = _MockSkinCtx()
        cb = SkinAwareCheckbox((0, 0, 200, 24), "CB", ctx,
                               on_toggle=lambda v: values.append(v))

        cb.on_mouse_down((10, 12))
        cb.on_mouse_up((10, 12))
        self.assertEqual(values, [True])

        cb.on_mouse_down((10, 12))
        cb.on_mouse_up((10, 12))
        self.assertEqual(values, [True, False])

    def test_disabled_ignores(self):
        ctx = _MockSkinCtx()
        cb = SkinAwareCheckbox((0, 0, 160, 24), "Disabled", ctx)
        cb._state = D2DCheckbox.DISABLED

        self.assertFalse(cb.on_mouse_down((10, 12)))
        self.assertFalse(cb.on_mouse_up((10, 12)))
        self.assertFalse(cb.checked)

    def test_setters(self):
        ctx = _MockSkinCtx()
        cb = SkinAwareCheckbox((10, 10, 120, 24), "Old", ctx)
        cb.set_rect((20, 20, 200, 30))
        self.assertEqual(cb.rect, (20, 20, 200, 30))

        cb.set_text("New")
        self.assertEqual(cb.text, "New")

        cb.set_checked(True)
        self.assertTrue(cb.checked)

    def test_thirdstate_slots_available(self):
        ctx = _MockSkinCtx()
        cb = SkinAwareCheckbox((0, 0, 120, 24), "X", ctx)
        self.assertIsNotNone(cb._slots_third)
        self.assertEqual(cb._slots_third['normal'], 86)

    def test_thirdstate_selects_third_slots(self):
        ctx = _MockSkinCtx()
        cb = SkinAwareCheckbox((0, 0, 200, 24), "Toggle", ctx, is_thirdstate=True)
        self.assertTrue(cb.is_thirdstate)
        cb._state = D2DCheckbox.NORMAL
        cb.set_thirdstate(True)
        self.assertTrue(cb.is_thirdstate)

    def test_thirdstate_click_clears(self):
        ctx = _MockSkinCtx()
        cb = SkinAwareCheckbox((0, 0, 200, 24), "Third", ctx, is_thirdstate=True)
        self.assertTrue(cb.is_thirdstate)
        cb.on_mouse_down((20, 20))
        cb.on_mouse_up((20, 20))
        self.assertFalse(cb.is_thirdstate)
        self.assertFalse(cb.checked)

    def test_fallback_draw_no_crash(self):
        app = wx.GetApp() or wx.App(False)
        import pyd2d
        wic = pyd2d.GetWICFactory()
        factory = pyd2d.GetD2DFactory()
        if not wic or not factory:
            self.skipTest("D2D factories not available")
        wic_bmp = wic.CreateBitmap(200, 100)
        rt = factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        ctx = _MockSkinCtx()
        ctx.rt = rt
        ctx.wic_factory = wic
        ctx.dw_factory = pyd2d.GetDWriteFactory()
        ctx.d2d_cache = None
        cb = SkinAwareCheckbox((0, 0, 160, 24), "Option", ctx)
        rt.BeginDraw()
        cb.draw(ctx, (0, 0, 200, 100))
        rt.EndDraw()

    def test_real_skin_checkbox_slots(self):
        skin_name = _find_skin()
        if skin_name is None:
            self.skipTest("无皮肤文件")
        skin = SheSkin(skin_name)
        if not skin._loaded:
            self.skipTest("皮肤未加载")
        ctx = SkinContext(skin)

        for slot in (76, 77, 78, 79, 80, 81, 82, 83, 84, 85):
            block = ctx.get_block(slot)
            self.assertIsNotNone(block, f"Slot {slot} is None")
            if block is not None:
                self.assertGreater(block.bg_width, 0,
                                   f"Slot {slot} bg_width <= 0")
                self.assertGreater(block.bg_height, 0,
                                   f"Slot {slot} bg_height <= 0")


class TestSkinAwareLabel(unittest.TestCase):

    def test_inherits_d2dlabel(self):
        ctx = _MockSkinCtx()
        lbl = SkinAwareLabel((0, 0, 120, 24), "Label", ctx)
        self.assertIsInstance(lbl, D2DLabel)

    def test_default_subcat(self):
        ctx = _MockSkinCtx()
        lbl = SkinAwareLabel((0, 0, 120, 24), "Test", ctx)
        self.assertEqual(lbl._subcat, 'Label')

    def test_setters(self):
        ctx = _MockSkinCtx()
        lbl = SkinAwareLabel((10, 10, 120, 24), "Old", ctx)
        lbl.set_rect((20, 20, 200, 30))
        self.assertEqual(lbl.rect, (20, 20, 200, 30))

        lbl.set_text("New")
        self.assertEqual(lbl.text, "New")

    def test_disabled_no_activate(self):
        ctx = _MockSkinCtx()
        lbl = SkinAwareLabel((0, 0, 120, 24), "Disabled", ctx)
        lbl._state = D2DLabel.DISABLED
        lbl._on_activate()
        self.assertFalse(lbl.on_mouse_up((20, 20)))
        self.assertEqual(lbl._state, D2DLabel.DISABLED)

    def test_fallback_draw_no_crash(self):
        app = wx.GetApp() or wx.App(False)
        import pyd2d
        wic = pyd2d.GetWICFactory()
        factory = pyd2d.GetD2DFactory()
        if not wic or not factory:
            self.skipTest("D2D factories not available")
        wic_bmp = wic.CreateBitmap(200, 100)
        rt = factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        ctx = _MockSkinCtx()
        ctx.rt = rt
        ctx.wic_factory = wic
        ctx.dw_factory = pyd2d.GetDWriteFactory()
        ctx.d2d_cache = None
        lbl = SkinAwareLabel((0, 0, 160, 24), "Label", ctx)
        rt.BeginDraw()
        lbl.draw(ctx, (0, 0, 200, 100))
        rt.EndDraw()

    def test_real_skin_label_font(self):
        skin_name = _find_skin()
        if skin_name is None:
            self.skipTest("无皮肤文件")
        skin = SheSkin(skin_name)
        if not skin._loaded:
            self.skipTest("皮肤未加载")
        ctx = SkinContext(skin)
        font_info = ctx.get_font_info('Label')
        self.assertIsNotNone(font_info)
        self.assertIn('face_name', font_info)
        self.assertIn('height', font_info)


class TestSkinAwareRadioButton(unittest.TestCase):

    def test_inherits_d2dradiobutton(self):
        ctx = _MockSkinCtx()
        rb = SkinAwareRadioButton((0, 0, 120, 24), "Option", ctx)
        self.assertIsInstance(rb, D2DRadioButton)

    def test_default_slots(self):
        ctx = _MockSkinCtx()
        rb = SkinAwareRadioButton((0, 0, 120, 24), "Option", ctx)
        self.assertEqual(rb._slots_unc['normal'], 91)
        self.assertEqual(rb._slots_chk['normal'], 96)

    def test_click_selects(self):
        ctx = _MockSkinCtx()
        rb = SkinAwareRadioButton((0, 0, 120, 24), "Option", ctx)
        rb.on_mouse_down((20, 20))
        rb.on_mouse_up((20, 20))
        self.assertTrue(rb.checked)

    def test_click_stays_checked(self):
        ctx = _MockSkinCtx()
        rb = SkinAwareRadioButton((0, 0, 120, 24), "Option", ctx, checked=True)
        rb.on_mouse_down((20, 20))
        rb.on_mouse_up((20, 20))
        self.assertTrue(rb.checked)

    def test_disabled_ignores(self):
        ctx = _MockSkinCtx()
        rb = SkinAwareRadioButton((0, 0, 120, 24), "Disabled", ctx)
        rb._state = D2DRadioButton.DISABLED
        self.assertFalse(rb.on_mouse_down((20, 20)))
        self.assertFalse(rb.checked)

    def test_setters(self):
        ctx = _MockSkinCtx()
        rb = SkinAwareRadioButton((10, 10, 120, 24), "Old", ctx)
        rb.set_rect((20, 20, 200, 30))
        self.assertEqual(rb.rect, (20, 20, 200, 30))

        rb.set_text("New")
        self.assertEqual(rb.text, "New")

        rb.set_checked(True)
        self.assertTrue(rb.checked)

    def test_toggle_state(self):
        ctx = _MockSkinCtx()
        rb = SkinAwareRadioButton((10, 10, 120, 24), "Test", ctx)
        self.assertFalse(rb.checked)
        rb.on_mouse_down((20, 20))
        rb.on_mouse_up((20, 20))
        self.assertTrue(rb.checked)

    def test_fallback_draw_no_crash(self):
        app = wx.GetApp() or wx.App(False)
        import pyd2d
        wic = pyd2d.GetWICFactory()
        factory = pyd2d.GetD2DFactory()
        if not wic or not factory:
            self.skipTest("D2D factories not available")
        wic_bmp = wic.CreateBitmap(200, 100)
        rt = factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        ctx = _MockSkinCtx()
        ctx.rt = rt
        ctx.wic_factory = wic
        ctx.dw_factory = pyd2d.GetDWriteFactory()
        ctx.d2d_cache = None
        rb = SkinAwareRadioButton((0, 0, 160, 24), "Option", ctx)
        rt.BeginDraw()
        rb.draw(ctx, (0, 0, 200, 100))
        rt.EndDraw()

    def test_real_skin_radio_slots(self):
        skin_name = _find_skin()
        if skin_name is None:
            self.skipTest("无皮肤文件")
        skin = SheSkin(skin_name)
        if not skin._loaded:
            self.skipTest("皮肤未加载")
        ctx = SkinContext(skin)

        for slot in (91, 92, 93, 94, 95, 96, 97, 98, 99, 100):
            block = ctx.get_block(slot)
            self.assertIsNotNone(block, f"Slot {slot} is None")
            if block is not None:
                self.assertGreater(block.bg_width, 0,
                                   f"Slot {slot} bg_width <= 0")
                self.assertGreater(block.bg_height, 0,
                                   f"Slot {slot} bg_height <= 0")


class TestSkinAwareGroupBox(unittest.TestCase):

    def test_inherits_d2dgroupbox(self):
        ctx = _MockSkinCtx()
        gb = SkinAwareGroupBox((0, 0, 200, 80), "Group", ctx)
        self.assertIsInstance(gb, D2DGroupBox)

    def test_default_subcat(self):
        ctx = _MockSkinCtx()
        gb = SkinAwareGroupBox((0, 0, 200, 80), "Test", ctx)
        self.assertEqual(gb._subcat, 'GroupBox')

    def test_default_border_slots(self):
        ctx = _MockSkinCtx()
        gb = SkinAwareGroupBox((0, 0, 200, 80), "Test", ctx)
        self.assertEqual(gb._border_slots['normal'], 101)

    def test_default_text_bg_slots(self):
        ctx = _MockSkinCtx()
        gb = SkinAwareGroupBox((0, 0, 200, 80), "Test", ctx)
        self.assertEqual(gb._text_bg_slots['normal'], 103)
        self.assertEqual(gb._text_bg_slots['disabled'], 104)

    def test_setters(self):
        ctx = _MockSkinCtx()
        gb = SkinAwareGroupBox((10, 10, 200, 80), "Old", ctx)
        gb.set_rect((20, 20, 300, 100))
        self.assertEqual(gb.rect, (20, 20, 300, 100))
        gb.set_text("New Title")
        self.assertEqual(gb.text, "New Title")

    def test_mouse_events_return_false(self):
        ctx = _MockSkinCtx()
        gb = SkinAwareGroupBox((10, 10, 200, 80), "Title", ctx)
        self.assertFalse(gb.on_mouse_down((110, 50)))
        self.assertFalse(gb.on_mouse_up((110, 50)))
        self.assertFalse(gb.on_mouse_move((110, 50)))
        self.assertFalse(gb.on_mouse_leave())

    def test_children_add_remove(self):
        ctx = _MockSkinCtx()
        gb = SkinAwareGroupBox((0, 0, 200, 80), "Title", ctx)
        from sheskin.controls import SkinAwareLabel
        lbl = SkinAwareLabel((0, 0, 100, 24), "Child", ctx)
        gb.add(lbl)
        self.assertEqual(len(gb.children), 1)
        gb.remove(lbl)
        self.assertEqual(len(gb.children), 0)

    def test_children_clear(self):
        ctx = _MockSkinCtx()
        gb = SkinAwareGroupBox((0, 0, 200, 80), "Title", ctx)
        from sheskin.controls import SkinAwareLabel
        gb.add(SkinAwareLabel((0, 0, 100, 24), "A", ctx))
        gb.add(SkinAwareLabel((0, 0, 100, 24), "B", ctx))
        gb.clear()
        self.assertEqual(len(gb.children), 0)

    def test_fallback_draw_no_crash(self):
        app = wx.GetApp() or wx.App(False)
        import pyd2d
        wic = pyd2d.GetWICFactory()
        factory = pyd2d.GetD2DFactory()
        if not wic or not factory:
            self.skipTest("D2D factories not available")
        wic_bmp = wic.CreateBitmap(300, 150)
        rt = factory.CreateWicBitmapRenderTarget(
            target=wic_bmp,
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED)

        ctx = _MockSkinCtx()
        ctx.rt = rt
        ctx.wic_factory = wic
        ctx.dw_factory = pyd2d.GetDWriteFactory()
        ctx.d2d_cache = None
        gb = SkinAwareGroupBox((10, 10, 250, 80), "Group Title", ctx)
        rt.BeginDraw()
        gb.draw(ctx, (0, 0, 300, 150))
        rt.EndDraw()

    def test_real_skin_groupbox_slots(self):
        from sheskin.skin import SheSkin
        from sheskin.controls.skin_context import SkinContext
        skin_name = _find_skin()
        if skin_name is None:
            self.skipTest("无皮肤文件")
        skin = SheSkin(skin_name)
        if not skin._loaded:
            self.skipTest("皮肤文件未加载")
        ctx = SkinContext(skin)
        gb = SkinAwareGroupBox((0, 0, 200, 80), "Group", ctx)
        normal_slot = gb._border_slots['normal']
        block = ctx.get_block(normal_slot)
        self.assertIsNotNone(block, f"Slot {normal_slot} 无 block")
        self.assertGreater(block.bg_width, 0, f"Slot {normal_slot} bg_width <= 0")
        self.assertGreater(block.bg_height, 0, f"Slot {normal_slot} bg_height <= 0")


class TestClassBasedLayout(unittest.TestCase):

    def test_d2d_hbox_class(self):
        c1 = self._make_ctrl((99, 99, 80, 30))
        c2 = self._make_ctrl((99, 99, 100, 30))
        box = D2DHBox([c1, c2], spacing=8, margin=10)
        box.layout((0, 0, 400, 100))

        self.assertEqual(c1.rect, (10, 10, 80, 30))
        self.assertEqual(c2.rect, (10 + 80 + 8, 10, 100, 30))

    def test_d2d_vbox_class(self):
        c1 = self._make_ctrl((99, 99, 120, 30))
        c2 = self._make_ctrl((99, 99, 120, 40))
        box = D2DVBox([c1, c2], spacing=10, margin=15)
        box.layout((0, 0, 300, 200))

        self.assertEqual(c1.rect, (15, 15, 120, 30))
        self.assertEqual(c2.rect, (15, 15 + 30 + 10, 120, 40))

    def test_add_remove_controls(self):
        c1 = self._make_ctrl((0, 0, 50, 20))
        c2 = self._make_ctrl((0, 0, 60, 20))
        box = D2DHBox([c1])
        box.add(c2)
        self.assertEqual(len(box.controls), 2)

        box.remove(c2)
        self.assertEqual(len(box.controls), 1)

        box.clear()
        self.assertEqual(len(box.controls), 0)

    def test_spacing_margin_properties(self):
        box = D2DHBox([], spacing=20, margin=5)
        self.assertEqual(box.spacing, 20)
        self.assertEqual(box.margin, 5)

        box.spacing = 30
        self.assertEqual(box.spacing, 30)

        box.margin = 10
        self.assertEqual(box.margin, 10)

    def test_re_layout(self):
        c1 = self._make_ctrl((99, 99, 80, 30))
        box = D2DHBox([c1], spacing=10, margin=15)
        box.layout((0, 0, 400, 100))
        self.assertEqual(c1.rect, (15, 15, 80, 30))

        box.margin = 30
        box.layout((0, 0, 400, 100))
        self.assertEqual(c1.rect, (30, 30, 80, 30))

    def test_skin_aware_layout_from_skin(self):
        ctx = _MockSkinCtx()
        box = SkinAwareHBox.from_skin(ctx, [], spacing_key='btn_gap')
        self.assertIsInstance(box, SkinAwareHBox)
        self.assertEqual(box._ctx, ctx)

    @staticmethod
    def _make_ctrl(rect):
        class _Ctrl:
            def __init__(self, r):
                self._rect = r
            @property
            def rect(self):
                return self._rect
            def set_rect(self, r):
                self._rect = r
        return _Ctrl(rect)


if __name__ == '__main__':
    unittest.main()