# pyd2d API 参考文档

---

## 目录

1. [模块入口函数](#1-模块入口函数)
2. [COMObject（COM 对象基类）](#2-comobject)
3. [D2DFactory（Direct2D 工厂）](#3-d2dfactory)
4. [RenderTarget（渲染目标）](#4-rendertarget)
5. [HWNDRenderTarget](#5-hwndrendertarget)
6. [DCRenderTarget](#6-dcrendertarget)
7. [BitmapRenderTarget](#7-bitmaprendertarget)
8. [Brush 系列](#8-brush-系列)
9. [Geometry 系列](#9-geometry-系列)
10. [Bitmap / Image](#10-bitmap--image)
11. [Layer / StrokeStyle / DrawingStateBlock](#11-layer--strokestyle--drawingstateblock)
12. [WICFactory（WIC 图像工厂）](#12-wicfactory)
13. [WICBitmap 系列](#13-wicbitmap-系列)
14. [DWriteFactory（DirectWrite 工厂）](#14-dwritefactory)
15. [FontCollection / FontFamily / DWriteFont / FontFace / LocalizedStrings](#15-fontcollection--fontfamily--dwritefont--fontface--localizedstrings)
16. [TextFormat / TextLayout](#16-textformat--textlayout)
17. [数据结构类](#17-数据结构类)
18. [错误与异常类](#18-错误与异常类)
19. [常量枚举](#19-常量枚举)
20. [内置工具函数](#20-内置工具函数)
21. [类继承层次](#21-类继承层次)

---

## 1. 模块入口函数

### `InitializeCOM(options=0)`
初始化 COM 运行时。首次使用任何 pyd2d 功能前必须调用。
- `options`: COM 初始化标志，默认 0（`COINIT_APARTMENTTHREADED`），传 2 为 `COINIT_MULTITHREADED`
- 若已初始化则静默返回
- 注意: `GetD2DFactory`/`GetDWriteFactory`/`GetWICFactory` 内部会自动处理初始化

### `UninitializeCOM()`
卸载 COM 运行时。应用程序退出前调用。

### `GetD2DFactory() -> D2DFactory`
获取全局单例 `D2DFactory`。首次调用时自动创建。内部存储在模块变量 `_d2d_factory`。

### `GetWICFactory() -> WICFactory`
获取全局单例 `WICFactory`。首次调用时自动创建。内部存储在模块变量 `_wic_factory`。

> **注意**: `WICFactory.__init__` 内部调用 `CoInitializeEx(NULL, 2)`，`__dealloc__` 调用 `CoUninitialize()`。
> 在测试环境中，多次创建/销毁 WICFactory 会减少 COM 引用计数，可能导致后续工厂初始化失败。
> 建议始终使用 `GetWICFactory()` 获取全局单例，避免手动创建。

### `GetDWriteFactory() -> DWriteFactory`
获取全局单例 `DWriteFactory`。首次调用时自动创建。内部存储在模块变量 `_dwrite_factory`。

---

## 2. COMObject

所有 COM 对象的基类，管理底层 COM 指针的生命周期。不可直接实例化（`__init__` 抛出 `TypeError`）。

### `Release()`
释放底层 COM 对象。调用后对象不可再使用。对象被 Python GC 回收时会自动调用 `__dealloc__` → `Release()`。

---

## 3. D2DFactory

继承 `COMObject`。Direct2D 工厂，负责创建渲染目标、几何图形、画笔样式。

### `D2DFactory(factoryType=0, debugLevel=0)`
- `factoryType`: `D2D_FACTORY_TYPE` 枚举值
  - `0` (`SINGLE_THREADED`)
  - `1` (`MULTI_THREADED`)
- `debugLevel`: `DEBUG_LEVEL` 枚举值
  - `0` (`NONE`), `1` (`ERROR`), `2` (`WARNING`), `3` (`INFORMATION`)

### `CreateHwndRenderTarget(hwnd, width, height, ...) -> HWNDRenderTarget`
创建窗口绑定的渲染目标。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `hwnd` | `int` | — | 窗口句柄 |
| `width` | `int` | — | 宽度（像素） |
| `height` | `int` | — | 高度（像素） |
| `presentOptions` | `int` | `0` | `PRESENT_OPTIONS.NONE` / `RETAIN_CONTENTS` / `IMMEDIATELY` |
| `rtType` | `int` | `0` | `RENDER_TARGET_TYPE.DEFAULT` / `SOFTWARE` / `HARDWARE` |
| `pixelFormat` | `int` | `0` | `DXGI_FORMAT` 值 |
| `alphaMode` | `int` | `0` | `ALPHA_MODE.UNKNOWN` / `PREMULTIPLIED` / `STRAIGHT` / `IGNORE` |
| `dpiX` | `float` | `0` | 水平 DPI |
| `dpiY` | `float` | `0` | 垂直 DPI |
| `usage` | `int` | `0` | `RENDER_TARGET_USAGE` |
| `featureLevel` | `int` | `0` | `FEATURE_LEVEL.DEFAULT` / `LEVEL_9` / `LEVEL_10` |

### `CreateDCRenderTarget(rtType=0, pixelFormat=0, alphaMode=0, dpiX=0, dpiY=0, usage=0, featureLevel=0) -> DCRenderTarget`
创建设备上下文绑定的渲染目标。sheSkin 框架使用此模式配合 DIBSection 做离屏渲染。

### `CreateWicBitmapRenderTarget(target, rtType=0, pixelFormat=0, alphaMode=0, dpiX=0, dpiY=0) -> RenderTarget`
创建绑定到 WIC Bitmap 的渲染目标（用于位图离屏渲染）。
- `target`: `WICBitmap` 对象

### `CreatePathGeometry() -> PathGeometry`
创建一个空的 `PathGeometry` 对象，可通过 `Open()` 获得 `GeometrySink` 构建几何图形。

### `CreateStrokeStyle(startCap=0, endCap=0, dashCap=0, lineJoin=0, miterLimit=10.0, dashStyle=0, dashOffset=0.0) -> StrokeStyle`
创建线条描边样式。

| 参数 | 枚举值 |
|------|--------|
| `startCap` | `CAP_STYLE`: `FLAT`(0), `SQUARE`(1), `ROUND`(2), `TRIANGLE`(3) |
| `endCap` | 同上 |
| `dashCap` | 同上 |
| `lineJoin` | `LINE_JOIN`: `MITER`(0), `BEVEL`(1), `ROUND`(2), `MITER_OR_BEVEL`(3) |
| `dashStyle` | `DASH_STYLE`: `SOLID`(0), `DASH`(1), `DOT`(2), `DASH_DOT`(3), `DASH_DOT_DOT`(4), `CUSTOM`(5) |

### `CreateDrawingStateBlock(antialiasMode=0, textAntialiasMode=0, tag1=0, tag2=0, transform_m11=1.0, transform_m12=0.0, transform_m21=0.0, transform_m22=1.0, transform_dx=0.0, transform_dy=0.0) -> DrawingStateBlock`
创建绘制状态块。用于 `rt.SaveDrawingState` / `rt.RestoreDrawingState` 保存/恢复 clip、transform、antialias 状态。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `antialiasMode` | `int` | `0` | `ANTIALIAS_MODE.PER_PRIMITIVE` / `ALIASED` |
| `textAntialiasMode` | `int` | `0` | `TEXT_ANTIALIAS_MODE.DEFAULT` / `CLEARTYPE` / `GRAYSCALE` / `ALIASED` |
| `tag1` | `int` | `0` | 调试标签 1 |
| `tag2` | `int` | `0` | 调试标签 2 |
| `transform_m11` ~ `transform_dy` | `float` | 单位矩阵 | 初始变换矩阵 6 个分量 |

---

## 4. RenderTarget

继承 `Resource` → `COMObject`。基础渲染目标（`HWNDRenderTarget`、`DCRenderTarget`、`BitmapRenderTarget` 的父类）。

### 绘制生命周期
```python
rt.BeginDraw()           # 开始帧
# ... 绘制命令 ...
rt.EndDraw()             # 结束帧
```

### 形状绘制

| 方法 | 签名 |
|------|------|
| `Clear(r, g, b, a=1.0)` | 清空渲染目标为纯色（r/g/b/a: 0.0 ~ 1.0） |
| `DrawLine(x1, y1, x2, y2, brush, strokeWidth=1.0, strokeStyle=None)` | 画线段 |
| `DrawRectangle(l, t, r, b, brush, strokeWidth=1.0, strokeStyle=None)` | 画矩形边框 |
| `FillRectangle(l, t, r, b, brush)` | 填充矩形 |
| `DrawRoundedRectangle(l, t, r, b, radiusX, radiusY, brush, strokeWidth=1.0, strokeStyle=None)` | 画圆角矩形边框 |
| `FillRoundedRectangle(l, t, r, b, radiusX, radiusY, brush)` | 填充圆角矩形 |
| `DrawEllipse(cx, cy, rx, ry, brush, strokeWidth=1.0, strokeStyle=None)` | 画椭圆边框 |
| `FillEllipse(cx, cy, rx, ry, brush)` | 填充椭圆 |
| `DrawGeometry(geometry, brush, strokeWidth=1.0, strokeStyle=None)` | 画几何路径 |
| `FillGeometry(geometry, brush)` | 填充几何路径 |

### 位图绘制

#### `DrawBitmap(bitmap, l, t, r, b, opacity=1.0, interpolationMode=1, srcRect=None)`
绘制 D2D 位图到目标矩形。

| 参数 | 说明 |
|------|------|
| `bitmap` | `Bitmap` 对象 |
| `l, t, r, b` | 目标矩形（float） |
| `opacity` | 不透明度 0~1 |
| `interpolationMode` | `BITMAP_INTERPOLATION_MODE`: `NEAREST_NEIGHBOR`(0), `LINEAR`(1) |
| `srcRect` | 源矩形 `(left, top, right, bottom)`，None 表示整张位图 |

### 文本绘制

#### `DrawText(text, textFormat, l, t, r, b, brush, options=0, measuringMode=0)`
简单文本绘制（不创建 TextLayout）。

| 参数 | 说明 |
|------|------|
| `text` | `str` 文本 |
| `textFormat` | `TextFormat` 对象 |
| `l, t, r, b` | 布局矩形（float） |
| `brush` | `Brush` 对象 |
| `options` | `DRAW_TEXT_OPTIONS`: `NONE`(0), `NO_SNAP`(1), `CLIP`(2), `ENABLE_COLOR_FONT`(4), `DISABLE_COLOR_BITMAP_SNAPPING`(8) |
| `measuringMode` | `MEASURING_MODE`: `NATURAL`(0), `GDI_CLASSIC`(1), `GDI_NATURAL`(2) |

#### `DrawTextLayout(x, y, textLayout, brush, options=0)`
绘制预排版的 TextLayout。

| 参数 | 说明 |
|------|------|
| `x, y` | 绘制位置（float） |
| `textLayout` | `TextLayout` 对象 |
| `brush` | `Brush` 对象 |
| `options` | `DRAW_TEXT_OPTIONS` 值 |

### 画笔创建

#### `CreateSolidColorBrush(r, g, b, a=1.0, opacity=1.0) -> SolidColorBrush`
创建纯色画笔。
- r/g/b/a: 0.0~1.0，**注意参数顺序是 (r, g, b, a) 不是 BGRA**
- opacity: 额外乘数

> **重要**: 颜色参数顺序是 RGBA（r=红, g=绿, b=蓝），但像素缓冲区格式是 BGRA。
> 例如红色画笔: `CreateSolidColorBrush(1.0, 0.0, 0.0, 1.0)`，在 BGRA 像素中 index 2 = R = 255。

#### `CreateGradientStopCollection(stops, gamma=0, extendMode=0) -> GradientStopCollection`
创建渐变停靠点集合。
- `stops`: `[(position, r, g, b, a), ...]`
- `gamma`: `GAMMA.GAMMA_2_2`(0) / `GAMMA_1_0`(1)
- `extendMode`: `EXTEND_MODE.CLAMP`(0) / `WRAP`(1) / `MIRROR`(2)

#### `CreateLinearGradientBrush(gradientStopCollection, x1, y1, x2, y2, opacity=1.0) -> LinearGradientBrush`
创建线性渐变画笔。

#### `CreateRadialGradientBrush(gradientStopCollection, cx, cy, ox, oy, rx, ry, opacity=1.0) -> RadialGradientBrush`
创建径向渐变画笔。

| 参数 | 说明 |
|------|------|
| `gradientStopCollection` | `GradientStopCollection` 对象 |
| `cx, cy` | 渐变中心点 |
| `ox, oy` | 渐变原点偏移 |
| `rx, ry` | 水平/垂直半径 |
| `opacity` | 不透明度 0~1 |

#### `CreateBitmapBrush(bitmap, extendModeX=0, extendModeY=0, interpolationMode=1, opacity=1.0) -> BitmapBrush`
创建位图画笔。

| 参数 | 说明 |
|------|------|
| `bitmap` | `Bitmap` 对象 |
| `extendModeX` | `EXTEND_MODE`: `CLAMP`(0) / `WRAP`(1) / `MIRROR`(2) |
| `extendModeY` | 同上 |
| `interpolationMode` | `BITMAP_INTERPOLATION_MODE`: `NEAREST_NEIGHBOR`(0) / `LINEAR`(1) |
| `opacity` | 不透明度 0~1 |

### 位图创建

#### `CreateBitmapFromWicBitmap(source, dxgiFormat=0, alphaMode=1, dpiX=96.0, dpiY=96.0) -> Bitmap`
从 WIC Bitmap 创建 D2D Bitmap。
- `source`: `WICBitmap` / `WICBitmapFrameDecode` / `WICFormatConverter` 对象
- `dxgiFormat`: 默认 `DXGI_FORMAT.UNKNOWN`(0)
- `alphaMode`: 默认 `ALPHA_MODE.PREMULTIPLIED`(1)

### 裁剪

#### `PushAxisAlignedClip(left, top, right, bottom, antialiasMode=0)`
推入轴对齐裁剪矩形。后续绘制仅在此矩形内可见。
- `antialiasMode`: `ANTIALIAS_MODE.PER_PRIMITIVE`(0) / `ALIASED`(1)

#### `PopAxisAlignedClip()`
弹出裁剪矩形。

### 图层

#### `CreateLayer(width=0, height=0) -> Layer`
创建图层。width/height=0 表示自动尺寸。

#### `PushLayer(layer, contentLeft=0, contentTop=0, contentRight=0, contentBottom=0, geometricMask=None, maskAntialiasMode=0, maskTransform_m11=1, maskTransform_m12=0, maskTransform_m21=0, maskTransform_m22=1, maskTransform_dx=0, maskTransform_dy=0, opacity=1.0, opacityBrush=None, layerOptions=0)`
推入图层。支持几何遮罩、不透明度、变换矩阵。
- `layerOptions`: `LAYER_OPTIONS.NONE`(0) / `INITIALIZE_FOR_CLEARTYPE`(1)

#### `PopLayer()`
弹出图层。

### 渲染控制

#### `Flush()`
强制提交所有待处理渲染命令到设备。失败时抛出 `Direct2DError`。

#### `SetTextAntialiasMode(mode)`
设置文本抗锯齿模式。
- `mode`: `TEXT_ANTIALIAS_MODE.DEFAULT`(0) / `CLEARTYPE`(1) / `GRAYSCALE`(2) / `ALIASED`(3)

#### `GetTextAntialiasMode() -> int`
获取当前文本抗锯齿模式。

#### `SetAntialiasMode(mode)`
设置图形抗锯齿模式。
- `mode`: `ANTIALIAS_MODE.PER_PRIMITIVE`(0) / `ALIASED`(1)

#### `IsSupported(rtType=0, pixelFormat=87, alphaMode=0, dpiX=96.0, dpiY=96.0, usage=0, minLevel=0) -> bool`
检查给定渲染目标属性是否被当前设备支持。

| 参数 | 说明 |
|------|------|
| `rtType` | `RENDER_TARGET_TYPE` |
| `pixelFormat` | `DXGI_FORMAT`，默认 `B8G8R8A8_UNORM`(87) |
| `alphaMode` | `ALPHA_MODE` |
| `dpiX, dpiY` | DPI，默认 96.0 |
| `usage` | `RENDER_TARGET_USAGE` |
| `minLevel` | `FEATURE_LEVEL` |

#### `GetDpi() -> (dpiX: float, dpiY: float)`
获取渲染目标 DPI。

#### `SetDpi(dpiX, dpiY)`
设置渲染目标 DPI。

#### `CreateCompatibleRenderTarget(width=0, height=0, pixelWidth=0, pixelHeight=0, pixelFormat=87, alphaMode=0, options=0) -> BitmapRenderTarget`
创建兼容的离屏渲染目标，用于两层绘制或缓存。

| 参数 | 说明 |
|------|--------|
| `width, height` | DIP 尺寸（float），0 表示自动 |
| `pixelWidth, pixelHeight` | 像素尺寸（int），0 表示自动 |
| `pixelFormat` | `DXGI_FORMAT`，默认 `B8G8R8A8_UNORM`(87) |
| `alphaMode` | `ALPHA_MODE`，默认 `UNKNOWN`(0) |
| `options` | `COMPATIBLE_RENDER_TARGET_OPTIONS.NONE`(0) / `GDI_COMPATIBLE`(1) |

### 状态管理

#### `SaveDrawingState(state)`
将当前 clip、transform、antialias 等绘制状态保存到 `DrawingStateBlock`。

#### `RestoreDrawingState(state)`
恢复之前保存的绘制状态。

```python
block = factory.CreateDrawingStateBlock()
rt.SaveDrawingState(block)
rt.SetTransform(2, 0, 0, 1, 5, 10)
# ... 子控件绘制 ...
rt.RestoreDrawingState(block)
```

### 变换

#### `GetTransform() -> (m11, m12, m21, m22, dx, dy)`
获取当前变换矩阵（6 个 float 值）。

#### `SetTransform(m11=1, m12=0, m21=0, m22=1, dx=0, dy=0)`
设置变换矩阵。默认值对应单位矩阵。

---

## 5. HWNDRenderTarget

继承 `RenderTarget`，额外方法：

### `Resize(width, height)`
调整窗口渲染目标尺寸。失败时抛出 `Direct2DError`。

---

## 6. DCRenderTarget

继承 `RenderTarget`，额外方法：

### `BindDC(hdc, left=0, top=0, right=0, bottom=0)`
绑定 HDC（设备上下文句柄，需要传 `int` 类型的指针值）。
- `hdc`: `int` — HDC 指针值（unsigned long long）
- `left, top, right, bottom`: 子矩形，全 0 表示整区域（当 right > 0 且 bottom > 0 时才传子矩形指针）

> **注意**: `DCRenderTarget.BindDC` 绑定到内存 DC 的 DIB section 后，`EndDraw` 可能不写入像素。
> 测试中建议使用 `WicBitmapRenderTarget` 代替 `DCRenderTarget + DIB section` 做离屏渲染验证。

---

## 7. BitmapRenderTarget

继承 `RenderTarget`，用于离屏位图渲染。

### `GetBitmap() -> Bitmap`
获取此渲染目标包含的位图。可用于将离屏渲染结果作为纹理源。

```python
bmp_rt = rt.CreateCompatibleRenderTarget(200, 100)
bmp_rt.BeginDraw()
bmp_rt.Clear(1, 1, 1, 1)
bmp_rt.EndDraw()
bmp = bmp_rt.GetBitmap()
rt.DrawBitmap(bmp, 0, 0, 200, 100)
```

---

## 8. Brush 系列

### `Brush` (基类, 继承 `Resource` → `COMObject`)
#### `GetOpacity() -> float`
获取画笔不透明度。

### `SolidColorBrush` (继承 `Brush`)
#### `SetColor(r, g, b, a=1.0)`
修改纯色画笔颜色（不必重新创建）。

#### `GetColor() -> (r, g, b, a)`
获取画笔当前颜色。返回 4 个 float 的元组。

### `LinearGradientBrush` (继承 `Brush`)
#### `GetStartPoint() -> (x, y)`
获取渐变起点。

#### `GetEndPoint() -> (x, y)`
获取渐变终点。

### `RadialGradientBrush` (继承 `Brush`)
#### `GetCenter() -> (x, y)`
获取渐变中心点。

#### `GetGradientOriginOffset() -> (x, y)`
获取渐变原点偏移。

#### `GetRadiusX() -> float`
获取水平半径。

#### `GetRadiusY() -> float`
获取垂直半径。

### `GradientStopCollection` (继承 `Resource` → `COMObject`)
渐变停靠点集合，由 `RenderTarget.CreateGradientStopCollection` 创建。无公开方法。

### `BitmapBrush` (继承 `Brush`)
位图画笔，由 `RenderTarget.CreateBitmapBrush` 创建。无额外公开方法。

---

## 9. Geometry 系列

### `Geometry` (基类, 继承 `Resource` → `COMObject`)

> **注意**: 以下 Geometry 方法中，`worldTransform` 参数在当前实现中固定为单位矩阵，
> 不接受外部传入的变换矩阵。`tolerance` 参数对应 Direct2D 的 `flatteningTolerance`。

#### `FillContainsPoint(x, y, tolerance=0.0) -> bool`
判断点是否在几何填充区域内。
- `x, y`: 测试点（DIP 坐标）
- `tolerance`: 平坦容差（0 = 默认）

#### `StrokeContainsPoint(x, y, strokeWidth=1.0, strokeStyle=None, tolerance=0.0) -> bool`
判断点是否在几何描边路径上。

#### `GetBounds() -> (left, top, right, bottom)`
获取几何边界框。返回 4 个 float 的元组。

#### `GetWidenedBounds(strokeWidth=1.0, strokeStyle=None, tolerance=0.0) -> (left, top, right, bottom)`
获取描边后几何的边界框。返回 4 个 float 的元组。

#### `CombineWithGeometry(other, combineMode, tolerance=0.0) -> PathGeometry`
两个几何的布尔组合运算。返回新的 `PathGeometry`。
- `combineMode`: `COMBINE_MODE.UNION`(0) / `INTERSECT`(1) / `XOR`(2) / `EXCLUDE`(3)

#### `Simplify(simplificationOption=0, tolerance=0.0) -> PathGeometry`
几何简化（如将曲线转为线段）。返回新的 `PathGeometry`。
- `simplificationOption`: `GEOMETRY_SIMPLIFICATION_OPTION.CUBICS_AND_LINES`(0) / `OPTION_LINES`(1)

#### `Outline(tolerance=0.0) -> PathGeometry`
生成几何轮廓路径。返回新的 `PathGeometry`。

#### `Tessellate(tolerance=0.0) -> PathGeometry`
> **注意**: 当前实现是 `Outline` 的别名，并非真正的三角化分解。

#### `ComputeArea(tolerance=0.0) -> float`
计算几何面积。

#### `CompareWithGeometry(other, tolerance=0.0) -> int`
比较两个几何的关系。返回 `GEOMETRY_RELATION` 值。
- `UNKNOWN`(0), `DISJOINT`(1), `IS_CONTAINED`(2), `CONTAINS`(3), `OVERLAP`(4)

### `PathGeometry` (继承 `Geometry`)
#### `Open() -> GeometrySink`
打开几何路径开始构建。

### `SimplifiedGeometrySink` (基类, 继承 `COMObject`)
#### `BeginFigure(x, y, figureBegin=0)`
- `figureBegin`: `FIGURE_BEGIN.FILLED`(0) / `HOLLOW`(1)

#### `EndFigure(figureEnd=0)`
- `figureEnd`: `FIGURE_END.OPEN`(0) / `CLOSED`(1)

#### `Close()`
关闭 sink，提交几何图形。失败时抛出 `Direct2DError`。

#### `SetFillMode(fillMode)`
- `fillMode`: `FILL_MODE.ALTERNATE`(0) / `WINDING`(1)

### `GeometrySink` (继承 `SimplifiedGeometrySink`)
#### `AddLine(x, y)` — 添加线段
#### `AddBezier(x1, y1, x2, y2, x3, y3)` — 添加三次贝塞尔曲线
#### `AddQuadraticBezier(x1, y1, x2, y2)` — 添加二次贝塞尔曲线
#### `AddArc(x, y, rx, ry, rotationAngle, sweepDirection, arcSize)` — 添加圆弧
  - `sweepDirection`: `SWEEP_DIRECTION.COUNTER_CLOCKWISE`(0) / `CLOCKWISE`(1)
  - `arcSize`: `ARC_SIZE.SMALL`(0) / `LARGE`(1)

---

## 10. Bitmap / Image

### `Image` (基类, 继承 `Resource` → `COMObject`)
无公开方法。

### `Bitmap` (继承 `Image`)
#### `GetSize() -> (width: float, height: float)`
返回 DIP 尺寸。

#### `GetPixelSize() -> (width: int, height: int)`
返回像素尺寸。

---

## 11. Layer / StrokeStyle / DrawingStateBlock

### `Layer` (继承 `Resource` → `COMObject`)
图层对象，由 `RenderTarget.CreateLayer` 创建。无公开方法。

### `StrokeStyle` (继承 `Resource` → `COMObject`)
描边样式对象，由 `D2DFactory.CreateStrokeStyle` 创建。无公开方法。

### `DrawingStateBlock` (继承 `Resource` → `COMObject`)
绘制状态块，由 `D2DFactory.CreateDrawingStateBlock` 创建。用于 `SaveDrawingState` / `RestoreDrawingState`。无公开方法。

---

## 12. WICFactory

继承 `COMObject`。Windows Imaging Component 工厂。

### `WICFactory()`
创建 WIC 工厂。内部自动调用 `CoInitializeEx(NULL, 2)` 和 `CoCreateInstance`。

> **警告**: `WICFactory.__dealloc__` 会调用 `CoUninitialize()`，减少 COM 引用计数。
> 在测试环境中，频繁创建/销毁 WICFactory 可能导致 COM 引用计数归零，使后续 D2D/DWrite 工厂初始化失败。
> 建议始终通过 `GetWICFactory()` 获取全局单例，不要手动创建 WICFactory 实例。

### `CreateBitmap(width, height, guid_bytes=None) -> WICBitmap`
创建 WIC 内存位图（PBGRA 格式）。
- `guid_bytes`: 自定义像素格式 GUID（当前不支持，传 None）

### `CreateDecoderFromFilename(filename) -> WICBitmapDecoder`
从文件创建位图解码器（支持 PNG/BMP/JPEG）。

### `CreateFormatConverter() -> WICFormatConverter`
创建格式转换器（用于将任何 WIC 源转为 PBGRA）。

### `SaveBitmap(bitmap, filename)`
将 WICBitmap 保存到文件。根据扩展名自动选择编码器：
- `.png` → PNG 编码
- `.bmp` → BMP 编码
- `.jpg` / `.jpeg` → JPEG 编码
- 其他扩展名抛出 `ValueError`

---

## 13. WICBitmap 系列

### `WICBitmap` (继承 `COMObject`)
#### `Lock(left=0, top=0, width=0, height=0, flags=1) -> WICBitmapLock`
锁定位图内存区域。
- `flags`: `1`（`WICBitmapLockWrite`，默认），`0` 为 `WICBitmapLockRead`，`2` 为 `WICBitmapLockRead|Write`

#### `GetSize() -> (width: int, height: int)`

### `WICBitmapLock` (继承 `COMObject`)
#### `GetDataPointer() -> (address: int, cbSize: int)`
获取锁定的内存数据指针和字节大小。`address` 为内存地址整数值（unsigned long long）。

> **用法示例**:
> ```python
> lock = wic_bmp.Lock(0, 0, W, H, 2)  # WICBitmapLockRead
> addr, cb = lock.GetDataPointer()
> buf = (ctypes.c_ubyte * cb).from_address(addr)
> data = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 4)
> ```

### `WICBitmapDecoder` (继承 `COMObject`)
#### `GetFrame(index=0) -> WICBitmapFrameDecode`
获取解码帧。默认取第一帧（index=0）。

### `WICBitmapFrameDecode` (继承 `COMObject`)
空壳类，作为 `WICFormatConverter.Initialize` 的输入源。无公开方法。
可传给 `RenderTarget.CreateBitmapFromWicBitmap` 创建 D2D Bitmap。

### `WICFormatConverter` (继承 `COMObject`)
#### `Initialize(source)`
将源图像转换为 PBGRA 格式。`source` 可以是 `WICBitmap`、`WICBitmapFrameDecode` 等任何 `COMObject` 子类。

---

## 14. DWriteFactory

继承 `COMObject`。DirectWrite 工厂。

### `DWriteFactory(factoryType=0)`
- `factoryType`: `DWRITE_FACTORY_TYPE.SHARED`(0) / `ISOLATED`(1)

### `CreateTextFormat(familyName, size, weight=500, style=0, stretch=5) -> TextFormat`
创建文本格式对象。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `familyName` | `str` | — | 字体族名称（如 `"Segoe UI"`） |
| `size` | `float` | — | 字体大小（DIP） |
| `weight` | `int` | `500` | `FONT_WEIGHT`（100~950），默认 `NORMAL`(400)/`MEDIUM`(500) |
| `style` | `int` | `0` | `FONT_STYLE`: `NORMAL`(0) / `OBLIQUE`(1) / `ITALIC`(2) |
| `stretch` | `int` | `5` | `FONT_STRETCH`: 默认 `NORMAL`(5) |

### `CreateTextLayout(text, textFormat, maxWidth, maxHeight) -> TextLayout`
创建文本布局对象，用于复杂排版和命中测试。

| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | 文本内容 |
| `textFormat` | `TextFormat` | 文本格式 |
| `maxWidth` | `float` | 最大宽度 |
| `maxHeight` | `float` | 最大高度 |

### `GetSystemFontCollection(checkForUpdates=False) -> FontCollection`
获取系统字体集合。
- `checkForUpdates`: 是否检查字体更新

---

## 15. FontCollection / FontFamily / DWriteFont / FontFace / LocalizedStrings

### `FontCollection` (继承 `COMObject`)
#### `GetFontFamilyCount() -> int`
获取字体族数量。

#### `GetFontFamily(index) -> FontFamily`
按索引获取字体族。

### `FontFamily` (继承 `COMObject`)
#### `GetFamilyNames() -> LocalizedStrings`
获取字体族的本地化名称列表。

#### `GetFontCount() -> int`
获取此字体族中的字体数量。

### `DWriteFont` (继承 `COMObject`)
#### `GetWeight() -> int`
获取字体粗细（`FONT_WEIGHT` 值）。

#### `GetStyle() -> int`
获取字体样式（`FONT_STYLE` 值）。

#### `GetStretch() -> int`
获取字体拉伸（`FONT_STRETCH` 值）。

### `FontFace` (继承 `COMObject`)
字体面对象。当前为空壳类，预留用于未来扩展。

### `LocalizedStrings` (继承 `COMObject`)
#### `GetCount() -> int`
获取本地化字符串数量。

#### `GetString(index) -> str`
按索引获取本地化字符串。内部自动分配缓冲区。

---

## 16. TextFormat / TextLayout

### `TextFormat` (继承 `COMObject`)
文本格式，描述字体和段落属性。

#### `SetTextAlignment(alignment)`
设置文本对齐方式。
- `alignment`: `TEXT_ALIGNMENT.LEADING`(0) / `TRAILING`(1) / `CENTER`(2) / `JUSTIFIED`(3)

#### `SetParagraphAlignment(alignment)`
设置段落对齐方式。
- `alignment`: `PARAGRAPH_ALIGNMENT.NEAR`(0) / `FAR`(1) / `CENTER`(2)

#### `SetWordWrapping(wrapping)`
设置自动换行模式。
- `wrapping`: `WORD_WRAPPING.WRAP`(0) / `NO_WRAP`(1) / `EMERGENCY_BREAK`(2) / `WHOLE_WORD`(3) / `CHARACTER`(4)

### `TextLayout` (继承 `TextFormat`)
文本布局，表示经过完整分析和格式化的文本块。

#### `GetMaxWidth() -> float`
获取布局最大宽度。

#### `GetMetrics() -> TEXT_METRICS`
获取文本布局的整体度量信息。返回 `TEXT_METRICS` 对象。

#### `SetTrimming(granularity, delimiter=0, delimiterCount=0)`
设置文本裁剪选项。

| 参数 | 类型 | 说明 |
|------|------|------|
| `granularity` | `int` | `TRIMMING_GRANULARITY.NONE`(0) / `CHARACTER`(1) / `WORD`(2) |
| `delimiter` | `int` | 分隔符字符代码 |
| `delimiterCount` | `int` | 分隔符重复次数 |

#### `HitTestPoint(x, y) -> (isTrailingHit: bool, isInside: bool, hitTestMetrics: HIT_TEST_METRICS)`
测试指定点是否在文本范围内。

| 参数 | 类型 | 说明 |
|------|------|------|
| `x, y` | `float` | 测试点坐标 |

返回值：
- `isTrailingHit`: 是否命中尾部
- `isInside`: 是否在文本区域内
- `hitTestMetrics`: `HIT_TEST_METRICS` 对象

#### `HitTestTextPosition(position, isTrailingHit=False) -> (pointX: float, pointY: float, hitTestMetrics: HIT_TEST_METRICS)`
获取指定文本位置的像素坐标。

| 参数 | 类型 | 说明 |
|------|------|------|
| `position` | `int` | 文本位置（字符索引） |
| `isTrailingHit` | `bool` | 是否取尾部边 |

返回值：
- `pointX, pointY`: 像素坐标
- `hitTestMetrics`: `HIT_TEST_METRICS` 对象

#### `GetClusterMetrics() -> list[CLUSTER_METRICS]`
获取所有字符簇的度量信息。返回 `CLUSTER_METRICS` 对象列表。

#### `GetLineMetrics() -> list[LINE_METRICS]`
获取所有行的度量信息。返回 `LINE_METRICS` 对象列表。

#### `SetUnderline(hasUnderline, start=0, length=0xFFFFFFFF)`
为指定文本范围设置下划线。

| 参数 | 类型 | 说明 |
|------|------|------|
| `hasUnderline` | `bool` | 是否显示下划线 |
| `start` | `int` | 起始位置（默认 0） |
| `length` | `int` | 范围长度（默认 0xFFFFFFFF = 全部） |

#### `SetStrikethrough(hasStrikethrough, start=0, length=0xFFFFFFFF)`
为指定文本范围设置删除线。

| 参数 | 类型 | 说明 |
|------|------|------|
| `hasStrikethrough` | `bool` | 是否显示删除线 |
| `start` | `int` | 起始位置（默认 0） |
| `length` | `int` | 范围长度（默认 0xFFFFFFFF = 全部） |

---

## 17. 数据结构类

以下类为纯 Python 数据容器，由 `TextLayout` 方法返回。

### `TEXT_METRICS`
文本布局的整体度量。

| 属性 | 类型 | 说明 |
|------|------|------|
| `left` | `float` | 左边界 |
| `top` | `float` | 上边界 |
| `width` | `float` | 文本宽度（不含尾部空白） |
| `widthIncludingTrailingWhitespace` | `float` | 含尾部空白的宽度 |
| `height` | `float` | 文本高度 |
| `layoutWidth` | `float` | 布局宽度 |
| `layoutHeight` | `float` | 布局高度 |
| `maxBidiReorderingDepth` | `int` | 最大双向重排深度 |
| `lineCount` | `int` | 行数 |

### `HIT_TEST_METRICS`
命中测试度量。

| 属性 | 类型 | 说明 |
|------|------|------|
| `textPosition` | `int` | 文本位置 |
| `length` | `int` | 范围长度 |
| `left` | `float` | 左边界 |
| `top` | `float` | 上边界 |
| `width` | `float` | 宽度 |
| `height` | `float` | 高度 |
| `bidiLevel` | `int` | 双向嵌套级别 |
| `isText` | `bool` | 是否为文本 |
| `isTrimmed` | `bool` | 是否被裁剪 |

### `CLUSTER_METRICS`
字符簇度量。

| 属性 | 类型 | 说明 |
|------|------|------|
| `width` | `float` | 簇宽度 |
| `length` | `int` | 簇中字符数（UTF-16 code units） |
| `canWrapLineAfter` | `bool` | 是否可在簇后换行 |
| `isWhitespace` | `bool` | 是否为空白 |
| `isNewline` | `bool` | 是否为换行 |
| `isSoftHyphen` | `bool` | 是否为软连字符 |
| `isRightToLeft` | `bool` | 是否为从右到左 |

### `LINE_METRICS`
行度量。

| 属性 | 类型 | 说明 |
|------|------|------|
| `length` | `int` | 行中字符数 |
| `trailingWhitespaceLength` | `int` | 尾部空白长度 |
| `newlineLength` | `int` | 换行符长度 |
| `height` | `float` | 行高 |
| `baseline` | `float` | 基线距离 |
| `isTrimmed` | `bool` | 是否被裁剪 |

---

## 18. 错误与异常类

### `COMError(OSError)`
COM 错误基类。

| 属性 | 类型 | 说明 |
|------|------|------|
| `hresult` | `int` | HRESULT 错误码 |
| `args` | `tuple` | `(error_message,)` — 通过 `FormatMessageW` 获取的系统错误描述 |

### `Direct2DError(COMError)`
Direct2D 错误。由 D2D 相关操作失败时抛出。

### `DirectWriteError(COMError)`
DirectWrite 错误。由 DWrite 相关操作失败时抛出。

---

## 19. 常量枚举

所有常量类定义在 `_pyd2d_const.pyi` 中，通过 `include` 合并到 `pyd2d` 模块。

### Direct2D 常量

#### `ALPHA_MODE`
| 常量 | 值 |
|------|-----|
| `UNKNOWN` | 0 |
| `PREMULTIPLIED` | 1 |
| `STRAIGHT` | 2 |
| `IGNORE` | 3 |

#### `ANTIALIAS_MODE`
| 常量 | 值 |
|------|-----|
| `PER_PRIMITIVE` | 0 |
| `ALIASED` | 1 |

#### `ARC_SIZE`
| 常量 | 值 |
|------|-----|
| `SMALL` | 0 |
| `LARGE` | 1 |

#### `BITMAP_INTERPOLATION_MODE`
| 常量 | 值 |
|------|-----|
| `NEAREST_NEIGHBOR` | 0 |
| `LINEAR` | 1 |

#### `CAP_STYLE`
| 常量 | 值 |
|------|-----|
| `FLAT` | 0 |
| `SQUARE` | 1 |
| `ROUND` | 2 |
| `TRIANGLE` | 3 |

#### `COMBINE_MODE`
| 常量 | 值 |
|------|-----|
| `UNION` | 0 |
| `INTERSECT` | 1 |
| `XOR` | 2 |
| `EXCLUDE` | 3 |

#### `COMPATIBLE_RENDER_TARGET_OPTIONS`
| 常量 | 值 |
|------|-----|
| `NONE` | 0x00000000 |
| `GDI_COMPATIBLE` | 0x00000001 |

#### `D2D_FACTORY_TYPE`
| 常量 | 值 |
|------|-----|
| `SINGLE_THREADED` | 0 |
| `MULTI_THREADED` | 1 |

#### `DASH_STYLE`
| 常量 | 值 |
|------|-----|
| `SOLID` | 0 |
| `DASH` | 1 |
| `DOT` | 2 |
| `DASH_DOT` | 3 |
| `DASH_DOT_DOT` | 4 |
| `CUSTOM` | 5 |

#### `DC_INITIALIZE_MODE`
| 常量 | 值 |
|------|-----|
| `COPY` | 0 |
| `CLEAR` | 1 |

#### `DEBUG_LEVEL`
| 常量 | 值 |
|------|-----|
| `NONE` | 0 |
| `ERROR` | 1 |
| `WARNING` | 2 |
| `INFORMATION` | 3 |

#### `DRAW_TEXT_OPTIONS`
| 常量 | 值 |
|------|-----|
| `NONE` | 0x00000000 |
| `NO_SNAP` | 0x00000001 |
| `CLIP` | 0x00000002 |
| `ENABLE_COLOR_FONT` | 0x00000004 |
| `DISABLE_COLOR_BITMAP_SNAPPING` | 0x00000008 |

#### `EXTEND_MODE`
| 常量 | 值 |
|------|-----|
| `CLAMP` | 0 |
| `WRAP` | 1 |
| `MIRROR` | 2 |

#### `FEATURE_LEVEL`
| 常量 | 值 |
|------|-----|
| `DEFAULT` | 0 |
| `LEVEL_9` | 0x9100 |
| `LEVEL_10` | 0xA000 |

#### `FIGURE_BEGIN`
| 常量 | 值 |
|------|-----|
| `FILLED` | 0 |
| `HOLLOW` | 1 |

#### `FIGURE_END`
| 常量 | 值 |
|------|-----|
| `OPEN` | 0 |
| `CLOSED` | 1 |

#### `FILL_MODE`
| 常量 | 值 |
|------|-----|
| `ALTERNATE` | 0 |
| `WINDING` | 1 |

#### `GAMMA`
| 常量 | 值 |
|------|-----|
| `GAMMA_2_2` | 0 |
| `GAMMA_1_0` | 1 |

#### `GEOMETRY_RELATION`
| 常量 | 值 |
|------|-----|
| `UNKNOWN` | 0 |
| `DISJOINT` | 1 |
| `IS_CONTAINED` | 2 |
| `CONTAINS` | 3 |
| `OVERLAP` | 4 |

#### `GEOMETRY_SIMPLIFICATION_OPTION`
| 常量 | 值 |
|------|-----|
| `CUBICS_AND_LINES` | 0 |
| `OPTION_LINES` | 1 |

#### `INTERPOLATION_MODE_DEFINITION`
| 常量 | 值 |
|------|-----|
| `NEAREST_NEIGHBOR` | 0 |
| `LINEAR` | 1 |
| `CUBIC` | 2 |
| `MULTI_SAMPLE_LINEAR` | 3 |
| `ANISOTROPIC` | 4 |
| `HIGH_QUALITY_CUBIC` | 5 |
| `FANT` | 6 |
| `MIPMAP_LINEAR` | 7 |

#### `LAYER_OPTIONS`
| 常量 | 值 |
|------|-----|
| `NONE` | 0x00000000 |
| `INITIALIZE_FOR_CLEARTYPE` | 0x00000001 |

#### `LINE_JOIN`
| 常量 | 值 |
|------|-----|
| `MITER` | 0 |
| `BEVEL` | 1 |
| `ROUND` | 2 |
| `MITER_OR_BEVEL` | 3 |

#### `MEASURING_MODE`
| 常量 | 值 |
|------|-----|
| `NATURAL` | 0 |
| `GDI_CLASSIC` | 1 |
| `GDI_NATURAL` | 2 |

#### `OPACITY_MASK_CONTENT`
| 常量 | 值 |
|------|-----|
| `GRAPHICS` | 0 |
| `TEXT_NATURAL` | 1 |
| `TEXT_GDI_COMPATIBLE` | 2 |

#### `PATH_SEGMENT`
| 常量 | 值 |
|------|-----|
| `NONE` | 0x00000000 |
| `FORCE_UNSTROKED` | 0x00000001 |
| `FORCE_ROUND_LINE_JOIN` | 0x00000002 |

#### `PRESENT_OPTIONS`
| 常量 | 值 |
|------|-----|
| `NONE` | 0x00000000 |
| `RETAIN_CONTENTS` | 0x00000001 |
| `IMMEDIATELY` | 0x00000002 |

#### `RENDER_TARGET_TYPE`
| 常量 | 值 |
|------|-----|
| `DEFAULT` | 0 |
| `SOFTWARE` | 1 |
| `HARDWARE` | 2 |

#### `RENDER_TARGET_USAGE`
| 常量 | 值 |
|------|-----|
| `NONE` | 0x00000000 |
| `FORCE_BITMAP_REMOTING` | 0x00000001 |
| `GDI_COMPATIBLE` | 0x00000002 |

#### `SWEEP_DIRECTION`
| 常量 | 值 |
|------|-----|
| `COUNTER_CLOCKWISE` | 0 |
| `CLOCKWISE` | 1 |

#### `TEXT_ANTIALIAS_MODE`
| 常量 | 值 |
|------|-----|
| `DEFAULT` | 0 |
| `CLEARTYPE` | 1 |
| `GRAYSCALE` | 2 |
| `ALIASED` | 3 |

#### `TEXTURE_TYPE`
| 常量 | 值 |
|------|-----|
| `ALIASED_1x1` | 0 |
| `CLEARTYPE_3x1` | 1 |

#### `WINDOW_STATE`
| 常量 | 值 |
|------|-----|
| `NONE` | 0x00000000 |
| `OCCLUDED` | 0x00000001 |

### DirectWrite 常量

#### `DWRITE_FACTORY_TYPE`
| 常量 | 值 |
|------|-----|
| `SHARED` | 0 |
| `ISOLATED` | 1 |

#### `FONT_FACE_TYPE`
| 常量 | 值 |
|------|-----|
| `CFF` | 0 |
| `TRUETYPE` | 1 |
| `OPENTYPE_COLLECTION` | 2 |
| `TYPE1` | 3 |
| `VECTOR` | 4 |
| `BITMAP` | 5 |
| `UNKNOWN` | 6 |
| `RAW_CFF` | 7 |
| `TRUETYPE_COLLECTION` | 2（别名 = `OPENTYPE_COLLECTION`） |

#### `FONT_FILE_TYPE`
| 常量 | 值 |
|------|-----|
| `UNKNOWN` | 0 |
| `CFF` | 1 |
| `TRUETYPE` | 2 |
| `OPENTYPE_COLLECTION` | 3 |
| `TYPE1_PFM` | 4 |
| `TYPE1_PFB` | 5 |
| `VECTOR` | 6 |
| `BITMAP` | 7 |
| `TRUETYPE_COLLECTION` | 3（别名 = `OPENTYPE_COLLECTION`） |

#### `FONT_WEIGHT`
| 常量 | 值 |
|------|-----|
| `THIN` | 100 |
| `EXTRA_LIGHT` / `ULTRA_LIGHT` | 200 |
| `LIGHT` | 300 |
| `SEMI_LIGHT` | 350 |
| `NORMAL` / `REGULAR` | 400 |
| `MEDIUM` | 500 |
| `DEMI_BOLD` | 600 |
| `BOLD` | 700 |
| `EXTRA_BOLD` / `ULTRA_BOLD` | 800 |
| `BLACK` / `HEAVY` | 900 |
| `EXTRA_BLACK` / `ULTRA_BLACK` | 950 |

#### `FONT_STRETCH`
| 常量 | 值 |
|------|-----|
| `UNDEFINED` | 0 |
| `ULTRA_CONDENSED` | 1 |
| `EXTRA_CONDENSED` | 2 |
| `CONDENSED` | 3 |
| `SEMI_CONDENSED` | 4 |
| `NORMAL` / `MEDIUM` | 5 |
| `SEMI_EXPANDED` | 6 |
| `EXPANDED` | 7 |
| `EXTRA_EXPANDED` | 8 |
| `ULTRA_EXPANDED` | 9 |

#### `FONT_STYLE`
| 常量 | 值 |
|------|-----|
| `NORMAL` | 0 |
| `OBLIQUE` | 1 |
| `ITALIC` | 2 |

#### `FONT_SIMULATIONS`
| 常量 | 值 |
|------|-----|
| `NONE` | 0 |
| `BOLD` | 1 |
| `OBLIQUE` | 2 |

#### `INFORMATIONAL_STRING_ID`
| 常量 | 值 |
|------|-----|
| `NONE` | 0 |
| `COPYRIGHT_NOTICE` | 1 |
| `VERSION_STRINGS` | 2 |
| `TRADEMARK` | 3 |
| `MANUFACTURER` | 4 |
| `DESIGNER` | 5 |
| `DESIGNER_URL` | 6 |
| `DESCRIPTION` | 7 |
| `FONT_VENDOR_URL` | 8 |
| `LICENSE_DESCRIPTION` | 9 |
| `LICENSE_INFO_URL` | 10 |
| `WIN32_FAMILY_NAMES` | 11 |
| `WIN32_SUBFAMILY_NAMES` | 12 |
| `TYPOGRAPHIC_FAMILY_NAMES` | 13 |
| `TYPOGRAPHIC_SUBFAMILY_NAMES` | 14 |
| `SAMPLE_TEXT` | 15 |
| `FULL_NAME` | 16 |
| `POSTSCRIPT_NAME` | 17 |
| `POSTSCRIPT_CID_NAME` | 18 |
| `WEIGHT_STRETCH_STYLE_FAMILY_NAME` | 19 |
| `DESIGN_SCRIPT_LANGUAGE_TAG` | 20 |
| `SUPPORTED_SCRIPT_LANGUAGE_TAG` | 21 |
| `PREFERRED_FAMILY_NAMES` | 13（别名 = `TYPOGRAPHIC_FAMILY_NAMES`） |
| `PREFERRED_SUBFAMILY_NAMES` | 14（别名 = `TYPOGRAPHIC_SUBFAMILY_NAMES`） |
| `WWS_FAMILY_NAME` | 19（别名 = `WEIGHT_STRETCH_STYLE_FAMILY_NAME`） |

#### `PIXEL_GEOMETRY`
| 常量 | 值 |
|------|-----|
| `FLAT` | 0 |
| `RGB` | 1 |
| `BGR` | 2 |

#### `RENDERING_MODE`
| 常量 | 值 |
|------|-----|
| `DEFAULT` | 0 |
| `ALIASED` | 1 |
| `GDI_CLASSIC` | 2 |
| `GDI_NATURAL` | 3 |
| `NATURAL` | 4 |
| `NATURAL_SYMMETRIC` | 5 |
| `OUTLINE` | 6 |
| `CLEARTYPE_GDI_CLASSIC` | 2（别名 = `GDI_CLASSIC`） |
| `CLEARTYPE_GDI_NATURAL` | 3（别名 = `GDI_NATURAL`） |
| `CLEARTYPE_NATURAL` | 4（别名 = `NATURAL`） |
| `CLEARTYPE_NATURAL_SYMMETRIC` | 5（别名 = `NATURAL_SYMMETRIC`） |

#### `TRIMMING_GRANULARITY`
| 常量 | 值 |
|------|-----|
| `NONE` | 0 |
| `CHARACTER` | 1 |
| `WORD` | 2 |

#### `TEXT_ALIGNMENT`
| 常量 | 值 |
|------|-----|
| `LEADING` | 0 |
| `TRAILING` | 1 |
| `CENTER` | 2 |
| `JUSTIFIED` | 3 |

#### `PARAGRAPH_ALIGNMENT`
| 常量 | 值 |
|------|-----|
| `NEAR` | 0 |
| `FAR` | 1 |
| `CENTER` | 2 |

#### `WORD_WRAPPING`
| 常量 | 值 |
|------|-----|
| `WRAP` | 0 |
| `NO_WRAP` | 1 |
| `EMERGENCY_BREAK` | 2 |
| `WHOLE_WORD` | 3 |
| `CHARACTER` | 4 |

#### `READING_DIRECTION`
| 常量 | 值 |
|------|-----|
| `LEFT_TO_RIGHT` | 0 |
| `RIGHT_TO_LEFT` | 1 |
| `TOP_TO_BOTTOM` | 2 |
| `BOTTOM_TO_TOP` | 3 |

#### `FLOW_DIRECTION`
| 常量 | 值 |
|------|-----|
| `TOP_TO_BOTTOM` | 0 |
| `BOTTOM_TO_TOP` | 1 |
| `LEFT_TO_RIGHT` | 2 |
| `RIGHT_TO_LEFT` | 3 |

#### `BREAK_CONDITION`
| 常量 | 值 |
|------|-----|
| `NEUTRAL` | 0 |
| `CAN_BREAK` | 1 |
| `MAY_NOT_BREAK` | 2 |
| `MUST_BREAK` | 3 |

#### `LINE_SPACING_METHOD`
| 常量 | 值 |
|------|-----|
| `DEFAULT` | 0 |
| `UNIFORM` | 1 |
| `PROPORTIONAL` | 2 |

#### `NUMBER_SUBSTITUTION_METHOD`
| 常量 | 值 |
|------|-----|
| `FROM_CULTURE` | 0 |
| `CONTEXTUAL` | 1 |
| `NONE` | 2 |
| `NATIONAL` | 3 |
| `TRADITIONAL` | 4 |

#### `SCRIPT_SHAPES`
| 常量 | 值 |
|------|-----|
| `DEFAULT` | 0 |
| `NO_VISUAL` | 1 |

#### `FONT_FEATURE_TAG`
OpenType 字体特性标签（4 字节整数编码）。常用值：

| 常量 | 值 | 说明 |
|------|-----|------|
| `DEFAULT` | 0x746C6664 | 默认特性 |
| `KERNING` | 0x6E72656B | 字距调整 |
| `STANDARD_LIGATURES` | 0x6167696C | 标准连字 |
| `DISCRETIONARY_LIGATURES` | 0x67696C64 | 任意连字 |
| `CONTEXTUAL_LIGATURES` | 0x67696C63 | 上下文连字 |
| `HISTORICAL_LIGATURES` | 0x67696C68 | 历史连字 |
| `REQUIRED_LIGATURES` | 0x67696C72 | 必需连字 |
| `SMALL_CAPITALS` | 0x70636D73 | 小型大写 |
| `PETITE_CAPITALS` | 0x70616370 | 微型大写 |
| `CONTEXTUAL_ALTERNATES` | 0x746C6163 | 上下文替代 |
| `STYLISTIC_ALTERNATES` | 0x746C6173 | 风格替代 |
| `SWASH` | 0x68737773 | 花饰 |
| `FRACTIONS` | 0x63617266 | 分数 |
| `ALTERNATIVE_FRACTIONS` | 0x63726661 | 替代分数 |
| `SLASHED_ZERO` | 0x6F72657A | 斜线零 |
| `SUBSCRIPT` | 0x73627573 | 下标 |
| `SUPERSCRIPT` | 0x73707573 | 上标 |
| `STYLISTIC_SET_1` ~ `STYLISTIC_SET_20` | 0x31307373 ~ 0x30327373 | 风格集 1-20 |
| `FULL_WIDTH` | 0x64697766 | 全角 |
| `HALF_WIDTH` | 0x64697768 | 半角 |
| `PROPORTIONAL_WIDTHS` | 0x64697770 | 等比宽度 |
| `LINING_FIGURES` | 0x6D756E6C | 等高数字 |
| `OLD_STYLE_FIGURES` | 0x6D756E6F | 旧式数字 |
| `PROPORTIONAL_FIGURES` | 0x6D756E70 | 等比数字 |
| `TABULAR_FIGURES` | 0x6D756E74 | 等宽数字 |
| ... | ... | 完整列表见源码 |

### DXGI 格式常量

#### `DXGI_FORMAT`
常用值：

| 常量 | 值 | 说明 |
|------|-----|------|
| `UNKNOWN` | 0 | 未知格式 |
| `R8G8B8A8_UNORM` | 28 | 8位 RGBA |
| `R8G8B8A8_UNORM_SRGB` | 29 | sRGB RGBA |
| `B8G8R8A8_UNORM` | 87 | 8位 BGRA（**pyd2d 默认**） |
| `B8G8R8A8_TYPELESS` | 90 | 无类型 BGRA |
| `B8G8R8A8_UNORM_SRGB` | 91 | sRGB BGRA |
| `A8_UNORM` | 65 | 8位 Alpha |

> 完整 DXGI_FORMAT 列表包含 190 个值，详见 `_pyd2d_const.pyi`。

#### `ALPHA_MAX`
常量值 `255`。Alpha 通道最大值。

---

## 20. 内置工具函数

### `nine_patch_draw(rt, bitmap, rect, margins, draw_flags=0)`

九宫格（Nine-Patch）位图绘制函数。将一张位图按九宫格方式拉伸绘制到目标矩形，
四角保持原始尺寸，四边和中心可拉伸或平铺。

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `rt` | `RenderTarget` | 渲染目标 |
| `bitmap` | `Bitmap` | 源位图 |
| `rect` | `(x, y, w, h)` | 目标矩形（int） |
| `margins` | `(left, top, right, bottom)` | 九宫格边距（int），定义四角区域大小 |
| `draw_flags` | `int` | 平铺标志，5 位十进制编码 `TLCTR`（默认 0 = 全部拉伸） |

#### `draw_flags` 编码

`draw_flags` 为 5 位十进制数，每一位控制对应区域是拉伸(0)还是平铺(1)：

| 位 | 位置 | 含义 |
|----|------|------|
| 万位 | `T` | 顶边（Top） |
| 千位 | `L` | 左边（Left） |
| 百位 | `C` | 中心（Center） |
| 十位 | `R` | 右边（Right） |
| 个位 | `B` | 底边（Bottom） |

#### 示例

```python
# 全部拉伸（默认）
nine_patch_draw(rt, bmp, (0, 0, 200, 50), (5, 5, 5, 5))

# 中心平铺，其余拉伸
nine_patch_draw(rt, bmp, (0, 0, 200, 50), (5, 5, 5, 5), draw_flags=00100)

# 顶边和底边平铺
nine_patch_draw(rt, bmp, (0, 0, 200, 50), (5, 5, 5, 5), draw_flags=10001)
```

#### 绘制逻辑

1. **四角**：始终按原始尺寸绘制，不拉伸不平铺
2. **四边 + 中心**：根据 `draw_flags` 对应位决定拉伸(0)或平铺(1)
3. **平铺**：通过内部 `_draw_tiled` 函数实现，将源区域重复绘制填满目标区域
4. **安全检查**：当边距大于目标尺寸或源尺寸时，自动跳过对应区域

---

## 21. 类继承层次

```
COMObject
├── D2DFactory
├── Resource
│   ├── Brush
│   │   ├── SolidColorBrush
│   │   ├── LinearGradientBrush
│   │   ├── RadialGradientBrush
│   │   └── BitmapBrush
│   ├── Image
│   │   └── Bitmap
│   ├── Geometry
│   │   └── PathGeometry
│   ├── GradientStopCollection
│   ├── Layer
│   ├── StrokeStyle
│   ├── DrawingStateBlock
│   └── RenderTarget
│       ├── HWNDRenderTarget
│       ├── DCRenderTarget
│       └── BitmapRenderTarget
├── SimplifiedGeometrySink
│   └── GeometrySink
├── WICFactory
├── WICBitmap
├── WICBitmapLock
├── WICBitmapDecoder
├── WICBitmapFrameDecode
├── WICFormatConverter
├── DWriteFactory
├── FontCollection
├── FontFamily
├── DWriteFont
├── FontFace
├── LocalizedStrings
└── TextFormat
    └── TextLayout
```

### 数据类（纯 Python，非 COMObject）
- `TEXT_METRICS`
- `HIT_TEST_METRICS`
- `CLUSTER_METRICS`
- `LINE_METRICS`

### 异常类
```
OSError
└── COMError
    ├── Direct2DError
    └── DirectWriteError
```
