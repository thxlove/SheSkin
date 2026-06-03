"""D2D 控件 — D2DComboBox / SkinAwareComboBox / D2DComboListPopup。"""
import ctypes
import ctypes.wintypes
import wx
import pyd2d
from .base_control import SheControl
from ..brush_cache import get_brush
from ..d2d_render import d2d_draw_block, d2d_draw_text, D2DBlockCache
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
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
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
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
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

COMBO_DROPDOWN_BTN_WIDTH = 20
COMBO_TEXT_PAD_X = 6
COMBO_TEXT_PAD_Y = 4
COMBO_BORDER_RADIUS = 3.0
COMBO_BORDER_WIDTH = 1.0

COMBO_LIST_ITEM_HEIGHT = 24
COMBO_LIST_BORDER_WIDTH = 1
COMBO_LIST_MAX_VISIBLE = 10
COMBO_LIST_MIN_WIDTH = 80

COMBO_COLORS = {
    'normal': {
        'bg': (1.0, 1.0, 1.0, 1.0),
        'border': (0.55, 0.55, 0.58, 1.0),
        'text': (0.13, 0.13, 0.13, 1.0),
        'btn_bg': (0.92, 0.92, 0.94, 1.0),
        'btn_border': (0.65, 0.65, 0.68, 1.0),
        'btn_arrow': (0.30, 0.30, 0.33, 1.0),
    },
    'hover': {
        'bg': (1.0, 1.0, 1.0, 1.0),
        'border': (0.18, 0.56, 0.92, 1.0),
        'text': (0.13, 0.13, 0.13, 1.0),
        'btn_bg': (0.88, 0.92, 0.96, 1.0),
        'btn_border': (0.18, 0.56, 0.92, 1.0),
        'btn_arrow': (0.18, 0.56, 0.92, 1.0),
    },
    'pressed': {
        'bg': (1.0, 1.0, 1.0, 1.0),
        'border': (0.11, 0.46, 0.76, 1.0),
        'text': (0.13, 0.13, 0.13, 1.0),
        'btn_bg': (0.82, 0.88, 0.94, 1.0),
        'btn_border': (0.11, 0.46, 0.76, 1.0),
        'btn_arrow': (0.11, 0.46, 0.76, 1.0),
    },
    'disabled': {
        'bg': (0.92, 0.92, 0.93, 1.0),
        'border': (0.78, 0.78, 0.80, 1.0),
        'text': (0.55, 0.55, 0.58, 1.0),
        'btn_bg': (0.88, 0.88, 0.90, 1.0),
        'btn_border': (0.78, 0.78, 0.80, 1.0),
        'btn_arrow': (0.55, 0.55, 0.58, 1.0),
    },
}

COMBO_LIST_COLORS = {
    'bg': (1.0, 1.0, 1.0, 1.0),
    'border': (0.65, 0.65, 0.68, 1.0),
    'item_hover_bg': (0.90, 0.94, 0.98, 1.0),
    'item_text': (0.13, 0.13, 0.13, 1.0),
    'item_text_disabled': (0.55, 0.55, 0.58, 1.0),
}


class D2DComboListPopup(wx.PopupWindow):
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

    def __init__(self, parent, items=None, selected=-1, on_select=None,
                 on_close=None, item_height=COMBO_LIST_ITEM_HEIGHT,
                 max_visible=COMBO_LIST_MAX_VISIBLE):
        super().__init__(parent, flags=wx.BORDER_NONE)
        self._items = list(items) if items else []
        self._selected = selected
        self._on_select = on_select
        self._on_close = on_close
        self._item_height = item_height
        self._max_visible = max_visible
        self._hovered_idx = -1
        self._captured = False
        self._item_rects = []

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
        self._outside_timer = None

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
        if self._old_wndproc:
            user32.SetWindowLongPtrW(self._hwnd, GWLP_WNDPROC, self._old_wndproc)
            self._old_wndproc = None

    def _custom_wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_NCHITTEST:
            return 1
        if msg == WM_LBUTTONDOWN:
            x = ctypes.c_short(lparam & 0xFFFF).value
            y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
            self._on_list_mouse_down((x, y))
            return 0
        if msg == WM_LBUTTONUP:
            x = ctypes.c_short(lparam & 0xFFFF).value
            y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
            self._on_list_mouse_up((x, y))
            return 0
        if msg == WM_MOUSEMOVE:
            x = ctypes.c_short(lparam & 0xFFFF).value
            y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
            self._on_list_mouse_move((x, y))
            return 0
        if msg == WM_MOUSELEAVE:
            self._on_list_mouse_leave()
            return 0
        if msg == WM_KEYDOWN:
            if wparam == VK_ESCAPE:
                self.dismiss()
                return 0
            if wparam == VK_RETURN:
                self._confirm_selection()
                return 0
            if wparam == VK_UP:
                self._move_hover(-1)
                return 0
            if wparam == VK_DOWN:
                self._move_hover(1)
                return 0
        return user32.CallWindowProcW(
            self._old_wndproc, hwnd, msg, wparam, lparam)

    def _bind_events(self):
        pass

    def _measure(self):
        n = len(self._items)
        visible = min(n, self._max_visible)
        self._width = max(COMBO_LIST_MIN_WIDTH, self._list_width)
        self._height = visible * self._item_height + COMBO_LIST_BORDER_WIDTH * 2

    def _layout_items(self):
        self._item_rects = []
        bw = COMBO_LIST_BORDER_WIDTH
        for i in range(len(self._items)):
            y = bw + i * self._item_height
            self._item_rects.append((bw, y, self._width - bw * 2, self._item_height))

    def _ensure_dibsection(self, w, h):
        if self._hBmp and self._width == w and self._height == h:
            return
        if self._hBmp:
            gdi32.SelectObject(self._hdc_mem, self._old_hBmp)
            gdi32.DeleteObject(self._hBmp)
            gdi32.DeleteDC(self._hdc_mem)
        bmi = _BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.biWidth = w
        bmi.biHeight = -h
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0
        ppv = ctypes.c_void_p()
        self._hdc_mem = gdi32.CreateCompatibleDC(None)
        self._hBmp = gdi32.CreateDIBSection(
            self._hdc_mem, ctypes.byref(bmi), 0, ctypes.byref(ppv), None, 0)
        self._old_hBmp = gdi32.SelectObject(self._hdc_mem, self._hBmp)
        self._ppvBits = ppv
        self._width = w
        self._height = h

    def _render(self):
        w = self._width
        h = self._height
        if w <= 0 or h <= 0:
            return
        self._ensure_dibsection(w, h)
        rt = self._dc_rt
        rt.BindDC(self._hdc_mem, 0, 0, w, h)
        rt.BeginDraw()
        rt.SetTransform(
            self._dpi_scale_x, 0.0, 0.0,
            self._dpi_scale_y, 0.0, 0.0)
        rt.Clear(0, 0, 0, 0)

        c = COMBO_LIST_COLORS
        bg_brush = get_brush(rt, *c['bg'])
        border_brush = get_brush(rt, *c['border'])
        rt.FillRectangle(0, 0, w, h, bg_brush)
        rt.DrawRectangle(0, 0, w, h, border_brush, COMBO_LIST_BORDER_WIDTH)

        text_fmt = self._get_text_fmt(dw_factory=self._dw_factory)
        text_fmt.SetTextAlignment(pyd2d.TEXT_ALIGNMENT.LEADING)
        for i, (ix, iy, iw, ih) in enumerate(self._item_rects):
            if i == self._hovered_idx:
                hover_brush = get_brush(rt, *c['item_hover_bg'])
                rt.FillRectangle(ix, iy, ix + iw, iy + ih, hover_brush)
            text = self._items[i] if isinstance(self._items[i], str) else self._items[i].get('text', '')
            text_color = c['item_text']
            text_brush = get_brush(rt, *text_color)
            rt.DrawText(text, text_fmt,
                        ix + COMBO_TEXT_PAD_X, iy,
                        ix + iw - COMBO_TEXT_PAD_X, iy + ih, text_brush)

        rt.EndDraw()

        blend = _BLENDFUNCTION()
        blend.BlendOp = AC_SRC_OVER
        blend.SourceConstantAlpha = 255
        blend.AlphaFormat = AC_SRC_ALPHA
        pt = _POINT()
        size = _SIZE(w, h)
        user32.UpdateLayeredWindow(
            self._hwnd, None, None, ctypes.byref(size),
            self._hdc_mem, ctypes.byref(pt), 0, ctypes.byref(blend), ULW_ALPHA)

    def popup(self, screen_pos, list_width):
        self._list_width = list_width
        self._measure()
        self._layout_items()
        self.SetSize(self._width, self._height)
        sx, sy = screen_pos
        self.SetPosition(wx.Point(int(sx), int(sy)))
        self._render()
        self.Show()
        self._start_outside_check()

    def dismiss(self):
        if self._closing:
            return
        self._closing = True
        self._stop_outside_check()
        self._uninstall_wndproc()
        self.Hide()
        if self._on_close:
            self._on_close()
        self.Destroy()

    def _start_outside_check(self):
        self._outside_timer = wx.Timer(self)
        self._outside_timer.Start(50)
        self.Bind(wx.EVT_TIMER, self._check_outside_click, self._outside_timer)

    def _stop_outside_check(self):
        if self._outside_timer:
            self._outside_timer.Stop()
            self._outside_timer = None

    def _check_outside_click(self, event):
        if self._closing:
            return
        btn_state = user32.GetAsyncKeyState(1)
        if btn_state & 0x8000:
            pt = _POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(self._hwnd, ctypes.byref(rect))
            in_rect = (rect.left <= pt.x <= rect.right and
                       rect.top <= pt.y <= rect.bottom)
            if not in_rect:
                self.dismiss()

    def _hit_item(self, pt):
        px, py = pt
        for i, (ix, iy, iw, ih) in enumerate(self._item_rects):
            if ix <= px <= ix + iw and iy <= py <= iy + ih:
                return i
        return -1

    def _on_list_mouse_down(self, pt):
        idx = self._hit_item(pt)
        self._captured = True

    def _on_list_mouse_up(self, pt):
        if not self._captured:
            return
        self._captured = False
        idx = self._hit_item(pt)
        if idx >= 0:
            self._confirm_idx(idx)

    def _on_list_mouse_move(self, pt):
        idx = self._hit_item(pt)
        if idx != self._hovered_idx:
            self._hovered_idx = idx
            self._render()

    def _on_list_mouse_leave(self):
        if self._hovered_idx != -1:
            self._hovered_idx = -1
            self._render()

    def _confirm_selection(self):
        if self._hovered_idx >= 0:
            self._confirm_idx(self._hovered_idx)
        else:
            self.dismiss()

    def _confirm_idx(self, idx):
        if self._on_select:
            self._on_select(idx)
        self.dismiss()

    def _move_hover(self, delta):
        n = len(self._items)
        if n == 0:
            return
        new_idx = self._hovered_idx + delta
        new_idx = max(0, min(n - 1, new_idx))
        if new_idx != self._hovered_idx:
            self._hovered_idx = new_idx
            self._render()


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", ctypes.c_ushort),
                ("biBitCount", ctypes.c_ushort), ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32)]


class D2DComboBox(SheControl):
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
            cls._dwrite_text_fmt.SetTextAlignment(
                pyd2d.TEXT_ALIGNMENT.LEADING)
            cls._dwrite_text_fmt.SetParagraphAlignment(
                pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return cls._dwrite_text_fmt

    def __init__(self, rect, items=None, selected=-1, on_change=None):
        super().__init__(rect, "")
        self._items = list(items) if items else []
        self._selected = selected
        self._on_change = on_change
        self._dropped_down = False
        self._btn_state = self.NORMAL
        self._btn_hovered = False
        self._btn_captured = False
        self._popup = None
        self._parent_wnd = None

    @property
    def items(self):
        return list(self._items)

    @property
    def selected(self):
        return self._selected

    @property
    def selected_text(self):
        if 0 <= self._selected < len(self._items):
            item = self._items[self._selected]
            return item if isinstance(item, str) else item.get('text', '')
        return ''

    @property
    def dropped_down(self):
        return self._dropped_down

    def set_items(self, items):
        self._items = list(items) if items else []
        self._selected = -1
        self._text_layout = None

    def set_parent_window(self, wnd):
        self._parent_wnd = wnd

    def _btn_rect(self):
        rx, ry, rw, rh = self._rect
        return (rx + rw - COMBO_DROPDOWN_BTN_WIDTH, ry,
                COMBO_DROPDOWN_BTN_WIDTH, rh)

    def _hit_btn(self, pt):
        rx, ry, rw, rh = self._rect
        bx = rx + rw - COMBO_DROPDOWN_BTN_WIDTH
        px, py = pt
        return bx <= px <= rx + rw and ry <= py <= ry + rh

    def _hit_text_area(self, pt):
        rx, ry, rw, rh = self._rect
        bx = rx + rw - COMBO_DROPDOWN_BTN_WIDTH
        px, py = pt
        return rx <= px < bx and ry <= py <= ry + rh

    def hit_test(self, pt):
        rx, ry, rw, rh = self._rect
        px, py = pt
        return rx <= px <= rx + rw and ry <= py <= ry + rh

    def on_mouse_down(self, pt):
        if self._state == self.DISABLED:
            return False
        if self.hit_test(pt):
            if self._hit_btn(pt) or self._hit_text_area(pt):
                self._btn_state = self.PRESSED
                self._btn_captured = True
                self._captured = True
                return True
        return False

    def on_mouse_up(self, pt):
        if self._state == self.DISABLED:
            return False
        was_captured = self._btn_captured
        self._btn_captured = False
        self._captured = False
        if was_captured and self.hit_test(pt):
            self._btn_state = self.HOVER
            if not self._dropped_down:
                self._show_dropdown()
            else:
                self._close_dropdown()
            return True
        self._btn_state = self.NORMAL
        return was_captured

    def on_mouse_move(self, pt):
        if self._state == self.DISABLED:
            return False
        inside = self.hit_test(pt)
        if self._btn_captured:
            if inside and self._btn_state != self.PRESSED:
                self._btn_state = self.PRESSED
                return True
            return False
        if inside:
            if self._btn_state != self.HOVER:
                self._btn_state = self.HOVER
                return True
        else:
            if self._btn_state == self.HOVER:
                self._btn_state = self.NORMAL
                return True
        return False

    def on_mouse_leave(self):
        if self._state == self.DISABLED:
            return False
        self._btn_captured = False
        self._captured = False
        if self._btn_state in (self.HOVER, self.PRESSED):
            self._btn_state = self.NORMAL
            return True
        return False

    def _show_dropdown(self):
        if self._dropped_down or not self._parent_wnd:
            return
        self._dropped_down = True
        self._btn_state = self.PRESSED

        rx, ry, rw, rh = self._rect
        screen_pos = self._parent_wnd.ClientToScreen(wx.Point(int(rx), int(ry + rh)))

        def on_select(idx):
            old = self._selected
            self._selected = idx
            self._text_layout = None
            if self._on_change and idx != old:
                self._on_change(idx, old)

        def on_close():
            self._dropped_down = False
            self._btn_state = self.NORMAL
            self._popup = None
            if self._parent_wnd and hasattr(self._parent_wnd, 'composite'):
                self._parent_wnd.composite()

        popup = D2DComboListPopup(
            self._parent_wnd, items=self._items, selected=self._selected,
            on_select=on_select, on_close=on_close)
        self._popup = popup
        popup.popup((screen_pos.x, screen_pos.y), rw)

    def _close_dropdown(self):
        if self._popup:
            self._popup.dismiss()
        self._dropped_down = False
        self._btn_state = self.NORMAL

    def _get_state_name(self):
        if self._state == self.DISABLED:
            return 'disabled'
        if self._dropped_down:
            return 'pressed'
        return {self.NORMAL: 'normal', self.HOVER: 'hover',
                self.PRESSED: 'pressed'}.get(self._btn_state, 'normal')

    def draw(self, ctx, client_rect):
        rx, ry, rw, rh = self._rect
        rt = ctx.rt
        state_name = self._get_state_name()
        c = COMBO_COLORS.get(state_name, COMBO_COLORS['normal'])

        bg_brush = get_brush(rt, *c['bg'])
        border_brush = get_brush(rt, *c['border'])
        rt.FillRectangle(rx, ry, rx + rw, ry + rh, bg_brush)
        rt.DrawRectangle(rx, ry, rx + rw, ry + rh, border_brush, COMBO_BORDER_WIDTH)

        bx = rx + rw - COMBO_DROPDOWN_BTN_WIDTH
        btn_bg = get_brush(rt, *c['btn_bg'])
        btn_border = get_brush(rt, *c['btn_border'])
        rt.FillRectangle(bx, ry, rx + rw, ry + rh, btn_bg)
        rt.DrawLine(bx, ry, bx, ry + rh, border_brush, COMBO_BORDER_WIDTH)

        arrow_brush = get_brush(rt, *c['btn_arrow'])
        cx = bx + COMBO_DROPDOWN_BTN_WIDTH / 2
        cy = ry + rh / 2
        aw = 4
        ah = 3
        rt.DrawLine(cx - aw, cy - ah, cx, cy + ah, arrow_brush, 1.5)
        rt.DrawLine(cx, cy + ah, cx + aw, cy - ah, arrow_brush, 1.5)

        text = self.selected_text
        if text:
            text_fmt = self._get_text_fmt(dw_factory=ctx.dw_factory)
            text_brush = get_brush(rt, *c['text'])
            rt.DrawText(text, text_fmt,
                        rx + COMBO_TEXT_PAD_X, ry,
                        bx - COMBO_TEXT_PAD_X, ry + rh, text_brush)


class SkinAwareComboBox(D2DComboBox):
    _STATE_NAMES = {0: 'normal', 1: 'hover', 2: 'pressed', 3: 'disabled'}

    def __init__(self, rect, skin_context, items=None, selected=-1,
                 on_change=None, subcat_name='ComboBox'):
        super().__init__(rect, items=items, selected=selected, on_change=on_change)
        self._ctx = skin_context
        self._subcat = subcat_name
        self._slots = CONTROL_SLOTS.get(self._subcat, {})
        self._dwrite_text_fmt_cached = None

    def _has_skin_blocks(self):
        dropdown_slots = self._slots.get('dropdown', {})
        for state_name in ('normal', 'pressed'):
            slot = dropdown_slots.get(state_name)
            if slot is not None:
                block = self._ctx.get_block(slot)
                if not is_block_empty(block):
                    return True
        return False

    def _get_text_fmt_cached(self, dw_factory=None):
        if self._dwrite_text_fmt_cached is not None:
            return self._dwrite_text_fmt_cached
        font_info = self._ctx.get_font_info(self._subcat)
        if font_info:
            font_name = font_info.get('face_name', DEFAULT_FONT_FAMILY)
            font_size = float(abs(font_info.get('height', 9))) * PT_TO_DIP
            font_weight = font_info.get('weight', pyd2d.FONT_WEIGHT.NORMAL)
            font_style = pyd2d.FONT_STYLE.ITALIC if font_info.get('italic') else pyd2d.FONT_STYLE.NORMAL
        else:
            font_name = DEFAULT_FONT_FAMILY
            font_size = DEFAULT_FONT_SIZE_DIP
            font_weight = pyd2d.FONT_WEIGHT.NORMAL
            font_style = pyd2d.FONT_STYLE.NORMAL
        if dw_factory is None:
            dw_factory = pyd2d.GetDWriteFactory()
        self._dwrite_text_fmt_cached = dw_factory.CreateTextFormat(
            font_name, font_size, weight=font_weight, style=font_style,
            stretch=pyd2d.FONT_STRETCH.NORMAL)
        self._dwrite_text_fmt_cached.SetTextAlignment(
            pyd2d.TEXT_ALIGNMENT.LEADING)
        self._dwrite_text_fmt_cached.SetParagraphAlignment(
            pyd2d.PARAGRAPH_ALIGNMENT.CENTER)
        return self._dwrite_text_fmt_cached

    def _get_dropdown_state_slot(self, state_name):
        dropdown_slots = self._slots.get('dropdown', {})
        return dropdown_slots.get(state_name)

    def draw(self, ctx, client_rect):
        if not self._has_skin_blocks():
            D2DComboBox.draw(self, ctx, client_rect)
            return

        rx, ry, rw, rh = self._rect
        rt = ctx.rt

        state_name = self._get_state_name()
        c = COMBO_COLORS.get(state_name, COMBO_COLORS['normal'])

        bg_brush = get_brush(rt, *c['bg'])
        border_brush = get_brush(rt, *c['border'])
        rt.FillRectangle(rx, ry, rx + rw, ry + rh, bg_brush)
        rt.DrawRectangle(rx, ry, rx + rw, ry + rh, border_brush, COMBO_BORDER_WIDTH)

        bx = rx + rw - COMBO_DROPDOWN_BTN_WIDTH
        slot = self._get_dropdown_state_slot(state_name)
        if slot is not None:
            btn_block = self._ctx.get_block(slot)
            if not is_block_empty(btn_block):
                d2d_draw_block(rt, self._ctx.skin_img, btn_block,
                               (int(bx), int(ry), COMBO_DROPDOWN_BTN_WIDTH, int(rh)),
                               wic_factory=ctx.wic_factory,
                               d2d_cache=self._ctx.cache)
            else:
                self._draw_fallback_btn(rt, c, bx, ry, rh)
        else:
            self._draw_fallback_btn(rt, c, bx, ry, rh)

        text = self.selected_text
        if text:
            text_fmt = self._get_text_fmt_cached(dw_factory=ctx.dw_factory)
            text_state = self.DISABLED if self._state == self.DISABLED else self.NORMAL
            text_color = self._ctx.get_text_color(self._subcat, text_state)
            d2d_draw_text(rt, ctx.dw_factory, text, text_fmt, text_color,
                          rx + COMBO_TEXT_PAD_X, ry,
                          bx - rx - COMBO_TEXT_PAD_X * 2, rh)

    def _draw_fallback_btn(self, rt, c, bx, ry, rh):
        btn_bg = get_brush(rt, *c['btn_bg'])
        btn_border = get_brush(rt, *c['btn_border'])
        rt.FillRectangle(bx, ry, bx + COMBO_DROPDOWN_BTN_WIDTH, ry + rh, btn_bg)
        arrow_brush = get_brush(rt, *c['btn_arrow'])
        cx = bx + COMBO_DROPDOWN_BTN_WIDTH / 2
        cy = ry + rh / 2
        aw = 4
        ah = 3
        rt.DrawLine(cx - aw, cy - ah, cx, cy + ah, arrow_brush, 1.5)
        rt.DrawLine(cx, cy + ah, cx + aw, cy - ah, arrow_brush, 1.5)
