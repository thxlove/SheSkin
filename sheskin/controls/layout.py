"""D2D 布局系统 — HBox / VBox，支持皮肤属性驱动的间距和边距。"""
from ..layout import DEFAULTS


def d2d_hbox(controls, container_rect, *, spacing=8, margin=12):
    """水平排列控件，保持各自宽度不变。"""
    return D2DHBox(controls, spacing=spacing, margin=margin).layout(container_rect)


def d2d_vbox(controls, container_rect, *, spacing=8, margin=12):
    """垂直排列控件，保持各自高度不变。"""
    return D2DVBox(controls, spacing=spacing, margin=margin).layout(container_rect)


class D2DLayout:
    def __init__(self, controls=None, *, spacing=8, margin=12):
        self._controls = list(controls) if controls else []
        self._spacing = spacing
        self._margin = margin
        self._last_container = None

    @property
    def spacing(self):
        return self._spacing

    @spacing.setter
    def spacing(self, value):
        self._spacing = value

    @property
    def margin(self):
        return self._margin

    @margin.setter
    def margin(self, value):
        self._margin = value

    @property
    def controls(self):
        return self._controls

    @property
    def rect(self):
        if self._last_container:
            return self._last_container
        return self._measure_natural()

    def set_rect(self, rect):
        self.layout(rect)

    def overhang_top(self):
        return 0.0

    def _measure_natural(self):
        raise NotImplementedError

    def _walk_controls(self):
        for ctrl in self._controls:
            if isinstance(ctrl, D2DLayout):
                yield from ctrl._walk_controls()
            else:
                yield ctrl

    def add(self, ctrl):
        self._controls.append(ctrl)

    def remove(self, ctrl):
        self._controls.remove(ctrl)

    def clear(self):
        self._controls.clear()

    def layout(self, container_rect):
        cx, cy, cw, ch = container_rect
        self._last_container = container_rect
        if not self._controls:
            return
        self._do_layout(cx, cy, cw, ch)

    def _do_layout(self, cx, cy, cw, ch):
        raise NotImplementedError


class D2DHBox(D2DLayout):
    def _do_layout(self, cx, cy, cw, ch):
        x = cx + self._margin
        for ctrl in self._controls:
            _, _, rw, rh = ctrl.rect
            ctrl.set_rect((x, cy + self._margin, rw, rh))
            x += rw + self._spacing

    def _measure_natural(self):
        if not self._controls:
            return (0, 0, self._margin * 2, self._margin * 2)
        total_w = 0
        max_h = 0
        for ctrl in self._controls:
            _, _, rw, rh = ctrl.rect
            total_w += rw
            if rh > max_h:
                max_h = rh
        total_w += self._spacing * max(0, len(self._controls) - 1)
        return (0, 0, total_w + self._margin * 2, max_h + self._margin * 2)


class D2DVBox(D2DLayout):
    def _do_layout(self, cx, cy, cw, ch):
        y = cy + self._margin
        for ctrl in self._controls:
            _, _, rw, rh = ctrl.rect
            top_extra = getattr(ctrl, 'overhang_top', lambda: 0.0)()
            ctrl.set_rect((cx + self._margin, y + top_extra, rw, rh))
            y += rh + self._spacing + top_extra

    def _measure_natural(self):
        if not self._controls:
            return (0, 0, self._margin * 2, self._margin * 2)
        total_h = 0
        max_w = 0
        for ctrl in self._controls:
            _, _, rw, rh = ctrl.rect
            total_h += rh
            if rw > max_w:
                max_w = rw
            top_extra = getattr(ctrl, 'overhang_top', lambda: 0.0)()
            total_h += top_extra
        total_h += self._spacing * max(0, len(self._controls) - 1)
        return (0, 0, max_w + self._margin * 2, total_h + self._margin * 2)


class SkinAwareHBox(D2DHBox):
    def __init__(self, controls=None, *, skin_context=None, spacing=8, margin=12):
        super().__init__(controls, spacing=spacing, margin=margin)
        self._ctx = skin_context

    @classmethod
    def from_skin(cls, skin_context, controls=None,
                  spacing_key='btn_gap', margin_key='btn_gap'):
        props = {}
        if skin_context.skin is not None and skin_context.skin._loaded:
            props = skin_context.skin.get_props('NormalWindow')
        spacing = props.get(spacing_key, DEFAULTS.get('btn_gap', 1))
        margin = props.get(margin_key, spacing)
        return cls(controls, skin_context=skin_context, spacing=spacing, margin=margin)


class SkinAwareVBox(D2DVBox):
    def __init__(self, controls=None, *, skin_context=None, spacing=8, margin=12):
        super().__init__(controls, spacing=spacing, margin=margin)
        self._ctx = skin_context

    @classmethod
    def from_skin(cls, skin_context, controls=None,
                  spacing_key='btn_gap', margin_key='btn_gap'):
        props = {}
        if skin_context.skin is not None and skin_context.skin._loaded:
            props = skin_context.skin.get_props('NormalWindow')
        spacing = props.get(spacing_key, DEFAULTS.get('btn_gap', 1))
        margin = props.get(margin_key, spacing)
        return cls(controls, skin_context=skin_context, spacing=spacing, margin=margin)