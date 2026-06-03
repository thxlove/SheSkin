"""SheSkin Framework 全控件演示 — 干净、分类清晰。"""
import wx
import pyd2d

from sheskin import SheLayeredFrame
from sheskin.brush_cache import get_brush
from sheskin.controls import (
    # 基础
    SheControl, Spacer,
    # 按钮
    SkinAwareButton, SkinAwareBitmapButton, ICON_ONLY, ICON_ABOVE_TEXT, ICON_LEFT_TEXT,
    # 输入
    SkinAwareCheckbox, SkinAwareRadioButton, RadioGroup,
    SkinAwareEditBox, SkinAwareTextBox,
    SkinAwareComboBox, SkinAwareSpinCtrl, SkinAwareTrackBar,
    # 显示
    SkinAwareLabel, SkinAwareGroupBox, SkinAwareProgress,
    SkinAwareStatusBar,
    # 容器/布局
    SkinAwareTabCtrl, SkinAwareHBox, SkinAwareVBox,
    # 高级
    SkinAwareHeaderCtrl, SkinAwareScrollBar, SkinAwareListBox, SkinAwareTreeCtrl,
    SkinAwareTreeCtrl as _SATC, TreeNode,
    draw_ctrl_border,
    # 菜单
    MenuItemData, SeparatorData, menu_separator,
    # 上下文
    SkinContext,
    # D2D 基础控件 (fallback)
    D2DButton, D2DLabel, D2DHBox, D2DVBox,
    D2DHeaderCtrl, ColumnDef, D2DScrollBar,
    D2DGroupBox, D2DCheckbox, D2DRadioButton, D2DProgress,
    D2DEditBox, D2DTextBox, D2DComboBox, D2DSpinCtrl, D2DTrackBar,
    D2DTabCtrl, D2DListBox, D2DTreeCtrl,
)


def _choose_skin():
    from sheskin.skin_data import get_skin_names
    names = get_skin_names()
    if not names:
        raise FileNotFoundError("无可用皮肤")
    for preferred in ('Red', 'ENJOY', 'Q2008', 'Aero', 'Asus'):
        if preferred in names:
            return preferred
    return names[0]


# =====================================================================
# 辅助
# =====================================================================

def _make_icon(r, g, b, size=16):
    img = wx.Image(size, size)
    img.SetRGB(wx.Rect(0, 0, size, size), r, g, b)
    img.SetAlpha(bytearray([200] * size * size))
    return wx.Bitmap(img)


# =====================================================================
# 各 Tab 页创建函数
# =====================================================================

def _page_buttons(ctx, icons):
    """按钮类控件。"""
    click_count = [0]

    btn_click = SkinAwareButton((0, 0, 120, 32), "点击计数", ctx,
                                on_click=lambda: _inc(click_count, lbl_cnt))
    lbl_cnt = SkinAwareButton((0, 0, 120, 32), "计数: 0", ctx)

    btn_disabled = SkinAwareButton((0, 0, 120, 32), "禁用按钮", ctx)
    btn_disabled._state = SkinAwareButton.DISABLED

    btn_row1 = SkinAwareHBox([btn_click, lbl_cnt, btn_disabled], spacing=8)

    # BitmapButton
    ib_new = SkinAwareBitmapButton((0, 0, 36, 36), ctx, icon=icons.get('new'),
                                   layout_mode=ICON_ONLY,
                                   on_click=lambda: print("[demo] 新建"))
    ib_open = SkinAwareBitmapButton((0, 0, 100, 32), ctx, icon=icons.get('open'),
                                    text="打开", layout_mode=ICON_LEFT_TEXT,
                                    on_click=lambda: print("[demo] 打开"))
    ib_save = SkinAwareBitmapButton((0, 0, 80, 48), ctx, icon=icons.get('save'),
                                    text="保存", layout_mode=ICON_ABOVE_TEXT,
                                    on_click=lambda: print("[demo] 保存"))
    btn_row2 = SkinAwareHBox([ib_new, ib_open, ib_save], spacing=8)

    return [btn_row1, Spacer(0, 8), btn_row2]


def _page_inputs(ctx):
    """输入类控件。"""
    # Checkbox
    cb1 = SkinAwareCheckbox((0, 0, 200, 24), "启用功能", ctx,
                            on_toggle=lambda v: print(f"[demo] 功能: {v}"))
    cb2 = SkinAwareCheckbox((0, 0, 200, 24), "调试模式", ctx, checked=True,
                            on_toggle=lambda v: print(f"[demo] 调试: {v}"))
    cb3 = SkinAwareCheckbox((0, 0, 200, 24), "自动保存", ctx)
    cb4 = SkinAwareCheckbox((0, 0, 200, 24), "禁用选项", ctx)
    cb4._state = SkinAwareCheckbox.DISABLED

    # RadioButton
    rb_a = SkinAwareRadioButton((0, 0, 200, 24), "1280 x 720", ctx, checked=True)
    rb_b = SkinAwareRadioButton((0, 0, 200, 24), "1920 x 1080", ctx)
    rb_c = SkinAwareRadioButton((0, 0, 200, 24), "2560 x 1440", ctx)
    rg = RadioGroup()
    rg.add(rb_a)
    rg.add(rb_b)
    rg.add(rb_c)

    gb_check = SkinAwareGroupBox((0, 0, 220, 130), "复选框", ctx)
    gb_check.add(cb1)
    gb_check.add(cb2)
    gb_check.add(cb3)
    gb_check.add(cb4)

    gb_radio = SkinAwareGroupBox((0, 0, 220, 110), "单选按钮", ctx)
    gb_radio.add(rg)

    # EditBox
    edit_normal = SkinAwareEditBox((0, 0, 220, 24), ctx, text="可编辑文本",
                                   placeholder="请输入...",
                                   on_change=lambda t: print(f"[demo] 文本: '{t}'"),
                                   on_enter=lambda: print("[demo] Enter"))
    edit_readonly = SkinAwareEditBox((0, 0, 220, 24), ctx, text="只读内容", readonly=True)
    edit_placeholder = SkinAwareEditBox((0, 0, 220, 24), ctx, placeholder="空输入框")

    # ComboBox
    combo = SkinAwareComboBox((0, 0, 220, 26), ctx,
                              items=['经典蓝', '暗夜黑', '极光绿', '日落橙', '樱桃红'],
                              selected=0,
                              on_change=lambda idx, old: print(f"[demo] 主题: {idx}"))

    # SpinCtrl
    spin = SkinAwareSpinCtrl((0, 0, 120, 24), ctx, value=50,
                             on_change=lambda v: print(f"[demo] Spin: {v}"))

    # TrackBar
    track = SkinAwareTrackBar((0, 0, 220, 28), ctx, value=50, resolution=1,
                              on_change=lambda v: print(f"[demo] 音量: {v}"))

    left = SkinAwareVBox.from_skin(ctx, [gb_check, Spacer(0, 4), gb_radio])
    right = SkinAwareVBox.from_skin(ctx, [
        edit_normal, edit_readonly, edit_placeholder, Spacer(0, 4),
        combo, spin, track
    ])

    return [SkinAwareHBox([left, right], spacing=16)]


def _page_text(ctx):
    """多行文本 & 列表。"""
    # TextBox
    tb_normal = SkinAwareTextBox((0, 0, 300, 120), ctx,
                                 text="多行文本编辑框\n第二行内容\n第三行\n第四行\n第五行",
                                 placeholder="输入多行文本...",
                                 on_change=lambda t: print(f"[demo] TextBox: {len(t)} chars"))
    tb_readonly = SkinAwareTextBox((0, 0, 300, 80), ctx,
                                   text="只读多行文本\n不可编辑", readonly=True)
    tb_scroll = SkinAwareTextBox((0, 0, 300, 150), ctx,
                                 text="\n".join(f"第{i+1}行 — 滚动条演示" for i in range(20))
                                       + "\n这是一行非常长的文本内容用来演示横向滚动条自动激活的效果",
                                 placeholder="带滚动条的多行编辑框...")

    # ListBox
    lb_single = SkinAwareListBox((0, 0, 200, 120), ctx,
                                 items=[f"列表项 {i+1}" for i in range(30)],
                                 mode=SkinAwareListBox.SINGLE,
                                 on_change=lambda sel: print(f"[demo] ListBox: {sel}"),
                                 on_double_click=lambda idx: print(f"[demo] 双击: {idx}"))
    lb_multi = SkinAwareListBox((0, 0, 200, 100), ctx,
                                items=["苹果", "香蕉", "橙子", "葡萄", "西瓜", "草莓"],
                                mode=SkinAwareListBox.EXTENDED,
                                on_change=lambda sel: print(f"[demo] 多选: {sel}"))

    left = SkinAwareVBox.from_skin(ctx, [tb_normal, tb_readonly, tb_scroll])
    right = SkinAwareVBox.from_skin(ctx, [lb_single, lb_multi])

    return [SkinAwareHBox([left, right], spacing=12)]


def _page_tree(ctx):
    """树控件。"""
    tree = SkinAwareTreeCtrl((0, 0, 400, 300), ctx,
                             on_sel_changed=lambda n: print(f"[demo] 选中: {n.text if n else None}"),
                             on_item_activated=lambda n: print(f"[demo] 激活: {n.text}"))
    root = tree.add_root("项目根目录")
    for i in range(5):
        folder = tree.append_item(root, f"文件夹 {i+1}")
        for j in range(3):
            sub = tree.append_item(folder, f"子项目 {i+1}-{j+1}")
            for k in range(2):
                tree.append_item(sub, f"文件 {i+1}-{j+1}-{k+1}")
    tree.expand(root)
    tree.set_context_menu([
        MenuItemData('展开全部', callback=lambda d: tree.expand_all()),
        MenuItemData('折叠全部', callback=lambda d: tree.collapse_all()),
        menu_separator(),
        MenuItemData('属性', callback=lambda d: print("[demo] 属性")),
    ])
    return [tree]


def _page_advanced(ctx):
    """高级控件：ScrollBar / CtrlBorder / Progress。"""
    # ScrollBar
    sb_vert = SkinAwareScrollBar((0, 0, 16, 120), ctx, scroll_pos=20,
                                 scroll_max=100, page_size=10,
                                 orientation=SkinAwareScrollBar.VERTICAL,
                                 on_scroll=lambda v: print(f"[demo] V-Scroll: {v}"))
    sb_horz = SkinAwareScrollBar((0, 0, 200, 16), ctx, scroll_pos=30,
                                 scroll_max=100, page_size=20,
                                 orientation=SkinAwareScrollBar.HORIZONTAL,
                                 on_scroll=lambda v: print(f"[demo] H-Scroll: {v}"))

    # CtrlBorder
    border_demo = _CtrlBorderDemo((0, 0, 300, 80), ctx)

    # Progress
    prog1 = SkinAwareProgress((0, 0, 300, 18), ctx, value=60)
    prog2 = SkinAwareProgress((0, 0, 300, 18), ctx, value=30)
    prog2._state = SkinAwareProgress.DISABLED

    return [sb_vert, sb_horz, Spacer(0, 4),
            border_demo, Spacer(0, 4), prog1, prog2]


# =====================================================================
# CtrlBorder 演示控件
# =====================================================================

class _CtrlBorderDemo(SheControl):
    def __init__(self, rect, skin_context=None):
        super().__init__(rect, "")
        self._ctx = skin_context
        self._hover_idx = -1

    def _box_rects(self):
        rx, ry, rw, rh = self._rect
        bw = (rw - 6) // 4
        bh = rh - 20
        return [(rx + i * (bw + 2), ry + 16, bw, bh) for i in range(4)]

    def hit_test(self, pt):
        rx, ry, rw, rh = self._rect
        return rx <= pt[0] <= rx + rw and ry <= pt[1] <= ry + rh

    def on_mouse_move(self, pt):
        old = self._hover_idx
        self._hover_idx = -1
        for i, (bx, by, bw, bh) in enumerate(self._box_rects()):
            if bx <= pt[0] <= bx + bw and by <= pt[1] <= by + bh:
                self._hover_idx = i
                break
        return self._hover_idx != old

    def on_mouse_leave(self):
        old = self._hover_idx
        self._hover_idx = -1
        return old >= 0

    def draw(self, ctx, client_rect):
        from sheskin.controls.headerctrl import CTRLBORDER_COLORS
        rx, ry, rw, rh = self._rect
        rt = ctx.rt

        label_fmt = ctx.dw_factory.CreateTextFormat(
            "Microsoft YaHei", 10.0,
            weight=pyd2d.FONT_WEIGHT.NORMAL,
            style=pyd2d.FONT_STYLE.NORMAL,
            stretch=pyd2d.FONT_STRETCH.NORMAL)
        label_brush = get_brush(rt, 0.4, 0.4, 0.4, 1.0)
        rt.DrawText("CtrlBorder 边框状态:", label_fmt,
                     float(rx), float(ry),
                     float(rx + rw), float(ry + 16), label_brush)

        states = ['normal', 'default', 'hover', 'disabled']
        labels = ['Normal', 'Default', 'Hover', 'Disabled']
        for i, (state, label, br) in enumerate(zip(states, labels, self._box_rects())):
            draw_ctrl_border(rt, br, state=state, skin_context=self._ctx)
            if i == self._hover_idx:
                hl = get_brush(rt, 0.0, 0.47, 0.84, 0.15)
                bx, by, bw, bh = br
                rt.FillRectangle(float(bx + 1), float(by + 1),
                                 float(bx + bw - 1), float(by + bh - 1), hl)
            c = CTRLBORDER_COLORS.get(state, CTRLBORDER_COLORS['normal'])
            text_brush = get_brush(rt, *c['outer'])
            rt.DrawText(label, label_fmt,
                        float(br[0]), float(br[1] + br[3] - 16),
                        float(br[0] + br[2]), float(br[1] + br[3]),
                        text_brush)


def _inc(cnt, lbl_btn):
    cnt[0] += 1
    lbl_btn.set_text(f"计数: {cnt[0]}")


# =====================================================================
# 主入口
# =====================================================================

def main():
    app = wx.App(False)
    skin_name = _choose_skin()
    print(f"[demo] 加载皮肤: {skin_name}")

    frame = SheLayeredFrame(
        skin_name,
        title=f"SheSkin Demo — {skin_name}",
        size=(900, 640),
        has_max=True, has_min=True, has_help=False)

    # --- 菜单栏 ---
    frame.set_menubar_items([
        MenuItemData('文件', submenu=[
            MenuItemData('新建', callback=lambda d: print("[demo] 新建")),
            MenuItemData('打开', callback=lambda d: print("[demo] 打开")),
            menu_separator(),
            MenuItemData('退出', callback=lambda d: frame.Close()),
        ]),
        MenuItemData('编辑', submenu=[
            MenuItemData('撤销', callback=lambda d: print("[demo] 撤销")),
            MenuItemData('重做', callback=lambda d: print("[demo] 重做")),
            menu_separator(),
            MenuItemData('查找', submenu=[
                MenuItemData('查找...', callback=lambda d: print("[demo] 查找")),
                MenuItemData('替换...', callback=lambda d: print("[demo] 替换")),
            ]),
        ]),
        MenuItemData('帮助', submenu=[
            MenuItemData('关于', callback=lambda d: print("[demo] 关于")),
        ]),
    ])

    # --- 工具栏 ---
    icon_new = _make_icon(60, 160, 60)
    icon_open = _make_icon(60, 120, 200)
    icon_save = _make_icon(200, 160, 60)
    icon_cut = _make_icon(200, 80, 80)
    icon_copy = _make_icon(80, 160, 200)
    icon_paste = _make_icon(160, 120, 200)
    icons = {'new': icon_new, 'open': icon_open, 'save': icon_save,
             'cut': icon_cut, 'copy': icon_copy, 'paste': icon_paste}

    frame.set_toolbar_items(
        [{'text': '新建', 'icon': icon_new},
         {'text': '打开', 'icon': icon_open},
         {'text': '保存', 'icon': icon_save},
         '|',
         {'text': '剪切', 'icon': icon_cut},
         {'text': '复制', 'icon': icon_copy},
         {'text': '粘贴', 'icon': icon_paste}],
        on_click=lambda idx, data: print(f"[demo] 工具栏 #{idx}"))

    # --- 状态栏 ---
    frame.set_statusbar_items(["就绪", "行: 1", "UTF-8"])

    # --- 右键菜单 ---
    frame.set_context_menu([
        MenuItemData('打开工具窗口', callback=lambda d: _open_tool_window(frame, skin_name)),
        menu_separator(),
        MenuItemData('属性', callback=lambda d: print("[demo] 属性")),
    ])

    # --- 客户区控件 ---
    if frame.skin is not None and frame.skin._loaded:
        ctx = SkinContext(frame.skin)
        controls = _build_controls(ctx, icons, frame)
    else:
        controls = _build_fallback_controls()

    for ctrl in controls:
        frame.register_d2d_control(ctrl)
        if hasattr(ctrl, 'children'):
            for child in ctrl.children:
                frame.register_d2d_control(child)
        if isinstance(ctrl, (SkinAwareEditBox, SkinAwareTextBox)):
            ctrl.bind_to_frame(frame)
        if isinstance(ctrl, SkinAwareListBox):
            ctrl.bind_to_frame(frame)
        if hasattr(ctrl, 'children'):
            for child in ctrl.children:
                if isinstance(child, (SkinAwareEditBox, SkinAwareTextBox)):
                    child.bind_to_frame(frame)
                if isinstance(child, SkinAwareListBox):
                    child.bind_to_frame(frame)

    frame.Show()
    app.MainLoop()


def _build_controls(ctx, icons, frame):
    """构建皮肤化 TabCtrl 及所有子页面控件。"""
    cx, cy, cw, ch = frame.get_client_rect()
    tab = SkinAwareTabCtrl((cx, cy, cw, ch), ctx,
                           on_change=lambda idx, old: print(f"[demo] Tab: {idx}"))

    # 各分类页面
    tab.add_page("按钮", controls=_page_buttons(ctx, icons))
    tab.add_page("输入", controls=_page_inputs(ctx))
    tab.add_page("文本/列表", controls=_page_text(ctx))
    tab.add_page("树控件", controls=_page_tree(ctx))
    tab.add_page("高级", controls=_page_advanced(ctx))
    tab.add_page("关于", controls=[
        SkinAwareLabel((0, 0, 300, 24), "SheSkin Framework v1.0", ctx),
        SkinAwareLabel((0, 0, 300, 24), "wxPython + Direct2D 自绘引擎", ctx),
    ])

    return tab.all_controls


def _build_fallback_controls():
    """无皮肤时的 fallback 控件。"""
    tab = D2DTabCtrl((20, 10, 860, 580))

    click_count = [0]
    btn = D2DButton((0, 0, 120, 32), "Click", on_click=lambda: None)
    lbl = D2DButton((0, 0, 120, 32), "Count: 0")
    btn_d = D2DButton((0, 0, 120, 32), "Disabled")
    btn_d._state = D2DButton.DISABLED

    tab.add_page("按钮", controls=[D2DHBox([btn, lbl, btn_d], spacing=8)])
    tab.add_page("关于", controls=[
        D2DLabel((0, 0, 300, 24), "SheSkin Framework (fallback)"),
    ])

    return tab.all_controls


def _open_tool_window(parent, skin_name):
    tw = SheLayeredFrame(
        skin_name, parent=parent,
        title="工具窗口", window_type='ToolWindow',
        size=(280, 200),
        has_max=False, has_min=False, has_help=False)

    if tw.skin is not None and tw.skin._loaded:
        ctx = SkinContext(tw.skin)
        tw_label = SkinAwareLabel((0, 0, 240, 24), "ToolWindow 浮动面板", ctx)
        tw_btn = SkinAwareButton((0, 0, 100, 30), "关闭", ctx,
                                 on_click=lambda: tw.Close())
        vbox = SkinAwareVBox([tw_label, Spacer(0, 8), tw_btn], spacing=6, margin=10)
    else:
        tw_label = D2DLabel((0, 0, 240, 24), "ToolWindow 浮动面板")
        tw_btn = D2DButton((0, 0, 100, 30), "关闭", on_click=lambda: tw.Close())
        vbox = D2DVBox([tw_label, Spacer(0, 8), tw_btn], spacing=6, margin=10)

    tw.add_client_draw(lambda ctx, rect: vbox.layout(rect))
    for c in vbox._walk_controls():
        tw.register_d2d_control(c)
    tw.Show()


if __name__ == '__main__':
    main()
