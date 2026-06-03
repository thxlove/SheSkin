"""SheControl — 所有 sheSkin 自绘控件的统一基类。

遵循 Rule 11（Win32 按钮行为契约）:
  - MouseUp 触发（非 MouseDown），支持拖出取消
  - _captured 期间始终显示 PRESSED，不因拖出切换 NORMAL
  - _on_activate() 由子类覆写，定义激活行为
"""
import wx


class SheControl:
    NORMAL = 0
    HOVER = 1
    PRESSED = 2
    DISABLED = 3

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        orig_draw = cls.__dict__.get('draw')
        if orig_draw is None or orig_draw is SheControl.draw:
            return
        def _visible_draw(self, ctx, client_rect):
            if not getattr(self, '_visible', True):
                return
            return orig_draw(self, ctx, client_rect)
        cls.draw = _visible_draw

    def __init__(self, rect, text=""):
        self._rect = rect
        self._text = text
        self._state = self.NORMAL
        self._captured = False
        self._text_layout = None
        self._hit_geometry = None
        self._visible = True
        self._cursor_type = wx.CURSOR_ARROW
        self._context_menu_items = None

    @property
    def cursor_type(self):
        return self._cursor_type

    def set_hit_geometry(self, geometry):
        self._hit_geometry = geometry

    @property
    def rect(self):
        return self._rect

    def set_rect(self, rect):
        self._rect = rect
        self._text_layout = None

    @property
    def text(self):
        return self._text

    def set_text(self, text):
        self._text = text
        self._text_layout = None

    def hit_test(self, pt):
        if self._hit_geometry is not None:
            rx, ry = self._rect[0], self._rect[1]
            px, py = float(pt[0]) - rx, float(pt[1]) - ry
            return self._hit_geometry.FillContainsPoint(px, py)
        rx, ry, rw, rh = self._rect
        px, py = pt
        return rx <= px <= rx + rw and ry <= py <= ry + rh

    def overhang_top(self):
        return 0.0

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        if self.hit_test(pt):
            self._state = self.PRESSED
            self._captured = True
            return True
        return False

    def on_mouse_up(self, pt):
        if self._state == self.DISABLED:
            return False
        self._captured = False
        if self.hit_test(pt):
            was_pressed = self._state == self.PRESSED
            self._state = self.HOVER
            if was_pressed:
                self._on_activate()
            return True
        was_pressed = self._state == self.PRESSED
        self._state = self.NORMAL
        return was_pressed

    def _on_activate(self):
        """子类覆写此方法定义激活行为（MouseUp 在区域内释放时调用）。"""

    def on_mouse_move(self, pt):
        if self._state == self.DISABLED:
            return False
        inside = self.hit_test(pt)
        if self._captured:
            if inside and self._state != self.PRESSED:
                self._state = self.PRESSED
                return True
            return False
        if inside and self._state != self.HOVER:
            self._state = self.HOVER
            return True
        if not inside and self._state == self.HOVER:
            self._state = self.NORMAL
            return True
        return False

    def on_mouse_leave(self):
        if self._state == self.DISABLED:
            return False
        self._captured = False
        if self._state in (self.HOVER, self.PRESSED):
            self._state = self.NORMAL
            return True
        return False

    def set_context_menu(self, items):
        """设置控件级右键菜单项。设为 None 清除。"""
        self._context_menu_items = items

    def get_context_menu(self):
        """返回控件级右键菜单项，无则返回 None。"""
        return self._context_menu_items

    def on_right_down(self, pt):
        """右键按下回调。返回 True 表示该控件处理了右键事件。"""
        if self._state == self.DISABLED:
            return False
        return self.hit_test(pt) and self._context_menu_items is not None

    def on_mouse_wheel(self, pt, delta):
        """鼠标滚轮回调。delta>0 向上滚，delta<0 向下滚。返回 True 表示已处理。"""
        return False

    def draw(self, ctx, client_rect):
        """就地绘制控件。

        Args:
            ctx: DrawContext（含 rt/skin/wic_factory/dw_factory/d2d_cache）。
            client_rect: (x, y, w, h) 控件在 RenderTarget 上的绝对坐标。
        """
        raise NotImplementedError


class Spacer(SheControl):
    """占位控件 — 不渲染、不交互，仅在布局中占据空间。

    用法：
        gap = Spacer(0, 12)  # 12px 垂直间距
        indent = Spacer(20, 0)  # 20px 水平缩进
        box = Spacer(100, 80)  # 100×80 固定区域占位
    """

    def __init__(self, width=0, height=0):
        super().__init__((0, 0, max(0, width), max(0, height)), "")
        self._state = self.DISABLED

    def on_mouse_down(self, pt):
        return False

    def on_mouse_up(self, pt):
        return False

    def on_mouse_move(self, pt):
        return False

    def on_mouse_leave(self):
        return False

    def draw(self, ctx, client_rect):
        pass