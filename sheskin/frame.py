"""SheLayeredFrame -- pyd2d D2D 渲染 + WS_EX_LAYERED 分层窗口。
管道: DC RenderTarget -> DIBSection -> UpdateLayeredWindow
"""
import ctypes
import ctypes.wintypes
from collections import OrderedDict

import numpy as np
import wx

import pyd2d
from .skin import SheSkin
from .titlebar import SheTitleBar
from .menubar import SheMenuBar
from .draw_context import DrawContext
from .draw_node import DrawNode
from .layout import CONTROL_SLOTS, DEFAULTS
from .block import is_block_empty
from .bitmap import apply_color_key
from .d2d_render import d2d_draw_block, D2DBlockCache
from .geometry_hittest import GeometryHitTester
from .brush_cache import BrushCache
from .controls.base_control import SheControl
from .controls.statusbar import D2DStatusBar, SkinAwareStatusBar
from .controls.toolbar import D2DToolBar, SkinAwareToolBar
from .controls.menu import D2DContextMenu, SkinAwareContextMenu, MenuItemData, SeparatorData
from .controls.skin_context import SkinContext
from .config import STATUSBAR_HEIGHT, TOOLBAR_HEIGHT

LRESULT = ctypes.c_longlong
HWND = ctypes.wintypes.HWND
UINT = ctypes.c_uint
WPARAM = ctypes.wintypes.WPARAM
LPARAM = ctypes.wintypes.LPARAM

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

GWL_EXSTYLE = -20
GWLP_WNDPROC = -4
WS_EX_LAYERED = 0x00080000

WM_NCHITTEST = 0x0084
WM_NCMOUSEMOVE = 0x00A0
WM_NCLBUTTONDOWN = 0x00A1
WM_NCLBUTTONUP = 0x00A2
WM_NCLBUTTONDBLCLK = 0x00A3
WM_ACTIVATE = 0x0006
WM_SIZE = 0x0005
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSELEAVE = 0x02A3
WM_NCMOUSELEAVE = 0x02A2

HTTOP = 12
HTBOTTOM = 15
HTLEFT = 10
HTRIGHT = 11
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17
HTCAPTION = 2
HTCLOSE = 20
HTMAXBUTTON = 9
HTMINBUTTON = 8
HTHELP = 21
HTNOWHERE = 0
HTCLIENT = 1

_CORNER_HT = {
    'topleft': HTTOPLEFT,
    'topright': HTTOPRIGHT,
    'bottomleft': HTBOTTOMLEFT,
    'bottomright': HTBOTTOMRIGHT,
}

_EDGE_HT = {
    'top': HTTOP,
    'bottom': HTBOTTOM,
    'left': HTLEFT,
    'right': HTRIGHT,
}

ULW_ALPHA = 0x02
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)


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


user32.DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.CallWindowProcW = ctypes.windll.user32.CallWindowProcW
user32.CallWindowProcW.argtypes = [ctypes.c_void_p, HWND, UINT, WPARAM, LPARAM]
user32.CallWindowProcW.restype = LRESULT
user32.GetWindowRect.argtypes = [HWND, ctypes.c_void_p]
user32.GetWindowRect.restype = ctypes.c_bool
user32.GetClientRect.argtypes = [HWND, ctypes.c_void_p]
user32.GetClientRect.restype = ctypes.c_bool
user32.GetWindowLongW.argtypes = [HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_ulong
user32.SetWindowLongW.argtypes = [HWND, ctypes.c_int, ctypes.c_ulong]
user32.SetWindowLongW.restype = ctypes.c_ulong
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
user32.ScreenToClient.argtypes = [HWND, ctypes.c_void_p]
user32.ScreenToClient.restype = ctypes.c_bool
user32.SetCapture.argtypes = [HWND]
user32.SetCapture.restype = HWND
user32.ReleaseCapture.restype = ctypes.c_bool
user32.MoveWindow.argtypes = [HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, ctypes.c_bool]
user32.MoveWindow.restype = ctypes.c_bool
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int

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
gdi32.GetDeviceCaps.argtypes = [HWND, ctypes.c_int]
gdi32.GetDeviceCaps.restype = ctypes.c_int


class SheLayeredFrame(wx.Frame):
    """D2D 渲染 + WS_EX_LAYERED 的皮肤窗口。

    管道: DCRenderTarget -> DIBSection -> UpdateLayeredWindow
    """

    def __init__(self, skin_name, parent=None, id=wx.ID_ANY,
                 title="", window_type='NormalWindow',
                 pos=wx.DefaultPosition, size=(800, 600),
                 has_max=True, has_min=True, has_help=False):
        super().__init__(parent, id, title, pos, size,
                        style=wx.FRAME_SHAPED | wx.NO_BORDER)

        self._skin_name = skin_name
        self._skin = None
        self._titlebar = None
        self._menubar = None
        self._toolbar = None
        self._statusbar = None
        self._window_type = window_type
        self._has_max = has_max
        self._has_min = has_min
        self._has_help = has_help
        self._state_name = 'active'

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

        self._old_wndproc = None
        self._wndproc_cb = None
        self._hwnd = None
        self._active = True
        self._dirty = True
        self._closing = False
        self._menu_click_handler = None
        self._context_menu_items = None
        self._active_menu = None
        self._client_callbacks = []
        self._d2d_controls = []
        self._all_interactables = []
        self._focused_ctrl = None
        self._hit_tester = None
        self._render_tree = None
        self._client_node = None
        self._icon_bmp = None
        self._border_alpha_key = None
        self._border_alpha_data = None
        self._alpha_brush_cache = OrderedDict()
        self._alpha_np_cache = {}
        self._brush_cache = None
        self._frame_id = 0
        self._caret_timer = wx.Timer(self)
        self._caret_timer.Start(50)

        self._init_skin()
        self._init_d2d()
        self._setup_window()
        self._bind_events()

        if pos == wx.DefaultPosition:
            self.Center()

    def _init_skin(self):
        self._skin = SheSkin(self._skin_name)
        self._skin.load()
        self._titlebar = SheTitleBar(self._skin, self._window_type)
        self._menubar = SheMenuBar(self._skin)
        self._menubar.set_frame(self)

        props = self._skin.get_props(self._window_type)
        if props.get('help_btn_fixed'):
            self._has_help = True

    @property
    def skin(self):
        return self._skin

    def _init_d2d(self):
        self._d2d_factory = pyd2d.GetD2DFactory()
        self._wic_factory = pyd2d.GetWICFactory()
        self._dw_factory = pyd2d.GetDWriteFactory()
        self._d2d_cache = D2DBlockCache()
        self._hit_tester = GeometryHitTester(self._d2d_factory)
        self._d2d_layer = None

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
        self._brush_cache = BrushCache(self._dc_rt)

    def _ensure_border_alpha(self, state):
        slots = CONTROL_SLOTS.get(self._window_type)
        if not slots:
            return

        key_parts = [state]
        for block_name in ('top', 'bottom', 'left', 'right'):
            key_parts.append(slots[block_name][state])
        cache_key = tuple(key_parts)

        if self._border_alpha_key == cache_key and self._border_alpha_data:
            return
        self._border_alpha_key = cache_key
        self._border_alpha_data = None
        self._alpha_brush_cache.clear()
        self._alpha_np_cache.clear()

        data = {}
        for block_name in ('top', 'bottom', 'left', 'right'):
            slot_idx = slots[block_name][state]
            block = self._skin.get_block(slot_idx)
            if is_block_empty(block) or block.bg_width <= 0 or block.bg_height <= 0:
                continue
            if block.bg_color_key == 0xFFFFFFFF:
                continue

            sub = self._skin.skin_img.GetSubImage(wx.Rect(
                int(block.bg_left), int(block.bg_top),
                int(block.bg_width), int(block.bg_height)))
            sub = apply_color_key(sub, block.bg_color_key)
            if not sub.HasAlpha():
                sub.InitAlpha()

            alpha_data = bytearray(sub.GetAlpha())
            has_transparent = any(
                b == 0 for b in alpha_data[:min(len(alpha_data), 1024)])
            if not has_transparent:
                continue

            data[block_name] = {
                'img': sub,
                'ml': block.margin_left,
                'mt': block.margin_top,
                'mr': block.margin_right,
                'mb': block.margin_bottom,
            }

        if data:
            self._border_alpha_data = data

    def _get_alpha_np(self, img, block_name):
        w, h = img.GetWidth(), img.GetHeight()
        key = (block_name, w, h)
        if key not in self._alpha_np_cache:
            self._alpha_np_cache[key] = np.frombuffer(
                img.GetAlpha(), dtype=np.uint8).reshape(h, w)
        return self._alpha_np_cache[key]

    def _get_alpha_brush(self, w, h, b_left, b_top, b_right, b_bottom):
        self._ensure_border_alpha(self._state_name)
        if not self._border_alpha_data:
            return None

        cache_parts = [w, h, b_left, b_top, b_right, b_bottom]
        for block_name in ('top', 'bottom', 'left', 'right'):
            d = self._border_alpha_data.get(block_name)
            if d:
                cache_parts.append(block_name)
                cache_parts.extend([d['ml'], d['mt'], d['mr'], d['mb']])
        cache_key = tuple(cache_parts)

        if cache_key in self._alpha_brush_cache:
            return self._alpha_brush_cache[cache_key]

        mask = np.full((h, w), 255, dtype=np.uint8)

        top_data = self._border_alpha_data.get('top')
        if top_data:
            ti = top_data['img']
            t_w, t_h = ti.GetWidth(), ti.GetHeight()
            t_alpha = self._get_alpha_np(ti, 'top')
            ml, mr = top_data['ml'], top_data['mr']
            copy_h = min(t_h, b_top, h)
            if ml > 0 and copy_h > 0:
                copy_w = min(ml, w, t_w)
                mask[0:copy_h, 0:copy_w] = t_alpha[0:copy_h, 0:copy_w]
            if mr > 0 and copy_h > 0:
                copy_w = min(mr, w, t_w)
                mask[0:copy_h, w - copy_w:w] = t_alpha[0:copy_h, t_w - copy_w:t_w]

        bot_data = self._border_alpha_data.get('bottom')
        if bot_data:
            bi = bot_data['img']
            b_w, b_h = bi.GetWidth(), bi.GetHeight()
            b_alpha = self._get_alpha_np(bi, 'bottom')
            ml, mr = bot_data['ml'], bot_data['mr']
            copy_h = min(b_h, b_bottom, h)
            y_start = h - copy_h
            if ml > 0 and copy_h > 0:
                copy_w = min(ml, w, b_w)
                mask[y_start:h, 0:copy_w] = b_alpha[b_h - copy_h:b_h, 0:copy_w]
            if mr > 0 and copy_h > 0:
                copy_w = min(mr, w, b_w)
                mask[y_start:h, w - copy_w:w] = b_alpha[
                    b_h - copy_h:b_h, b_w - copy_w:b_w]

        left_data = self._border_alpha_data.get('left')
        if left_data:
            li = left_data['img']
            l_w, l_h = li.GetWidth(), li.GetHeight()
            l_alpha = self._get_alpha_np(li, 'left')
            mid_h = h - b_top - b_bottom
            copy_h = min(l_h, mid_h)
            copy_w = min(l_w, b_left, w)
            if copy_h > 0 and copy_w > 0:
                mask[b_top:b_top + copy_h, 0:copy_w] = l_alpha[0:copy_h, 0:copy_w]

        right_data = self._border_alpha_data.get('right')
        if right_data:
            ri = right_data['img']
            r_w, r_h = ri.GetWidth(), ri.GetHeight()
            r_alpha = self._get_alpha_np(ri, 'right')
            mid_h = h - b_top - b_bottom
            copy_h = min(r_h, mid_h)
            copy_w = min(r_w, b_right, w)
            if copy_h > 0 and copy_w > 0:
                mask[b_top:b_top + copy_h, w - copy_w:w] = r_alpha[
                    0:copy_h, r_w - copy_w:r_w]

        a = mask.astype(np.float32) / 255.0
        bgra = np.zeros((h, w, 4), dtype=np.uint8)
        bgra[:, :, 0] = (mask.astype(np.float32) * a).astype(np.uint8)
        bgra[:, :, 1] = (mask.astype(np.float32) * a).astype(np.uint8)
        bgra[:, :, 2] = (mask.astype(np.float32) * a).astype(np.uint8)
        bgra[:, :, 3] = mask

        wic_bmp = self._wic_factory.CreateBitmap(w, h)
        lock = wic_bmp.Lock(0, 0, w, h)
        addr, cb_size = lock.GetDataPointer()
        pixels = (ctypes.c_ubyte * cb_size).from_address(addr)
        ctypes.memmove(pixels, bgra.tobytes(), cb_size)
        del lock

        d2d_bmp = self._dc_rt.CreateBitmapFromWicBitmap(wic_bmp)
        brush = self._dc_rt.CreateBitmapBrush(d2d_bmp)
        self._alpha_brush_cache[cache_key] = brush
        while len(self._alpha_brush_cache) > 16:
            self._alpha_brush_cache.popitem(last=False)
        return brush

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

    def _custom_wndproc(self, hwnd, msg, wparam, lparam):
        if self._closing:
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        try:
            if msg == WM_NCHITTEST:
                return self._on_nchittest(msg, wparam, lparam)
            elif msg == WM_ACTIVATE:
                active = (wparam & 0xFFFF) != 0
                if active != self._active:
                    self._active = active
                    self._state_name = 'active' if active else 'inactive'
                    self._dirty = True
                    self._do_composite()
            elif msg == WM_SIZE:
                self._dirty = True
                self._do_composite()
            elif msg == WM_NCLBUTTONDBLCLK:
                return 0
            elif msg == WM_NCLBUTTONDOWN:
                hit = wparam & 0xFF
                self._titlebar.set_hover(None)
                button_name = {
                    HTCLOSE: 'close', HTMAXBUTTON: 'max',
                    HTMINBUTTON: 'min', HTHELP: 'help',
                }.get(hit)
                if button_name:
                    self._titlebar.set_pressed(button_name)
                    self._dirty = True
                    self._do_composite()
                if hit == HTCLOSE:
                    wx.CallAfter(self.Close)
                    return 0
                elif hit == HTMAXBUTTON:
                    wx.CallAfter(self._on_sys_maximize)
                    return 0
                elif hit == HTMINBUTTON:
                    wx.CallAfter(self._on_sys_minimize)
                    return 0
                elif hit == HTHELP:
                    return 0
            elif msg == WM_NCMOUSEMOVE:
                self._sync_interactable_contexts()
                dims = self._skin.get_border_dims(self._window_type, self._state_name)
                if dims:
                    b_left = dims['border_left']
                    b_right = dims['border_right']
                    b_top = dims['title_h']
                    bw = self._width - b_left - b_right
                    rect = (b_left, 0, bw, b_top)
                else:
                    rect = None
                sx = ctypes.c_short(lparam & 0xFFFF).value
                sy = ctypes.c_short((lparam >> 16) & 0xFFFF).value
                wx_pos = self.GetScreenPosition()
                px = sx - wx_pos.x
                py = sy - wx_pos.y
                if rect and self._titlebar.on_mouse_move(
                    (px, py), rect, self._state_name,
                    self._has_max, self._has_min, self._has_help,
                    self.IsMaximized()):
                    self._dirty = True
                    self._do_composite()
            elif msg == WM_NCLBUTTONUP:
                self._sync_interactable_contexts()
                if self._titlebar.on_mouse_up((0, 0)):
                    self._dirty = True
                    self._do_composite()
        except Exception as e:
            import traceback
            print(f"[WNDPROC ERROR] msg=0x{msg:04X}: {e}")
            traceback.print_exc()
        if self._old_wndproc:
            return user32.CallWindowProcW(ctypes.c_void_p(self._old_wndproc), hwnd, msg, wparam, lparam)
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _on_nchittest(self, msg, wparam, lparam):
        self._sync_interactable_contexts()
        sx = ctypes.c_long(lparam & 0xFFFF).value
        sy = ctypes.c_long((lparam >> 16) & 0xFFFF).value
        wx_pos = self.GetScreenPosition()
        px = sx - wx_pos.x
        py = sy - wx_pos.y

        w = self._width
        h = self._height
        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        if not dims:
            return HTCLIENT

        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        b_bottom = dims['border_bottom']

        button_hit = self._titlebar.get_nchittest_code((px, py))
        if button_hit == 'close':
            return HTCLOSE
        elif button_hit == 'max':
            return HTMAXBUTTON
        elif button_hit == 'min':
            return HTMINBUTTON
        elif button_hit == 'help':
            return HTHELP
        elif button_hit == 'titlebar':
            return HTCAPTION

        if self._hit_tester is None:
            return HTCLIENT

        zone, detail = self._hit_tester.classify_border_point(
            px, py, w, h, b_left, b_top, b_right, b_bottom)

        if zone == 'corner':
            if self._hit_tester.hit_test(px, py):
                return _CORNER_HT[detail]
            return HTNOWHERE
        elif zone == 'edge':
            return _EDGE_HT[detail]

        if not self._hit_tester.hit_test(px, py):
            return HTNOWHERE
        return HTCLIENT

    def _bind_events(self):
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self._on_left_up)
        self.Bind(wx.EVT_LEFT_DCLICK, self._on_left_dclick)
        self.Bind(wx.EVT_RIGHT_DOWN, self._on_right_down)
        self.Bind(wx.EVT_MOTION, self._on_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self.Bind(wx.EVT_CHAR, self._on_char)
        self.Bind(wx.EVT_SET_FOCUS, self._on_set_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self._on_kill_focus)
        self.Bind(wx.EVT_TIMER, self._on_caret_timer)
        self.Bind(wx.EVT_MOUSEWHEEL, self._on_mouse_wheel)

    def Show(self, show=True):
        if show:
            self._dirty = True
            self._do_composite()
        return super().Show(show)

    def _on_size(self, event):
        self._dirty = True
        self._do_composite()
        event.Skip()

    def _on_left_down(self, event):
        px, py = event.GetPosition()
        self._sync_interactable_contexts()
        dirty = False
        for ia in self._all_interactables:
            if not getattr(ia, '_visible', True):
                continue
            if ia.on_mouse_down((px, py)):
                dirty = True
        if dirty:
            self._dirty = True
            self._do_composite()
        event.Skip()

    def _on_left_up(self, event):
        px, py = event.GetPosition()
        self._sync_interactable_contexts()
        dirty = False
        for ia in self._all_interactables:
            if not getattr(ia, '_visible', True) and not getattr(ia, '_captured', False):
                continue
            if ia.on_mouse_up((px, py)):
                dirty = True
        if self._menubar and self._menubar._items:
            idx = self._menubar.last_clicked_idx
            # 仅当无下拉菜单模式时使用旧回调（向后兼容纯文本 menubar）
            if idx >= 0 and self._menu_click_handler and self._menubar._active_menu_idx < 0:
                self._menu_click_handler(idx)
        if dirty:
            self._dirty = True
            self._do_composite()
        event.Skip()

    def _on_left_dclick(self, event):
        px, py = event.GetPosition()
        self._sync_interactable_contexts()
        dirty = False
        for ia in self._all_interactables:
            if not getattr(ia, '_visible', True):
                continue
            if hasattr(ia, 'on_double_click') and ia.hit_test((px, py)):
                if ia.on_double_click((px, py)):
                    dirty = True
            elif ia.on_mouse_down((px, py)):
                dirty = True
        if dirty:
            self._dirty = True
            self._do_composite()
        event.Skip()

    def _on_motion(self, event):
        px, py = event.GetPosition()
        self._sync_interactable_contexts()
        dirty = False
        cursor_type = wx.CURSOR_ARROW
        for ia in self._all_interactables:
            if not getattr(ia, '_visible', True) and not getattr(ia, '_captured', False):
                continue
            if ia.on_mouse_move((px, py)):
                dirty = True
            if getattr(ia, '_visible', True) and ia.hit_test((px, py)) and getattr(ia, '_state', 0) != getattr(ia, 'DISABLED', 3):
                cursor_type = getattr(ia, '_cursor_type', wx.CURSOR_ARROW)
        wx.SetCursor(wx.Cursor(cursor_type))
        if dirty:
            self._dirty = True
            self._do_composite()
        event.Skip()

    def _on_leave(self, event):
        dirty = False
        for ia in self._all_interactables:
            if ia.on_mouse_leave():
                dirty = True
        wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        if self._menubar and hasattr(self._menubar, '_hover_item') and self._menubar._hover_item is not None:
            self._menubar._hover_item = None
            dirty = True
        if dirty:
            self._dirty = True
            self._do_composite()
        event.Skip()

    def _on_mouse_wheel(self, event):
        px, py = event.GetPosition()
        delta = event.GetWheelDelta()  # 通常 120
        rotation = event.GetWheelRotation()  # 正=向上，负=向下
        # 归一化：每次滚轮"咔嗒"为 ±1
        steps = rotation // delta if delta else 0
        if steps == 0:
            event.Skip()
            return
        self._sync_interactable_contexts()
        dirty = False
        for ia in reversed(self._all_interactables):
            if not getattr(ia, '_visible', True):
                continue
            if hasattr(ia, 'on_mouse_wheel'):
                # 用基类 hit_test 检测整个 rect（含 scrollbar 区域）
                if SheControl.hit_test(ia, (px, py)):
                    if ia.on_mouse_wheel((px, py), steps):
                        dirty = True
                        break
        if dirty:
            self._dirty = True
            self._do_composite()
        event.Skip()

    def _on_close(self, event):
        self._closing = True
        if self._caret_timer:
            self._caret_timer.Stop()
        self._uninstall_wndproc()
        self._cleanup()
        event.Skip()

    def _on_key_down(self, event):
        if self._focused_ctrl:
            if not getattr(self._focused_ctrl, '_visible', True):
                self._focused_ctrl = None
            elif hasattr(self._focused_ctrl, 'on_key_down'):
                key_code = event.GetKeyCode()
                modifiers = event.GetModifiers()
                if self._focused_ctrl.on_key_down(key_code, modifiers):
                    self._dirty = True
                    self._do_composite()
                    return
        event.Skip()

    def _on_char(self, event):
        if self._focused_ctrl:
            if not getattr(self._focused_ctrl, '_visible', True):
                self._focused_ctrl = None
            elif hasattr(self._focused_ctrl, 'on_char'):
                char_code = event.GetUnicodeKey()
                if char_code != wx.WXK_NONE:
                    if self._focused_ctrl.on_char(char_code):
                        self._dirty = True
                        self._do_composite()
                        return
        event.Skip()

    def _on_set_focus(self, event):
        event.Skip()

    def _on_kill_focus(self, event):
        if self._focused_ctrl and hasattr(self._focused_ctrl, 'set_focus'):
            self._focused_ctrl.set_focus(False)
            self._focused_ctrl = None
            self._dirty = True
            self._do_composite()
        event.Skip()

    def _on_caret_timer(self, event):
        dirty = False
        for ia in self._all_interactables:
            if hasattr(ia, 'tick_caret') and ia.tick_caret():
                dirty = True
        if dirty:
            self._dirty = True
            self._do_composite()

    def set_focused_control(self, ctrl):
        if self._focused_ctrl is ctrl:
            return
        if self._focused_ctrl and hasattr(self._focused_ctrl, 'set_focus'):
            self._focused_ctrl.set_focus(False)
        self._focused_ctrl = ctrl
        if ctrl and hasattr(ctrl, 'set_focus'):
            ctrl.set_focus(True)
        self._dirty = True
        self._do_composite()

    def _on_right_down(self, event):
        px, py = event.GetPosition()
        screen_pos = self.ClientToScreen(event.GetPosition())
        screen_pos = (screen_pos.x, screen_pos.y)

        # 优先检查控件级右键菜单（后注册的控件在上层，逆序遍历）
        self._sync_interactable_contexts()
        for ia in reversed(self._all_interactables):
            if not getattr(ia, '_visible', True):
                continue
            if hasattr(ia, 'on_right_down') and ia.on_right_down((px, py)):
                menu_items = ia.get_context_menu()
                if menu_items:
                    self.popup_menu(menu_items, screen_pos=screen_pos)
                    event.Skip()
                    return

        # 无控件级菜单时使用窗口级菜单
        if self._context_menu_items:
            self.popup_menu(self._context_menu_items, screen_pos=screen_pos)
        event.Skip()

    def _on_sys_minimize(self):
        self._titlebar.set_pressed(None)
        self._titlebar.set_hover(None)
        self._dirty = True
        self._do_composite()
        self.Iconize(True)

    def _on_sys_maximize(self):
        self._titlebar.set_pressed(None)
        self._titlebar.set_hover(None)
        self._dirty = True
        self._do_composite()
        self.Maximize(not self.IsMaximized())

    def _ensure_dibsection(self, w, h):
        if w == self._width and h == self._height and self._hBmp:
            return
        if self._hBmp and w <= self._dib_max_w and h <= self._dib_max_h:
            self._width = w
            self._height = h
            return
        self._release_dibsection()

        alloc_w = max(w, getattr(self, '_dib_max_w', 0))
        alloc_h = max(h, getattr(self, '_dib_max_h', 0))
        self._dib_max_w = alloc_w
        self._dib_max_h = alloc_h
        self._width = w
        self._height = h

        hdc_screen = user32.GetDC(None)
        bmi = _BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.biWidth = alloc_w
        bmi.biHeight = -alloc_h
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0
        bmi.biSizeImage = alloc_w * alloc_h * 4

        self._ppvBits = ctypes.c_void_p()
        self._hBmp = gdi32.CreateDIBSection(
            hdc_screen, ctypes.byref(bmi), 0, ctypes.byref(self._ppvBits), None, 0)
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
        if not self._dirty:
            return
        self._dirty = False
        try:
            self._composite()
            self._push()
        except Exception:
            import traceback
            print("[_do_composite ERROR]")
            traceback.print_exc()

    def _draw_border_section(self, ctx, w, h):
        slots = CONTROL_SLOTS.get(self._window_type)
        if not slots:
            return

        skin_img = self._skin.skin_img
        top_b = self._skin.get_block(slots['top'][self._state_name])
        left_b = self._skin.get_block(slots['left'][self._state_name])
        right_b = self._skin.get_block(slots['right'][self._state_name])
        bottom_b = self._skin.get_block(slots['bottom'][self._state_name])
        bg_b = self._skin.get_block(slots.get('bg', {}).get('normal', 271))

        if not is_block_empty(bg_b):
            d2d_draw_block(ctx.rt, skin_img, bg_b,
                           (0, 0, w, h), ctx.wic_factory, ctx.d2d_cache)

        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        b_bottom = dims['border_bottom']

        if not is_block_empty(top_b):
            d2d_draw_block(ctx.rt, skin_img, top_b,
                           (0, 0, w, b_top), ctx.wic_factory, ctx.d2d_cache)

        if not is_block_empty(left_b):
            d2d_draw_block(ctx.rt, skin_img, left_b,
                           (0, b_top, b_left, h - b_top - b_bottom),
                           ctx.wic_factory, ctx.d2d_cache)

        if not is_block_empty(right_b):
            d2d_draw_block(ctx.rt, skin_img, right_b,
                           (w - b_right, b_top, b_right, h - b_top - b_bottom),
                           ctx.wic_factory, ctx.d2d_cache)

        bw = w - b_left - b_right
        bh = h - b_top - b_bottom
        if bw > 0 and bh > 0:
            if not is_block_empty(bottom_b):
                d2d_draw_block(ctx.rt, skin_img, bottom_b,
                               (0, h - b_bottom, w, b_bottom),
                               ctx.wic_factory, ctx.d2d_cache)

    def _draw_titlebar_section(self, ctx):
        w, h = self._width, self._height
        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        bw = w - b_left - b_right

        title_rect = (b_left, 0, bw, b_top)
        title_text = self.GetTitle() if self.GetTitle() else ""
        self._titlebar.draw_d2d(
            ctx, title_rect, self._state_name,
            title=title_text,
            icon=self._icon_bmp,
            has_icon=self._icon_bmp is not None,
            has_max=self._has_max,
            has_min=self._has_min,
            has_help=self._has_help,
            is_maximized=self.IsMaximized())

    def _draw_menubar_section(self, ctx):
        w, h = self._width, self._height
        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        b_bottom = dims['border_bottom']
        bw = w - b_left - b_right
        bh = h - b_top - b_bottom

        menu_h = self._skin.get_menu_bar_height()
        if not (menu_h > 0 and bh > 0 and self._menubar._items):
            return
        menu_rect = (b_left, b_top, bw, menu_h)
        self._menubar.set_rect(menu_rect)
        self._menubar.draw_d2d(ctx)

    def _toolbar_height(self):
        if self._toolbar is None or not self._toolbar._items:
            return 0
        return TOOLBAR_HEIGHT

    def _draw_toolbar_section(self, ctx):
        if self._toolbar is None:
            return
        if not self._toolbar._items:
            return
        w, h = self._width, self._height
        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        if not dims:
            return
        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        b_bottom = dims['border_bottom']
        bw = w - b_left - b_right
        if bw <= 0:
            return
        menu_h = self._skin.get_menu_bar_height()
        has_menu = menu_h > 0 and self._menubar._items
        tb_top = b_top + (menu_h if has_menu else 0)
        tb_h = self._toolbar_height()
        self._toolbar.set_rect((b_left, tb_top, bw, tb_h))
        self._toolbar.draw(ctx, (b_left, b_top, bw, h - b_top - b_bottom))

    def _draw_statusbar_section(self, ctx):
        if self._statusbar is None:
            return
        if not self._statusbar._items:
            return
        w, h = self._width, self._height
        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        if not dims:
            return
        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        b_bottom = dims['border_bottom']
        bw = w - b_left - b_right
        if bw <= 0 or h - b_bottom <= b_top:
            return
        sb_top = h - b_bottom - STATUSBAR_HEIGHT
        self._statusbar.set_rect((b_left, sb_top, bw, STATUSBAR_HEIGHT))
        self._statusbar.draw(ctx, (b_left, b_top, bw, h - b_top - b_bottom))

    def _draw_client_section(self, ctx):
        w, h = self._width, self._height
        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        b_bottom = dims['border_bottom']
        bw = w - b_left - b_right
        bh = h - b_top - b_bottom

        if not self._client_callbacks or bw <= 0 or bh <= 0:
            return

        menu_h = self._skin.get_menu_bar_height()
        client_top = b_top + (menu_h if menu_h > 0 and self._menubar._items else 0)
        client_h = h - b_bottom - client_top
        if client_h <= 0:
            return

        client_rect = (b_left, client_top, bw, client_h)
        l, t, cw, ch = client_rect
        ctx.rt.PushAxisAlignedClip(
            float(l), float(t), float(l + cw), float(t + ch))
        try:
            for cb in self._client_callbacks:
                cb(ctx, client_rect)
        finally:
            ctx.rt.PopAxisAlignedClip()

    def _build_render_tree(self, w, h):
        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        if not dims:
            self._render_tree = None
            return
        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        b_bottom = dims['border_bottom']
        bw = w - b_left - b_right
        bh = h - b_top - b_bottom

        root = DrawNode((0, 0, w, h), name='frame_root')

        root.add_child(DrawNode((0, 0, w, h),
            draw_fn=lambda ctx, cr, _w=w, _h=h: self._draw_border_section(ctx, _w, _h),
            name='border'))

        root.add_child(DrawNode((b_left, 0, bw, b_top),
            draw_fn=lambda ctx, cr: self._draw_titlebar_section(ctx),
            name='titlebar'))

        menu_h = self._skin.get_menu_bar_height()
        if menu_h > 0 and bh > 0 and self._menubar._items:
            menu_rect = (b_left, b_top, bw, menu_h)
            root.add_child(DrawNode(menu_rect,
                draw_fn=lambda ctx, cr: self._draw_menubar_section(ctx),
                name='menubar'))

        client_top = b_top + (menu_h if menu_h > 0 and self._menubar._items else 0)

        tb_h = self._toolbar_height()
        if tb_h > 0 and self._toolbar is not None and self._toolbar._items and bw > 0:
            tb_rect = (b_left, client_top, bw, tb_h)
            root.add_child(DrawNode(tb_rect,
                draw_fn=lambda ctx, cr: self._draw_toolbar_section(ctx),
                name='toolbar'))
            client_top = client_top + tb_h

        client_h = h - b_bottom - client_top

        sb_h = STATUSBAR_HEIGHT
        if self._statusbar is not None and self._statusbar._items and client_h > sb_h:
            client_h = client_h - sb_h

        if client_h > 0 and bw > 0:
            client_node = DrawNode((b_left, client_top, bw, client_h),
                                   clip=True, name='client_area')
            root.add_child(client_node)
            for cb in self._client_callbacks:
                client_node.add_child(DrawNode((0, 0, bw, client_h),
                    draw_fn=lambda ctx, cr, _cb=cb: _cb(ctx, cr),
                    name='user_cb'))
            self._client_node = client_node
        else:
            self._client_node = None

        if self._statusbar is not None and self._statusbar._items and bw > 0 and sb_h > 0:
            sb_top = client_top + client_h
            sb_rect = (b_left, sb_top, bw, sb_h)
            root.add_child(DrawNode(sb_rect,
                draw_fn=lambda ctx, cr: self._draw_statusbar_section(ctx),
                name='statusbar'))

        self._render_tree = root

        self._all_interactables = []
        self._all_interactables.append(self._titlebar)
        if self._menubar and self._menubar._items:
            self._all_interactables.append(self._menubar)
        if self._toolbar and self._toolbar._items:
            self._all_interactables.append(self._toolbar)
        self._all_interactables.extend(self._d2d_controls)

    def _sync_interactable_contexts(self):
        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        if not dims:
            return
        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        bw = self._width - b_left - b_right
        title_rect = (b_left, 0, bw, b_top)
        self._titlebar.sync_context(
            title_rect, self._state_name,
            self._has_max, self._has_min, self._has_help,
            self.IsMaximized())

    def _composite(self):
        if self._closing or not self._dc_rt:
            return
        w, h = self.GetClientSize()
        if w <= 0 or h <= 0:
            return
        self._ensure_dibsection(w, h)

        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        if not dims:
            return

        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        b_bottom = dims['border_bottom']

        corner_r = dims.get('corner_radius', 0)
        if self._hit_tester is not None:
            self._hit_tester.init_window_shape(
                w, h, corner_r,
                b_left, b_top, b_right, b_bottom)

        self._build_render_tree(w, h)

        self._dc_rt.BindDC(self._hdc_mem, 0, 0, w, h)
        self._dc_rt.BeginDraw()
        self._dc_rt.SetTransform(
            self._dpi_scale_x, 0.0, 0.0,
            self._dpi_scale_y, 0.0, 0.0)
        ctx = DrawContext(self._dc_rt, self._skin, self._wic_factory,
                          self._dw_factory, self._d2d_cache)
        layer_pushed = False
        try:
            self._dc_rt.Clear(0.0, 0.0, 0.0, 0.0)

            alpha_brush = self._get_alpha_brush(w, h, b_left, b_top, b_right, b_bottom)
            if alpha_brush is not None:
                if self._d2d_layer is None:
                    self._d2d_layer = self._dc_rt.CreateLayer()
                self._dc_rt.PushLayer(
                    self._d2d_layer,
                    contentLeft=0.0, contentTop=0.0,
                    contentRight=float(w), contentBottom=float(h),
                    opacityBrush=alpha_brush)
                layer_pushed = True

            try:
                self._render_tree.render(ctx)
            finally:
                if layer_pushed:
                    self._dc_rt.PopLayer()
        finally:
            self._dc_rt.EndDraw()
            self._frame_id += 1
            self._brush_cache.end_frame()

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
        if self._brush_cache:
            self._brush_cache.clear()
        self._alpha_brush_cache.clear()
        self._alpha_np_cache.clear()
        self._release_dibsection()
        self._dc_rt = None
        self._d2d_factory = None
        self._dw_factory = None
        self._wic_factory = None

    def composite(self):
        self._dirty = True
        self._do_composite()

    def SetTitle(self, title):
        super().SetTitle(title)
        self._dirty = True
        self._do_composite()

    def set_menubar_items(self, items):
        self._menubar.set_items(items)
        self._dirty = True
        self._do_composite()

    def set_statusbar_items(self, items):
        if self._skin is not None and self._skin._loaded:
            skin_ctx = SkinContext(self._skin)
            self._statusbar = SkinAwareStatusBar(
                (0, 0, 100, STATUSBAR_HEIGHT), skin_ctx, items=items)
        else:
            self._statusbar = D2DStatusBar(
                (0, 0, 100, STATUSBAR_HEIGHT), items=items)
        self._dirty = True
        self._do_composite()

    def set_toolbar_items(self, items, on_click=None):
        if self._skin is not None and self._skin._loaded:
            skin_ctx = SkinContext(self._skin)
            self._toolbar = SkinAwareToolBar(
                (0, 0, 100, TOOLBAR_HEIGHT), skin_ctx, on_click=on_click)
        else:
            self._toolbar = D2DToolBar(
                (0, 0, 100, TOOLBAR_HEIGHT), on_click=on_click)
        for item in items:
            if isinstance(item, str):
                if item == '|':
                    self._toolbar.add_separator()
                else:
                    self._toolbar.add_button(item)
            elif isinstance(item, dict):
                if item.get('type') == 'separator':
                    self._toolbar.add_separator()
                else:
                    self._toolbar.add_button(
                        item.get('text', ''),
                        icon=item.get('icon'),
                        disabled=item.get('disabled', False),
                        data=item.get('data'))
        self._dirty = True
        self._do_composite()

    def set_icon(self, icon_bmp):
        self._icon_bmp = icon_bmp
        self._dirty = True
        self._do_composite()

    def add_client_draw(self, callback):
        self._client_callbacks.append(callback)
        if self._client_node is not None:
            cw, ch = self._client_node.rect[2], self._client_node.rect[3]
            self._client_node.add_child(DrawNode((0, 0, cw, ch),
                draw_fn=lambda ctx, cr, _cb=callback: _cb(ctx, cr),
                name='user_cb'))
        self._dirty = True

    def remove_client_draw(self, callback):
        if callback in self._client_callbacks:
            self._client_callbacks.remove(callback)
        self._dirty = True

    def get_client_rect(self):
        """返回客户区矩形 (x, y, w, h)，窗口绝对坐标。"""
        if self._skin is None or not self._skin._loaded:
            return (0, 0, self._width, self._height)
        dims = self._skin.get_border_dims(self._window_type, self._state_name)
        if not dims:
            return (0, 0, self._width, self._height)
        b_left = dims['border_left']
        b_right = dims['border_right']
        b_top = dims['title_h']
        b_bottom = dims['border_bottom']
        bw = self._width - b_left - b_right
        menu_h = self._skin.get_menu_bar_height()
        client_top = b_top + (menu_h if menu_h > 0 and self._menubar and self._menubar._items else 0)
        tb_h = self._toolbar_height()
        if tb_h > 0 and self._toolbar and self._toolbar._items:
            client_top += tb_h
        client_h = self._height - dims['border_bottom'] - client_top
        sb_h = STATUSBAR_HEIGHT
        if self._statusbar is not None and self._statusbar._items and client_h > sb_h:
            client_h -= sb_h
        return (b_left, client_top, bw, max(0, client_h))

    def set_menu_click_handler(self, handler):
        self._menu_click_handler = handler

    def popup_menu(self, items, screen_pos=None):
        if self._active_menu is not None:
            try:
                self._active_menu.dismiss()
            except Exception:
                pass
            self._active_menu = None

        if screen_pos is None:
            pos = wx.GetMousePosition()
            screen_pos = (pos.x, pos.y)

        if self._skin is not None and self._skin._loaded:
            skin_ctx = SkinContext(self._skin)
            menu = SkinAwareContextMenu(self, skin_ctx, items=items)
        else:
            menu = D2DContextMenu(self, items=items)

        self._active_menu = menu

        def _on_menu_close(self_ref=menu):
            if self_ref is self._active_menu:
                self._active_menu = None

        menu._on_close = _on_menu_close
        menu.popup(screen_pos)
        return menu

    def set_context_menu(self, items):
        self._context_menu_items = items

    def register_d2d_control(self, control):
        if not isinstance(control, SheControl):
            raise TypeError(
                f"register_d2d_control requires a SheControl instance, "
                f"got {type(control).__name__}")
        if control not in self._d2d_controls:
            self._d2d_controls.append(control)
            self.add_client_draw(control.draw)
            if hasattr(control, 'set_parent_window'):
                control.set_parent_window(self)
            self._dirty = True

    def unregister_d2d_control(self, control):
        if control in self._d2d_controls:
            self._d2d_controls.remove(control)
            self.remove_client_draw(control.draw)