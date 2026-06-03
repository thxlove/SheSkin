"""共享工具 — EditBox / TextBox 共用的常量、颜色、剪贴板、光标闪烁。"""
import wx

TEXT_PAD_X = 4
TEXT_PAD_Y = 3
CARET_WIDTH = 1.0
CARET_BLINK_MS = 500

EDIT_COLORS = {
    'normal': {
        'bg': (1.0, 1.0, 1.0, 1.0),
        'text': (0.0, 0.0, 0.0, 1.0),
        'sel_bg': (0.0, 0.47, 0.84, 1.0),
        'sel_text': (1.0, 1.0, 1.0, 1.0),
        'caret': (0.0, 0.0, 0.0, 1.0),
    },
    'focused': {
        'bg': (1.0, 1.0, 1.0, 1.0),
        'text': (0.0, 0.0, 0.0, 1.0),
        'sel_bg': (0.0, 0.47, 0.84, 1.0),
        'sel_text': (1.0, 1.0, 1.0, 1.0),
        'caret': (0.0, 0.0, 0.0, 1.0),
    },
    'readonly': {
        'bg': (0.94, 0.94, 0.95, 1.0),
        'text': (0.0, 0.0, 0.0, 1.0),
        'sel_bg': (0.0, 0.47, 0.84, 1.0),
        'sel_text': (1.0, 1.0, 1.0, 1.0),
        'caret': (0.0, 0.0, 0.0, 1.0),
    },
    'disabled': {
        'bg': (0.96, 0.96, 0.97, 1.0),
        'text': (0.55, 0.55, 0.58, 1.0),
        'sel_bg': (0.70, 0.70, 0.73, 1.0),
        'sel_text': (1.0, 1.0, 1.0, 1.0),
        'caret': (0.55, 0.55, 0.58, 1.0),
    },
}


def clipboard_copy(text):
    try:
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            return True
    except Exception:
        pass
    return False


def clipboard_paste():
    try:
        if wx.TheClipboard.Open():
            data = wx.TextDataObject()
            if wx.TheClipboard.GetData(data):
                wx.TheClipboard.Close()
                return data.GetText().replace('\r\n', '\n').replace('\r', '\n')
            wx.TheClipboard.Close()
    except Exception:
        pass
    return None


def get_shift_from_mouse():
    try:
        mods = wx.GetMouseState().GetModifiers()
        return bool(mods & wx.MOD_SHIFT)
    except Exception:
        return False


def resolve_edit_colors(focused, readonly, disabled, state):
    if disabled:
        return EDIT_COLORS['disabled']
    if readonly:
        return EDIT_COLORS['readonly']
    if focused:
        return EDIT_COLORS['focused']
    return EDIT_COLORS['normal']
