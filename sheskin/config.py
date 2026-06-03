"""sheSkin 框架级配置常量。

所有硬编码默认值集中于此，避免散落在各模块中。
"""

BASE_DPI = 96.0
PT_TO_DIP = BASE_DPI / 72.0

DEFAULT_FONT_FAMILY = "Microsoft YaHei"
DEFAULT_FONT_SIZE_DIP = 13.0

CHECKBOX_BOX_SIZE = 16
CHECKBOX_TEXT_OFFSET = 6
CHECKBOX_BOX_LEFT_PAD = 2
CHECKBOX_CHECK_INSET = 3.0
CHECKBOX_TEXT_PADDING_RIGHT = 8

RADIO_BOX_SIZE = 16
RADIO_TEXT_OFFSET = 6
RADIO_BOX_LEFT_PAD = 2
RADIO_DOT_INSET = 4.5
RADIO_TEXT_PADDING_RIGHT = 8

GROUPBOX_TITLE_PAD_X = 8
GROUPBOX_TITLE_PAD_Y = 2
GROUPBOX_BORDER_RADIUS = 6.0
GROUPBOX_BORDER_WIDTH = 1.5

GROUPBOX_COLORS = {
    'normal': {
        'border': (0.55, 0.55, 0.58, 1.0),
        'text': (0.15, 0.15, 0.18, 1.0),
        'text_bg': (0.92, 0.92, 0.95, 1.0),
    },
    'disabled': {
        'border': (0.78, 0.78, 0.80, 1.0),
        'text': (0.65, 0.65, 0.68, 1.0),
        'text_bg': (0.92, 0.92, 0.95, 1.0),
    },
}

LABEL_TEXT_PADDING_X = 2
LABEL_TEXT_PADDING_Y = 4

MENUBAR_LEFT_PAD = 4
MENUBAR_ITEM_PAD = 16
MENUBAR_TEXT_X_OFFSET = 8

DEFAULT_TITLE_HEIGHT = 30
DEFAULT_BORDER_WIDTH = 4

BUTTON_TEXT_PADDING_X = 8
BUTTON_TEXT_PADDING_Y = 4

BUTTON_COLORS = {
    'normal': {
        'bg': (0.15, 0.56, 0.92, 1.0),
        'fg': (1.0, 1.0, 1.0, 1.0),
        'border': (0.11, 0.46, 0.76, 1.0),
    },
    'hover': {
        'bg': (0.18, 0.60, 0.96, 1.0),
        'fg': (1.0, 1.0, 1.0, 1.0),
        'border': (0.14, 0.50, 0.80, 1.0),
    },
    'pressed': {
        'bg': (0.10, 0.46, 0.78, 1.0),
        'fg': (1.0, 1.0, 1.0, 1.0),
        'border': (0.07, 0.38, 0.64, 1.0),
    },
    'disabled': {
        'bg': (0.75, 0.75, 0.78, 1.0),
        'fg': (0.55, 0.55, 0.55, 1.0),
        'border': (0.65, 0.65, 0.68, 1.0),
    },
}

CHECKBOX_COLORS = {
    'normal': {
        'box_bg': (0.96, 0.96, 0.98, 1.0),
        'box_border': (0.55, 0.55, 0.58, 1.0),
        'check': (0.0, 0.47, 0.84, 1.0),
        'text': (0.15, 0.15, 0.15, 1.0),
    },
    'hover': {
        'box_bg': (0.88, 0.94, 0.98, 1.0),
        'box_border': (0.18, 0.56, 0.92, 1.0),
        'check': (0.0, 0.47, 0.84, 1.0),
        'text': (0.15, 0.15, 0.15, 1.0),
    },
    'pressed': {
        'box_bg': (0.82, 0.88, 0.94, 1.0),
        'box_border': (0.11, 0.46, 0.76, 1.0),
        'check': (0.0, 0.47, 0.84, 1.0),
        'text': (0.15, 0.15, 0.15, 1.0),
    },
    'disabled': {
        'box_bg': (0.85, 0.85, 0.88, 1.0),
        'box_border': (0.65, 0.65, 0.68, 1.0),
        'check': (0.55, 0.55, 0.55, 1.0),
        'text': (0.55, 0.55, 0.55, 1.0),
    },
}

TOOLBAR_HEIGHT = 30

LABEL_COLORS = {
    'normal': {'text': (0.15, 0.15, 0.15, 1.0)},
    'disabled': {'text': (0.55, 0.55, 0.55, 1.0)},
}

RADIO_COLORS = {
    'normal': {
        'circle_bg': (0.96, 0.96, 0.98, 1.0),
        'circle_border': (0.55, 0.55, 0.58, 1.0),
        'dot': (0.0, 0.47, 0.84, 1.0),
        'text': (0.15, 0.15, 0.15, 1.0),
    },
    'hover': {
        'circle_bg': (0.88, 0.94, 0.98, 1.0),
        'circle_border': (0.18, 0.56, 0.92, 1.0),
        'dot': (0.0, 0.47, 0.84, 1.0),
        'text': (0.15, 0.15, 0.15, 1.0),
    },
    'pressed': {
        'circle_bg': (0.82, 0.88, 0.94, 1.0),
        'circle_border': (0.11, 0.46, 0.76, 1.0),
        'dot': (0.0, 0.47, 0.84, 1.0),
        'text': (0.15, 0.15, 0.15, 1.0),
    },
    'disabled': {
        'circle_bg': (0.85, 0.85, 0.88, 1.0),
        'circle_border': (0.65, 0.65, 0.68, 1.0),
        'dot': (0.55, 0.55, 0.55, 1.0),
        'text': (0.55, 0.55, 0.55, 1.0),
    },
}

SPINCTRL_BTN_SIZE = 20
SPINCTRL_TEXT_PAD = 4

SPINCTRL_COLORS = {
    'normal': {
        'btn_bg': (0.88, 0.88, 0.90, 1.0),
        'btn_fg': (0.15, 0.15, 0.18, 1.0),
        'btn_border': (0.65, 0.65, 0.68, 1.0),
        'text': (0.15, 0.15, 0.18, 1.0),
    },
    'hover': {
        'btn_bg': (0.82, 0.82, 0.85, 1.0),
        'btn_fg': (0.10, 0.10, 0.12, 1.0),
        'btn_border': (0.55, 0.55, 0.58, 1.0),
        'text': (0.15, 0.15, 0.18, 1.0),
    },
    'pressed': {
        'btn_bg': (0.75, 0.75, 0.78, 1.0),
        'btn_fg': (0.05, 0.05, 0.07, 1.0),
        'btn_border': (0.50, 0.50, 0.53, 1.0),
        'text': (0.15, 0.15, 0.18, 1.0),
    },
    'disabled': {
        'btn_bg': (0.92, 0.92, 0.93, 1.0),
        'btn_fg': (0.60, 0.60, 0.62, 1.0),
        'btn_border': (0.78, 0.78, 0.80, 1.0),
        'text': (0.55, 0.55, 0.55, 1.0),
    },
}

PROGRESS_BORDER_RADIUS = 4.0
PROGRESS_BORDER_WIDTH = 1.0

PROGRESS_COLORS = {
    'normal': {
        'track_bg': (0.88, 0.88, 0.90, 1.0),
        'track_border': (0.65, 0.65, 0.68, 1.0),
        'fill': (0.0, 0.47, 0.84, 1.0),
    },
    'disabled': {
        'track_bg': (0.92, 0.92, 0.93, 1.0),
        'track_border': (0.78, 0.78, 0.80, 1.0),
        'fill': (0.65, 0.65, 0.68, 1.0),
    },
}

STATUSBAR_HEIGHT = 24
STATUSBAR_ITEM_PAD_X = 8
STATUSBAR_ITEM_PAD_Y = 2
STATUSBAR_SEPARATOR_WIDTH = 2

STATUSBAR_COLORS = {
    'normal': {
        'bg': (0.90, 0.90, 0.92, 1.0),
        'item_bg': (0.88, 0.88, 0.90, 1.0),
        'item_border': (0.70, 0.70, 0.72, 1.0),
        'separator': (0.65, 0.65, 0.68, 1.0),
        'text': (0.15, 0.15, 0.18, 1.0),
    },
    'disabled': {
        'bg': (0.93, 0.93, 0.94, 1.0),
        'item_bg': (0.90, 0.90, 0.92, 1.0),
        'item_border': (0.78, 0.78, 0.80, 1.0),
        'separator': (0.78, 0.78, 0.80, 1.0),
        'text': (0.55, 0.55, 0.55, 1.0),
    },
}