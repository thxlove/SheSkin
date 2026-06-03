"""DrawContext — 标准化绘制上下文，统一所有绘制接口的参数传递。

性能设计要点:
  - 所有 DrawContext 字段均为引用传递（零拷贝），避免逐帧分配
  - rt/wic/dw 工厂由 Frame 拥有，DrawContext 只持有引用
  - draw_cache 用于跨帧复用 D2D 资源（Brushes/Bitmaps/TextLayouts）
"""


class DrawContext:
    """捆绑所有渲染所需资源的标准化上下文。

    Frame 在 _composite() 开头构造一个 DrawContext，
    传递给所有组件的 draw(ctx, ...) 方法，替代散乱的 rt/wic/dw/cache 参数列表。
    """

    def __init__(self, rt, skin, wic_factory, dw_factory, d2d_cache=None):
        self.rt = rt
        self.skin = skin
        self.wic_factory = wic_factory
        self.dw_factory = dw_factory
        self.d2d_cache = d2d_cache if d2d_cache is not None else {}