"""D2D SolidColorBrush 缓存池 — 避免每帧重复创建/泄露。

注意: pyd2d 对象不支持 weakref，因此使用 id(rt) 作为缓存键。
BrushCache.clear() 会在 Frame 销毁时调用，确保条目及时清理。
"""

import weakref

_brush_registry = {}


class BrushCache:
    MAX_UNUSED_FRAMES = 120

    def __init__(self, render_target):
        self._rt = render_target
        self._cache = {}
        self._frame_id = 0
        _brush_registry[id(render_target)] = self

    def get(self, r, g, b, a=1.0):
        key = (round(r, 4), round(g, 4), round(b, 4), round(a, 4))
        entry = self._cache.get(key)
        if entry is not None:
            brush, _ = entry
            brush.SetColor(r, g, b, a)
            self._cache[key] = (brush, self._frame_id)
            return brush
        brush = self._rt.CreateSolidColorBrush(r, g, b, a)
        self._cache[key] = (brush, self._frame_id)
        return brush

    def end_frame(self):
        self._frame_id += 1
        stale = [
            key for key, (brush, last_id) in self._cache.items()
            if self._frame_id - last_id > self.MAX_UNUSED_FRAMES
        ]
        for key in stale:
            brush, _ = self._cache.pop(key)
            brush.Release()

    def clear(self):
        _brush_registry.pop(id(self._rt), None)
        for brush, _ in self._cache.values():
            brush.Release()
        self._cache.clear()


def get_brush(rt, r, g, b, a=1.0):
    cache = _brush_registry.get(id(rt))
    if cache is not None:
        return cache.get(r, g, b, a)
    return rt.CreateSolidColorBrush(r, g, b, a)