"""不规则窗体命中测试 — 基于 D2D PathGeometry 的像素级命中判定。

用途:
  - 圆角窗口透明角落事件穿透
  - 弹出层异形区域命中判定
  - 控件异形点击区域判定
"""
import pyd2d


def create_rounded_rect_geometry(d2d_factory, left, top, right, bottom, radius):
    """构建圆角矩形 PathGeometry。

    使用 4 条直线 + 4 条 Arc 构建圆角矩形。

    Args:
        d2d_factory: D2DFactory
        left, top, right, bottom: 矩形边界
        radius: 圆角半径
    Returns:
        PathGeometry
    """
    geo = d2d_factory.CreatePathGeometry()
    sink = geo.Open()

    l, t, r, b = float(left), float(top), float(right), float(bottom)
    rad = float(radius)

    sink.BeginFigure(l + rad, t, 0)

    sink.AddLine(r - rad, t)
    sink.AddArc(r, t + rad, rad, rad, 0.0,
                pyd2d.SWEEP_DIRECTION.COUNTER_CLOCKWISE,
                pyd2d.ARC_SIZE.SMALL)
    sink.AddLine(r, b - rad)
    sink.AddArc(r - rad, b, rad, rad, 0.0,
                pyd2d.SWEEP_DIRECTION.COUNTER_CLOCKWISE,
                pyd2d.ARC_SIZE.SMALL)
    sink.AddLine(l + rad, b)
    sink.AddArc(l, b - rad, rad, rad, 0.0,
                pyd2d.SWEEP_DIRECTION.COUNTER_CLOCKWISE,
                pyd2d.ARC_SIZE.SMALL)
    sink.AddLine(l, t + rad)
    sink.AddArc(l + rad, t, rad, rad, 0.0,
                pyd2d.SWEEP_DIRECTION.COUNTER_CLOCKWISE,
                pyd2d.ARC_SIZE.SMALL)

    sink.EndFigure(1)  # D2D1_FIGURE_END_CLOSED
    sink.Close()
    return geo


class GeometryHitTester:
    """基于 D2D PathGeometry 的命中测试器。

    以窗口轮廓 Geometry 判定客户区命中，非客户区命中由边框区域判定。
    """

    def __init__(self, d2d_factory):
        self._d2d_factory = d2d_factory
        self._window_geo = None
        self._geometry_cache_key = None

    def init_window_shape(self, w, h, corner_radius, border_left,
                          border_top, border_right, border_bottom):
        """根据窗口尺寸和皮肤参数构建命中测试 Geometry。

        - _window_geo: 窗口外轮廓（用于判断是否在窗口范围内）
        - _border_geo: 非客户区边框区域（用于判断是否在边框/标题栏）
        """
        cache_key = (w, h, corner_radius, border_left, border_top,
                     border_right, border_bottom)
        if cache_key == self._geometry_cache_key:
            return

        r = float(corner_radius)
        if r > 0:
            self._window_geo = create_rounded_rect_geometry(
                self._d2d_factory, 0, 0, w, h, r)
        else:
            self._window_geo = create_rounded_rect_geometry(
                self._d2d_factory, 0, 0, w, h, 0)

        self._geometry_cache_key = cache_key

    def hit_test(self, px, py):
        if self._window_geo is None:
            return True
        return self._window_geo.FillContainsPoint(float(px), float(py))

    def classify_border_point(self, px, py, w, h,
                               border_left, border_top,
                               border_right, border_bottom):
        """判定点位于窗口边框的哪个分区（纯几何判定，不含圆角 hit-test）。

        Frame 应针对 'corner' 分区额外调用 hit_test 判定圆角穿透。

        Returns:
            (zone, detail) 元组:
            - zone: 'corner' | 'edge' | 'client' | 'outside'
            - detail: 'topleft' | 'topright' | 'bottomleft' | 'bottomright' |
                      'top' | 'bottom' | 'left' | 'right' | None
        """
        if py < border_top:
            if px < border_left:
                return ('corner', 'topleft')
            elif px >= w - border_right:
                return ('corner', 'topright')
            return ('edge', 'top')
        elif py >= h - border_bottom:
            if px < border_left:
                return ('corner', 'bottomleft')
            elif px >= w - border_right:
                return ('corner', 'bottomright')
            return ('edge', 'bottom')
        elif px < border_left:
            return ('edge', 'left')
        elif px >= w - border_right:
            return ('edge', 'right')
        return ('client', None)

    def get_window_geometry(self):
        return self._window_geo

    def get_corner_radius(self):
        if self._geometry_cache_key is None:
            return 0
        return self._geometry_cache_key[2]