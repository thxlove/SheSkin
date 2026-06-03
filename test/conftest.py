"""全局测试配置 — 统一管理 wx.App 和 pyd2d factory 生命周期。"""
import os
import sys
import ctypes

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# COM 引用计数缓冲：多次 CoInitializeEx 防止 WICFactory.__dealloc__
# 中的 CoUninitialize 将 COM 引用计数归零导致所有 COM 对象失效。
_COM_INIT_COUNT = 8

# 保持 wx.App 引用，防止被垃圾回收
_wx_app = None


def pytest_configure(config):
    """在所有测试开始前，确保 wx.App 唯一实例已创建，并建立 COM 引用计数缓冲。"""
    global _wx_app

    # 建立 COM 引用计数缓冲
    ole32 = ctypes.windll.ole32
    for _ in range(_COM_INIT_COUNT):
        ole32.CoInitializeEx(None, 2)  # COINIT_APARTMENTTHREADED

    import wx
    _wx_app = wx.GetApp()
    if _wx_app is None:
        _wx_app = wx.App(False)

    # 预热 pyd2d factories，确保它们在 COM 环境有效时创建
    import pyd2d
    pyd2d.GetD2DFactory()
    pyd2d.GetWICFactory()
    pyd2d.GetDWriteFactory()


def pytest_unconfigure(config):
    """测试结束后释放 COM 引用计数缓冲。"""
    ole32 = ctypes.windll.ole32
    for _ in range(_COM_INIT_COUNT):
        ole32.CoUninitialize()
