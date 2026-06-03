"""DrawNode — 绘制树节点，替代扁平回调列表。

设计:
  - 树形结构天然支持 z-order（子节点按索引从小到大，从后到前绘制）
  - clip 属性控制子区域裁剪（自动 Push/PopAxisAlignedClip）
  - rect 相对于父节点偏移，render 时计算绝对坐标

用法:
  root = DrawNode((0, 0, w, h), name='root')
  border = root.add_child(DrawNode((0, 0, w, h), draw_fn=draw_border, name='border'))
  titlebar = root.add_child(DrawNode((b_left, 0, bw, b_top), draw_fn=draw_titlebar, name='titlebar'))
  client = root.add_child(DrawNode((b_left, top, bw, ch), clip=True, name='client'))
  client.add_child(DrawNode((0, 0, bw, ch), draw_fn=user_cb, name='user_content'))
"""


class DrawNode:

    def __init__(self, rect, draw_fn=None, clip=False, name=''):
        self.rect = rect
        self.draw_fn = draw_fn
        self.children = []
        self.clip = clip
        self.name = name
        self.visible = True

    def add_child(self, child):
        self.children.append(child)
        return child

    def remove_child(self, child):
        self.children.remove(child)

    def clear_children(self):
        self.children.clear()

    def render(self, ctx, parent_offset=None):
        if not self.visible:
            return
        if parent_offset is None:
            parent_offset = (0, 0)
        ox, oy = parent_offset
        x, y, w, h = self.rect
        fx, fy = float(ox + x), float(oy + y)
        final_rect = (ox + x, oy + y, w, h)
        child_offset = (ox + x, oy + y)

        if self.clip and w > 0 and h > 0:
            ctx.rt.PushAxisAlignedClip(fx, fy, fx + w, fy + h)
            try:
                if self.draw_fn:
                    self.draw_fn(ctx, final_rect)
                for child in self.children:
                    child.render(ctx, child_offset)
            finally:
                ctx.rt.PopAxisAlignedClip()
        else:
            if self.draw_fn:
                self.draw_fn(ctx, final_rect)
            for child in self.children:
                child.render(ctx, child_offset)