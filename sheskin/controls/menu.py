"""D2DContextMenu — D2D 渲染的右键弹出菜单。

设计要点:
  - 基于 wx.PopupWindow 的独立分层窗口
  - 自带 D2D 渲染管线 (DCRenderTarget + DIBSection + UpdateLayeredWindow)
  - 遵循 Win32 菜单交互: hover 高亮、MouseUp 触发、点击外部关闭
  - 支持菜单项、分割线、子菜单、禁用项
  - 点击菜单外区域通过 WM_ACTIVATE 失活检测关闭
"""
import ctypes
import ctypes.wintypes
import wx
import pyd2d
from ..brush_cache import get_brush
from ..d2d_render import d2d_draw_block, D2DBlockCache
from ..block import is_block_empty
from ..layout import CONTROL_SLOTS
from ..config import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP

LRESULT = ctypes.c_longlong
HWND = ctypes.wintypes.HWND

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

GWL_EXSTYLE = -20
GWLP_WNDPROC = -4
WS_EX_LAYERED = 0x00080000

WM_NCHITTEST = 0x0084
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MOUSELEAVE = 0x02A3
WM_KEYDOWN = 0x0100
VK_ESCAPE = 0x1B
VK_RETURN = 0x0D
VK_UP = 0x26
VK_DOWN = 0x28

ULW_ALPHA = 0x02
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, ctypes.c_uint,
                              ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)


class _BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte),
                ("SourceConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_ubyte)]


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", ctypes.c_ushort),
                ("biBitCount", ctypes.c_ushort), ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32)]


user32.DefWindowProcW.argtypes = [HWND, ctypes.c_uint, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.CallWindowProcW.argtypes = [ctypes.c_void_p, HWND, ctypes.c_uint,
                                    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
user32.CallWindowProcW.restype = LRESULT
user32.GetWindowLongW.argtypes = [HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_ulong
user32.SetWindowLongPtrW = ctypes.windll.user32.SetWindowLongPtrW
user32.SetWindowLongPtrW.argtypes = [HWND, ctypes.c_int, ctypes.c_ssize_t]
user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.UpdateLayeredWindow.argtypes = [HWND, HWND, ctypes.c_void_p, ctypes.c_void_p,
    HWND, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong]
user32.UpdateLayeredWindow.restype = ctypes.c_bool
user32.GetDC.argtypes = [HWND]
user32.GetDC.restype = HWND
user32.ReleaseDC.argtypes = [HWND, HWND]
user32.ReleaseDC.restype = ctypes.c_int
user32.GetCursorPos.argtypes = [ctypes.c_void_p]
user32.GetCursorPos.restype = ctypes.c_bool
user32.SetCapture.argtypes = [HWND]
user32.SetCapture.restype = HWND
user32.ReleaseCapture.restype = ctypes.c_bool
user32.WindowFromPoint.argtypes = [ctypes.c_void_p]
user32.WindowFromPoint.restype = HWND
user32.IsChild.argtypes = [HWND, HWND]
user32.IsChild.restype = ctypes.c_bool
gdi32.GetDeviceCaps.argtypes = [HWND, ctypes.c_int]
gdi32.GetDeviceCaps.restype = ctypes.c_int
gdi32.CreateCompatibleDC.argtypes = [HWND]
gdi32.CreateCompatibleDC.restype = HWND
gdi32.CreateDIBSection.argtypes = [HWND, ctypes.c_void_p, ctypes.c_uint,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
gdi32.CreateDIBSection.restype = ctypes.wintypes.HBITMAP
gdi32.SelectObject.argtypes = [HWND, ctypes.wintypes.HGDIOBJ]
gdi32.SelectObject.restype = ctypes.wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = [ctypes.wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = ctypes.c_int
gdi32.DeleteDC.argtypes = [HWND]
gdi32.DeleteDC.restype = ctypes.c_int


MENU_ITEM_HEIGHT = 26
MENU_SEPARATOR_HEIGHT = 6
MENU_TEXT_LEFT_MARGIN = 28
MENU_TEXT_RIGHT_MARGIN = 16
MENU_SUBMENU_ICON_MARGIN = 16
MENU_IMG_LEFT_MARGIN = 4
MENU_MIN_WIDTH = 160
MENU_BORDER_RADIUS = 4.0
MENU_BORDER_WIDTH = 1.0
MENU_SHADOW_OFFSET = 2

MENU_COLORS = {
    'normal': {
        'bg': (1.0, 1.0, 1.0, 1.0),
        'border': (0.72, 0.72, 0.75, 1.0),
        'item_bg': (1.0, 1.0, 1.0, 0.0),
        'item_hover_bg': (0.90, 0.94, 0.98, 1.0),
        'item_pressed_bg': (0.82, 0.88, 0.94, 1.0),
        'text': (0.13, 0.13, 0.13, 1.0),
        'text_disabled': (0.55, 0.55, 0.58, 1.0),
        'separator': (0.82, 0.82, 0.85, 1.0),
        'submenu_arrow': (0.40, 0.40, 0.43, 1.0),
    },
}


class MenuItemData:
    def __init__(self, text='', callback=None, disabled=False,
                 submenu=None, data=None):
        self.text = text
        self.callback = callback
        self.disabled = disabled
        self.submenu = submenu
        self.data = data

    @property
    def is_separator(self):
        return False

    @property
    def has_submenu(self):
        return self.submenu is not None and len(self.submenu) > 0


class SeparatorData:
    @property
    def is_separator(self):
        return True

    @property
    def disabled(self):
        return False

    @property
    def has_submenu(self):
        return False


def menu_separator():
    return SeparatorData()


_separator = menu_separator


class D2DContextMenu(wx.PopupWindow):
    _dwrite_text_fmt = None

    @classmethod
    def _get_text_fmt(cls, dw_factory=None):
        if cls._dwrite_text_fmt is None:
            if dw_factory is None:
                dw_factory = pyd2d.GetDWriteFactory()
            cls._dwrite_text_fmt = dw_factory.CreateTextFormat(
                DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE_DIP,
                weight=pyd2d.FONT_WEIGHT.NORMAL,
                style=pyd2d.FONT_STYLE.NORMAL,
                stretch=pyd2d.FONT_STRETCH.NORMAL)
            cls._dwrite_text_fmt.SetParagraphAlignment(
                pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return cls._dwrite_text_fmt

    def __init__(self, parent, items=None, on_close=None):
        super().__init__(parent, flags=wx.BORDER_NONE)
        self._items = list(items) if items else []
        self._on_close = on_close
        self._hovered_idx = -1
        self._pressed_idx = -1
        self._captured = False
        self._submenu_popup = None
        self._submenu_timer = None
        self._item_rects = []
        self._menu_width = MENU_MIN_WIDTH
        self._root_menu = None
        self._outside_timer = None

        self._d2d_factory = None
        self._dc_rt = None
        self._wic_factory = None
        self._dw_factory = None
        self._d2d_cache = None
        self._hdc_mem = None
        self._hBmp = None
        self._ppvBits = None
        self._old_hBmp = None
        self._width = 0
        self._height = 0
        self._hwnd = None
        self._old_wndproc = None
        self._wndproc_cb = None
        self._closing = False

        self._init_d2d()
        self._setup_window()
        self._bind_events()

    def _init_d2d(self):
        self._d2d_factory = pyd2d.GetD2DFactory()
        self._wic_factory = pyd2d.GetWICFactory()
        self._dw_factory = pyd2d.GetDWriteFactory()
        self._d2d_cache = D2DBlockCache()

        hdc_screen = user32.GetDC(None)
        dpi_x = gdi32.GetDeviceCaps(hdc_screen, 88)
        dpi_y = gdi32.GetDeviceCaps(hdc_screen, 90)
        user32.ReleaseDC(None, hdc_screen)
        self._dpi_scale_x = 96.0 / max(dpi_x, 1)
        self._dpi_scale_y = 96.0 / max(dpi_y, 1)

        self._dc_rt = self._d2d_factory.CreateDCRenderTarget(
            rtType=pyd2d.RENDER_TARGET_TYPE.DEFAULT,
            pixelFormat=pyd2d.DXGI_FORMAT.B8G8R8A8_UNORM,
            alphaMode=pyd2d.ALPHA_MODE.PREMULTIPLIED,
            dpiX=float(dpi_x), dpiY=float(dpi_y))

    def _setup_window(self):
        self._hwnd = HWND(self.GetHandle())
        ex = user32.GetWindowLongW(self._hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(self._hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED)
        self._install_wndproc()

    def _install_wndproc(self):
        self._wndproc_cb = WNDPROC(self._custom_wndproc)
        wndproc_addr = ctypes.cast(self._wndproc_cb, ctypes.c_void_p)
        self._old_wndproc = user32.SetWindowLongPtrW(
            self._hwnd, GWLP_WNDPROC, wndproc_addr.value)

    def _uninstall_wndproc(self):
        if self._old_wndproc and self._hwnd:
            user32.SetWindowLongPtrW(
                self._hwnd, GWLP_WNDPROC, self._old_wndproc)
            self._old_wndproc = None

    def _get_root_menu(self):
        root = self
        while root._root_menu is not None:
            root = root._root_menu
        return root

    def _is_our_hwnd(self, hwnd):
        root = self._get_root_menu()
        if hwnd == root._hwnd:
            return True
        sub = root._submenu_popup
        while sub is not None:
            if hwnd == sub._hwnd:
                return True
            sub = sub._submenu_popup
        return False

    def _custom_wndproc(self, hwnd, msg, wparam, lparam):
        if self._closing:
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        try:
            if msg == WM_NCHITTEST:
                return 1
            elif msg == WM_LBUTTONDOWN:
                px = ctypes.c_short(lparam & 0xFFFF).value
                py = ctypes.c_short((lparam >> 16) & 0xFFFF).value
                self._on_mouse_down((px, py))
                return 0
            elif msg == WM_LBUTTONUP:
                px = ctypes.c_short(lparam & 0xFFFF).value
                py = ctypes.c_short((lparam >> 16) & 0xFFFF).value
                self._on_mouse_up((px, py))
                return 0
            elif msg == WM_MOUSEMOVE:
                px = ctypes.c_short(lparam & 0xFFFF).value
                py = ctypes.c_short((lparam >> 16) & 0xFFFF).value
                self._on_mouse_move((px, py))
                return 0
            elif msg == WM_MOUSELEAVE:
                self._on_mouse_leave()
                return 0
            elif msg == WM_KEYDOWN:
                vk = wparam & 0xFF
                if vk == VK_ESCAPE:
                    self.dismiss()
                    return 0
                elif vk == VK_RETURN:
                    self._activate_hovered()
                    return 0
                elif vk == VK_UP:
                    self._navigate(-1)
                    return 0
                elif vk == VK_DOWN:
                    self._navigate(1)
                    return 0
        except Exception:
            import traceback
            print("[ContextMenu WNDPROC ERROR]")
            traceback.print_exc()
        if self._old_wndproc:
            return user32.CallWindowProcW(
                ctypes.c_void_p(self._old_wndproc), hwnd, msg, wparam, lparam)
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _dismiss_root(self):
        root = self._get_root_menu()
        if not root._closing:
            root.dismiss()

    def _bind_events(self):
        pass

    def add_item(self, text='', callback=None, disabled=False,
                 submenu=None, data=None):
        item = MenuItemData(text=text, callback=callback,
                            disabled=disabled, submenu=submenu, data=data)
        self._items.append(item)
        return len(self._items) - 1

    def add_separator(self):
        self._items.append(SeparatorData())
        return len(self._items) - 1

    def _measure(self):
        dw = self._dw_factory
        text_fmt = self._get_text_fmt(dw_factory=dw)
        max_text_w = 0.0
        for item in self._items:
            if item.is_separator:
                continue
            if item.text:
                measure = dw.CreateTextLayout(
                    item.text, text_fmt, 2000.0, float(MENU_ITEM_HEIGHT))
                max_text_w = max(max_text_w, measure.GetMetrics().width)

        content_w = MENU_TEXT_LEFT_MARGIN + max_text_w + MENU_TEXT_RIGHT_MARGIN
        has_submenu = any(getattr(it, 'has_submenu', False) for it in self._items)
        if has_submenu:
            content_w += MENU_SUBMENU_ICON_MARGIN
        self._menu_width = max(int(content_w), MENU_MIN_WIDTH)

        total_h = 0
        self._item_rects = []
        for item in self._items:
            if item.is_separator:
                self._item_rects.append((0, total_h, self._menu_width,
                                         MENU_SEPARATOR_HEIGHT))
                total_h += MENU_SEPARATOR_HEIGHT
            else:
                self._item_rects.append((0, total_h, self._menu_width,
                                         MENU_ITEM_HEIGHT))
                total_h += MENU_ITEM_HEIGHT

        return self._menu_width, total_h

    def popup(self, screen_pos):
        w, h = self._measure()
        self._width = w
        self._height = h

        sx, sy = screen_pos
        disp_w = wx.Display.GetFromPoint(wx.Point(sx, sy))
        if disp_w >= 0:
            rect = wx.Display(disp_w).GetClientArea()
            if sx + w > rect.Right:
                sx = rect.Right - w
            if sy + h > rect.Bottom:
                sy = rect.Bottom - h
            sx = max(sx, rect.Left)
            sy = max(sy, rect.Top)

        self.SetSize(sx, sy, w, h)
        self._ensure_dibsection(w, h)
        self._do_composite()
        self.Show()
        self._start_outside_check()

    def dismiss(self):
        self._stop_outside_check()
        self._close_submenu()
        if self._submenu_timer:
            self._submenu_timer.Stop()
            self._submenu_timer = None
        self._closing = True
        self._uninstall_wndproc()
        self._cleanup()
        self.Hide()
        if self._on_close:
            self._on_close()
        wx.CallAfter(self.Destroy)

    def _start_outside_check(self):
        if self._outside_timer:
            return
        self._outside_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_outside_check, self._outside_timer)
        self._outside_timer.Start(50)

    def _stop_outside_check(self):
        if self._outside_timer:
            self._outside_timer.Stop()
            self.Unbind(wx.EVT_TIMER, handler=self._on_outside_check,
                        source=self._outside_timer)
            self._outside_timer = None

    def _on_outside_check(self, event):
        if self._closing:
            return
        VK_LBUTTON = 0x01
        if not user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000:
            return
        pt = _POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        # WindowFromPoint 无法看到分层窗口，改用窗口矩形判断
        if self._is_pt_in_our_windows(pt.x, pt.y):
            return
        root = self._get_root_menu()
        if not root._closing:
            root.dismiss()

    def _is_pt_in_our_windows(self, sx, sy):
        """检查屏幕坐标 (sx, sy) 是否在菜单或子菜单的窗口矩形内。"""
        root = self._get_root_menu()
        menu = root
        while menu is not None:
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(menu._hwnd, ctypes.byref(rect))
            if rect.left <= sx <= rect.right and rect.top <= sy <= rect.bottom:
                return True
            menu = menu._submenu_popup
        return False

    def _close_submenu(self):
        if self._submenu_popup is not None:
            self._submenu_popup.dismiss()
            self._submenu_popup = None

    def _hit_test(self, pt):
        px, py = pt
        for i, (x, y, w, h) in enumerate(self._item_rects):
            if x <= px <= x + w and y <= py <= y + h:
                return i
        return -1

    def _on_mouse_down(self, pt):
        idx = self._hit_test(pt)
        if idx < 0:
            self.dismiss()
            return
        item = self._items[idx]
        if item.is_separator or item.disabled:
            return
        self._captured = True
        self._pressed_idx = idx
        user32.SetCapture(self._hwnd)

    def _on_mouse_up(self, pt):
        user32.ReleaseCapture()
        if self._captured:
            idx = self._hit_test(pt)
            if idx >= 0 and idx == self._pressed_idx:
                item = self._items[idx]
                if not item.is_separator and not item.disabled:
                    if item.has_submenu:
                        self._show_submenu(idx)
                    else:
                        if item.callback:
                            item.callback(item.data)
                        self.dismiss()
                        return
            self._captured = False
            self._pressed_idx = -1
            return

        idx = self._hit_test(pt)
        if idx < 0:
            self.dismiss()
            return

        item = self._items[idx]
        if not item.is_separator and not item.disabled:
            if item.has_submenu:
                self._show_submenu(idx)
            else:
                if item.callback:
                    item.callback(item.data)
                self.dismiss()

    def _on_mouse_move(self, pt):
        idx = self._hit_test(pt)
        if idx == self._hovered_idx:
            return
        self._hovered_idx = idx
        self._do_composite()

        if idx >= 0:
            item = self._items[idx]
            if not item.is_separator and item.has_submenu:
                if self._submenu_timer:
                    self._submenu_timer.Stop()
                self._submenu_timer = wx.Timer(self)
                self.Bind(wx.EVT_TIMER,
                          lambda e, i=idx: self._show_submenu(i),
                          self._submenu_timer)
                self._submenu_timer.Start(300, oneShot=True)
            else:
                self._close_submenu()
                if self._submenu_timer:
                    self._submenu_timer.Stop()
                    self._submenu_timer = None

    def _on_mouse_leave(self):
        self._hovered_idx = -1
        self._do_composite()

    def _show_submenu(self, idx):
        if self._submenu_popup is not None:
            if self._submenu_popup._items == self._items[idx].submenu:
                return
            self._close_submenu()

        item = self._items[idx]
        if not item.has_submenu:
            return

        rect = self._item_rects[idx]
        screen_pos = self.ClientToScreen((rect[0] + rect[2], rect[1]))
        sub = self._create_submenu(item.submenu)
        sub._root_menu = self._get_root_menu()
        self._submenu_popup = sub
        sub.popup(screen_pos)

    def _create_submenu(self, items):
        return D2DContextMenu(
            self.GetParent(), items=items,
            on_close=lambda: self._clear_submenu_ref())

    def _clear_submenu_ref(self):
        self._submenu_popup = None

    def _activate_hovered(self):
        if self._hovered_idx < 0:
            return
        item = self._items[self._hovered_idx]
        if item.is_separator or item.disabled:
            return
        if item.has_submenu:
            self._show_submenu(self._hovered_idx)
        else:
            if item.callback:
                item.callback(item.data)
            self.dismiss()

    def _navigate(self, direction):
        start = max(0, self._hovered_idx) if self._hovered_idx >= 0 else -1
        idx = start + direction
        while 0 <= idx < len(self._items):
            item = self._items[idx]
            if not item.is_separator and not item.disabled:
                break
            idx += direction
        else:
            if direction > 0:
                idx = 0
                while idx < len(self._items):
                    item = self._items[idx]
                    if not item.is_separator and not item.disabled:
                        break
                    idx += 1
            else:
                idx = len(self._items) - 1
                while idx >= 0:
                    item = self._items[idx]
                    if not item.is_separator and not item.disabled:
                        break
                    idx -= 1

        if 0 <= idx < len(self._items):
            self._hovered_idx = idx
            self._do_composite()

    def _ensure_dibsection(self, w, h):
        if w == self._width and h == self._height and self._hBmp:
            return
        self._release_dibsection()
        self._width = w
        self._height = h

        hdc_screen = user32.GetDC(None)
        bmi = _BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.biWidth = w
        bmi.biHeight = -h
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0
        bmi.biSizeImage = w * h * 4

        self._ppvBits = ctypes.c_void_p()
        self._hBmp = gdi32.CreateDIBSection(
            hdc_screen, ctypes.byref(bmi), 0,
            ctypes.byref(self._ppvBits), None, 0)
        self._hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        self._old_hBmp = gdi32.SelectObject(self._hdc_mem, self._hBmp)
        user32.ReleaseDC(None, hdc_screen)

    def _release_dibsection(self):
        if self._hdc_mem:
            if self._old_hBmp:
                gdi32.SelectObject(self._hdc_mem, self._old_hBmp)
                self._old_hBmp = None
            gdi32.DeleteDC(self._hdc_mem)
            self._hdc_mem = None
        if self._hBmp:
            gdi32.DeleteObject(self._hBmp)
            self._hBmp = None
        self._ppvBits = None

    def _do_composite(self):
        if self._closing or not self._dc_rt:
            return
        w, h = self._width, self._height
        if w <= 0 or h <= 0:
            return

        self._ensure_dibsection(w, h)
        self._dc_rt.BindDC(self._hdc_mem, 0, 0, w, h)
        self._dc_rt.BeginDraw()
        self._dc_rt.SetTransform(
            self._dpi_scale_x, 0.0, 0.0,
            self._dpi_scale_y, 0.0, 0.0)
        try:
            self._dc_rt.Clear(0.0, 0.0, 0.0, 0.0)
            self._draw_content(self._dc_rt)
        finally:
            self._dc_rt.EndDraw()

        self._push()

    def _draw_content(self, rt):
        c = MENU_COLORS['normal']
        w, h = float(self._width), float(self._height)

        shadow_brush = get_brush(rt, 0.0, 0.0, 0.0, 0.15)
        rt.FillRectangle(
            float(MENU_SHADOW_OFFSET), float(MENU_SHADOW_OFFSET),
            w + float(MENU_SHADOW_OFFSET), h + float(MENU_SHADOW_OFFSET),
            shadow_brush)

        bg_brush = get_brush(rt, *c['bg'])
        rt.FillRectangle(0.0, 0.0, w, h, bg_brush)

        border_brush = get_brush(rt, *c['border'])
        rt.DrawRectangle(0.5, 0.5, w - 0.5, h - 0.5, border_brush,
                         MENU_BORDER_WIDTH)

        dw = self._dw_factory
        text_fmt = self._get_text_fmt(dw_factory=dw)

        for i, (x, y, iw, ih) in enumerate(self._item_rects):
            item = self._items[i]
            if item.is_separator:
                sep_brush = get_brush(rt, *c['separator'])
                sep_x = float(MENU_BORDER_WIDTH)
                sep_y = float(y) + float(ih) / 2.0
                sep_right = float(iw) - MENU_BORDER_WIDTH
                rt.FillRectangle(sep_x, sep_y,
                                 sep_right, sep_y + 1.0,
                                 sep_brush)
                continue

            is_hovered = (i == self._hovered_idx)
            is_pressed = (i == self._pressed_idx and self._captured)

            if is_pressed:
                item_bg = get_brush(rt, *c['item_pressed_bg'])
                rt.FillRectangle(float(x), float(y),
                                 float(x + iw), float(y + ih), item_bg)
            elif is_hovered:
                item_bg = get_brush(rt, *c['item_hover_bg'])
                rt.FillRectangle(float(x), float(y),
                                 float(x + iw), float(y + ih), item_bg)

            if item.disabled:
                text_brush = get_brush(rt, *c['text_disabled'])
            else:
                text_brush = get_brush(rt, *c['text'])

            if item.text:
                text_x = float(x + MENU_TEXT_LEFT_MARGIN)
                text_y = float(y)
                text_w = float(iw - MENU_TEXT_LEFT_MARGIN - MENU_TEXT_RIGHT_MARGIN)
                text_h = float(ih)
                if item.has_submenu:
                    text_w -= MENU_SUBMENU_ICON_MARGIN
                rt.DrawText(item.text, text_fmt,
                           text_x, text_y,
                           text_x + text_w, text_y + text_h,
                           text_brush)

            if item.has_submenu:
                arrow_brush = get_brush(rt, *c['submenu_arrow'])
                arrow_x = float(x + iw - MENU_SUBMENU_ICON_MARGIN + 4)
                arrow_cy = float(y + ih / 2.0)
                rt.FillRectangle(arrow_x, arrow_cy - 3.0,
                                 arrow_x + 3.0, arrow_cy - 1.0,
                                 arrow_brush)
                rt.FillRectangle(arrow_x, arrow_cy - 1.0,
                                 arrow_x + 5.0, arrow_cy + 1.0,
                                 arrow_brush)
                rt.FillRectangle(arrow_x, arrow_cy + 1.0,
                                 arrow_x + 3.0, arrow_cy + 3.0,
                                 arrow_brush)

    def _push(self):
        if not self._hdc_mem or not self._hBmp:
            return
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(self._hwnd, ctypes.byref(rect))
        pt_dst = _POINT(rect.left, rect.top)
        pt_src = _POINT(0, 0)
        size = _SIZE(self._width, self._height)
        blend = _BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
        user32.UpdateLayeredWindow(
            self._hwnd, None, ctypes.byref(pt_dst), ctypes.byref(size),
            self._hdc_mem, ctypes.byref(pt_src), 0,
            ctypes.byref(blend), ULW_ALPHA)

    def _cleanup(self):
        self._release_dibsection()
        self._dc_rt = None
        self._d2d_factory = None
        self._dw_factory = None
        self._wic_factory = None


class SkinAwareContextMenu(D2DContextMenu):
    _dwrite_text_fmt = None

    @classmethod
    def _get_text_fmt(cls, dw_factory=None, skin_ctx=None):
        if cls._dwrite_text_fmt is None:
            if dw_factory is None:
                dw_factory = pyd2d.GetDWriteFactory()
            if skin_ctx is not None:
                font_info = skin_ctx.get_font_info('Menu')
            else:
                font_info = None
            face = font_info.get('face_name', DEFAULT_FONT_FAMILY) if font_info else DEFAULT_FONT_FAMILY
            height = (font_info.get('height', -9) if font_info else -9) * -1.0
            weight = font_info.get('weight', pyd2d.FONT_WEIGHT.NORMAL) if font_info else pyd2d.FONT_WEIGHT.NORMAL
            italic = font_info.get('italic', False) if font_info else False
            cls._dwrite_text_fmt = dw_factory.CreateTextFormat(
                face, float(height),
                weight=weight,
                style=pyd2d.FONT_STYLE.ITALIC if italic else pyd2d.FONT_STYLE.NORMAL,
                stretch=pyd2d.FONT_STRETCH.NORMAL)
            cls._dwrite_text_fmt.SetParagraphAlignment(
                pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return cls._dwrite_text_fmt

    def __init__(self, parent, skin_context, items=None, on_close=None):
        super().__init__(parent, items=items, on_close=on_close)
        self._ctx = skin_context
        self._skin = skin_context.skin if skin_context else None
        self._skin_img = self._skin.skin_img if self._skin and self._skin._loaded else None
        defaults = CONTROL_SLOTS.get('Menu', {})
        self._bg_slot = defaults.get('bg', {}).get('normal')
        self._sep_slot = defaults.get('separator', {}).get('normal')
        self._item_slots = defaults.get('item', {})

        self._item_height = MENU_ITEM_HEIGHT
        self._sep_height = MENU_SEPARATOR_HEIGHT
        self._text_left_margin = MENU_TEXT_LEFT_MARGIN
        self._sep_left_margin = MENU_TEXT_LEFT_MARGIN
        self._img_left_margin = MENU_IMG_LEFT_MARGIN
        self._submenu_icon_margin = MENU_SUBMENU_ICON_MARGIN
        self._text_colors = {
            0: (0, 0, 0, 255),
            1: (0, 0, 0, 255),
            2: (0, 0, 0, 255),
            3: (128, 128, 128, 255),
        }

        if self._skin and self._skin._loaded:
            props = self._skin.get_props('Menu')
            if props.get('item_height'):
                self._item_height = max(10, int(props['item_height']))
            if props.get('sep_height'):
                val = int(props['sep_height'])
                self._sep_height = 1 if val > 2 else max(2, val)
            if props.get('text_left_margin'):
                self._text_left_margin = int(props['text_left_margin'])
            if props.get('sep_left_margin'):
                self._sep_left_margin = int(props['sep_left_margin'])
            if props.get('img_left_margin'):
                self._img_left_margin = int(props['img_left_margin'])
            if props.get('submenu_icon_margin'):
                self._submenu_icon_margin = int(props['submenu_icon_margin'])
            for state_idx, key in enumerate(
                    ['text_color_n', 'text_color_o', 'text_color_s', 'text_color_d']):
                tc = props.get(key)
                if tc and isinstance(tc, wx.Colour):
                    self._text_colors[state_idx] = (tc.Red(), tc.Green(),
                                                     tc.Blue(), tc.Alpha())

    def _has_skin_blocks(self):
        if self._ctx is None:
            return False
        bg_block = self._ctx.get_block(self._bg_slot) if self._bg_slot is not None else None
        has_bg = (bg_block is not None
                  and bg_block.bg_width > 0
                  and bg_block.bg_height > 0)
        has_item = False
        for state in ('normal', 'default', 'pressed'):
            slot = self._item_slots.get(state)
            if slot is not None:
                block = self._ctx.get_block(slot)
                if block is not None and block.bg_width > 0 and block.bg_height > 0:
                    has_item = True
                    break
        return has_bg and has_item

    def _measure(self):
        dw = self._dw_factory
        text_fmt = self._get_text_fmt(dw_factory=dw, skin_ctx=self._ctx)
        max_text_w = 0.0
        for item in self._items:
            if item.is_separator:
                continue
            if item.text:
                measure = dw.CreateTextLayout(
                    item.text, text_fmt, 2000.0, float(self._item_height))
                max_text_w = max(max_text_w, measure.GetMetrics().width)

        content_w = self._text_left_margin + max_text_w + MENU_TEXT_RIGHT_MARGIN
        has_submenu = any(getattr(it, 'has_submenu', False) for it in self._items)
        if has_submenu:
            content_w += self._submenu_icon_margin
        self._menu_width = max(int(content_w), MENU_MIN_WIDTH)

        total_h = 0
        self._item_rects = []
        for item in self._items:
            if item.is_separator:
                self._item_rects.append((0, total_h, self._menu_width,
                                         self._sep_height))
                total_h += self._sep_height
            else:
                self._item_rects.append((0, total_h, self._menu_width,
                                         self._item_height))
                total_h += self._item_height

        return self._menu_width, total_h

    def _create_submenu(self, items):
        return SkinAwareContextMenu(
            self.GetParent(), self._ctx, items=items,
            on_close=lambda: self._clear_submenu_ref())

    def _draw_content(self, rt):
        if not self._has_skin_blocks():
            D2DContextMenu._draw_content(self, rt)
            return

        w, h = float(self._width), float(self._height)
        skin_img = self._skin_img

        bg_block = self._ctx.get_block(self._bg_slot) if self._bg_slot is not None else None
        if bg_block is not None and bg_block.bg_width > 0 and bg_block.bg_height > 0:
            d2d_draw_block(rt, skin_img, bg_block,
                           (0, 0, int(w), int(h)),
                           wic_factory=self._wic_factory,
                           d2d_cache=self._d2d_cache)

        sep_block = self._ctx.get_block(self._sep_slot) if self._sep_slot is not None else None

        dw = self._dw_factory
        text_fmt = self._get_text_fmt(dw_factory=dw, skin_ctx=self._ctx)

        for i, (x, y, iw, ih) in enumerate(self._item_rects):
            item = self._items[i]
            if item.is_separator:
                bw = int(MENU_BORDER_WIDTH)
                if sep_block is not None and sep_block.bg_width > 0 and sep_block.bg_height > 0:
                    d2d_draw_block(rt, skin_img, sep_block,
                                   (bw, int(y), int(iw) - bw * 2, int(ih)),
                                   wic_factory=self._wic_factory,
                                   d2d_cache=self._d2d_cache)
                else:
                    c = MENU_COLORS['normal']
                    sep_brush = get_brush(rt, *c['separator'])
                    sep_x = float(MENU_BORDER_WIDTH)
                    sep_y = float(y) + float(ih) / 2.0
                    sep_right = float(iw) - MENU_BORDER_WIDTH
                    rt.FillRectangle(sep_x, sep_y,
                                     sep_right, sep_y + 1.0,
                                     sep_brush)
                continue

            is_hovered = (i == self._hovered_idx)
            is_pressed = (i == self._pressed_idx and self._captured)
            is_disabled = item.disabled

            if is_disabled:
                state_name = 'disabled'
            elif is_pressed:
                state_name = 'pressed'
            elif is_hovered:
                state_name = 'default'
            else:
                state_name = 'normal'

            item_slot = self._item_slots.get(state_name)
            if item_slot is None:
                if state_name == 'default':
                    item_slot = self._item_slots.get('normal')
                elif state_name == 'disabled':
                    item_slot = self._item_slots.get('normal')

            if item_slot is not None:
                item_block = self._ctx.get_block(item_slot)
                if item_block is not None and item_block.bg_width > 0 and item_block.bg_height > 0:
                    d2d_draw_block(rt, skin_img, item_block,
                                   (int(x), int(y), int(iw), int(ih)),
                                   wic_factory=self._wic_factory,
                                   d2d_cache=self._d2d_cache)

            state_idx = {'normal': 0, 'default': 1, 'pressed': 2, 'disabled': 3}.get(state_name, 0)
            text_color = self._text_colors.get(state_idx, (0, 0, 0, 255))
            text_brush = get_brush(rt,
                                   text_color[0] / 255.0,
                                   text_color[1] / 255.0,
                                   text_color[2] / 255.0,
                                   text_color[3] / 255.0 if len(text_color) > 3 else 1.0)

            if item.text:
                text_x = float(x + self._text_left_margin)
                text_y = float(y)
                text_w = float(iw - self._text_left_margin - MENU_TEXT_RIGHT_MARGIN)
                text_h = float(ih)
                if item.has_submenu:
                    text_w -= self._submenu_icon_margin
                rt.DrawText(item.text, text_fmt,
                           text_x, text_y,
                           text_x + text_w, text_y + text_h,
                           text_brush)

            if item.has_submenu:
                arrow_color = self._text_colors.get(0, (0, 0, 0, 255))
                arrow_brush = get_brush(rt,
                                        arrow_color[0] / 255.0,
                                        arrow_color[1] / 255.0,
                                        arrow_color[2] / 255.0,
                                        arrow_color[3] / 255.0 if len(arrow_color) > 3 else 1.0)
                arrow_x = float(x + iw - self._submenu_icon_margin + 4)
                arrow_cy = float(y + ih / 2.0)
                rt.FillRectangle(arrow_x, arrow_cy - 3.0,
                                 arrow_x + 3.0, arrow_cy - 1.0,
                                 arrow_brush)
                rt.FillRectangle(arrow_x, arrow_cy - 1.0,
                                 arrow_x + 5.0, arrow_cy + 1.0,
                                 arrow_brush)
                rt.FillRectangle(arrow_x, arrow_cy + 1.0,
                                 arrow_x + 3.0, arrow_cy + 3.0,
                                 arrow_brush)
