"""D2D 控件 — D2DTreeCtrl / SkinAwareTreeCtrl 树控件。

参考 wx.TreeCtrl 行为：
- 层级展开/折叠（点击 +/- 按钮或双击节点）
- 图标支持（ImageList 模式：normal / selected / expanded 图标索引）
- 选中（单选模式）
- 纵向 ScrollBar
- 键盘导航：Up/Down 移动选中，Home/End 首尾，Left 折叠/移到父节点，Right 展开/移到子节点
- 事件：on_sel_changed / on_item_expanded / on_item_collapsed / on_item_activated
"""
import wx
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush
from ..d2d_render import d2d_draw_text
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP
from .headerctrl import draw_ctrl_border
from .scrollbar import D2DScrollBar, SkinAwareScrollBar

SCROLLBAR_WIDTH = 16
ITEM_PAD_X = 4
INDENT_WIDTH = 20
TOGGLE_BTN_SIZE = 9
TOGGLE_BTN_PAD = 4

TREECTRL_COLORS = {
    'normal': {
        'bg': (1.0, 1.0, 1.0, 1.0),
        'item_bg': None,
        'item_text': (0.0, 0.0, 0.0, 1.0),
        'line': (0.6, 0.6, 0.65, 1.0),
        'toggle_btn': (0.4, 0.4, 0.45, 1.0),
        'toggle_btn_bg': (0.95, 0.95, 0.97, 1.0),
    },
    'hover': {
        'item_bg': (0.90, 0.93, 0.98, 1.0),
        'item_text': (0.0, 0.0, 0.0, 1.0),
    },
    'selected': {
        'item_bg': (0.20, 0.45, 0.78, 1.0),
        'item_text': (1.0, 1.0, 1.0, 1.0),
    },
    'selected_no_focus': {
        'item_bg': (0.70, 0.75, 0.82, 1.0),
        'item_text': (1.0, 1.0, 1.0, 1.0),
    },
    'disabled': {
        'bg': (0.96, 0.96, 0.97, 1.0),
        'item_text': (0.55, 0.55, 0.58, 1.0),
    },
}


class TreeNode:
    """树节点数据模型。"""

    def __init__(self, text='', data=None, icon_normal=-1,
                 icon_selected=-1, icon_expanded=-1):
        self.text = text
        self.data = data
        self.icon_normal = icon_normal
        self.icon_selected = icon_selected
        self.icon_expanded = icon_expanded
        self.expanded = False
        self.children = []
        self.parent = None

    def add_child(self, node):
        node.parent = self
        self.children.append(node)
        return node

    def insert_child(self, index, node):
        node.parent = self
        self.children.insert(index, node)
        return node

    def remove_child(self, node):
        if node in self.children:
            self.children.remove(node)
            node.parent = None

    def child_count(self):
        return len(self.children)

    def has_children(self):
        return len(self.children) > 0

    def is_expanded(self):
        return self.expanded

    def expand(self):
        if self.has_children():
            self.expanded = True

    def collapse(self):
        self.expanded = False

    def toggle(self):
        if self.expanded:
            self.collapse()
        else:
            self.expand()

    def depth(self):
        d = 0
        n = self.parent
        while n is not None:
            d += 1
            n = n.parent
        return d


def _flatten_visible(root):
    """将展开的树扁平化为可见节点列表。"""
    result = []
    if root is None:
        return result
    result.append(root)
    if root.expanded:
        for child in root.children:
            result.extend(_flatten_visible(child))
    return result


class D2DTreeCtrl(SheControl):
    """D2D 自绘树控件 — 无 HWND，纯 D2D 渲染。

    行为参考 wx.TreeCtrl：
    - 点击 +/- 按钮展开/折叠
    - 双击节点展开/折叠
    - 点击节点文本选中
    - 键盘导航
    - 纵向 ScrollBar
    """

    def __init__(self, rect, on_sel_changed=None, on_item_expanded=None,
                 on_item_collapsed=None, on_item_activated=None):
        super().__init__(rect, "")
        self._root = None
        self._visible_nodes = []
        self._selected_node = None
        self._hover_node = None
        self._focused = False
        self._frame = None
        self._cursor_type = wx.CURSOR_ARROW
        self._scroll_y = 0
        self._v_scrollbar = None
        self._dwrite_text_fmt = None
        self._image_list = None

        self._on_sel_changed = on_sel_changed
        self._on_item_expanded = on_item_expanded
        self._on_item_collapsed = on_item_collapsed
        self._on_item_activated = on_item_activated

    # ---- 公共 API ----

    @property
    def root(self):
        return self._root

    def add_root(self, text='', data=None, icon_normal=-1,
                 icon_selected=-1, icon_expanded=-1):
        self._root = TreeNode(text, data, icon_normal, icon_selected, icon_expanded)
        self._refresh_visible()
        return self._root

    def append_item(self, parent, text='', data=None, icon_normal=-1,
                    icon_selected=-1, icon_expanded=-1):
        node = TreeNode(text, data, icon_normal, icon_selected, icon_expanded)
        parent.add_child(node)
        self._refresh_visible()
        return node

    def insert_item(self, parent, index, text='', data=None, icon_normal=-1,
                    icon_selected=-1, icon_expanded=-1):
        node = TreeNode(text, data, icon_normal, icon_selected, icon_expanded)
        parent.insert_child(index, node)
        self._refresh_visible()
        return node

    def delete_item(self, node):
        if node is None:
            return
        if node.parent is not None:
            node.parent.remove_child(node)
        elif node is self._root:
            self._root = None
        if self._selected_node is node:
            self._selected_node = None
        self._refresh_visible()

    def delete_children(self, node):
        if node is None:
            return
        node.children.clear()
        if node is self._root or self._is_ancestor(node, self._selected_node):
            if self._selected_node is not node and not self._is_ancestor(node, self._selected_node):
                pass
            else:
                self._selected_node = node
        self._refresh_visible()

    def delete_all_items(self):
        self._root = None
        self._selected_node = None
        self._hover_node = None
        self._scroll_y = 0
        self._refresh_visible()

    def expand(self, node):
        if node and node.has_children() and not node.expanded:
            node.expand()
            self._refresh_visible()
            if self._on_item_expanded:
                self._on_item_expanded(node)

    def collapse(self, node):
        if node and node.expanded:
            node.collapse()
            self._refresh_visible()
            if self._on_item_collapsed:
                self._on_item_collapsed(node)

    def toggle(self, node):
        if node and node.has_children():
            if node.expanded:
                self.collapse(node)
            else:
                self.expand(node)

    def expand_all(self, node=None):
        if node is None:
            node = self._root
        if node is None:
            return
        node.expanded = True
        for child in node.children:
            self.expand_all(child)
        self._refresh_visible()

    def collapse_all(self, node=None):
        if node is None:
            node = self._root
        if node is None:
            return
        node.expanded = False
        for child in node.children:
            self.collapse_all(child)
        self._refresh_visible()

    def select_item(self, node):
        if self._selected_node is not node:
            self._selected_node = node
            self._ensure_node_visible(node)
            if self._on_sel_changed:
                self._on_sel_changed(node)

    def get_selection(self):
        return self._selected_node

    def get_item_text(self, node):
        return node.text if node else ''

    def set_item_text(self, node, text):
        if node:
            node.text = text

    def get_item_data(self, node):
        return node.data if node else None

    def set_item_data(self, node, data):
        if node:
            node.data = data

    def get_item_parent(self, node):
        return node.parent if node else None

    def get_children(self, node):
        return list(node.children) if node else []

    def set_image_list(self, image_list):
        self._image_list = image_list

    def hit_test_node(self, pt):
        """返回点击位置的 (node, flags)。flags: 'toggle'|'icon'|'label'|None"""
        cx, cy, cw, ch = self._content_rect()
        px, py = pt
        if not (cx <= px <= cx + cw and cy <= py <= cy + ch):
            return None, None
        dw_factory = self._get_dw_factory()
        lh = self._line_height(dw_factory)
        idx = int((py - cy + self._scroll_y) // lh)
        if 0 <= idx < len(self._visible_nodes):
            node = self._visible_nodes[idx]
            depth = node.depth()
            indent = depth * INDENT_WIDTH
            toggle_x = cx + indent + ITEM_PAD_X
            icon_x = toggle_x + TOGGLE_BTN_SIZE + TOGGLE_BTN_PAD
            text_x = icon_x
            if self._image_list and node.icon_normal >= 0:
                text_x = icon_x + 16 + ITEM_PAD_X
            if toggle_x <= px <= toggle_x + TOGGLE_BTN_SIZE and node.has_children():
                return node, 'toggle'
            if icon_x <= px < text_x:
                return node, 'icon'
            if text_x <= px <= cx + cw:
                return node, 'label'
            return node, None
        return None, None

    # ---- 内部方法 ----

    def _is_ancestor(self, ancestor, node):
        n = node
        while n is not None:
            if n is ancestor:
                return True
            n = n.parent
        return False

    def _refresh_visible(self):
        self._visible_nodes = _flatten_visible(self._root)
        self._update_scrollbar()

    def _get_dw_factory(self):
        return pyd2d.GetDWriteFactory()

    def _get_text_fmt(self, dw_factory=None):
        if self._dwrite_text_fmt is not None:
            return self._dwrite_text_fmt
        if dw_factory is None:
            dw_factory = self._get_dw_factory()
        self._dwrite_text_fmt = dw_factory.CreateTextFormat(
            DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
            weight=pyd2d.FONT_WEIGHT.NORMAL,
            style=pyd2d.FONT_STYLE.NORMAL,
            stretch=pyd2d.FONT_STRETCH.NORMAL)
        self._dwrite_text_fmt.SetParagraphAlignment(pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return self._dwrite_text_fmt

    def _line_height(self, dw_factory=None):
        fmt = self._get_text_fmt(dw_factory)
        if fmt is None:
            return DEFAULT_FONT_SIZE_DIP + ITEM_PAD_X * 2
        try:
            factory = dw_factory or self._get_dw_factory()
            layout = factory.CreateTextLayout("Ay", fmt, 100000.0, 1000.0)
            if layout:
                lm = layout.GetLineMetrics()
                if lm:
                    return lm[0].height + ITEM_PAD_X * 2
        except Exception:
            pass
        return DEFAULT_FONT_SIZE_DIP + ITEM_PAD_X * 2

    def _content_rect(self):
        rx, ry, rw, rh = self._rect
        sb_w = SCROLLBAR_WIDTH if self._has_v_scrollbar() else 0
        return (rx + 2, ry + 2, rw - 4 - sb_w, rh - 4)

    def _has_v_scrollbar(self):
        return self._v_scrollbar is not None

    def _total_height(self, dw_factory=None):
        lh = self._line_height(dw_factory)
        return len(self._visible_nodes) * lh

    def _node_y(self, node, dw_factory=None):
        try:
            idx = self._visible_nodes.index(node)
        except ValueError:
            return -1
        lh = self._line_height(dw_factory)
        return idx * lh

    def _node_rect(self, node, dw_factory=None):
        cx, cy, cw, ch = self._content_rect()
        try:
            idx = self._visible_nodes.index(node)
        except ValueError:
            return (0, 0, 0, 0)
        lh = self._line_height(dw_factory)
        y = cy + idx * lh - self._scroll_y
        return (cx, y, cw, lh)

    def _update_scrollbar(self, dw_factory=None):
        if self._v_scrollbar is None:
            return
        lh = self._line_height(dw_factory)
        total = len(self._visible_nodes) * lh
        _, _, _, ch = self._content_rect()
        self._v_scrollbar.set_scroll_info(
            scroll_max=max(0, total - ch),
            page_size=ch)
        max_scroll = max(0, total - ch)
        if self._scroll_y > max_scroll:
            self._scroll_y = max_scroll
        self._v_scrollbar.set_scroll_pos(self._scroll_y)

    def _ensure_node_visible(self, node, dw_factory=None):
        if node is None:
            return
        try:
            idx = self._visible_nodes.index(node)
        except ValueError:
            return
        lh = self._line_height(dw_factory)
        _, _, _, ch = self._content_rect()
        item_top = idx * lh
        if item_top < self._scroll_y:
            self._scroll_y = item_top
        elif item_top + lh > self._scroll_y + ch:
            self._scroll_y = item_top + lh - ch
        self._scroll_y = max(0, self._scroll_y)
        if self._v_scrollbar:
            self._v_scrollbar.set_scroll_pos(self._scroll_y)

    def _border_state(self):
        if self._state == self.DISABLED:
            return 'disabled'
        if self._focused:
            return 'default'
        if self._state == self.HOVER:
            return 'hover'
        return 'normal'

    # ---- 滚动条 ----

    def set_parent_window(self, wnd):
        """由 frame.register_d2d_control 调用，自动创建 scrollbar。"""
        self._frame = wnd
        self._ensure_scrollbar()

    def bind_to_frame(self, frame):
        self._frame = frame
        self._ensure_scrollbar()

    def _ensure_scrollbar(self):
        if self._v_scrollbar is not None:
            return
        rx, ry, rw, rh = self._rect
        sb_cls = self._get_scrollbar_class()
        if sb_cls is SkinAwareScrollBar:
            self._v_scrollbar = sb_cls(
                (rx + rw - SCROLLBAR_WIDTH, ry + 2,
                 SCROLLBAR_WIDTH, rh - 4),
                self._ctx,
                scroll_pos=0, scroll_max=0, page_size=1,
                orientation=D2DScrollBar.VERTICAL,
                on_scroll=self._on_v_scroll)
        else:
            self._v_scrollbar = sb_cls(
                (rx + rw - SCROLLBAR_WIDTH, ry + 2,
                 SCROLLBAR_WIDTH, rh - 4),
                scroll_pos=0, scroll_max=0, page_size=1,
                orientation=D2DScrollBar.VERTICAL,
                on_scroll=self._on_v_scroll)
        self._update_scrollbar()

    def _get_scrollbar_class(self):
        return D2DScrollBar

    def _sync_scrollbar_rect(self):
        if self._v_scrollbar is None:
            return
        rx, ry, rw, rh = self._rect
        self._v_scrollbar._rect = (
            rx + rw - SCROLLBAR_WIDTH, ry + 2,
            SCROLLBAR_WIDTH, rh - 4)
        self._update_scrollbar()

    def set_rect(self, rect):
        super().set_rect(rect)
        self._sync_scrollbar_rect()

    def _on_v_scroll(self, pos):
        self._scroll_y = pos
        return True

    # ---- 焦点 ----

    def set_focus(self, focused):
        if self._focused == focused:
            return
        self._focused = focused

    # ---- 鼠标事件 ----

    def hit_test(self, pt):
        if not super().hit_test(pt):
            return False
        if self._v_scrollbar and self._v_scrollbar.hit_test(pt):
            return False
        return True

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._v_scrollbar and self._v_scrollbar.hit_test(pt):
            return self._v_scrollbar.on_mouse_down(pt)
        if not super().hit_test(pt):
            return False
        if self._frame:
            self._frame.set_focused_control(self)
        else:
            self.set_focus(True)

        node, flags = self.hit_test_node(pt)
        if node is None:
            return True

        if flags == 'toggle' and node.has_children():
            self.toggle(node)
            return True

        self.select_item(node)
        return True

    def on_mouse_up(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._v_scrollbar and self._v_scrollbar._captured:
            return self._v_scrollbar.on_mouse_up(pt)
        return False

    def on_mouse_move(self, pt):
        if self._state == self.DISABLED:
            return False
        if self._v_scrollbar and self._v_scrollbar._captured:
            return self._v_scrollbar.on_mouse_move(pt)
        if self._v_scrollbar and self._v_scrollbar.hit_test(pt):
            return self._v_scrollbar.on_mouse_move(pt)
        cx, cy, cw, ch = self._content_rect()
        px, py = pt
        if not (cx <= px <= cx + cw and cy <= py <= cy + ch):
            if self._hover_node is not None:
                self._hover_node = None
                return True
            return False
        dw_factory = self._get_dw_factory()
        lh = self._line_height(dw_factory)
        idx = int((py - cy + self._scroll_y) // lh)
        new_hover = self._visible_nodes[idx] if 0 <= idx < len(self._visible_nodes) else None
        changed = new_hover is not self._hover_node
        self._hover_node = new_hover
        return changed

    def on_mouse_leave(self):
        changed = self._hover_node is not None
        self._hover_node = None
        if self._v_scrollbar:
            self._v_scrollbar.on_mouse_leave()
        return changed

    def on_mouse_wheel(self, pt, delta):
        if self._state == self.DISABLED:
            return False
        if not super().hit_test(pt):
            return False
        if self._v_scrollbar is None or self._v_scrollbar._scroll_max <= 0:
            return False
        # delta > 0 向上滚，delta < 0 向下滚
        lh = self._line_height(self._get_dw_factory())
        scroll_delta = -delta * lh
        new_pos = max(0, min(self._v_scrollbar._scroll_max,
                              self._scroll_y + scroll_delta))
        if new_pos != self._scroll_y:
            self._scroll_y = new_pos
            self._v_scrollbar.set_scroll_pos(self._scroll_y)
            return True
        return False

    def on_double_click(self, pt):
        if self._state == self.DISABLED:
            return False
        node, flags = self.hit_test_node(pt)
        if node is None:
            return False
        if node.has_children():
            self.toggle(node)
        if self._on_item_activated:
            self._on_item_activated(node)
        return True

    # ---- 键盘事件 ----

    def on_key_down(self, key_code, modifiers):
        if self._state == self.DISABLED:
            return False
        if not self._visible_nodes:
            return False
        changed = False

        if key_code == wx.WXK_UP:
            new_node = self._move_up()
            if new_node:
                self.select_item(new_node)
                changed = True
        elif key_code == wx.WXK_DOWN:
            new_node = self._move_down()
            if new_node:
                self.select_item(new_node)
                changed = True
        elif key_code == wx.WXK_HOME:
            if self._visible_nodes:
                self.select_item(self._visible_nodes[0])
                changed = True
        elif key_code == wx.WXK_END:
            if self._visible_nodes:
                self.select_item(self._visible_nodes[-1])
                changed = True
        elif key_code == wx.WXK_LEFT:
            if self._selected_node:
                if self._selected_node.has_children() and self._selected_node.expanded:
                    self.collapse(self._selected_node)
                    changed = True
                elif self._selected_node.parent:
                    self.select_item(self._selected_node.parent)
                    changed = True
        elif key_code == wx.WXK_RIGHT:
            if self._selected_node:
                if self._selected_node.has_children() and not self._selected_node.expanded:
                    self.expand(self._selected_node)
                    changed = True
                elif self._selected_node.has_children() and self._selected_node.expanded:
                    first_child = self._selected_node.children[0]
                    self.select_item(first_child)
                    changed = True
        return changed

    def on_char(self, char_code):
        return False

    def tick_caret(self):
        return False

    def _move_up(self):
        if self._selected_node is None:
            return self._visible_nodes[0] if self._visible_nodes else None
        try:
            idx = self._visible_nodes.index(self._selected_node)
        except ValueError:
            return self._visible_nodes[0] if self._visible_nodes else None
        if idx > 0:
            return self._visible_nodes[idx - 1]
        return None

    def _move_down(self):
        if self._selected_node is None:
            return self._visible_nodes[0] if self._visible_nodes else None
        try:
            idx = self._visible_nodes.index(self._selected_node)
        except ValueError:
            return self._visible_nodes[0] if self._visible_nodes else None
        if idx < len(self._visible_nodes) - 1:
            return self._visible_nodes[idx + 1]
        return None

    # ---- 绘制 ----

    def _draw_toggle_button(self, rt, x, y, node, c):
        """绘制 +/- 展开折叠按钮。"""
        sz = float(TOGGLE_BTN_SIZE)
        bx, by = float(x), float(y)

        btn_bg = get_brush(rt, *c['toggle_btn_bg'])
        rt.FillRectangle(bx, by, bx + sz, by + sz, btn_bg)

        btn_brush = get_brush(rt, *c['toggle_btn'])
        # 画 +/- 号
        mid = sz / 2.0
        # 横线
        rt.FillRectangle(bx + 2.0, by + mid - 0.5, bx + sz - 2.0, by + mid + 0.5, btn_brush)
        # 竖线（仅折叠状态）
        if not node.expanded:
            rt.FillRectangle(bx + mid - 0.5, by + 2.0, bx + mid + 0.5, by + sz - 2.0, btn_brush)

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt
        dw_factory = ctx.dw_factory
        text_fmt = self._get_text_fmt(dw_factory)
        lh = self._line_height(dw_factory)

        border_state = self._border_state()
        draw_ctrl_border(rt, (rx, ry, rw, rh), state=border_state)

        cx, cy, cw, ch = self._content_rect()
        if cw <= 0 or ch <= 0:
            return

        rt.PushAxisAlignedClip(float(cx), float(cy),
                               float(cx + cw), float(cy + ch))

        c = TREECTRL_COLORS['disabled'] if self._state == self.DISABLED else TREECTRL_COLORS['normal']
        bg_brush = get_brush(rt, *c['bg'])
        rt.FillRectangle(float(cx), float(cy),
                         float(cx + cw), float(cy + ch), bg_brush)

        first_visible = max(0, int(self._scroll_y // lh))
        last_visible = min(len(self._visible_nodes),
                           first_visible + int(ch // lh) + 2)

        for i in range(first_visible, last_visible):
            node = self._visible_nodes[i]
            ix, iy, iw, ih = cx, cy + i * lh - self._scroll_y, cw, lh
            if iy + ih < cy or iy > cy + ch:
                continue

            is_sel = node is self._selected_node
            is_hover = node is self._hover_node and not is_sel

            # 选中/悬停背景
            if is_sel:
                if self._focused:
                    sel_colors = TREECTRL_COLORS['selected']
                else:
                    sel_colors = TREECTRL_COLORS['selected_no_focus']
                sel_brush = get_brush(rt, *sel_colors['item_bg'])
                rt.FillRectangle(float(ix), float(iy),
                                 float(ix + iw), float(iy + ih), sel_brush)
                text_color = sel_colors['item_text']
            elif is_hover:
                hover_brush = get_brush(rt, *TREECTRL_COLORS['hover']['item_bg'])
                rt.FillRectangle(float(ix), float(iy),
                                 float(ix + iw), float(iy + ih), hover_brush)
                text_color = TREECTRL_COLORS['hover']['item_text']
            else:
                text_color = c['item_text']

            # 缩进
            depth = node.depth()
            indent = depth * INDENT_WIDTH
            cur_x = ix + indent + ITEM_PAD_X

            # +/- 按钮
            if node.has_children():
                btn_y = iy + (ih - TOGGLE_BTN_SIZE) / 2.0
                self._draw_toggle_button(rt, int(cur_x), int(btn_y), node, c)
                cur_x += TOGGLE_BTN_SIZE + TOGGLE_BTN_PAD
            else:
                cur_x += TOGGLE_BTN_SIZE + TOGGLE_BTN_PAD

            # 图标（暂不绘制，ImageList 后续支持）
            # if self._image_list and node.icon_normal >= 0:
            #     ...

            # 文本
            if node.text and text_fmt:
                text_fmt.SetTextAlignment(pyd2d.TEXT_ALIGNMENT.LEADING)
                text_brush = get_brush(rt, *text_color)
                rt.DrawText(node.text, text_fmt,
                            float(cur_x), float(iy),
                            float(ix + iw - ITEM_PAD_X), float(iy + ih),
                            text_brush)

        rt.PopAxisAlignedClip()

        if self._v_scrollbar:
            self._v_scrollbar.draw(ctx, client_rect)


class SkinAwareTreeCtrl(D2DTreeCtrl):
    """皮肤化树控件 — 无皮肤数据时 fallback 到 D2DTreeCtrl 渲染。"""

    def __init__(self, rect, skin_context, on_sel_changed=None,
                 on_item_expanded=None, on_item_collapsed=None,
                 on_item_activated=None, subcat='TreeView'):
        super().__init__(rect, on_sel_changed=on_sel_changed,
                         on_item_expanded=on_item_expanded,
                         on_item_collapsed=on_item_collapsed,
                         on_item_activated=on_item_activated)
        self._ctx = skin_context
        self._subcat = subcat
        self._dwrite_text_fmt_cached = None

    def _get_text_fmt_cached(self, dw_factory=None):
        if self._dwrite_text_fmt_cached is not None:
            return self._dwrite_text_fmt_cached
        self._dwrite_text_fmt_cached = self._ctx.get_text_format(
            self._subcat, dw_factory=dw_factory,
            alignment=pyd2d.TEXT_ALIGNMENT.LEADING,
            para_alignment=pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return self._dwrite_text_fmt_cached

    def _get_text_color(self, state_idx):
        return self._ctx.get_text_color(self._subcat, state_idx)

    def _get_scrollbar_class(self):
        return SkinAwareScrollBar

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt
        dw_factory = ctx.dw_factory
        text_fmt = self._get_text_fmt_cached(dw_factory)
        lh = self._line_height(dw_factory)

        border_state = self._border_state()
        draw_ctrl_border(rt, (rx, ry, rw, rh), state=border_state,
                         skin_context=self._ctx)

        cx, cy, cw, ch = self._content_rect()
        if cw <= 0 or ch <= 0:
            return

        rt.PushAxisAlignedClip(float(cx), float(cy),
                               float(cx + cw), float(cy + ch))

        c = TREECTRL_COLORS['disabled'] if self._state == self.DISABLED else TREECTRL_COLORS['normal']
        bg_brush = get_brush(rt, *c['bg'])
        rt.FillRectangle(float(cx), float(cy),
                         float(cx + cw), float(cy + ch), bg_brush)

        first_visible = max(0, int(self._scroll_y // lh))
        last_visible = min(len(self._visible_nodes),
                           first_visible + int(ch // lh) + 2)

        for i in range(first_visible, last_visible):
            node = self._visible_nodes[i]
            ix, iy, iw, ih = cx, cy + i * lh - self._scroll_y, cw, lh
            if iy + ih < cy or iy > cy + ch:
                continue

            is_sel = node is self._selected_node
            is_hover = node is self._hover_node and not is_sel

            if is_sel:
                if self._focused:
                    sel_colors = TREECTRL_COLORS['selected']
                else:
                    sel_colors = TREECTRL_COLORS['selected_no_focus']
                sel_brush = get_brush(rt, *sel_colors['item_bg'])
                rt.FillRectangle(float(ix), float(iy),
                                 float(ix + iw), float(iy + ih), sel_brush)
                text_color = self._get_text_color(2) if self._focused else self._get_text_color(3)
            elif is_hover:
                hover_brush = get_brush(rt, *TREECTRL_COLORS['hover']['item_bg'])
                rt.FillRectangle(float(ix), float(iy),
                                 float(ix + iw), float(iy + ih), hover_brush)
                text_color = self._get_text_color(1)
            else:
                text_color = self._get_text_color(0)

            depth = node.depth()
            indent = depth * INDENT_WIDTH
            cur_x = ix + indent + ITEM_PAD_X

            if node.has_children():
                btn_y = iy + (ih - TOGGLE_BTN_SIZE) / 2.0
                self._draw_toggle_button(rt, int(cur_x), int(btn_y), node, c)
                cur_x += TOGGLE_BTN_SIZE + TOGGLE_BTN_PAD
            else:
                cur_x += TOGGLE_BTN_SIZE + TOGGLE_BTN_PAD

            if node.text and text_fmt:
                text_fmt.SetTextAlignment(pyd2d.TEXT_ALIGNMENT.LEADING)
                d2d_draw_text(rt, dw_factory, node.text, text_fmt, text_color,
                              float(cur_x), float(iy),
                              float(iw - ITEM_PAD_X * 2), float(ih))

        rt.PopAxisAlignedClip()

        if self._v_scrollbar:
            self._v_scrollbar.draw(ctx, client_rect)
