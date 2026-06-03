"""窗体/控件块槽位布局。

包含控件布局定义和槽位映射。
所有数据自包含，无外部依赖。
"""

from collections import Counter

# ====================================================================
# 状态列表常量
# ====================================================================
BUTTON_STATES = ['normal', 'hover', 'pressed', 'disabled']
BUTTON5_STATES = ['normal', 'hover', 'default', 'pressed', 'disabled']
COMBOBOX4_STATES = ['normal', 'default', 'hover', 'disabled']
COMBOBOX5_STATES = ['normal', 'default', 'hover', 'pressed', 'disabled']
TABCTRL4_STATES = ['normal', 'default', 'pressed', 'disabled']
TABCTRL2_STATES = ['normal', 'disabled']
PROGRESS2_STATES = ['normal', 'disabled']
SPINCTRL4_STATES = ['normal', 'default', 'pressed', 'disabled']
TRACKBAR5_STATES = ['normal', 'default', 'hover', 'pressed', 'disabled']
TRACKBAR2_STATES = ['normal', 'disabled']
HEADERCTRL4_STATES = ['normal', 'default', 'pressed', 'disabled']
SCROLLBAR4_STATES = ['normal', 'default', 'pressed', 'disabled']
CHECKBOX5_STATES = ['normal', 'hover', 'default', 'pressed', 'disabled']
RADIOBUTTON5_STATES = ['normal', 'hover', 'default', 'pressed', 'disabled']

# ====================================================================
# 控件布局定义（原 parse_she_config 中的 _ITEMS 列表）
# ====================================================================

NORMAL_WINDOW_ITEMS = [
    {'name': 'TopBorder',    'name_cn': '上边框',   'states': ['active', 'inactive'], 'slot_start': 0},
    {'name': 'LeftBorder',   'name_cn': '左边框',   'states': ['active', 'inactive'], 'slot_start': 2},
    {'name': 'RightBorder',  'name_cn': '右边框',   'states': ['active', 'inactive'], 'slot_start': 4},
    {'name': 'BottomBorder', 'name_cn': '下边框',   'states': ['active', 'inactive'], 'slot_start': 6},
    {'name': 'CloseBtn',     'name_cn': '关闭按钮',   'states': ['normal', 'hover', 'pressed', 'disabled'], 'slot_start': 8},
    {'name': 'MaxBtn',       'name_cn': '最大化按钮', 'states': ['normal', 'hover', 'pressed', 'disabled'], 'slot_start': 12},
    {'name': 'RestoreBtn',   'name_cn': '还原按钮', 'states': ['normal', 'hover', 'pressed', 'disabled'], 'slot_start': 16},
    {'name': 'MinBtn',       'name_cn': '最小化按钮', 'states': ['normal', 'hover', 'pressed', 'disabled'], 'slot_start': 20},
    {'name': 'HelpBtn',      'name_cn': '帮助按钮',   'states': ['normal', 'hover', 'pressed', 'disabled'], 'slot_start': 24},
    {'name': 'TextInfo',     'name_cn': '其他信息',   'states': [],
     'properties': [
         {'name': 'text_color_n',  'name_cn': '文本颜色N',  'row': 0, 'col': 49},
         {'name': 'text_color_d',  'name_cn': '文本颜色D',  'row': 0, 'col': 50},
         {'name': 'text_area1_x',  'name_cn': '文本区域1X', 'row': 1, 'col': 37},
         {'name': 'text_area1_y',  'name_cn': '文本区域1Y', 'row': 1, 'col': 38},
         {'name': 'text_area2_x',  'name_cn': '文本区域2X', 'row': 1, 'col': 39},
         {'name': 'text_area2_y',  'name_cn': '文本区域2Y', 'row': 1, 'col': 40},
         {'name': 'text_align',    'name_cn': '文本对齐',   'row': 0, 'col': 2},
         {'name': 'text_fixed',    'name_cn': '文本固定',   'row': 0, 'col': 8},
         {'name': 'close_btn_x',   'name_cn': '关闭按钮X',  'row': 1, 'col': 25},
         {'name': 'close_btn_y',   'name_cn': '关闭按钮Y',  'row': 1, 'col': 26},
         {'name': 'max_btn_x',     'name_cn': '最大化按钮X', 'row': 1, 'col': 27},
         {'name': 'max_btn_y',     'name_cn': '最大化按钮Y', 'row': 1, 'col': 28},
         {'name': 'min_btn_x',     'name_cn': '最小化按钮X', 'row': 1, 'col': 29},
         {'name': 'min_btn_y',     'name_cn': '最小化按钮Y', 'row': 1, 'col': 30},
         {'name': 'help_btn_x',    'name_cn': '帮助按钮X',  'row': 1, 'col': 31},
         {'name': 'help_btn_y',    'name_cn': '帮助按钮Y',  'row': 1, 'col': 32},
         {'name': 'help_btn_fixed','name_cn': '帮助按钮固定', 'row': 0, 'col': 1},
         {'name': 'icon_x',        'name_cn': '图标X',      'row': 1, 'col': 33},
         {'name': 'icon_y',        'name_cn': '图标Y',      'row': 1, 'col': 34},
         {'name': 'icon_w',        'name_cn': '图标W',      'row': 1, 'col': 35},
         {'name': 'icon_h',        'name_cn': '图标H',      'row': 1, 'col': 36},
         {'name': 'font',          'name_cn': '字体',       'font_index': 0, 'type': 'LOGFONTW'},
     ]},
]

TOOL_WINDOW_ITEMS = [
    {'name': 'TopBorder',    'name_cn': '上边框',   'states': ['active', 'inactive'], 'slot_start': 28},
    {'name': 'LeftBorder',   'name_cn': '左边框',   'states': ['active', 'inactive'], 'slot_start': 30},
    {'name': 'RightBorder',  'name_cn': '右边框',   'states': ['active', 'inactive'], 'slot_start': 32},
    {'name': 'BottomBorder', 'name_cn': '下边框',   'states': ['active', 'inactive'], 'slot_start': 34},
    {'name': 'CloseBtn',     'name_cn': '关闭按钮',   'states': ['normal', 'hover', 'pressed', 'disabled'], 'slot_start': 36},
    {'name': 'TextInfo',     'name_cn': '其他信息',   'states': [],
     'properties': [
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 0, 'col': 51},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 0, 'col': 52},
         {'name': 'text_area1_x', 'name_cn': '文本区域1X', 'row': 1, 'col': 43},
         {'name': 'text_area1_y', 'name_cn': '文本区域1Y', 'row': 1, 'col': 44},
         {'name': 'text_area2_x', 'name_cn': '文本区域2X', 'row': 1, 'col': 45},
         {'name': 'text_area2_y', 'name_cn': '文本区域2Y', 'row': 1, 'col': 46},
         {'name': 'text_align',   'name_cn': '文本对齐',   'row': 0, 'col': 3},
         {'name': 'close_btn_x',  'name_cn': '关闭按钮X',  'row': 1, 'col': 41},
         {'name': 'close_btn_y',  'name_cn': '关闭按钮Y',  'row': 1, 'col': 42},
         {'name': 'font',         'name_cn': '字体',       'font_index': 1, 'type': 'LOGFONTW'},
     ]},
]

BORDER_WINDOW_ITEMS = [
    {'name': 'TopBorder',    'name_cn': '上边框',   'states': ['active', 'inactive'], 'slot_start': 40},
    {'name': 'LeftBorder',   'name_cn': '左边框',   'states': ['active', 'inactive'], 'slot_start': 42},
    {'name': 'RightBorder',  'name_cn': '右边框',   'states': ['active', 'inactive'], 'slot_start': 44},
    {'name': 'BottomBorder', 'name_cn': '下边框',   'states': ['active', 'inactive'], 'slot_start': 46},
]

WINDOWBG_ITEMS = [
    {'name': 'Background', 'name_cn': '背景', 'states': ['normal'], 'slot_start': 271},
]

MENUBAR_ITEMS = [
    {'name': 'Background',  'name_cn': '背景',       'states': ['normal'], 'slot_start': 48},
    {'name': 'MenuItem',    'name_cn': '菜单项',     'states': BUTTON_STATES, 'slot_start': 49},
    {'name': 'MDIClose',    'name_cn': 'MDI关闭项',  'states': BUTTON_STATES, 'slot_start': 53},
    {'name': 'MDIRestore',  'name_cn': 'MDI还原项',  'states': BUTTON_STATES, 'slot_start': 57},
    {'name': 'MDIMin',      'name_cn': 'MDI最小化项', 'states': BUTTON_STATES, 'slot_start': 61},
    {'name': 'TextInfo',    'name_cn': '其他信息',   'states': [],
     'properties': [
         {'name': 'height',       'name_cn': '高度',     'row': 0, 'col': 13},
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 1, 'col': 1},
         {'name': 'text_color_o', 'name_cn': '文本颜色O', 'row': 1, 'col': 2},
         {'name': 'text_color_s', 'name_cn': '文本颜色S', 'row': 1, 'col': 3},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 1, 'col': 4},
         {'name': 'font',         'name_cn': '字体',     'font_index': 2, 'type': 'LOGFONTW'},
     ]},
]

GROUPBOX_ITEMS = [
    {'name': 'BorderBg',   'name_cn': '边框背景', 'states': ['normal', 'disabled'], 'slot_start': 101},
    {'name': 'TextBg',     'name_cn': '文本背景', 'states': ['normal', 'disabled'], 'slot_start': 103},
    {'name': 'TextInfo',   'name_cn': '文本信息', 'states': [],
     'properties': [
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 0, 'col': 53},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 0, 'col': 54},
         {'name': 'font',         'name_cn': '字体',       'font_index': 7, 'type': 'LOGFONTW'},
     ]},
]

LABEL_ITEMS = [
    {'name': 'TextInfo',   'name_cn': '文本信息', 'states': [],
     'properties': [
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 1, 'col': 22},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 1, 'col': 23},
         {'name': 'font',         'name_cn': '字体',       'font_index': 12, 'type': 'LOGFONTW'},
     ]},
]

PUSHBUTTON_ITEMS = [
    {'name': 'Button',     'name_cn': '按钮',     'states': BUTTON5_STATES, 'slot_start': 71},
    {'name': 'TextInfo',   'name_cn': '文本信息', 'states': [],
     'properties': [
         {'name': 'text_color_n',  'name_cn': '文本颜色N',  'row': 0, 'col': 30},
         {'name': 'text_color_o',  'name_cn': '文本颜色O',  'row': 0, 'col': 31},
         {'name': 'text_color_h',  'name_cn': '文本颜色H',  'row': 0, 'col': 32},
         {'name': 'text_color_s',  'name_cn': '文本颜色S',  'row': 0, 'col': 33},
         {'name': 'text_color_d',  'name_cn': '文本颜色D',  'row': 0, 'col': 34},
         {'name': 'text_offset_s_x', 'name_cn': '文本偏移SX', 'row': 1, 'col': 53},
         {'name': 'text_offset_s_y', 'name_cn': '文本偏移SY', 'row': 1, 'col': 54},
         {'name': 'font',          'name_cn': '字体',       'font_index': 4, 'type': 'LOGFONTW'},
     ]},
]

CHECKBOX_ITEMS = [
    {'name': 'Unchecked',  'name_cn': '未选型',   'states': CHECKBOX5_STATES, 'slot_start': 76},
    {'name': 'Checked',    'name_cn': '选中型',   'states': CHECKBOX5_STATES, 'slot_start': 81},
    {'name': 'ThirdState', 'name_cn': '第三型',   'states': CHECKBOX5_STATES, 'slot_start': 86},
    {'name': 'TextInfo',   'name_cn': '文本信息', 'states': [],
     'properties': [
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 0, 'col': 25},
         {'name': 'text_color_o', 'name_cn': '文本颜色O', 'row': 0, 'col': 26},
         {'name': 'text_color_h', 'name_cn': '文本颜色H', 'row': 0, 'col': 27},
         {'name': 'text_color_s', 'name_cn': '文本颜色S', 'row': 0, 'col': 28},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 0, 'col': 29},
         {'name': 'font',         'name_cn': '字体',       'font_index': 5, 'type': 'LOGFONTW'},
     ]},
]

RADIOBUTTON_ITEMS = [
    {'name': 'Unchecked',  'name_cn': '未选型',   'states': RADIOBUTTON5_STATES, 'slot_start': 91},
    {'name': 'Checked',    'name_cn': '选中型',   'states': RADIOBUTTON5_STATES, 'slot_start': 96},
    {'name': 'TextInfo',   'name_cn': '文本信息', 'states': [],
     'properties': [
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 0, 'col': 35},
         {'name': 'text_color_o', 'name_cn': '文本颜色O', 'row': 0, 'col': 36},
         {'name': 'text_color_h', 'name_cn': '文本颜色H', 'row': 0, 'col': 37},
         {'name': 'text_color_s', 'name_cn': '文本颜色S', 'row': 0, 'col': 38},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 0, 'col': 39},
         {'name': 'font',         'name_cn': '字体',       'font_index': 6, 'type': 'LOGFONTW'},
     ]},
]

COMBOBOX_ITEMS = [
    {'name': 'DropDown',  'name_cn': '下拉按钮', 'states': COMBOBOX5_STATES, 'slot_start': 214},
    {'name': 'TextInfo',  'name_cn': '其他信息', 'states': [],
     'properties': [
         {'name': 'btn_zoom', 'name_cn': '按钮放大', 'row': 0, 'col': 20},
     ]},
]

TABCTRL_ITEMS = [
    {'name': 'TopBtn',     'name_cn': '按钮', 'states': ['normal', 'default', 'pressed'], 'slot_start': 166, 'group_cn': '上部型'},
    {'name': 'TopBtn',     'name_cn': '按钮', 'states': ['disabled'], 'slot_start': 170, 'group_cn': '上部型'},
    {'name': 'TopBody',    'name_cn': '主块', 'states': TABCTRL2_STATES, 'slot_start': 186, 'group_cn': '上部型'},
    {'name': 'BottomBtn',  'name_cn': '按钮', 'states': ['normal', 'default', 'pressed'], 'slot_start': 171, 'group_cn': '下部型'},
    {'name': 'BottomBtn',  'name_cn': '按钮', 'states': ['disabled'], 'slot_start': 175, 'group_cn': '下部型'},
    {'name': 'BottomBody', 'name_cn': '主块', 'states': TABCTRL2_STATES, 'slot_start': 188, 'group_cn': '下部型'},
    {'name': 'LeftBtn',    'name_cn': '按钮', 'states': ['normal', 'default', 'pressed'], 'slot_start': 176, 'group_cn': '左部型'},
    {'name': 'LeftBtn',    'name_cn': '按钮', 'states': ['disabled'], 'slot_start': 180, 'group_cn': '左部型'},
    {'name': 'LeftBody',   'name_cn': '主块', 'states': TABCTRL2_STATES, 'slot_start': 190, 'group_cn': '左部型'},
    {'name': 'RightBtn',   'name_cn': '按钮', 'states': ['normal', 'default', 'pressed'], 'slot_start': 181, 'group_cn': '右部型'},
    {'name': 'RightBtn',   'name_cn': '按钮', 'states': ['disabled'], 'slot_start': 185, 'group_cn': '右部型'},
    {'name': 'RightBody',  'name_cn': '主块', 'states': TABCTRL2_STATES, 'slot_start': 192, 'group_cn': '右部型'},
    {'name': 'TextInfo',   'name_cn': '文本信息', 'states': [],
     'properties': [
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 1, 'col': 9},
         {'name': 'text_color_o', 'name_cn': '文本颜色O', 'row': 1, 'col': 10},
         {'name': 'text_color_h', 'name_cn': '文本颜色H', 'row': 1, 'col': 10},
         {'name': 'text_color_s', 'name_cn': '文本颜色S', 'row': 1, 'col': 12},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 1, 'col': 13},
         {'name': 'font',         'name_cn': '字体',       'font_index': 11, 'type': 'LOGFONTW'},
     ]},
]

PROGRESS_ITEMS = [
    {'name': 'HBackground', 'name_cn': '背景', 'states': PROGRESS2_STATES, 'slot_start': 154, 'group_cn': '水平进度条'},
    {'name': 'HForeground', 'name_cn': '前景', 'states': PROGRESS2_STATES, 'slot_start': 156, 'group_cn': '水平进度条'},
    {'name': 'VBackground', 'name_cn': '背景', 'states': PROGRESS2_STATES, 'slot_start': 160, 'group_cn': '垂直进度条'},
    {'name': 'VForeground', 'name_cn': '前景', 'states': PROGRESS2_STATES, 'slot_start': 162, 'group_cn': '垂直进度条'},
]

SPINCTRL_ITEMS = [
    {'name': 'HLeftBtn',   'name_cn': '左部按钮', 'states': SPINCTRL4_STATES, 'slot_start': 202, 'group_cn': '水平调节器'},
    {'name': 'HRightBtn',  'name_cn': '右部按钮', 'states': SPINCTRL4_STATES, 'slot_start': 206, 'group_cn': '水平调节器'},
    {'name': 'VTopBtn',    'name_cn': '上部按钮', 'states': SPINCTRL4_STATES, 'slot_start': 194, 'group_cn': '垂直调节器'},
    {'name': 'VBottomBtn', 'name_cn': '下部按钮', 'states': SPINCTRL4_STATES, 'slot_start': 198, 'group_cn': '垂直调节器'},
]

TRACKBAR_ITEMS = [
    {'name': 'HSquareBtn', 'name_cn': '方型按钮', 'states': TRACKBAR5_STATES, 'slot_start': 219, 'group_cn': '水平滑块条'},
    {'name': 'HUpBtn',     'name_cn': '上型按钮', 'states': TRACKBAR5_STATES, 'slot_start': 224, 'group_cn': '水平滑块条'},
    {'name': 'HDownBtn',   'name_cn': '下型按钮', 'states': TRACKBAR5_STATES, 'slot_start': 229, 'group_cn': '水平滑块条'},
    {'name': 'HTrack',     'name_cn': '水平滑条', 'states': TRACKBAR2_STATES, 'slot_start': 251, 'group_cn': '水平滑块条'},
    {'name': 'VSquareBtn', 'name_cn': '方型按钮', 'states': TRACKBAR5_STATES, 'slot_start': 234, 'group_cn': '垂直滑块条'},
    {'name': 'VLeftBtn',   'name_cn': '左型按钮', 'states': TRACKBAR5_STATES, 'slot_start': 239, 'group_cn': '垂直滑块条'},
    {'name': 'VRightBtn',  'name_cn': '右型按钮', 'states': TRACKBAR5_STATES, 'slot_start': 244, 'group_cn': '垂直滑块条'},
    {'name': 'VTrack',     'name_cn': '垂直滑条', 'states': TRACKBAR2_STATES, 'slot_start': 249, 'group_cn': '垂直滑块条'},
]

HEADERCTRL_ITEMS = [
    {'name': 'Button',   'name_cn': '按钮', 'states': HEADERCTRL4_STATES, 'slot_start': 150},
    {'name': 'TextInfo', 'name_cn': '文本信息', 'states': [],
     'properties': [
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 0, 'col': 57},
         {'name': 'text_color_o', 'name_cn': '文本颜色O', 'row': 0, 'col': 58},
         {'name': 'text_color_s', 'name_cn': '文本颜色S', 'row': 0, 'col': 59},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 0, 'col': 60},
         {'name': 'font',         'name_cn': '字体',       'font_index': 10, 'type': 'LOGFONTW'},
     ]},
]

REBAR_ITEMS = [
    {'name': 'HGrip', 'name_cn': '水平把手', 'states': ['normal'], 'slot_start': 300},
    {'name': 'VGrip', 'name_cn': '垂直把手', 'states': ['normal'], 'slot_start': 301},
]

TOOLBAR_ITEMS = [
    {'name': 'HBackground', 'name_cn': '水平', 'states': ['normal'], 'slot_start': 266, 'group_cn': '背景'},
    {'name': 'VBackground', 'name_cn': '垂直', 'states': ['normal'], 'slot_start': 105, 'group_cn': '背景'},
    {'name': 'Button',      'name_cn': '按钮', 'states': TABCTRL4_STATES, 'slot_start': 106},
    {'name': 'HSeparator',  'name_cn': '水平', 'states': ['normal'], 'slot_start': 111, 'group_cn': '分割条'},
    {'name': 'VSeparator',  'name_cn': '垂直', 'states': ['normal'], 'slot_start': 110, 'group_cn': '分割条'},
    {'name': 'TextInfo',    'name_cn': '文本信息', 'states': [],
     'properties': [
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 1, 'col': 14},
         {'name': 'text_color_o', 'name_cn': '文本颜色O', 'row': 1, 'col': 15},
         {'name': 'text_color_s', 'name_cn': '文本颜色S', 'row': 1, 'col': 16},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 1, 'col': 17},
         {'name': 'font',         'name_cn': '字体',       'font_index': 8, 'type': 'LOGFONTW'},
     ]},
]

STATUSBAR_ITEMS = [
    {'name': 'Background', 'name_cn': '背景',   'states': ['normal'], 'slot_start': 112},
    {'name': 'Item',       'name_cn': '项目',   'states': TABCTRL2_STATES, 'slot_start': 114},
    {'name': 'Separator',  'name_cn': '分割条', 'states': ['normal'], 'slot_start': 113},
    {'name': 'TextInfo',   'name_cn': '文本信息', 'states': [],
     'properties': [
         {'name': 'text_color_n', 'name_cn': '文本颜色N', 'row': 1, 'col': 7},
         {'name': 'text_color_d', 'name_cn': '文本颜色D', 'row': 1, 'col': 8},
         {'name': 'font',         'name_cn': '字体',       'font_index': 9, 'type': 'LOGFONTW'},
     ]},
]

MENU_ITEMS = [
    {'name': 'Background', 'name_cn': '背景',   'states': ['normal'], 'slot_start': 65},
    {'name': 'Separator',  'name_cn': '分割条', 'states': ['normal'], 'slot_start': 66},
    {'name': 'MenuItem',   'name_cn': '菜单项', 'states': TABCTRL4_STATES, 'slot_start': 67},
    {'name': 'TextInfo',   'name_cn': '其他信息', 'states': [],
     'properties': [
         {'name': 'item_height',       'name_cn': '项目高度',         'row': 0, 'col': 7},
         {'name': 'text_color_n',      'name_cn': '文本颜色N',        'row': 0, 'col': 61},
         {'name': 'text_color_o',      'name_cn': '文本颜色O',        'row': 0, 'col': 62},
         {'name': 'text_color_s',      'name_cn': '文本颜色S',        'row': 0, 'col': 63},
         {'name': 'text_color_d',      'name_cn': '文本颜色D',        'row': 1, 'col': 0},
         {'name': 'text_left_margin',  'name_cn': '文本左边距离',     'row': 0, 'col': 11},
         {'name': 'sep_height',        'name_cn': '分割条高度',       'row': 0, 'col': 8},
         {'name': 'sep_left_margin',   'name_cn': '分割条左边距离',   'row': 0, 'col': 12},
         {'name': 'img_left_margin',   'name_cn': '图片左边距离',     'row': 0, 'col': 10},
         {'name': 'submenu_icon_margin','name_cn': '子菜单图标左边距离', 'row': 0, 'col': 9},
         {'name': 'font',              'name_cn': '字体',              'font_index': 3, 'type': 'LOGFONTW'},
     ]},
]

DATETIME_ITEMS = [
    {'name': 'Button',   'name_cn': '按钮', 'states': ['normal', 'default'], 'slot_start': 261},
    {'name': 'Button',   'name_cn': '按钮', 'states':['pressed', 'disabled'], 'slot_start': 264},
    {'name': 'TextInfo', 'name_cn': '其他信息', 'states': [],
     'properties': [
         {'name': 'btn_zoom', 'name_cn': '按钮放大', 'row': 0, 'col': 21},
     ]},
]

DATECTRL_ITEMS = [
    {'name': 'LeftBtn',  'name_cn': '左部按钮', 'states': TABCTRL4_STATES, 'slot_start': 124},
    {'name': 'RightBtn', 'name_cn': '右部按钮', 'states': TABCTRL4_STATES, 'slot_start': 128},
    {'name': 'TextInfo', 'name_cn': '其他信息', 'states': [],
     'properties': [
         {'name': 'bg_color_n', 'name_cn': '背景色N', 'row': 1, 'col': 5},
         {'name': 'bg_color_d', 'name_cn': '背景色D', 'row': 1, 'col': 6},
     ]},
]

CTRLBORDER_ITEMS = [
    {'name': 'BaseInfo', 'name_cn': '基本信息', 'states': [],
     'properties': [
         {'name': 'draw_border', 'name_cn': '是否绘图',   'row': 0, 'col': 0},
         {'name': 'outer_color_n',     'name_cn': '外边框N',    'row': 0, 'col': 40},
         {'name': 'outer_color_o',     'name_cn': '外边框O',    'row': 0, 'col': 41},
         {'name': 'outer_color_h',     'name_cn': '外边框H',    'row': 0, 'col': 42},
         {'name': 'outer_color_d',     'name_cn': '外边框D',    'row': 0, 'col': 43},
         {'name': 'inner_color_n',     'name_cn': '内边框N',    'row': 0, 'col': 44},
         {'name': 'inner_color_o',     'name_cn': '内边框O',    'row': 0, 'col': 45},
         {'name': 'inner_color_h',     'name_cn': '内边框H',    'row': 0, 'col': 46},
         {'name': 'inner_color_d',     'name_cn': '内边框D',    'row': 0, 'col': 47},
         {'name': 'width_curve', 'name_cn': '宽度曲率',   'row': 0, 'col': 22},
         {'name': 'height_curve','name_cn': '高度曲率',   'row': 0, 'col': 23},
     ]},
    {'name': 'Normal',   'name_cn': '默认态', 'states': ['normal'], 'slot_start': 210},
    {'name': 'Default',  'name_cn': '预选态', 'states': ['default'], 'slot_start': 211},
    {'name': 'Hover',    'name_cn': '热点态', 'states': ['hover'], 'slot_start': 212},
    {'name': 'Disabled', 'name_cn': '失效态', 'states': ['disabled'], 'slot_start': 213},
]

SCROLLBAR_ITEMS = [
    {'name': 'VTopBtn',     'name_cn': '上部按钮', 'states': SCROLLBAR4_STATES, 'slot_start': 116, 'group_cn': '垂直滚动条'},
    {'name': 'VBottomBtn',  'name_cn': '下部按钮', 'states': SCROLLBAR4_STATES, 'slot_start': 120, 'group_cn': '垂直滚动条'},
    {'name': 'HLeftBtn',    'name_cn': '左部按钮', 'states': SCROLLBAR4_STATES, 'slot_start': 124, 'group_cn': '水平滚动条'},
    {'name': 'HRightBtn',   'name_cn': '右部按钮', 'states': SCROLLBAR4_STATES, 'slot_start': 128, 'group_cn': '水平滚动条'},
    {'name': 'VTrack',      'name_cn': '垂直滑槽', 'states': SCROLLBAR4_STATES, 'slot_start': 132, 'group_cn': '垂直滚动条'},
    {'name': 'HTrack',      'name_cn': '水平滑槽', 'states': SCROLLBAR4_STATES, 'slot_start': 136, 'group_cn': '水平滚动条'},
    {'name': 'VThumb',      'name_cn': '垂直滑块', 'states': SCROLLBAR4_STATES, 'slot_start': 140, 'group_cn': '垂直滚动条'},
    {'name': 'HThumb',      'name_cn': '水平滑块', 'states': SCROLLBAR4_STATES, 'slot_start': 144, 'group_cn': '水平滚动条'},
    {'name': 'SizeBoxLB',   'name_cn': '左下型',   'states': ['normal'], 'slot_start': 148},
    {'name': 'SizeBoxRB',   'name_cn': '右下型',   'states': ['normal'], 'slot_start': 149},
    {'name': 'SizeInfo',    'name_cn': '大小信息',  'states': [],
     'properties': [
         {'name': 'vert_btn_h',    'name_cn': '垂直按钮高',   'row': 0, 'col': 18},
         {'name': 'vert_thumb_max','name_cn': '垂直滑块最大', 'row': 0, 'col': 19},
         {'name': 'vert_bar_w',    'name_cn': '垂直栏宽',     'row': 0, 'col': 17},
         {'name': 'horz_btn_w',    'name_cn': '水平按钮宽',   'row': 0, 'col': 15},
         {'name': 'horz_thumb_max','name_cn': '水平滑块最大', 'row': 0, 'col': 16},
         {'name': 'horz_bar_h',    'name_cn': '水平栏高',     'row': 0, 'col': 14},
     ]},
]

# ====================================================================
# CONTROL_LAYOUTS — 控件类型 → 布局定义
# ====================================================================
CONTROL_LAYOUTS = {
    0: {
        'name': 'WINDOW',
        'name_cn': '窗体',
        'subcategories': [
            {'name': 'NormalWindow',  'name_cn': '普通窗体', 'children': NORMAL_WINDOW_ITEMS, 'slot_start': 0},
            {'name': 'ToolWindow',    'name_cn': '工具窗体', 'children': TOOL_WINDOW_ITEMS, 'slot_start': 28},
            {'name': 'BorderWindow',  'name_cn': '边框窗体', 'children': BORDER_WINDOW_ITEMS, 'slot_start': 40},
            {'name': 'MenuBar',       'name_cn': '菜单栏',   'children': MENUBAR_ITEMS, 'slot_start': 48},
            {'name': 'WindowBg',      'name_cn': '窗体背景', 'children': WINDOWBG_ITEMS, 'slot_start': 271},
        ],
    },
    20: {
        'name': 'PUSHBUTTON',
        'name_cn': '普通按钮',
        'subcategories': [
            {'name': 'PushButton', 'name_cn': '普通按钮', 'children': PUSHBUTTON_ITEMS, 'slot_start': 71},
        ],
    },
    21: {
        'name': 'RADIOBUTTON',
        'name_cn': '单选按钮',
        'subcategories': [
            {'name': 'RadioButton', 'name_cn': '单选按钮', 'children': RADIOBUTTON_ITEMS, 'slot_start': 91},
        ],
    },
    2: {
        'name': 'CHECKBOX',
        'name_cn': '选择按钮',
        'subcategories': [
            {'name': 'CheckBox', 'name_cn': '选择按钮', 'children': CHECKBOX_ITEMS, 'slot_start': 76},
        ],
    },
    8: {
        'name': 'GROUPBOX',
        'name_cn': '分组框',
        'subcategories': [
            {'name': 'GroupBox', 'name_cn': '分组框', 'children': GROUPBOX_ITEMS, 'slot_start': 101},
        ],
    },
    12: {
        'name': 'LABEL',
        'name_cn': '标签',
        'subcategories': [
            {'name': 'Label', 'name_cn': '标签', 'children': LABEL_ITEMS, 'slot_start': 66},
        ],
    },
    24: {
        'name': 'SCROLLBAR',
        'name_cn': '滚动条',
        'subcategories': [
            {'name': 'ScrollBar', 'name_cn': '滚动条', 'children': SCROLLBAR_ITEMS, 'slot_start': 116},
        ],
    },
    3: {
        'name': 'COMBOBOX',
        'name_cn': '组合框',
        'subcategories': [
            {'name': 'ComboBox', 'name_cn': '组合框', 'children': COMBOBOX_ITEMS, 'slot_start': 0},
        ],
    },
    28: {
        'name': 'TABCTRL',
        'name_cn': '选择夹',
        'subcategories': [
            {'name': 'TabCtrl', 'name_cn': '选择夹', 'children': TABCTRL_ITEMS, 'slot_start': 0},
        ],
    },
    19: {
        'name': 'PROGRESS',
        'name_cn': '进度条',
        'subcategories': [
            {'name': 'Progress', 'name_cn': '进度条', 'children': PROGRESS_ITEMS, 'slot_start': 0},
        ],
    },
    26: {
        'name': 'SPINCTRL',
        'name_cn': '调节器',
        'subcategories': [
            {'name': 'SpinCtrl', 'name_cn': '调节器', 'children': SPINCTRL_ITEMS, 'slot_start': 0},
        ],
    },
    31: {
        'name': 'TRACKBAR',
        'name_cn': '滑块条',
        'subcategories': [
            {'name': 'TrackBar', 'name_cn': '滑块条', 'children': TRACKBAR_ITEMS, 'slot_start': 0},
        ],
    },
    9: {
        'name': 'HEADERCTRL',
        'name_cn': '列表头',
        'subcategories': [
            {'name': 'HeaderCtrl', 'name_cn': '列表头', 'children': HEADERCTRL_ITEMS, 'slot_start': 0},
        ],
    },
    22: {
        'name': 'REBAR',
        'name_cn': 'Rebar',
        'subcategories': [
            {'name': 'Rebar', 'name_cn': 'Rebar', 'children': REBAR_ITEMS, 'slot_start': 0},
        ],
    },
    29: {
        'name': 'TOOLBAR',
        'name_cn': '工具栏',
        'subcategories': [
            {'name': 'ToolBar', 'name_cn': '工具栏', 'children': TOOLBAR_ITEMS, 'slot_start': 0},
        ],
    },
    27: {
        'name': 'STATUSBAR',
        'name_cn': '状态栏',
        'subcategories': [
            {'name': 'StatusBar', 'name_cn': '状态栏', 'children': STATUSBAR_ITEMS, 'slot_start': 0},
        ],
    },
    16: {
        'name': 'MENU',
        'name_cn': '菜单',
        'subcategories': [
            {'name': 'Menu', 'name_cn': '菜单', 'children': MENU_ITEMS, 'slot_start': 0},
        ],
    },
    6: {
        'name': 'DATETIME',
        'name_cn': '时间控件',
        'subcategories': [
            {'name': 'DateTime', 'name_cn': '时间控件', 'children': DATETIME_ITEMS, 'slot_start': 0},
        ],
    },
    17: {
        'name': 'DATECTRL',
        'name_cn': '日期控件',
        'subcategories': [
            {'name': 'DateCtrl', 'name_cn': '日期控件', 'children': DATECTRL_ITEMS, 'slot_start': 0},
        ],
    },
    36: {
        'name': 'CTRLBORDER',
        'name_cn': '控件边框',
        'subcategories': [
            {'name': 'CtrlBorder', 'name_cn': '控件边框', 'children': CTRLBORDER_ITEMS, 'slot_start': 0},
        ],
    },
}

# ====================================================================
# 回退默认值
# ====================================================================
DEFAULTS = {
    'text_color_n':       (0, 0, 80),
    'text_color_d':       (128, 128, 128),
    'text_color_h':       (0, 0, 0),
    'text_color_s':       (0, 0, 0),
    'text_color_o':       (0, 0, 0),
    'bg_color_n':         (255, 255, 255),
    'bg_color_d':         (240, 240, 240),
    'outer_color_n':      (0, 0, 0),
    'outer_color_o':      (0, 0, 0),
    'outer_color_h':      (0, 0, 0),
    'outer_color_d':      (0, 0, 0),
    'inner_color_n':      (0, 0, 0),
    'inner_color_o':      (0, 0, 0),
    'inner_color_h':      (0, 0, 0),
    'inner_color_d':      (0, 0, 0),
    'font_height':        -9,
    'icon_pad':            2,
    'icon_w':             16,
    'icon_h':             16,
    'icon_x':              4,
    'icon_y':              4,
    'icon_text_gap':       4,
    'text_align':         'center',
    'text_fixed':          0,
    'text_area1_x':        0,
    'text_area1_y':        0,
    'text_area2_x':        0,
    'text_area2_y':        0,
    'text_offset_s_x':     0,
    'text_offset_s_y':     0,
    'text_left_margin':    4,
    'img_left_margin':     4,
    'submenu_icon_margin': 4,
    'sep_left_margin':     4,
    'btn_gap':             1,
    'btn_size':           16,
    'btn_zoom':            0,
    'menu_height':        24,
    'item_height':        24,
    'sep_height':          6,
    'draw_border':         1,
    'width_curve':         0,
    'height_curve':        0,
    'vert_btn_h':         16,
    'vert_thumb_max':    100,
    'vert_bar_w':         16,
    'horz_btn_w':         16,
    'horz_thumb_max':    100,
    'horz_bar_h':         16,
    'help_btn_fixed':      0,
}

# ====================================================================
# 状态名 → 槽位索引偏移
# ====================================================================
STATE_MAP = {
    'normal': 0,
    'hover': 3,
    'pressed': 2,
    'disabled': 4,
}

# ====================================================================
# 位图解码标志
# ====================================================================
CHANNEL_ORDER = 'BGR'
FLIP_ROWS = True
CK_AS_BGR = False

CHANNEL_ORDERS_MAP = {
    'BGR': (2, 1, 0),
    'RGB': (0, 1, 2),
}

# ====================================================================
# 槽位生成器
# ====================================================================

_KEY_MAP = {
    'TopBorder':       'top',
    'LeftBorder':      'left',
    'RightBorder':     'right',
    'BottomBorder':    'bottom',
    'CloseBtn':        'close',
    'MaxBtn':          'max',
    'RestoreBtn':      'restore',
    'MinBtn':          'min',
    'HelpBtn':         'help',
    'Background':      'bg',
    'HBackground':     'h_bg',
    'HForeground':     'h_fg',
    'VBackground':     'v_bg',
    'VForeground':     'v_fg',
    'MenuItem':        'item',
    'MDIClose':        'mdi_close',
    'MDIRestore':      'mdi_restore',
    'MDIMin':          'mdi_min',
    'Button':          'button',
    'Unchecked':       'unchecked',
    'Checked':         'checked',
    'ThirdState':      'third',
    'BorderBg':        'border_bg',
    'TextBg':          'text_bg',
    'DropDown':        'dropdown',
    'VTopBtn':         'v_top',
    'VBottomBtn':      'v_bottom',
    'HLeftBtn':        'h_left',
    'HRightBtn':       'h_right',
    'VTrack':          'v_track',
    'HTrack':          'h_track',
    'VThumb':          'v_thumb',
    'HThumb':          'h_thumb',
    'SizeBoxLB':       'size_lb',
    'SizeBoxRB':       'size_rb',
    'HSquareBtn':      'h_square',
    'HUpBtn':          'h_up',
    'HDownBtn':        'h_down',
    'VSquareBtn':      'v_square',
    'VLeftBtn':        'v_left',
    'VRightBtn':       'v_right',
    'HSeparator':      'h_sep',
    'VSeparator':      'v_sep',
    'Separator':       'separator',
    'HGrip':           'h_grip',
    'VGrip':           'v_grip',
    'TopBtn':          'top_btn',
    'BottomBtn':       'bottom_btn',
    'LeftBtn':         'left_btn',
    'RightBtn':        'right_btn',
    'TopBody':         'top_body',
    'BottomBody':      'bottom_body',
    'LeftBody':        'left_body',
    'RightBody':       'right_body',
    'Normal':          'normal',
    'Default':         'default',
    'Hover':           'hover',
    'Disabled':        'disabled',
    'Item':            'item',
}


def _key_for(item, used_counts):
    name = item['name']
    base = _KEY_MAP.get(name)
    if base is None:
        return name.lower()
    states = item.get('states', [])
    if used_counts > 1 and len(states) == 1 and states[0] == 'disabled':
        return base + '_disabled'
    if used_counts > 1 and name == 'Button' and base == 'button':
        first = states[0] if states else ''
        if first == 'normal':
            return base + '_n'
        if first == 'pressed':
            return base + '_pd'
    return base


def _extract_props(children):
    props = {}
    for child in children:
        if child['name'] not in ('TextInfo', 'BaseInfo', 'SizeInfo'):
            continue
        for prop in child.get('properties', []):
            entry = {}
            if 'row' in prop:
                entry['row'] = prop['row']
                entry['col'] = prop['col']
            if 'font_index' in prop:
                entry['font_index'] = prop['font_index']
                entry['type'] = prop.get('type')
            entry['default'] = DEFAULTS.get(prop['name'])
            props[prop['name']] = entry
    return props


def _collect_states(children):
    seen = set()
    result = []
    for child in children:
        if child['name'] in ('TextInfo', 'BaseInfo', 'SizeInfo'):
            continue
        for s in child.get('states', []):
            if s not in seen:
                seen.add(s)
                result.append(s)
    return result


def _build_slots(children):
    name_counts = Counter(c['name'] for c in children if c['name'] not in ('TextInfo', 'BaseInfo', 'SizeInfo'))
    slots = {}
    for child in children:
        if child['name'] in ('TextInfo', 'BaseInfo', 'SizeInfo'):
            continue
        key = _key_for(child, name_counts.get(child['name'], 1))
        states = child.get('states', [])
        slots[key] = {
            state: child['slot_start'] + i
            for i, state in enumerate(states)
        }
    return slots, _extract_props(children)


def _build_control_slots():
    result = {}
    bg_slot = None

    wc = CONTROL_LAYOUTS.get(0)
    if wc:
        for sub in wc.get('subcategories', []):
            if sub['name'] == 'WindowBg' and sub.get('children'):
                bg_slot = sub['children'][0]['slot_start']
                break

    for ctrl_type, layout in CONTROL_LAYOUTS.items():
        if not layout:
            continue
        for sub in layout.get('subcategories', []):
            sname = sub['name']
            if sname == 'WindowBg':
                continue
            children = sub.get('children', [])
            slots, props = _build_slots(children)
            entry = {
                'ctrl_type': ctrl_type,
                'subcat': sname,
            }
            entry.update(slots)
            entry['states'] = _collect_states(children)
            if props:
                entry['properties'] = props
            if ctrl_type == 0 and sname in ('NormalWindow', 'ToolWindow', 'BorderWindow'):
                if bg_slot is not None:
                    entry['bg'] = {'normal': bg_slot}
            result[sname] = entry
    return result


CONTROL_SLOTS = _build_control_slots()
