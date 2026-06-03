# cython: language_level=3
# cython: freethreading_compatible=True

include "_pyd2d_const.pyi"
from libc.stdint cimport int32_t, uint16_t, uint32_t, uint64_t, intptr_t, uintptr_t
from libc.stddef cimport wchar_t
from cpython.mem cimport PyMem_Malloc, PyMem_Free

cdef extern from *:
    """
    #define UNICODE
    #define _UNICODE
    """
    wchar_t* PyUnicode_AsWideCharString(object unicode, Py_ssize_t *size)
    object PyUnicode_FromWideChar(wchar_t *wstr, Py_ssize_t size)

cdef extern from "windows.h":
    """
    static const GUID _WicPbgraFormat = {0x6fddc324, 0x4e03, 0x4bfe, {0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x10}};
    static const GUID _EncoderPngFormat = {0x27949969, 0x876A, 0x41D7, {0x94, 0x47, 0x56, 0x8F, 0x6A, 0x35, 0xA4, 0xDC}};
    static const GUID _EncoderBmpFormat = {0x69BE8BB4, 0xD66D, 0x47C8, {0x86, 0x5A, 0xED, 0x15, 0x89, 0x43, 0x37, 0x82}};
    static const GUID _ContainerPngFormat = {0x1B7CFAF4, 0x713F, 0x473C, {0xBB, 0xCD, 0x61, 0x37, 0x42, 0x5F, 0xAE, 0xAF}};
    static const GUID _ContainerBmpFormat = {0x0AF1D87E, 0xFCFE, 0x4188, {0xBD, 0xEB, 0xA7, 0x90, 0x64, 0x71, 0xCB, 0xE3}};
    static const GUID _ContainerJpegFormat = {0x19E4A5AA, 0x5662, 0x4FC5, {0xA0, 0xC0, 0x17, 0x58, 0x02, 0x8E, 0x10, 0x57}};
    """
    ctypedef int32_t HRESULT
    ctypedef uint32_t ULONG
    ctypedef int BOOL
    ctypedef void* HWND
    ctypedef void* HDC
    ctypedef int32_t LONG
    ctypedef uint32_t UINT32
    ctypedef uint16_t UINT16
    ctypedef float FLOAT
    ctypedef uint64_t UINT64
    ctypedef uint32_t UINT
    ctypedef wchar_t WCHAR
    ctypedef unsigned char BYTE
    ctypedef unsigned long DWORD

    ctypedef struct GUID:
        unsigned long Data1
        unsigned short Data2
        unsigned short Data3
        unsigned char Data4[8]

    const GUID _WicPbgraFormat
    const GUID _EncoderPngFormat
    const GUID _EncoderBmpFormat
    const GUID _ContainerPngFormat
    const GUID _ContainerBmpFormat
    const GUID _ContainerJpegFormat

    unsigned int FormatMessageW(
        unsigned long dwFlags,
        void *lpSource,
        unsigned long dwMessageId,
        unsigned long dwLanguageId,
        wchar_t* lpBuffer,
        unsigned long nSize,
        void *Arguments) noexcept nogil
    bint SUCCEEDED(HRESULT hr) noexcept nogil
    bint FAILED(HRESULT hr) noexcept nogil

cdef extern from "objbase.h":
    HRESULT CoInitializeEx(
        void* pvReserved,
        unsigned long dwCoInit) noexcept nogil
    void CoUninitialize() noexcept nogil
    HRESULT CoCreateInstance(
        const GUID& rclsid,
        IUnknown* pUnkOuter,
        DWORD dwClsContext,
        const GUID& riid,
        void** ppv) noexcept nogil

    cdef cppclass IUnknown:
        void Release() noexcept nogil

    cdef cppclass IStream(IUnknown):
        pass

cdef extern from "dwrite.h":
    """
    #define IID_IDWriteFactory __uuidof(IDWriteFactory)
    """
    ctypedef int DWRITE_FACTORY_TYPE
    ctypedef int DWRITE_FONT_STYLE
    ctypedef int DWRITE_FONT_WEIGHT
    ctypedef int DWRITE_FONT_STRETCH
    ctypedef int DWRITE_TEXT_ALIGNMENT
    ctypedef int DWRITE_PARAGRAPH_ALIGNMENT
    ctypedef int DWRITE_WORD_WRAPPING

    ctypedef struct DWRITE_TEXT_METRICS:
        FLOAT  left
        FLOAT  top
        FLOAT  width
        FLOAT  widthIncludingTrailingWhitespace
        FLOAT  height
        FLOAT  layoutWidth
        FLOAT  layoutHeight
        UINT32 maxBidiReorderingDepth
        UINT32 lineCount

    ctypedef struct DWRITE_HIT_TEST_METRICS:
        UINT32 textPosition
        UINT32 length
        FLOAT  left
        FLOAT  top
        FLOAT  width
        FLOAT  height
        UINT32 bidiLevel
        BOOL isText
        BOOL isTrimmed

    ctypedef int DWRITE_TRIMMING_GRANULARITY

    ctypedef struct DWRITE_TRIMMING:
        DWRITE_TRIMMING_GRANULARITY granularity
        UINT32 delimiter
        UINT32 delimiterCount

    ctypedef struct DWRITE_TEXT_RANGE:
        UINT32 startPosition
        UINT32 length

    ctypedef struct DWRITE_CLUSTER_METRICS:
        FLOAT width
        UINT16 length
        UINT16 _bitfield

    ctypedef struct DWRITE_LINE_METRICS:
        UINT32 length
        UINT32 trailingWhitespaceLength
        UINT32 newlineLength
        FLOAT height
        FLOAT baseline
        BOOL isTrimmed

    cdef GUID IID_IDWriteFactory

    cdef cppclass IDWriteTextLayout:
        FLOAT GetMaxWidth() noexcept nogil
        HRESULT GetMetrics(DWRITE_TEXT_METRICS *textMetrics) noexcept nogil
        HRESULT SetTrimming(
            const DWRITE_TRIMMING *trimmingOptions,
            IUnknown *trimmingSign) noexcept nogil
        HRESULT HitTestPoint(
            FLOAT pointX, FLOAT pointY,
            BOOL *isTrailingHit, BOOL *isInside,
            DWRITE_HIT_TEST_METRICS *hitTestMetrics) noexcept nogil
        HRESULT HitTestTextPosition(
            UINT32 textPosition, BOOL isTrailingHit,
            FLOAT *pointX, FLOAT *pointY,
            DWRITE_HIT_TEST_METRICS *hitTestMetrics) noexcept nogil
        HRESULT GetClusterMetrics(
            DWRITE_CLUSTER_METRICS *clusterMetrics, UINT32 maxClusterCount,
            UINT32 *actualClusterCount) noexcept nogil
        HRESULT GetLineMetrics(
            DWRITE_LINE_METRICS *lineMetrics, UINT32 maxLineCount,
            UINT32 *actualLineCount) noexcept nogil
        HRESULT SetUnderline(BOOL hasUnderline, DWRITE_TEXT_RANGE textRange) noexcept nogil
        HRESULT SetStrikethrough(BOOL hasStrikethrough, DWRITE_TEXT_RANGE textRange) noexcept nogil
    cdef cppclass IDWriteFactory:
        HRESULT CreateTextFormat(
            const WCHAR *family_name,
            IDWriteFontCollection *collection,
            DWRITE_FONT_WEIGHT weight,
            DWRITE_FONT_STYLE style,
            DWRITE_FONT_STRETCH stretch,
            FLOAT size,
            const WCHAR *locale,
            IDWriteTextFormat **format) noexcept nogil
        HRESULT CreateTextLayout(
            WCHAR *string,
            UINT32 stringLength,
            IDWriteTextFormat *textFormat,
            FLOAT maxWidth,
            FLOAT maxHeight,
            IDWriteTextLayout **textLayout) noexcept nogil
        HRESULT GetSystemFontCollection(
            IDWriteFontCollection **fontCollection,
            BOOL checkForUpdates) noexcept nogil
    cdef cppclass IDWriteFontCollection:
        UINT32 GetFontFamilyCount() noexcept nogil
        HRESULT GetFontFamily(UINT32 index, IDWriteFontFamily **fontFamily) noexcept nogil
    cdef cppclass IDWriteFontFamily:
        HRESULT GetFamilyNames(IDWriteLocalizedStrings **names) noexcept nogil
        UINT32 GetFontCount() noexcept nogil
        HRESULT GetFont(UINT32 index, IDWriteFont **font) noexcept nogil
    cdef cppclass IDWriteLocalizedStrings:
        UINT32 GetCount() noexcept nogil
        HRESULT GetStringLength(UINT32 index, UINT32 *length) noexcept nogil
        HRESULT GetString(UINT32 index, WCHAR *stringBuffer, UINT32 bufferSize) noexcept nogil
    cdef cppclass IDWriteFont:
        DWRITE_FONT_WEIGHT GetWeight() noexcept nogil
        DWRITE_FONT_STYLE GetStyle() noexcept nogil
        DWRITE_FONT_STRETCH GetStretch() noexcept nogil
    cdef cppclass IDWriteTextFormat:
        HRESULT SetTextAlignment(DWRITE_TEXT_ALIGNMENT textAlignment) noexcept nogil
        HRESULT SetParagraphAlignment(DWRITE_PARAGRAPH_ALIGNMENT paragraphAlignment) noexcept nogil
        HRESULT SetWordWrapping(DWRITE_WORD_WRAPPING wordWrapping) noexcept nogil

    cdef cppclass IDWriteRenderingParams:
        pass

    HRESULT DWriteCreateFactory(
        DWRITE_FACTORY_TYPE factoryType,
        const GUID& iid, IUnknown** factory) noexcept nogil


cdef struct _CLUSTER_METRICS_RAW:
    FLOAT width
    UINT16 length
    UINT16 flags

cdef extern from "d2d1.h":
    ctypedef int D2D1_DEBUG_LEVEL
    ctypedef int D2D1_FACTORY_TYPE
    ctypedef int D2D1_RENDER_TARGET_TYPE
    ctypedef int D2D1_RENDER_TARGET_USAGE
    ctypedef int D2D1_FEATURE_LEVEL
    ctypedef int DXGI_FORMAT
    ctypedef int D2D1_ALPHA_MODE
    ctypedef int D2D1_RENDER_TARGET_USAGE
    ctypedef int D2D1_FEATURE_LEVEL
    ctypedef int D2D1_PRESENT_OPTIONS
    ctypedef int D2D1_CAP_STYLE
    ctypedef int D2D1_LINE_JOIN
    ctypedef int D2D1_DASH_STYLE
    ctypedef int D2D1_SWEEP_DIRECTION
    ctypedef int D2D1_ARC_SIZE
    ctypedef int D2D1_FILL_MODE
    ctypedef int D2D1_ANTIALIAS_MODE
    ctypedef int D2D1_TEXT_ANTIALIAS_MODE
    ctypedef int D2D1_BITMAP_INTERPOLATION_MODE
    ctypedef int D2D1_DRAW_TEXT_OPTIONS
    ctypedef int DWRITE_MEASURING_MODE
    ctypedef int D2D1_FIGURE_BEGIN
    ctypedef int D2D1_FIGURE_END
    ctypedef int D2D1_GAMMA
    ctypedef int D2D1_EXTEND_MODE
    ctypedef int D2D1_ANTIALIAS_MODE
    ctypedef int D2D1_LAYER_OPTIONS
    ctypedef int D2D1_COMBINE_MODE
    ctypedef int D2D1_GEOMETRY_RELATION
    ctypedef int D2D1_GEOMETRY_SIMPLIFICATION_OPTION
    ctypedef int D2D1_COMPATIBLE_RENDER_TARGET_OPTIONS

    ctypedef struct D2D1_FACTORY_OPTIONS:
        D2D1_DEBUG_LEVEL debugLevel
    ctypedef struct D2D1_PIXEL_FORMAT:
         DXGI_FORMAT     format
         D2D1_ALPHA_MODE alphaMode
    ctypedef struct D2D1_RENDER_TARGET_PROPERTIES:
         D2D1_RENDER_TARGET_TYPE  type
         D2D1_PIXEL_FORMAT        pixelFormat
         float                    dpiX
         float                    dpiY
         D2D1_RENDER_TARGET_USAGE usage
         D2D1_FEATURE_LEVEL       minLevel
    ctypedef struct D2D1_SIZE_U:
        UINT32 width
        UINT32 height
    ctypedef struct D2D1_HWND_RENDER_TARGET_PROPERTIES:
       HWND                 hwnd
       D2D1_SIZE_U          pixelSize
       D2D1_PRESENT_OPTIONS presentOptions
    ctypedef struct D3DCOLORVALUE:
        float r
        float g
        float b
        float a
    ctypedef D3DCOLORVALUE D2D1_COLOR_F
    ctypedef struct D2D1_MATRIX_3X2_F:
        float m11
        float m12
        float m21
        float m22
        float dx
        float dy
    ctypedef struct D2D1_BRUSH_PROPERTIES:
        FLOAT             opacity
        D2D1_MATRIX_3X2_F transform
    ctypedef struct D2D1_RECT_F:
        float left
        float top
        float right
        float bottom
    ctypedef UINT64 D2D1_TAG
    ctypedef struct D2D1_DRAWING_STATE_DESCRIPTION:
        D2D1_ANTIALIAS_MODE antialiasMode
        D2D1_TEXT_ANTIALIAS_MODE textAntialiasMode
        D2D1_TAG tag1
        D2D1_TAG tag2
        D2D1_MATRIX_3X2_F transform
    ctypedef struct D2D1_STROKE_STYLE_PROPERTIES:
        D2D1_CAP_STYLE  startCap
        D2D1_CAP_STYLE  endCap
        D2D1_CAP_STYLE  dashCap
        D2D1_LINE_JOIN  lineJoin
        FLOAT           miterLimit
        D2D1_DASH_STYLE dashStyle
        FLOAT           dashOffset
    ctypedef struct D2D1_TRIANGLE:
        UINT32 point1
        UINT32 point2
        UINT32 point3

    ctypedef struct D2D1_POINT_2F:
        float x
        float y
    ctypedef struct D2D1_BEZIER_SEGMENT:
        D2D1_POINT_2F point1
        D2D1_POINT_2F point2
        D2D1_POINT_2F point3
    ctypedef struct D2D1_SIZE_F:
        float width
        float height
    ctypedef struct D2D1_ROUNDED_RECT:
        D2D1_RECT_F rect
        FLOAT         radiusX
        FLOAT         radiusY
    ctypedef struct D2D1_LAYER_PARAMETERS:
        D2D1_RECT_F      contentBounds
        ID2D1Geometry    *geometricMask
        D2D1_ANTIALIAS_MODE maskAntialiasMode
        D2D1_MATRIX_3X2_F  maskTransform
        FLOAT             opacity
        ID2D1Brush        *opacityBrush
        D2D1_LAYER_OPTIONS layerOptions
    ctypedef struct D2D1_ARC_SEGMENT:
        D2D1_POINT_2F        point
        D2D1_SIZE_F          size
        FLOAT                rotationAngle
        D2D1_SWEEP_DIRECTION sweepDirection
        D2D1_ARC_SIZE        arcSize
    ctypedef struct D2D1_QUADRATIC_BEZIER_SEGMENT:
        D2D1_POINT_2F point1
        D2D1_POINT_2F point2
    ctypedef struct D2D1_ELLIPSE:
        D2D1_POINT_2F point
        FLOAT         radiusX
        FLOAT         radiusY
    ctypedef struct D2D1_BITMAP_PROPERTIES:
        D2D1_PIXEL_FORMAT pixelFormat
        FLOAT             dpiX
        FLOAT             dpiY
    ctypedef struct D2D1_GRADIENT_STOP:
        FLOAT         position
        D2D1_COLOR_F  color
    ctypedef struct D2D1_LINEAR_GRADIENT_BRUSH_PROPERTIES:
        D2D1_POINT_2F startPoint
        D2D1_POINT_2F endPoint
    ctypedef struct D2D1_RADIAL_GRADIENT_BRUSH_PROPERTIES:
        D2D1_POINT_2F center
        D2D1_POINT_2F gradientOriginOffset
        FLOAT         radiusX
        FLOAT         radiusY
    ctypedef struct D2D1_BITMAP_BRUSH_PROPERTIES:
        D2D1_EXTEND_MODE               extendModeX
        D2D1_EXTEND_MODE               extendModeY
        D2D1_BITMAP_INTERPOLATION_MODE interpolationMode
    ctypedef struct RECT:
        LONG left
        LONG top
        LONG right
        LONG bottom

    cdef cppclass ID2D1Bitmap:
        D2D1_SIZE_F GetSize() noexcept nogil
        D2D1_SIZE_U GetPixelSize() noexcept nogil
    cdef cppclass ID2D1Layer
    cdef cppclass ID2D1GradientStopCollection
    cdef cppclass ID2D1LinearGradientBrush:
        D2D1_POINT_2F GetStartPoint() noexcept nogil
        D2D1_POINT_2F GetEndPoint() noexcept nogil
    cdef cppclass ID2D1RadialGradientBrush:
        D2D1_POINT_2F GetCenter() noexcept nogil
        D2D1_POINT_2F GetGradientOriginOffset() noexcept nogil
        FLOAT GetRadiusX() noexcept nogil
        FLOAT GetRadiusY() noexcept nogil
    cdef cppclass ID2D1BitmapBrush:
        pass
    cdef cppclass ID2D1Brush:
        FLOAT GetOpacity() noexcept nogil
    cdef cppclass ID2D1PathGeometry:
        HRESULT Open(ID2D1GeometrySink **geometrySink) noexcept nogil
    cdef cppclass ID2D1StrokeStyle
    cdef cppclass ID2D1Factory:
        HRESULT CreateHwndRenderTarget(
            const D2D1_RENDER_TARGET_PROPERTIES *renderTargetProperties,
            const D2D1_HWND_RENDER_TARGET_PROPERTIES *hwndRenderTargetProperties,
            ID2D1HwndRenderTarget **hwndRenderTarget) noexcept nogil
        HRESULT CreateDCRenderTarget(
            const D2D1_RENDER_TARGET_PROPERTIES *renderTargetProperties,
            ID2D1DCRenderTarget **dcRenderTarget) noexcept nogil
        HRESULT CreateWicBitmapRenderTarget(
            IWICBitmap *target,
            const D2D1_RENDER_TARGET_PROPERTIES *renderTargetProperties,
            ID2D1RenderTarget **wicRenderTarget) noexcept nogil
        HRESULT CreatePathGeometry(ID2D1PathGeometry **pathGeometry) noexcept nogil
        HRESULT CreateStrokeStyle(
            const D2D1_STROKE_STYLE_PROPERTIES *strokeStyleProperties,
            const FLOAT *dashes,
            UINT dashesCount,
            ID2D1StrokeStyle **strokeStyle) noexcept nogil
        HRESULT CreateDrawingStateBlock(
            const D2D1_DRAWING_STATE_DESCRIPTION *drawingStateDescription,
            IDWriteRenderingParams *textRenderingParams,
            ID2D1DrawingStateBlock **drawingStateBlock) noexcept nogil
    cdef cppclass ID2D1Geometry:
        HRESULT FillContainsPoint(
            D2D1_POINT_2F point,
            const D2D1_MATRIX_3X2_F *worldTransform,
            FLOAT flatteningTolerance,
            BOOL *contains) noexcept nogil
        HRESULT StrokeContainsPoint(
            D2D1_POINT_2F point,
            FLOAT strokeWidth,
            ID2D1StrokeStyle *strokeStyle,
            const D2D1_MATRIX_3X2_F *worldTransform,
            FLOAT flatteningTolerance,
            BOOL *contains) noexcept nogil
        HRESULT GetBounds(
            const D2D1_MATRIX_3X2_F *worldTransform,
            D2D1_RECT_F *bounds) noexcept nogil
        HRESULT GetWidenedBounds(
            FLOAT strokeWidth,
            ID2D1StrokeStyle *strokeStyle,
            const D2D1_MATRIX_3X2_F *worldTransform,
            FLOAT flatteningTolerance,
            D2D1_RECT_F *bounds) noexcept nogil
        HRESULT CombineWithGeometry(
            ID2D1Geometry *inputGeometry,
            D2D1_COMBINE_MODE combineMode,
            const D2D1_MATRIX_3X2_F *inputGeometryTransform,
            FLOAT flatteningTolerance,
            ID2D1SimplifiedGeometrySink *geometrySink) noexcept nogil
        HRESULT ComputeArea(
            const D2D1_MATRIX_3X2_F *worldTransform,
            FLOAT *area) noexcept nogil
        HRESULT CompareWithGeometry(
            ID2D1Geometry *inputGeometry,
            const D2D1_MATRIX_3X2_F *inputGeometryTransform,
            FLOAT flatteningTolerance,
            D2D1_GEOMETRY_RELATION *relation) noexcept nogil
        HRESULT Tessellate(
            const D2D1_MATRIX_3X2_F *worldTransform,
            FLOAT flatteningTolerance,
            ID2D1TessellationSink *tessellationSink) noexcept nogil
        HRESULT Outline(
            const D2D1_MATRIX_3X2_F *worldTransform,
            FLOAT flatteningTolerance,
            ID2D1SimplifiedGeometrySink *geometrySink) noexcept nogil
        HRESULT Simplify(
            D2D1_GEOMETRY_SIMPLIFICATION_OPTION simplificationOption,
            const D2D1_MATRIX_3X2_F *worldTransform,
            FLOAT flatteningTolerance,
            ID2D1SimplifiedGeometrySink *geometrySink) noexcept nogil
    cdef cppclass ID2D1GeometrySink:
        void AddArc(const D2D1_ARC_SEGMENT *arc) noexcept nogil
        void AddBezier(const D2D1_BEZIER_SEGMENT *bezier) noexcept nogil
        void AddLine(D2D1_POINT_2F point) noexcept nogil
        void AddQuadraticBezier(const D2D1_QUADRATIC_BEZIER_SEGMENT *bezier) noexcept nogil
        void BeginFigure(D2D1_POINT_2F startPoint, D2D1_FIGURE_BEGIN figureBegin) noexcept nogil
        HRESULT Close() noexcept nogil
        void EndFigure(D2D1_FIGURE_END figureEnd) noexcept nogil
        void SetFillMode(D2D1_FILL_MODE fillMode) noexcept nogil
    cdef cppclass ID2D1HwndRenderTarget:
        HRESULT Resize(const D2D1_SIZE_U *pixelSize) noexcept nogil
    cdef cppclass ID2D1DCRenderTarget:
        HRESULT BindDC(HDC hDC, const RECT *pSubRect) noexcept nogil
    cdef cppclass ID2D1RenderTarget:
        void BeginDraw() noexcept nogil
        void Clear(const D2D1_COLOR_F *clearColor) noexcept nogil
        void PushAxisAlignedClip(
            const D2D1_RECT_F *clipRect,
            D2D1_ANTIALIAS_MODE antialiasMode) noexcept nogil
        void PopAxisAlignedClip() noexcept nogil
        HRESULT CreateLayer(
            const D2D1_SIZE_F *size,
            ID2D1Layer **layer) noexcept nogil
        void PushLayer(
            const D2D1_LAYER_PARAMETERS *layerParameters,
            ID2D1Layer *layer) noexcept nogil
        void PopLayer() noexcept nogil
        HRESULT CreateBitmapFromWicBitmap(
            IWICBitmapSource *wicBitmapSource,
            const D2D1_BITMAP_PROPERTIES *bitmapProperties,
            ID2D1Bitmap **bitmap) noexcept nogil
        HRESULT CreateSolidColorBrush(
            const D2D1_COLOR_F *color,
            const D2D1_BRUSH_PROPERTIES *brushProperties,
            ID2D1SolidColorBrush **solidColorBrush) noexcept nogil
        HRESULT CreateGradientStopCollection(
            const D2D1_GRADIENT_STOP *gradientStops,
            UINT32 gradientStopsCount,
            D2D1_GAMMA colorInterpolationGamma,
            D2D1_EXTEND_MODE extendMode,
            ID2D1GradientStopCollection **gradientStopCollection) noexcept nogil
        HRESULT CreateLinearGradientBrush(
            const D2D1_LINEAR_GRADIENT_BRUSH_PROPERTIES *linearGradientBrushProperties,
            const D2D1_BRUSH_PROPERTIES *brushProperties,
            ID2D1GradientStopCollection *gradientStopCollection,
            ID2D1LinearGradientBrush **linearGradientBrush) noexcept nogil
        HRESULT CreateRadialGradientBrush(
            const D2D1_RADIAL_GRADIENT_BRUSH_PROPERTIES *radialGradientBrushProperties,
            const D2D1_BRUSH_PROPERTIES *brushProperties,
            ID2D1GradientStopCollection *gradientStopCollection,
            ID2D1RadialGradientBrush **radialGradientBrush) noexcept nogil
        HRESULT CreateBitmapBrush(
            ID2D1Bitmap *bitmap,
            const D2D1_BITMAP_BRUSH_PROPERTIES *bitmapBrushProperties,
            const D2D1_BRUSH_PROPERTIES *brushProperties,
            ID2D1BitmapBrush **bitmapBrush) noexcept nogil
        void DrawBitmap(
            ID2D1Bitmap *bitmap,
            const D2D1_RECT_F& destinationRectangle,
            FLOAT opacity,
            D2D1_BITMAP_INTERPOLATION_MODE interpolationMode,
            const D2D1_RECT_F *sourceRectangle) noexcept nogil
        void DrawEllipse(
            const D2D1_ELLIPSE *ellipse,
            ID2D1Brush *brush,
            FLOAT strokeWidth,
            ID2D1StrokeStyle *strokeStyle) noexcept nogil
        void DrawGeometry(
            ID2D1Geometry *geometry,
            ID2D1Brush *brush,
            FLOAT strokeWidth,
            ID2D1StrokeStyle *strokeStyle) noexcept nogil
        void DrawLine(
            D2D1_POINT_2F point0,
            D2D1_POINT_2F point1,
            ID2D1Brush *brush,
            FLOAT strokeWidth,
            ID2D1StrokeStyle *strokeStyle) noexcept nogil
        void DrawRectangle(
            const D2D1_RECT_F *rect,
            ID2D1Brush *brush,
            FLOAT strokeWidth,
            ID2D1StrokeStyle *strokeStyle) noexcept nogil
        void DrawRoundedRectangle(
            const D2D1_ROUNDED_RECT *roundedRect,
            ID2D1Brush *brush,
            FLOAT strokeWidth,
            ID2D1StrokeStyle *strokeStyle) noexcept nogil
        void FillRoundedRectangle(
            const D2D1_ROUNDED_RECT *roundedRect,
            ID2D1Brush *brush) noexcept nogil
        void DrawTextW(
            const WCHAR *string,
            UINT stringLength,
            IDWriteTextFormat *textFormat,
            const D2D1_RECT_F &layoutRect,
            ID2D1Brush *defaultForegroundBrush,
            D2D1_DRAW_TEXT_OPTIONS options,
            DWRITE_MEASURING_MODE measuringMode) noexcept nogil
        void DrawTextLayout(
            D2D1_POINT_2F origin,
            IDWriteTextLayout *textLayout,
            ID2D1Brush *defaultForegroundBrush,
            D2D1_DRAW_TEXT_OPTIONS options) noexcept nogil
        HRESULT EndDraw(D2D1_TAG *tag1, D2D1_TAG *tag2) noexcept nogil
        void FillEllipse(const D2D1_ELLIPSE *ellipse, ID2D1Brush *brush) noexcept nogil
        void FillGeometry(
            ID2D1Geometry *geometry,
            ID2D1Brush *brush,
            ID2D1Brush *opacityBrush) noexcept nogil
        void FillRectangle(const D2D1_RECT_F *rect, ID2D1Brush *brush) noexcept nogil
        void GetTransform(D2D1_MATRIX_3X2_F *transform) noexcept nogil
        void SetAntialiasMode(D2D1_ANTIALIAS_MODE antialiasMode) noexcept nogil
        void SetTransform(const D2D1_MATRIX_3X2_F *transform) noexcept nogil
        void SaveDrawingState(ID2D1DrawingStateBlock *drawingStateBlock) noexcept nogil
        void RestoreDrawingState(ID2D1DrawingStateBlock *drawingStateBlock) noexcept nogil
        HRESULT Flush(D2D1_TAG *tag1, D2D1_TAG *tag2) noexcept nogil
        void SetTextAntialiasMode(D2D1_TEXT_ANTIALIAS_MODE textAntialiasMode) noexcept nogil
        D2D1_TEXT_ANTIALIAS_MODE GetTextAntialiasMode() noexcept nogil
        void GetDpi(FLOAT *dpiX, FLOAT *dpiY) noexcept nogil
        void SetDpi(FLOAT dpiX, FLOAT dpiY) noexcept nogil
        HRESULT CreateCompatibleRenderTarget(
            D2D1_SIZE_F desiredSize,
            D2D1_SIZE_U desiredPixelSize,
            D2D1_PIXEL_FORMAT desiredFormat,
            D2D1_COMPATIBLE_RENDER_TARGET_OPTIONS options,
            ID2D1BitmapRenderTarget **bitmapRenderTarget) noexcept nogil
        BOOL IsSupported(const D2D1_RENDER_TARGET_PROPERTIES *renderTargetProperties) noexcept nogil
    cdef cppclass ID2D1BitmapRenderTarget(ID2D1RenderTarget):
        HRESULT GetBitmap(ID2D1Bitmap **bitmap) noexcept nogil
    cdef cppclass ID2D1DrawingStateBlock:
        void GetDescription(D2D1_DRAWING_STATE_DESCRIPTION *stateDescription) noexcept nogil
        void SetDescription(const D2D1_DRAWING_STATE_DESCRIPTION *stateDescription) noexcept nogil
    cdef cppclass ID2D1SimplifiedGeometrySink:
        void BeginFigure(D2D1_POINT_2F startPoint, int figureBegin) noexcept nogil
        HRESULT Close() noexcept nogil
        void EndFigure(int figureEnd) noexcept nogil
        void SetFillMode(D2D1_FILL_MODE fillMode) noexcept nogil
    cdef cppclass ID2D1TessellationSink:
        void AddTriangles(const D2D1_TRIANGLE *triangles, UINT32 trianglesCount) noexcept nogil
        HRESULT Close() noexcept nogil
    cdef cppclass ID2D1SolidColorBrush:
        void SetColor(const D2D1_COLOR_F *color) noexcept nogil
        D2D1_COLOR_F GetColor() noexcept nogil
    cdef cppclass IWICBitmapSource

    cdef const GUID IID_ID2D1Factory

    HRESULT D2D1CreateFactory(
        D2D1_FACTORY_TYPE factoryType,
        const GUID& riid,
        const D2D1_FACTORY_OPTIONS *pFactoryOptions,
        void **ppIFactory) noexcept nogil


cdef extern from "wincodec.h":
    ctypedef int WICBitmapCreateCacheOption
    ctypedef int WICDecodeOptions
    ctypedef int WICBitmapDitherType
    ctypedef int WICBitmapPaletteType
    ctypedef int WICBitmapEncoderCacheOption

    cdef GUID CLSID_WICImagingFactory
    cdef GUID IID_IWICImagingFactory

    cdef unsigned int GENERIC_READ
    cdef unsigned int GENERIC_WRITE

    ctypedef struct WICRect:
        int X
        int Y
        int Width
        int Height

    cdef cppclass IWICBitmapSource
    cdef cppclass IWICPalette

    cdef cppclass IWICBitmapLock(IUnknown):
        HRESULT GetDataPointer(UINT *pcbBufferSize, BYTE **ppbData) noexcept nogil

    cdef cppclass IWICBitmap(IUnknown):
        HRESULT Lock(const WICRect *prcLock, DWORD flags, IWICBitmapLock **ppILock) noexcept nogil
        HRESULT GetSize(UINT *puiWidth, UINT *puiHeight) noexcept nogil

    cdef cppclass IWICBitmapDecoder(IUnknown):
        HRESULT GetFrame(UINT index, IWICBitmapFrameDecode **ppIBitmapFrame) noexcept nogil

    cdef cppclass IWICBitmapFrameDecode(IUnknown)

    cdef cppclass IWICFormatConverter(IUnknown):
        HRESULT Initialize(
            IWICBitmapSource *pISource,
            const GUID &dstFormat,
            WICBitmapDitherType dither,
            const IUnknown *pIPalette,
            double alphaThresholdPercent,
            WICBitmapPaletteType paletteTranslate) noexcept nogil

    cdef cppclass IWICStream(IStream):
        HRESULT InitializeFromFilename(
            const WCHAR *wzFilename,
            DWORD dwDesiredAccess) noexcept nogil

    cdef cppclass IWICBitmapEncoder(IUnknown):
        HRESULT Initialize(
            IStream *pIStream,
            WICBitmapEncoderCacheOption cacheOption) noexcept nogil
        HRESULT CreateNewFrame(
            IWICBitmapFrameEncode **ppIFrameEncode,
            void **ppIEncoderOptions) noexcept nogil
        HRESULT Commit() noexcept nogil

    cdef cppclass IWICBitmapFrameEncode(IUnknown):
        HRESULT Initialize(
            void *pIEncoderOptions) noexcept nogil
        HRESULT SetSize(
            UINT uiWidth,
            UINT uiHeight) noexcept nogil
        HRESULT WriteSource(
            IWICBitmapSource *pIBitmapSource,
            WICRect *prc) noexcept nogil
        HRESULT Commit() noexcept nogil

    cdef cppclass IWICImagingFactory(IUnknown):
        HRESULT CreateBitmap(
            UINT uiWidth,
            UINT uiHeight,
            const GUID &pixelFormat,
            WICBitmapCreateCacheOption option,
            IWICBitmap **ppIBitmap) noexcept nogil
        HRESULT CreateDecoderFromFilename(
            const WCHAR *wzFilename,
            const GUID *pguidVendor,
            DWORD dwDesiredAccess,
            WICDecodeOptions metadataOptions,
            IWICBitmapDecoder **ppIDecoder) noexcept nogil
        HRESULT CreateFormatConverter(
            IWICFormatConverter **ppIFormatConverter) noexcept nogil
        HRESULT CreateStream(
            IWICStream **ppIStream) noexcept nogil
        HRESULT CreateEncoder(
            const GUID &guidContainerFormat,
            const GUID *pguidVendor,
            IWICBitmapEncoder **ppIEncoder) noexcept nogil


cdef getHRESULTstring(int hr):
    cdef int strBufLen = 0x1000
    cdef wchar_t[0x1000] strBuf
    cdef unsigned int ncopied = FormatMessageW(
        0x1200,
        NULL,
        hr,
        0,
        strBuf,
        strBufLen,
        NULL)
    if ncopied == 0:
        return 'unknown error %08x' % hr
    return PyUnicode_FromWideChar(strBuf, ncopied).rstrip("\r\n")


cdef extern from *:
    """
    #include <wincodec.h>

    static HRESULT _WIC_SaveToFile(
        IWICImagingFactory* pFactory,
        IWICBitmap* pBitmap,
        const wchar_t* filename,
        REFGUID containerFormat,
        const GUID* pVendor)
    {
        IWICStream* pStream = NULL;
        IWICBitmapEncoder* pEncoder = NULL;
        IWICBitmapFrameEncode* pFrame = NULL;
        UINT w, h;
        HRESULT hr;

        hr = pFactory->CreateStream(&pStream);
        if (FAILED(hr)) return hr;

        hr = pStream->InitializeFromFilename(filename, GENERIC_WRITE);
        if (FAILED(hr)) { pStream->Release(); return hr; }

        hr = pFactory->CreateEncoder(containerFormat, pVendor, &pEncoder);
        if (FAILED(hr)) { pStream->Release(); return hr; }

        hr = pEncoder->Initialize(pStream, WICBitmapEncoderNoCache);
        if (FAILED(hr)) { pEncoder->Release(); pStream->Release(); return hr; }

        pBitmap->GetSize(&w, &h);

        hr = pEncoder->CreateNewFrame(&pFrame, NULL);
        if (FAILED(hr)) { pEncoder->Release(); pStream->Release(); return hr; }

        hr = pFrame->Initialize(NULL);
        if (FAILED(hr)) { pFrame->Release(); pEncoder->Release(); pStream->Release(); return hr; }

        hr = pFrame->SetSize(w, h);
        if (FAILED(hr)) { pFrame->Release(); pEncoder->Release(); pStream->Release(); return hr; }

        hr = pFrame->WriteSource(pBitmap, NULL);
        if (FAILED(hr)) { pFrame->Release(); pEncoder->Release(); pStream->Release(); return hr; }

        hr = pFrame->Commit();
        if (FAILED(hr)) { pFrame->Release(); pEncoder->Release(); pStream->Release(); return hr; }

        hr = pEncoder->Commit();
        if (FAILED(hr)) { pFrame->Release(); pEncoder->Release(); pStream->Release(); return hr; }

        pFrame->Release();
        pEncoder->Release();
        pStream->Release();
        return hr;
    }
    """
    HRESULT _WIC_SaveToFile(
        IWICImagingFactory* pFactory,
        IWICBitmap* pBitmap,
        const wchar_t* filename,
        const GUID& containerFormat,
        const GUID* pVendor)


class COMError(OSError):
    def __init__(self, hresult):
        self.hresult = hresult
        self.args = (getHRESULTstring(hresult),)


class Direct2DError(COMError):
    pass

def InitializeCOM(options=0):
    cdef HRESULT hr = CoInitializeEx(NULL, options)
    if hr == 1:
        # already initialized
        pass
    elif FAILED(hr):
        raise COMError(hr)

def UninitializeCOM():
    CoUninitialize()

cdef class COMObject:
    cdef void* ptr

    def __init__(self):
        raise TypeError("This class cannot be instantiated directly.")

    cpdef Release(self):
        if self.ptr is not NULL:
            (<IUnknown*>self.ptr).Release()
            self.ptr = NULL

    def __dealloc__(self):
        self.Release()


_d2d_factory = None

def GetD2DFactory():
    global _d2d_factory
    if _d2d_factory is None:
        _d2d_factory = D2DFactory()
    return _d2d_factory

_wic_factory = None

def GetWICFactory():
    global _wic_factory
    if _wic_factory is None:
        _wic_factory = WICFactory()
    return _wic_factory

cdef class WICFactory(COMObject):
    def __init__(self):
        cdef IWICImagingFactory* factory
        CoInitializeEx(NULL, 2)
        res = CoCreateInstance(
            CLSID_WICImagingFactory,
            NULL,
            1,  # CLSCTX_INPROC_SERVER
            IID_IWICImagingFactory,
            <void**>&factory)
        if FAILED(res):
            raise COMError(res)
        self.ptr = <void*>factory

    def __dealloc__(self):
        self.Release()
        CoUninitialize()

    def CreateBitmap(self, int width, int height, guid_bytes=None):
        if guid_bytes is not None:
            raise NotImplementedError("Custom pixel format not yet supported")
        cdef IWICBitmap* bitmap
        res = (<IWICImagingFactory*>self.ptr).CreateBitmap(
            width, height,
            _WicPbgraFormat,
            <WICBitmapCreateCacheOption>1,
            &bitmap)
        if FAILED(res):
            raise COMError(res)
        cdef WICBitmap obj = WICBitmap.__new__(WICBitmap)
        obj.ptr = <void*>bitmap
        return obj

    def CreateDecoderFromFilename(self, str filename):
        cdef Py_ssize_t wlen = 0
        cdef wchar_t* wfilename = PyUnicode_AsWideCharString(filename, &wlen)
        if wfilename == NULL:
            raise MemoryError("Failed to convert filename to wide char")
        cdef IWICBitmapDecoder* decoder
        cdef HRESULT res
        res = (<IWICImagingFactory*>self.ptr).CreateDecoderFromFilename(
            wfilename, NULL, <DWORD>GENERIC_READ, <WICDecodeOptions>0, &decoder)
        PyMem_Free(wfilename)
        if FAILED(res):
            raise COMError(res)
        cdef WICBitmapDecoder obj = WICBitmapDecoder.__new__(WICBitmapDecoder)
        obj.ptr = <void*>decoder
        return obj

    def CreateFormatConverter(self):
        cdef IWICFormatConverter* converter
        res = (<IWICImagingFactory*>self.ptr).CreateFormatConverter(&converter)
        if FAILED(res):
            raise COMError(res)
        cdef WICFormatConverter obj = WICFormatConverter.__new__(WICFormatConverter)
        obj.ptr = <void*>converter
        return obj

    def SaveBitmap(self, WICBitmap bitmap not None, str filename):
        cdef Py_ssize_t wlen = 0
        cdef wchar_t* wfilename = PyUnicode_AsWideCharString(filename, &wlen)
        if wfilename == NULL:
            raise MemoryError("Failed to convert filename to wide char")

        cdef HRESULT res
        cdef const GUID* pVendor = NULL
        fn_lower = filename.lower()

        if fn_lower.endswith('.png'):
            res = _WIC_SaveToFile(
                <IWICImagingFactory*>self.ptr,
                <IWICBitmap*>bitmap.ptr,
                wfilename,
                _ContainerPngFormat,
                pVendor)
        elif fn_lower.endswith('.bmp'):
            res = _WIC_SaveToFile(
                <IWICImagingFactory*>self.ptr,
                <IWICBitmap*>bitmap.ptr,
                wfilename,
                _ContainerBmpFormat,
                pVendor)
        elif fn_lower.endswith('.jpg') or fn_lower.endswith('.jpeg'):
            res = _WIC_SaveToFile(
                <IWICImagingFactory*>self.ptr,
                <IWICBitmap*>bitmap.ptr,
                wfilename,
                _ContainerJpegFormat,
                pVendor)
        else:
            PyMem_Free(wfilename)
            raise ValueError(f"Unsupported format from filename: {filename}")

        PyMem_Free(wfilename)
        if FAILED(res):
            raise COMError(res)

cdef class D2DFactory(COMObject):
    def __init__(self, int factoryType=0, int debugLevel=0):
        cdef D2D1_FACTORY_OPTIONS options
        cdef ID2D1Factory* factory
        options.debugLevel = <D2D1_DEBUG_LEVEL>debugLevel
        res = D2D1CreateFactory(<D2D1_FACTORY_TYPE>factoryType, IID_ID2D1Factory, &options, <void**>&factory)
        if FAILED(res):
            raise Direct2DError(res)
        self.ptr = <void*>factory

    def CreateHwndRenderTarget(
            self,
            intptr_t hwnd,
            int width,
            int height,
            int presentOptions=0,
            int rtType=0,
            int pixelFormat=0,
            int alphaMode=0,
            float dpiX=0,
            float dpiY=0,
            int usage=0,
            int featureLevel=0):
        cdef D2D1_RENDER_TARGET_PROPERTIES rtp
        rtp.type = <D2D1_RENDER_TARGET_TYPE>rtType
        rtp.pixelFormat.format = <DXGI_FORMAT>pixelFormat
        rtp.pixelFormat.alphaMode = <D2D1_ALPHA_MODE>alphaMode
        rtp.dpiX = dpiX
        rtp.dpiY = dpiY
        rtp.usage = <D2D1_RENDER_TARGET_USAGE>usage
        rtp.minLevel = <D2D1_FEATURE_LEVEL>featureLevel
        cdef D2D1_HWND_RENDER_TARGET_PROPERTIES hrtp
        hrtp.hwnd = <HWND>hwnd
        hrtp.pixelSize.width = width
        hrtp.pixelSize.height = height
        hrtp.presentOptions = <D2D1_PRESENT_OPTIONS>presentOptions
        cdef ID2D1HwndRenderTarget* target
        res = (<ID2D1Factory*>self.ptr).CreateHwndRenderTarget(&rtp, &hrtp, <ID2D1HwndRenderTarget**>&target)
        if FAILED(res):
            raise Direct2DError(res)
        cdef HWNDRenderTarget obj = HWNDRenderTarget.__new__(HWNDRenderTarget)
        obj.ptr = <void*>target
        return obj

    def CreateDCRenderTarget(
            self,
            int rtType=0,
            int pixelFormat=0,
            int alphaMode=0,
            float dpiX=0,
            float dpiY=0,
            int usage=0,
            int featureLevel=0):
        cdef D2D1_RENDER_TARGET_PROPERTIES rtp
        rtp.type = <D2D1_RENDER_TARGET_TYPE>rtType
        rtp.pixelFormat.format = <DXGI_FORMAT>pixelFormat
        rtp.pixelFormat.alphaMode = <D2D1_ALPHA_MODE>alphaMode
        rtp.dpiX = dpiX
        rtp.dpiY = dpiY
        rtp.usage = <D2D1_RENDER_TARGET_USAGE>usage
        rtp.minLevel = <D2D1_FEATURE_LEVEL>featureLevel
        cdef ID2D1DCRenderTarget* target
        res = (<ID2D1Factory*>self.ptr).CreateDCRenderTarget(&rtp, <ID2D1DCRenderTarget**>&target)
        if FAILED(res):
            raise Direct2DError(res)
        cdef DCRenderTarget obj = DCRenderTarget.__new__(DCRenderTarget)
        obj.ptr = <void*>target
        return obj

    def CreateWicBitmapRenderTarget(
            self,
            WICBitmap target,
            int rtType=0,
            int pixelFormat=0,
            int alphaMode=0,
            float dpiX=0,
            float dpiY=0):
        cdef D2D1_RENDER_TARGET_PROPERTIES rtp
        rtp.type = <D2D1_RENDER_TARGET_TYPE>rtType
        rtp.pixelFormat.format = <DXGI_FORMAT>pixelFormat
        rtp.pixelFormat.alphaMode = <D2D1_ALPHA_MODE>alphaMode
        rtp.dpiX = dpiX
        rtp.dpiY = dpiY
        rtp.usage = <D2D1_RENDER_TARGET_USAGE>0
        rtp.minLevel = <D2D1_FEATURE_LEVEL>0
        cdef ID2D1RenderTarget* wrt
        cdef HRESULT res
        res = (<ID2D1Factory*>self.ptr).CreateWicBitmapRenderTarget(
            <IWICBitmap*>target.ptr,
            &rtp,
            <ID2D1RenderTarget**>&wrt)
        if FAILED(res):
            raise Direct2DError(res)
        cdef RenderTarget obj = RenderTarget.__new__(RenderTarget)
        obj.ptr = <void*>wrt
        return obj

    def CreatePathGeometry(self):
        cdef ID2D1PathGeometry* pgm
        res = (<ID2D1Factory*>self.ptr).CreatePathGeometry(<ID2D1PathGeometry**>&pgm)
        if FAILED(res):
            raise Direct2DError(res)
        cdef PathGeometry obj = PathGeometry.__new__(PathGeometry)
        obj.ptr = <void*>pgm
        return obj

    def CreateStrokeStyle(
            self,
            int startCap=0,
            int endCap=0,
            int dashCap=0,
            int lineJoin=0,
            float miterLimit=10.0,
            int dashStyle=0,
            float dashOffset=0.0):
        cdef D2D1_STROKE_STYLE_PROPERTIES ssp
        ssp.startCap = <D2D1_CAP_STYLE>startCap
        ssp.endCap = <D2D1_CAP_STYLE>endCap
        ssp.dashCap = <D2D1_CAP_STYLE>dashCap
        ssp.lineJoin = <D2D1_LINE_JOIN>lineJoin
        ssp.miterLimit = miterLimit
        ssp.dashStyle = <D2D1_DASH_STYLE>dashStyle
        ssp.dashOffset = dashOffset
        cdef ID2D1StrokeStyle *sstyle
        res = (<ID2D1Factory*>self.ptr).CreateStrokeStyle(&ssp, NULL, 0, <ID2D1StrokeStyle**>&sstyle)
        if FAILED(res):
            raise Direct2DError(res)
        cdef StrokeStyle obj = StrokeStyle.__new__(StrokeStyle)
        obj.ptr = <void*>sstyle
        return obj

    def CreateDrawingStateBlock(
            self,
            int antialiasMode=0,
            int textAntialiasMode=0,
            unsigned long long tag1=0,
            unsigned long long tag2=0,
            float transform_m11=1.0, float transform_m12=0.0,
            float transform_m21=0.0, float transform_m22=1.0,
            float transform_dx=0.0, float transform_dy=0.0):
        cdef D2D1_DRAWING_STATE_DESCRIPTION desc
        desc.antialiasMode = <D2D1_ANTIALIAS_MODE>antialiasMode
        desc.textAntialiasMode = <D2D1_TEXT_ANTIALIAS_MODE>textAntialiasMode
        desc.tag1 = tag1
        desc.tag2 = tag2
        desc.transform.m11 = transform_m11
        desc.transform.m12 = transform_m12
        desc.transform.m21 = transform_m21
        desc.transform.m22 = transform_m22
        desc.transform.dx = transform_dx
        desc.transform.dy = transform_dy
        cdef ID2D1DrawingStateBlock *block = NULL
        cdef HRESULT res = (<ID2D1Factory*>self.ptr).CreateDrawingStateBlock(
            &desc, NULL, &block)
        if FAILED(res):
            raise Direct2DError(res)
        cdef DrawingStateBlock obj = DrawingStateBlock.__new__(DrawingStateBlock)
        obj.ptr = <void*>block
        return obj


cdef class Resource(COMObject):
    pass


cdef class RenderTarget(Resource):
    def BeginDraw(self):
        (<ID2D1RenderTarget*>self.ptr).BeginDraw()

    def Clear(self, float r, float g, float b, float a=1.0):
        cdef D2D1_COLOR_F color
        color.r = r
        color.g = g
        color.b = b
        color.a = a
        (<ID2D1RenderTarget*>self.ptr).Clear(&color)

    def CreateBitmapFromWicBitmap(self, source, int dxgiFormat=0, int alphaMode=1, float dpiX=96.0, float dpiY=96.0):
        cdef D2D1_BITMAP_PROPERTIES properties
        properties.pixelFormat.format = <DXGI_FORMAT>dxgiFormat
        properties.pixelFormat.alphaMode = <D2D1_ALPHA_MODE>alphaMode
        properties.dpiX = dpiX
        properties.dpiY = dpiY
        cdef ID2D1Bitmap *bitmap = NULL
        cdef HRESULT res
        cdef void* src_ptr = (<COMObject?>source).ptr
        res = (<ID2D1RenderTarget*>self.ptr).CreateBitmapFromWicBitmap(
            <IWICBitmapSource*>src_ptr,
            &properties,
            <ID2D1Bitmap**>&bitmap)
        if FAILED(res):
            raise Direct2DError(res)
        cdef Bitmap obj = Bitmap.__new__(Bitmap)
        obj.ptr = <void*>bitmap
        return obj

    def CreateSolidColorBrush(self, float r, float g, float b, float a=1.0, float opacity=1.0):
        cdef D2D1_COLOR_F color
        color.r = r
        color.g = g
        color.b = b
        color.a = a
        cdef D2D1_BRUSH_PROPERTIES bprop
        bprop.opacity = opacity
        bprop.transform.m11 = 1.0
        bprop.transform.m12 = 0.0
        bprop.transform.m21 = 0.0
        bprop.transform.m22 = 1.0
        bprop.transform.dx = 0.0
        bprop.transform.dy = 0.0
        cdef ID2D1SolidColorBrush *brush
        res = (<ID2D1RenderTarget*>self.ptr).CreateSolidColorBrush(&color, &bprop, &brush)
        if FAILED(res):
            raise Direct2DError(res)
        cdef SolidColorBrush obj = SolidColorBrush.__new__(SolidColorBrush)
        obj.ptr = <void*>brush
        return obj

    def CreateGradientStopCollection(self, stops, int gamma=0, int extendMode=0):
        cdef int n = len(stops)
        cdef D2D1_GRADIENT_STOP* gstops = <D2D1_GRADIENT_STOP*>PyMem_Malloc(n * sizeof(D2D1_GRADIENT_STOP))
        cdef ID2D1GradientStopCollection* gsc = NULL
        cdef GradientStopCollection obj
        cdef HRESULT res
        cdef void* tmp_gsc
        if gstops == NULL:
            raise MemoryError
        try:
            for i in range(n):
                pos, r, g, b, a = stops[i]
                gstops[i].position = pos
                gstops[i].color.r = r
                gstops[i].color.g = g
                gstops[i].color.b = b
                gstops[i].color.a = a
            res = (<ID2D1RenderTarget*>self.ptr).CreateGradientStopCollection(
                gstops, n,
                <D2D1_GAMMA>gamma,
                <D2D1_EXTEND_MODE>extendMode,
                <ID2D1GradientStopCollection**>&tmp_gsc)
            gsc = <ID2D1GradientStopCollection*>tmp_gsc
            if FAILED(res):
                raise Direct2DError(res)
        finally:
            PyMem_Free(gstops)
        obj = GradientStopCollection.__new__(GradientStopCollection)
        obj.ptr = <void*>gsc
        return obj

    def CreateLinearGradientBrush(
            self,
            GradientStopCollection gradientStopCollection,
            float x1, float y1, float x2, float y2,
            float opacity=1.0):
        cdef D2D1_LINEAR_GRADIENT_BRUSH_PROPERTIES lgprop
        lgprop.startPoint.x = x1
        lgprop.startPoint.y = y1
        lgprop.endPoint.x = x2
        lgprop.endPoint.y = y2
        cdef D2D1_BRUSH_PROPERTIES bprop
        bprop.opacity = opacity
        bprop.transform.m11 = 1.0
        bprop.transform.m12 = 0.0
        bprop.transform.m21 = 0.0
        bprop.transform.m22 = 1.0
        bprop.transform.dx = 0.0
        bprop.transform.dy = 0.0
        cdef ID2D1LinearGradientBrush* brush
        res = (<ID2D1RenderTarget*>self.ptr).CreateLinearGradientBrush(
            &lgprop, &bprop,
            <ID2D1GradientStopCollection*>gradientStopCollection.ptr,
            &brush)
        if FAILED(res):
            raise Direct2DError(res)
        cdef LinearGradientBrush obj = LinearGradientBrush.__new__(LinearGradientBrush)
        obj.ptr = <void*>brush
        return obj

    def CreateRadialGradientBrush(
            self,
            GradientStopCollection gradientStopCollection,
            float cx, float cy, float ox, float oy, float rx, float ry,
            float opacity=1.0):
        cdef D2D1_RADIAL_GRADIENT_BRUSH_PROPERTIES rgprop
        rgprop.center.x = cx
        rgprop.center.y = cy
        rgprop.gradientOriginOffset.x = ox
        rgprop.gradientOriginOffset.y = oy
        rgprop.radiusX = rx
        rgprop.radiusY = ry
        cdef D2D1_BRUSH_PROPERTIES bprop
        bprop.opacity = opacity
        bprop.transform.m11 = 1.0
        bprop.transform.m12 = 0.0
        bprop.transform.m21 = 0.0
        bprop.transform.m22 = 1.0
        bprop.transform.dx = 0.0
        bprop.transform.dy = 0.0
        cdef ID2D1RadialGradientBrush* brush
        res = (<ID2D1RenderTarget*>self.ptr).CreateRadialGradientBrush(
            &rgprop, &bprop,
            <ID2D1GradientStopCollection*>gradientStopCollection.ptr,
            &brush)
        if FAILED(res):
            raise Direct2DError(res)
        cdef RadialGradientBrush obj = RadialGradientBrush.__new__(RadialGradientBrush)
        obj.ptr = <void*>brush
        return obj

    def CreateBitmapBrush(
            self,
            Bitmap bitmap,
            int extendModeX=0,
            int extendModeY=0,
            int interpolationMode=1,
            float opacity=1.0):
        cdef D2D1_BITMAP_BRUSH_PROPERTIES bbprop
        bbprop.extendModeX = <D2D1_EXTEND_MODE>extendModeX
        bbprop.extendModeY = <D2D1_EXTEND_MODE>extendModeY
        bbprop.interpolationMode = <D2D1_BITMAP_INTERPOLATION_MODE>interpolationMode
        cdef D2D1_BRUSH_PROPERTIES bprop
        bprop.opacity = opacity
        bprop.transform.m11 = 1.0
        bprop.transform.m12 = 0.0
        bprop.transform.m21 = 0.0
        bprop.transform.m22 = 1.0
        bprop.transform.dx = 0.0
        bprop.transform.dy = 0.0
        cdef ID2D1BitmapBrush* brush
        res = (<ID2D1RenderTarget*>self.ptr).CreateBitmapBrush(
            <ID2D1Bitmap*>bitmap.ptr,
            &bbprop, &bprop,
            &brush)
        if FAILED(res):
            raise Direct2DError(res)
        cdef BitmapBrush obj = BitmapBrush.__new__(BitmapBrush)
        obj.ptr = <void*>brush
        return obj

    def PushAxisAlignedClip(self, float left, float top, float right, float bottom, int antialiasMode=0):
        cdef D2D1_RECT_F clipRect
        clipRect.left = left
        clipRect.top = top
        clipRect.right = right
        clipRect.bottom = bottom
        (<ID2D1RenderTarget*>self.ptr).PushAxisAlignedClip(
            &clipRect, <D2D1_ANTIALIAS_MODE>antialiasMode)

    def PopAxisAlignedClip(self):
        (<ID2D1RenderTarget*>self.ptr).PopAxisAlignedClip()

    def CreateLayer(self, float width=0, float height=0):
        cdef D2D1_SIZE_F sz
        cdef D2D1_SIZE_F* pSize = NULL
        if width > 0 and height > 0:
            sz.width = width
            sz.height = height
            pSize = &sz
        cdef ID2D1Layer* layer = NULL
        cdef void* tmp_layer
        res = (<ID2D1RenderTarget*>self.ptr).CreateLayer(pSize, <ID2D1Layer**>&tmp_layer)
        layer = <ID2D1Layer*>tmp_layer
        if FAILED(res):
            raise Direct2DError(res)
        cdef Layer obj = Layer.__new__(Layer)
        obj.ptr = <void*>layer
        return obj

    def PushLayer(
            self,
            Layer layer,
            float contentLeft=0, float contentTop=0, float contentRight=0, float contentBottom=0,
            geometricMask=None,
            int maskAntialiasMode=0,
            float maskTransform_m11=1, float maskTransform_m12=0,
            float maskTransform_m21=0, float maskTransform_m22=1,
            float maskTransform_dx=0, float maskTransform_dy=0,
            float opacity=1.0,
            opacityBrush=None,
            int layerOptions=0):
        cdef D2D1_LAYER_PARAMETERS lp
        lp.contentBounds.left = contentLeft
        lp.contentBounds.top = contentTop
        lp.contentBounds.right = contentRight
        lp.contentBounds.bottom = contentBottom
        lp.geometricMask = NULL
        if geometricMask is not None:
            lp.geometricMask = <ID2D1Geometry*>((<COMObject?>geometricMask).ptr)
        lp.maskAntialiasMode = <D2D1_ANTIALIAS_MODE>maskAntialiasMode
        lp.maskTransform.m11 = maskTransform_m11
        lp.maskTransform.m12 = maskTransform_m12
        lp.maskTransform.m21 = maskTransform_m21
        lp.maskTransform.m22 = maskTransform_m22
        lp.maskTransform.dx = maskTransform_dx
        lp.maskTransform.dy = maskTransform_dy
        lp.opacity = opacity
        lp.opacityBrush = NULL
        if opacityBrush is not None:
            lp.opacityBrush = <ID2D1Brush*>((<COMObject?>opacityBrush).ptr)
        lp.layerOptions = <D2D1_LAYER_OPTIONS>layerOptions
        (<ID2D1RenderTarget*>self.ptr).PushLayer(
            &lp, <ID2D1Layer*>layer.ptr)

    def PopLayer(self):
        (<ID2D1RenderTarget*>self.ptr).PopLayer()

    def SetTransform(self, float m11, float m12, float m21, float m22, float dx, float dy):
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = m11
        mat.m12 = m12
        mat.m21 = m21
        mat.m22 = m22
        mat.dx = dx
        mat.dy = dy
        (<ID2D1RenderTarget*>self.ptr).SetTransform(&mat)

    def GetTransform(self):
        cdef D2D1_MATRIX_3X2_F mat
        (<ID2D1RenderTarget*>self.ptr).GetTransform(&mat)
        return (mat.m11, mat.m12, mat.m21, mat.m22, mat.dx, mat.dy)

    def SaveDrawingState(self, DrawingStateBlock state):
        (<ID2D1RenderTarget*>self.ptr).SaveDrawingState(
            <ID2D1DrawingStateBlock*>state.ptr)

    def RestoreDrawingState(self, DrawingStateBlock state):
        (<ID2D1RenderTarget*>self.ptr).RestoreDrawingState(
            <ID2D1DrawingStateBlock*>state.ptr)

    def DrawBitmap(
            self,
            Bitmap bitmap,
            float l,
            float t,
            float r,
            float b,
            float opacity=1.0,
            interpolationMode=1,
            srcRect=None):
        cdef D2D1_RECT_F dest, src
        dest.left = l
        dest.top = t
        dest.right = r
        dest.bottom = b
        cdef D2D1_RECT_F *srcRectPtr = NULL
        if srcRect is not None:
            src.left, src.top, src.right, src.bottom = srcRect
            srcRectPtr = &src
        (<ID2D1RenderTarget*>self.ptr).DrawBitmap(
            <ID2D1Bitmap*>bitmap.ptr,
            dest,
            opacity,
            <D2D1_BITMAP_INTERPOLATION_MODE>interpolationMode,
            srcRectPtr)

    def DrawEllipse(
            self,
            float cx,
            float cy,
            float rx,
            float ry,
            Brush brush,
            float strokeWidth=1.0,
            StrokeStyle strokeStyle=None):
        cdef D2D1_ELLIPSE el
        el.point.x = cx
        el.point.y = cy
        el.radiusX = rx
        el.radiusY = ry
        cdef ID2D1StrokeStyle *sstyle
        if strokeStyle is None:
            sstyle = NULL
        else:
            sstyle = <ID2D1StrokeStyle*>strokeStyle.ptr
        (<ID2D1RenderTarget*>self.ptr).DrawEllipse(&el, <ID2D1Brush*>brush.ptr, strokeWidth, sstyle)

    def DrawGeometry(self, Geometry geometry, Brush brush, float strokeWidth=1.0, StrokeStyle strokeStyle=None):
        cdef ID2D1StrokeStyle *sstyle
        if strokeStyle is None:
            sstyle = NULL
        else:
            sstyle = <ID2D1StrokeStyle*>strokeStyle.ptr
        (<ID2D1RenderTarget*>self.ptr).DrawGeometry(
            <ID2D1Geometry*>geometry.ptr,
            <ID2D1Brush*>brush.ptr,
            strokeWidth,
            sstyle)

    def DrawLine(
            self,
            float x1,
            float y1,
            float x2,
            float y2,
            Brush brush,
            float strokeWidth=1.0,
            StrokeStyle strokeStyle=None):
        cdef D2D1_POINT_2F point0
        point0.x = x1
        point0.y = y1
        cdef D2D1_POINT_2F point1
        point1.x = x2
        point1.y = y2
        cdef ID2D1StrokeStyle *sstyle
        if strokeStyle is None:
            sstyle = NULL
        else:
            sstyle = <ID2D1StrokeStyle*>strokeStyle.ptr
        (<ID2D1RenderTarget*>self.ptr).DrawLine(point0, point1, <ID2D1Brush*>brush.ptr, strokeWidth, sstyle)

    def DrawRectangle(
            self,
            float l,
            float t,
            float r,
            float b,
            Brush brush,
            float strokeWidth=1.0,
            StrokeStyle strokeStyle=None):
        cdef D2D1_RECT_F rect
        rect.left = l
        rect.top = t
        rect.right = r
        rect.bottom = b
        cdef ID2D1StrokeStyle *sstyle
        if strokeStyle is None:
            sstyle = NULL
        else:
            sstyle = <ID2D1StrokeStyle*>strokeStyle.ptr
        (<ID2D1RenderTarget*>self.ptr).DrawRectangle(&rect, <ID2D1Brush*>brush.ptr, strokeWidth, sstyle)

    def DrawRoundedRectangle(
            self,
            float l,
            float t,
            float r,
            float b,
            float radiusX,
            float radiusY,
            Brush brush,
            float strokeWidth=1.0,
            StrokeStyle strokeStyle=None):
        cdef D2D1_ROUNDED_RECT rr
        rr.rect.left = l
        rr.rect.top = t
        rr.rect.right = r
        rr.rect.bottom = b
        rr.radiusX = radiusX
        rr.radiusY = radiusY
        cdef ID2D1StrokeStyle *sstyle
        if strokeStyle is None:
            sstyle = NULL
        else:
            sstyle = <ID2D1StrokeStyle*>strokeStyle.ptr
        (<ID2D1RenderTarget*>self.ptr).DrawRoundedRectangle(&rr, <ID2D1Brush*>brush.ptr, strokeWidth, sstyle)

    def FillRoundedRectangle(
            self,
            float l,
            float t,
            float r,
            float b,
            float radiusX,
            float radiusY,
            Brush brush):
        cdef D2D1_ROUNDED_RECT rr
        rr.rect.left = l
        rr.rect.top = t
        rr.rect.right = r
        rr.rect.bottom = b
        rr.radiusX = radiusX
        rr.radiusY = radiusY
        (<ID2D1RenderTarget*>self.ptr).FillRoundedRectangle(&rr, <ID2D1Brush*>brush.ptr)

    def DrawText(
            self,
            str text,
            TextFormat textFormat,
            float l,
            float t,
            float r,
            float b,
            Brush brush,
            int options=0,
            int measuringMode=0):
        cdef D2D1_RECT_F rect
        rect.left = l
        rect.top = t
        rect.right = r
        rect.bottom = b
        cdef wchar_t *textBuf
        cdef Py_ssize_t _textLength
        textBuf = PyUnicode_AsWideCharString(text, &_textLength)
        cdef UINT textLength
        textLength = <UINT>_textLength
        if textBuf == NULL:
            raise MemoryError
        (<ID2D1RenderTarget*>self.ptr).DrawTextW(
            textBuf,
            <UINT>textLength,
            <IDWriteTextFormat*>textFormat.ptr,
            rect,
            <ID2D1Brush*>brush.ptr,
            <D2D1_DRAW_TEXT_OPTIONS>options,
            <DWRITE_MEASURING_MODE>measuringMode)
        PyMem_Free(<void*>textBuf)

    def DrawTextLayout(self, float x, float y, TextLayout textLayout, Brush brush, int options=0):
        cdef D2D1_POINT_2F pt
        pt.x = x
        pt.y = y
        (<ID2D1RenderTarget*>self.ptr).DrawTextLayout(
            pt,
            <IDWriteTextLayout*>textLayout.ptr,
            <ID2D1Brush*>brush.ptr,
            <D2D1_DRAW_TEXT_OPTIONS>options)

    def EndDraw(self):
        res = (<ID2D1RenderTarget*>self.ptr).EndDraw(NULL, NULL)
        if FAILED(res):
            raise Direct2DError(res)

    def FillEllipse(self, float cx, float cy, float rx, float ry, Brush brush):
        cdef D2D1_ELLIPSE el
        el.point.x = cx
        el.point.y = cy
        el.radiusX = rx
        el.radiusY = ry
        (<ID2D1RenderTarget*>self.ptr).FillEllipse(&el, <ID2D1Brush*>brush.ptr)

    def FillGeometry(self, Geometry geometry, Brush brush):
        (<ID2D1RenderTarget*>self.ptr).FillGeometry(<ID2D1Geometry*>geometry.ptr, <ID2D1Brush*>brush.ptr, NULL)

    def FillRectangle(self, float l, float t, float r, float b, Brush brush):
        cdef D2D1_RECT_F rect
        rect.left = l
        rect.top = t
        rect.right = r
        rect.bottom = b
        (<ID2D1RenderTarget*>self.ptr).FillRectangle(&rect, <ID2D1Brush*>brush.ptr)

    def GetTransform(self):
        cdef D2D1_MATRIX_3X2_F mat
        (<ID2D1RenderTarget*>self.ptr).GetTransform(&mat)
        return mat.m11, mat.m12, mat.m21, mat.m22, mat.dx, mat.dy

    def SetAntialiasMode(self, int mode):
        (<ID2D1RenderTarget*>self.ptr).SetAntialiasMode(<D2D1_ANTIALIAS_MODE>mode)

    def SetTransform(self, float m11=1, float m12=0, float m21=0, float m22=1, float dx=0, float dy=0):
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = m11
        mat.m12 = m12
        mat.m21 = m21
        mat.m22 = m22
        mat.dx = dx
        mat.dy = dy
        (<ID2D1RenderTarget*>self.ptr).SetTransform(&mat)

    def Flush(self):
        cdef D2D1_TAG tag1 = 0
        cdef D2D1_TAG tag2 = 0
        cdef HRESULT res = (<ID2D1RenderTarget*>self.ptr).Flush(&tag1, &tag2)
        if FAILED(res):
            raise Direct2DError(res)

    def SetTextAntialiasMode(self, int mode):
        (<ID2D1RenderTarget*>self.ptr).SetTextAntialiasMode(<D2D1_TEXT_ANTIALIAS_MODE>mode)

    def GetTextAntialiasMode(self):
        return <int>(<ID2D1RenderTarget*>self.ptr).GetTextAntialiasMode()

    def GetDpi(self):
        cdef FLOAT dpiX = 0.0
        cdef FLOAT dpiY = 0.0
        (<ID2D1RenderTarget*>self.ptr).GetDpi(&dpiX, &dpiY)
        return dpiX, dpiY

    def SetDpi(self, float dpiX, float dpiY):
        (<ID2D1RenderTarget*>self.ptr).SetDpi(dpiX, dpiY)

    def CreateCompatibleRenderTarget(self, float width=0, float height=0,
                                   int pixelWidth=0, int pixelHeight=0,
                                   int pixelFormat=87, int alphaMode=0,
                                   int options=0):
        cdef D2D1_SIZE_F desiredSize
        desiredSize.width = width
        desiredSize.height = height
        cdef D2D1_SIZE_U desiredPixelSize
        desiredPixelSize.width = <UINT32>pixelWidth
        desiredPixelSize.height = <UINT32>pixelHeight
        cdef D2D1_PIXEL_FORMAT desiredFormat
        desiredFormat.format = <DXGI_FORMAT>pixelFormat
        desiredFormat.alphaMode = <D2D1_ALPHA_MODE>alphaMode
        cdef ID2D1BitmapRenderTarget *bmpRT = NULL
        cdef HRESULT res = (<ID2D1RenderTarget*>self.ptr).CreateCompatibleRenderTarget(
            desiredSize, desiredPixelSize, desiredFormat,
            <D2D1_COMPATIBLE_RENDER_TARGET_OPTIONS>options, &bmpRT)
        if FAILED(res):
            raise Direct2DError(res)
        result = <RenderTarget>BitmapRenderTarget.__new__(BitmapRenderTarget)
        result.ptr = <void*>bmpRT
        return result

    def IsSupported(self, int rtType=0, int pixelFormat=87, int alphaMode=0,
                    float dpiX=96.0, float dpiY=96.0, int usage=0, int minLevel=0):
        cdef D2D1_RENDER_TARGET_PROPERTIES rtp
        rtp.type = <D2D1_RENDER_TARGET_TYPE>rtType
        rtp.pixelFormat.format = <DXGI_FORMAT>pixelFormat
        rtp.pixelFormat.alphaMode = <D2D1_ALPHA_MODE>alphaMode
        rtp.dpiX = dpiX
        rtp.dpiY = dpiY
        rtp.usage = <D2D1_RENDER_TARGET_USAGE>usage
        rtp.minLevel = <D2D1_FEATURE_LEVEL>minLevel
        return (<ID2D1RenderTarget*>self.ptr).IsSupported(&rtp) != 0


cdef class HWNDRenderTarget(RenderTarget):
    def Resize(self, int width, int height):
        cdef D2D1_SIZE_U size
        size.width = width
        size.height = height
        res = (<ID2D1HwndRenderTarget*>self.ptr).Resize(&size)
        if FAILED(res):
            raise Direct2DError(res)


cdef class DCRenderTarget(RenderTarget):
    def BindDC(self, unsigned long long hdc, int left=0, int top=0, int right=0, int bottom=0):
        cdef RECT subRect
        subRect.left = left
        subRect.top = top
        subRect.right = right
        subRect.bottom = bottom
        cdef RECT *pSubRect = NULL
        if right > 0 and bottom > 0:
            pSubRect = &subRect
        res = (<ID2D1DCRenderTarget*>self.ptr).BindDC(<HDC><uintptr_t>hdc, pSubRect)
        if FAILED(res):
            raise Direct2DError(res)


cdef class BitmapRenderTarget(RenderTarget):
    def GetBitmap(self):
        cdef ID2D1Bitmap *bmp = NULL
        cdef HRESULT res = (<ID2D1BitmapRenderTarget*>self.ptr).GetBitmap(&bmp)
        if FAILED(res):
            raise Direct2DError(res)
        cdef Bitmap obj = Bitmap.__new__(Bitmap)
        obj.ptr = <void*>bmp
        return obj


cdef class WICBitmap(COMObject):
    def Lock(self, int left=0, int top=0, int width=0, int height=0, int flags=1):
        cdef WICRect lockRect
        cdef WICRect* pLockRect = NULL
        if width > 0 and height > 0:
            lockRect.X = left
            lockRect.Y = top
            lockRect.Width = width
            lockRect.Height = height
            pLockRect = &lockRect
        cdef IWICBitmapLock* lock
        res = (<IWICBitmap*>self.ptr).Lock(pLockRect, <DWORD>flags, &lock)
        if FAILED(res):
            raise COMError(res)
        cdef WICBitmapLock obj = WICBitmapLock.__new__(WICBitmapLock)
        obj.ptr = <void*>lock
        return obj

    def GetSize(self):
        cdef UINT w, h
        (<IWICBitmap*>self.ptr).GetSize(&w, &h)
        return (w, h)


cdef class WICBitmapLock(COMObject):
    def GetDataPointer(self):
        cdef UINT cbSize = 0
        cdef BYTE* data = NULL
        res = (<IWICBitmapLock*>self.ptr).GetDataPointer(&cbSize, &data)
        if FAILED(res):
            raise COMError(res)
        return (<unsigned long long><uintptr_t>data, cbSize)


cdef class WICBitmapDecoder(COMObject):
    def GetFrame(self, unsigned int index=0):
        cdef IWICBitmapFrameDecode* frame
        res = (<IWICBitmapDecoder*>self.ptr).GetFrame(index, <IWICBitmapFrameDecode**>&frame)
        if FAILED(res):
            raise COMError(res)
        cdef WICBitmapFrameDecode obj = WICBitmapFrameDecode.__new__(WICBitmapFrameDecode)
        obj.ptr = <void*>frame
        return obj


cdef class WICBitmapFrameDecode(COMObject):
    pass


cdef class WICFormatConverter(COMObject):
    def Initialize(self, source):
        cdef void* src_ptr = (<COMObject?>source).ptr
        res = (<IWICFormatConverter*>self.ptr).Initialize(
            <IWICBitmapSource*>src_ptr,
            _WicPbgraFormat,
            <WICBitmapDitherType>0, NULL, 0.0, <WICBitmapPaletteType>0)
        if FAILED(res):
            raise COMError(res)


cdef class Brush(Resource):
    def GetOpacity(self):
        return (<ID2D1Brush*>self.ptr).GetOpacity()


cdef class SolidColorBrush(Brush):
    def SetColor(self, float r, float g, float b, float a=1.0):
        cdef D2D1_COLOR_F color
        color.r = r
        color.g = g
        color.b = b
        color.a = a
        (<ID2D1SolidColorBrush*>self.ptr).SetColor(&color)

    def GetColor(self):
        cdef D2D1_COLOR_F color = (<ID2D1SolidColorBrush*>self.ptr).GetColor()
        return (color.r, color.g, color.b, color.a)


cdef class GradientStopCollection(Resource):
    pass


cdef class LinearGradientBrush(Brush):
    def GetStartPoint(self):
        cdef D2D1_POINT_2F pt
        pt = (<ID2D1LinearGradientBrush*>self.ptr).GetStartPoint()
        return (pt.x, pt.y)
    def GetEndPoint(self):
        cdef D2D1_POINT_2F pt
        pt = (<ID2D1LinearGradientBrush*>self.ptr).GetEndPoint()
        return (pt.x, pt.y)


cdef class RadialGradientBrush(Brush):
    def GetCenter(self):
        cdef D2D1_POINT_2F pt
        pt = (<ID2D1RadialGradientBrush*>self.ptr).GetCenter()
        return (pt.x, pt.y)
    def GetGradientOriginOffset(self):
        cdef D2D1_POINT_2F pt
        pt = (<ID2D1RadialGradientBrush*>self.ptr).GetGradientOriginOffset()
        return (pt.x, pt.y)
    def GetRadiusX(self):
        return (<ID2D1RadialGradientBrush*>self.ptr).GetRadiusX()
    def GetRadiusY(self):
        return (<ID2D1RadialGradientBrush*>self.ptr).GetRadiusY()


cdef class BitmapBrush(Brush):
    pass


cdef class Layer(Resource):
    pass


cdef class DrawingStateBlock(Resource):
    pass


cdef class StrokeStyle(Resource):
    pass


cdef class Geometry(Resource):
    def FillContainsPoint(self, float x, float y, float tolerance=0.0):
        cdef D2D1_POINT_2F pt
        pt.x = x
        pt.y = y
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = 1.0
        mat.m12 = 0.0
        mat.m21 = 0.0
        mat.m22 = 1.0
        mat.dx = 0.0
        mat.dy = 0.0
        cdef BOOL contains = 0
        cdef HRESULT res = (<ID2D1Geometry*>self.ptr).FillContainsPoint(
            pt, &mat, tolerance, &contains)
        if FAILED(res):
            raise Direct2DError(res)
        return bool(contains)

    def StrokeContainsPoint(self, float x, float y,
            float strokeWidth=1.0, StrokeStyle strokeStyle=None,
            float tolerance=0.0):
        cdef D2D1_POINT_2F pt
        pt.x = x
        pt.y = y
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = 1.0
        mat.m12 = 0.0
        mat.m21 = 0.0
        mat.m22 = 1.0
        mat.dx = 0.0
        mat.dy = 0.0
        cdef BOOL contains = 0
        cdef ID2D1StrokeStyle *ss = NULL
        if strokeStyle is not None:
            ss = <ID2D1StrokeStyle*>strokeStyle.ptr
        cdef HRESULT res = (<ID2D1Geometry*>self.ptr).StrokeContainsPoint(
            pt, strokeWidth, ss, &mat, tolerance, &contains)
        if FAILED(res):
            raise Direct2DError(res)
        return bool(contains)

    def GetBounds(self):
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = 1.0
        mat.m12 = 0.0
        mat.m21 = 0.0
        mat.m22 = 1.0
        mat.dx = 0.0
        mat.dy = 0.0
        cdef D2D1_RECT_F bounds
        cdef HRESULT res = (<ID2D1Geometry*>self.ptr).GetBounds(&mat, &bounds)
        if FAILED(res):
            raise Direct2DError(res)
        return (bounds.left, bounds.top, bounds.right, bounds.bottom)

    def GetWidenedBounds(self, float strokeWidth=1.0,
            StrokeStyle strokeStyle=None, float tolerance=0.0):
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = 1.0
        mat.m12 = 0.0
        mat.m21 = 0.0
        mat.m22 = 1.0
        mat.dx = 0.0
        mat.dy = 0.0
        cdef ID2D1StrokeStyle *ss = NULL
        if strokeStyle is not None:
            ss = <ID2D1StrokeStyle*>strokeStyle.ptr
        cdef D2D1_RECT_F bounds
        cdef HRESULT res = (<ID2D1Geometry*>self.ptr).GetWidenedBounds(
            strokeWidth, ss, &mat, tolerance, &bounds)
        if FAILED(res):
            raise Direct2DError(res)
        return (bounds.left, bounds.top, bounds.right, bounds.bottom)

    def CombineWithGeometry(self, Geometry other, int combineMode, float tolerance=0.0):
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = 1.0
        mat.m12 = 0.0
        mat.m21 = 0.0
        mat.m22 = 1.0
        mat.dx = 0.0
        mat.dy = 0.0
        cdef PathGeometry result = GetD2DFactory().CreatePathGeometry()
        cdef GeometrySink sink = result.Open()
        cdef HRESULT res = (<ID2D1Geometry*>self.ptr).CombineWithGeometry(
            <ID2D1Geometry*>other.ptr,
            <D2D1_COMBINE_MODE>combineMode,
            &mat, tolerance,
            <ID2D1SimplifiedGeometrySink*>(<void*>sink.ptr))
        sink.Close()
        if FAILED(res):
            raise Direct2DError(res)
        return result

    def ComputeArea(self, float tolerance=0.0):
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = 1.0
        mat.m12 = 0.0
        mat.m21 = 0.0
        mat.m22 = 1.0
        mat.dx = 0.0
        mat.dy = 0.0
        cdef FLOAT area = 0.0
        cdef HRESULT res = (<ID2D1Geometry*>self.ptr).ComputeArea(&mat, &area)
        if FAILED(res):
            raise Direct2DError(res)
        return area

    def CompareWithGeometry(self, Geometry other, float tolerance=0.0):
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = 1.0
        mat.m12 = 0.0
        mat.m21 = 0.0
        mat.m22 = 1.0
        mat.dx = 0.0
        mat.dy = 0.0
        cdef D2D1_GEOMETRY_RELATION relation
        cdef HRESULT res = (<ID2D1Geometry*>self.ptr).CompareWithGeometry(
            <ID2D1Geometry*>other.ptr, &mat, tolerance, &relation)
        if FAILED(res):
            raise Direct2DError(res)
        return <int>relation

    def Outline(self, float tolerance=0.0):
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = 1.0
        mat.m12 = 0.0
        mat.m21 = 0.0
        mat.m22 = 1.0
        mat.dx = 0.0
        mat.dy = 0.0
        cdef PathGeometry result = GetD2DFactory().CreatePathGeometry()
        cdef ID2D1GeometrySink *gs
        cdef HRESULT res = (<ID2D1PathGeometry*>result.ptr).Open(&gs)
        if FAILED(res):
            raise Direct2DError(res)
        res = (<ID2D1Geometry*>self.ptr).Outline(&mat, tolerance, <ID2D1SimplifiedGeometrySink*>gs)
        gs.Close()
        if FAILED(res):
            raise Direct2DError(res)
        return result

    def Simplify(self, int simplificationOption=0, float tolerance=0.0):
        cdef D2D1_MATRIX_3X2_F mat
        mat.m11 = 1.0
        mat.m12 = 0.0
        mat.m21 = 0.0
        mat.m22 = 1.0
        mat.dx = 0.0
        mat.dy = 0.0
        cdef PathGeometry result = GetD2DFactory().CreatePathGeometry()
        cdef ID2D1GeometrySink *gs
        cdef HRESULT res = (<ID2D1PathGeometry*>result.ptr).Open(&gs)
        if FAILED(res):
            raise Direct2DError(res)
        res = (<ID2D1Geometry*>self.ptr).Simplify(
            <D2D1_GEOMETRY_SIMPLIFICATION_OPTION>simplificationOption,
            &mat, tolerance, <ID2D1SimplifiedGeometrySink*>gs)
        gs.Close()
        if FAILED(res):
            raise Direct2DError(res)
        return result

    def Tessellate(self, float tolerance=0.0):
        return self.Outline(tolerance)


cdef class PathGeometry(Geometry):
    def Open(self):
        cdef ID2D1GeometrySink *gs
        res = (<ID2D1PathGeometry*>self.ptr).Open(&gs)
        if FAILED(res):
            raise Direct2DError(res)
        cdef GeometrySink obj = GeometrySink.__new__(GeometrySink)
        obj.ptr = <void*>gs
        return obj


cdef class SimplifiedGeometrySink(COMObject):
    def BeginFigure(self, float x, float y, int figureBegin=0):
        cdef D2D1_POINT_2F pt
        pt.x = x
        pt.y = y
        (<ID2D1SimplifiedGeometrySink*>self.ptr).BeginFigure(pt, <D2D1_FIGURE_BEGIN>figureBegin)

    def Close(self):
        res = (<ID2D1SimplifiedGeometrySink*>self.ptr).Close()
        if FAILED(res):
            raise Direct2DError(res)

    def EndFigure(self, int figureEnd=0):
        (<ID2D1SimplifiedGeometrySink*>self.ptr).EndFigure(<D2D1_FIGURE_END>figureEnd)

    def SetFillMode(self, int fillMode):
        (<ID2D1SimplifiedGeometrySink*>self.ptr).SetFillMode(<D2D1_FILL_MODE>fillMode)


cdef class GeometrySink(SimplifiedGeometrySink):
    def AddArc(self, float x, float y, float rx, float ry, float rotationAngle, int sweepDirection, int arcSize):
        cdef D2D1_ARC_SEGMENT arc
        arc.point.x = x
        arc.point.y = y
        arc.size.width = rx
        arc.size.height = ry
        arc.rotationAngle = rotationAngle
        arc.sweepDirection = <D2D1_SWEEP_DIRECTION>sweepDirection
        arc.arcSize = <D2D1_ARC_SIZE>arcSize
        (<ID2D1GeometrySink*>self.ptr).AddArc(&arc)

    def AddBezier(self, float x1, float y1, float x2, float y2, float x3, float y3):
        cdef D2D1_BEZIER_SEGMENT bz
        bz.point1.x = x1
        bz.point1.y = y1
        bz.point2.x = x2
        bz.point2.y = y2
        bz.point3.x = x3
        bz.point3.y = y3
        (<ID2D1GeometrySink*>self.ptr).AddBezier(&bz)

    def AddLine(self, float x, float y):
        cdef D2D1_POINT_2F pt
        pt.x = x
        pt.y = y
        (<ID2D1GeometrySink*>self.ptr).AddLine(pt)

    def AddQuadraticBezier(self, float x1, float y1, float x2, float y2):
        cdef D2D1_QUADRATIC_BEZIER_SEGMENT bz
        bz.point1.x = x1
        bz.point1.y = y1
        bz.point2.x = x2
        bz.point2.y = y2
        (<ID2D1GeometrySink*>self.ptr).AddQuadraticBezier(&bz)


cdef class Image(Resource):
    pass


cdef class Bitmap(Image):

    def GetSize(self):
        cdef D2D1_SIZE_F size = (<ID2D1Bitmap*>self.ptr).GetSize()
        return (size.width, size.height)

    def GetPixelSize(self):
        cdef D2D1_SIZE_U size = (<ID2D1Bitmap*>self.ptr).GetPixelSize()
        return (size.width, size.height)


_dwrite_factory = None

def GetDWriteFactory():
    global _dwrite_factory
    if _dwrite_factory is None:
        _dwrite_factory = DWriteFactory()
    return _dwrite_factory

class DirectWriteError(COMError):
    pass

cdef class DWriteFactory(COMObject):
    def __init__(self, int factoryType=0):
        cdef IDWriteFactory* factory
        res = DWriteCreateFactory(
            <DWRITE_FACTORY_TYPE>factoryType,
            IID_IDWriteFactory,
            <IUnknown**>&factory)
        if FAILED(res):
            raise DirectWriteError(res)
        self.ptr = <void*>factory

    def CreateTextFormat(self, str familyName, float size, int weight=500, int style=0, int stretch=5):
        cdef IDWriteTextFormat *fmt
        cdef wchar_t *familyBuf
        familyBuf = PyUnicode_AsWideCharString(familyName, NULL)
        if familyBuf == NULL:
            raise MemoryError
        cdef wchar_t[1] localeBuf
        localeBuf[0] = 0
        res = (<IDWriteFactory*>self.ptr).CreateTextFormat(
            familyBuf,
            NULL,
            <DWRITE_FONT_WEIGHT>weight,
            <DWRITE_FONT_STYLE>style,
            <DWRITE_FONT_STRETCH>stretch,
            size,
            localeBuf,
            <IDWriteTextFormat**>&fmt)
        PyMem_Free(<void*>familyBuf)
        if FAILED(res):
            raise DirectWriteError(res)
        cdef TextFormat obj = TextFormat.__new__(TextFormat)
        obj.ptr = <void*>fmt
        return obj

    def CreateTextLayout(self, str text, TextFormat textFormat, float maxWidth, float maxHeight):
        cdef IDWriteTextLayout* layout
        cdef wchar_t *stringBuf
        cdef Py_ssize_t stringBufLen
        stringBuf = PyUnicode_AsWideCharString(text, &stringBufLen)
        if stringBuf == NULL:
            raise MemoryError
        res = (<IDWriteFactory*>self.ptr).CreateTextLayout(
            stringBuf,
            <UINT32>stringBufLen,
            <IDWriteTextFormat*>textFormat.ptr,
            maxWidth,
            maxHeight,
            &layout)
        PyMem_Free(stringBuf)
        if FAILED(res):
            raise DirectWriteError(res)
        cdef TextLayout obj = TextLayout.__new__(TextLayout)
        obj.ptr = <void*>layout
        return obj

    def GetSystemFontCollection(self, bint checkForUpdates=False):
        cdef IDWriteFontCollection *collection = NULL
        cdef HRESULT res = (<IDWriteFactory*>self.ptr).GetSystemFontCollection(
            &collection, <BOOL>checkForUpdates)
        if FAILED(res):
            raise DirectWriteError(res)
        cdef FontCollection obj = FontCollection.__new__(FontCollection)
        obj.ptr = <void*>collection
        return obj


cdef class FontCollection(COMObject):
    def GetFontFamilyCount(self):
        return (<IDWriteFontCollection*>self.ptr).GetFontFamilyCount()

    def GetFontFamily(self, unsigned int index):
        cdef IDWriteFontFamily *family = NULL
        cdef HRESULT res = (<IDWriteFontCollection*>self.ptr).GetFontFamily(index, &family)
        if FAILED(res):
            raise DirectWriteError(res)
        cdef FontFamily obj = FontFamily.__new__(FontFamily)
        obj.ptr = <void*>family
        return obj


cdef class FontFamily(COMObject):
    def GetFamilyNames(self):
        cdef IDWriteLocalizedStrings *names = NULL
        cdef HRESULT res = (<IDWriteFontFamily*>self.ptr).GetFamilyNames(&names)
        if FAILED(res):
            raise DirectWriteError(res)
        cdef LocalizedStrings obj = LocalizedStrings.__new__(LocalizedStrings)
        obj.ptr = <void*>names
        return obj

    def GetFontCount(self):
        return (<IDWriteFontFamily*>self.ptr).GetFontCount()


cdef class LocalizedStrings(COMObject):
    def GetCount(self):
        return (<IDWriteLocalizedStrings*>self.ptr).GetCount()

    def GetString(self, unsigned int index):
        cdef UINT32 length = 0
        cdef HRESULT res = (<IDWriteLocalizedStrings*>self.ptr).GetStringLength(
            index, &length)
        if FAILED(res):
            raise DirectWriteError(res)
        if length == 0:
            return ''
        cdef UINT32 bufSize = length + 1
        cdef wchar_t *buf = <wchar_t*>PyMem_Malloc(bufSize * sizeof(wchar_t))
        if buf == NULL:
            raise MemoryError()
        try:
            res = (<IDWriteLocalizedStrings*>self.ptr).GetString(
                index, buf, bufSize)
            if FAILED(res):
                raise DirectWriteError(res)
            return PyUnicode_FromWideChar(buf, length)
        finally:
            PyMem_Free(buf)


cdef class DWriteFont(COMObject):
    def GetWeight(self):
        return <int>(<IDWriteFont*>self.ptr).GetWeight()

    def GetStyle(self):
        return <int>(<IDWriteFont*>self.ptr).GetStyle()

    def GetStretch(self):
        return <int>(<IDWriteFont*>self.ptr).GetStretch()


cdef class FontFace(COMObject):
    pass


cdef class TextFormat(COMObject):
    def SetTextAlignment(self, int alignment):
        res = (<IDWriteTextFormat*>self.ptr).SetTextAlignment(
            <DWRITE_TEXT_ALIGNMENT>alignment)
        if FAILED(res):
            raise DirectWriteError(res)

    def SetParagraphAlignment(self, int alignment):
        res = (<IDWriteTextFormat*>self.ptr).SetParagraphAlignment(
            <DWRITE_PARAGRAPH_ALIGNMENT>alignment)
        if FAILED(res):
            raise DirectWriteError(res)

    def SetWordWrapping(self, int wrapping):
        res = (<IDWriteTextFormat*>self.ptr).SetWordWrapping(
            <DWRITE_WORD_WRAPPING>wrapping)
        if FAILED(res):
            raise DirectWriteError(res)


cdef class TextLayout(TextFormat):
    def GetMaxWidth(self):
        return (<IDWriteTextLayout*>self.ptr).GetMaxWidth()

    def GetMetrics(self):
        cdef DWRITE_TEXT_METRICS tm
        res = (<IDWriteTextLayout*>self.ptr).GetMetrics(&tm)
        if FAILED(res):
            raise DirectWriteError(res)
        TM = TEXT_METRICS()
        TM.left = tm.left
        TM.top = tm.top
        TM.width = tm.width
        TM.widthIncludingTrailingWhitespace = tm.widthIncludingTrailingWhitespace
        TM.height = tm.height
        TM.layoutWidth = tm.layoutWidth
        TM.layoutHeight = tm.layoutHeight
        TM.maxBidiReorderingDepth = tm.maxBidiReorderingDepth
        TM.lineCount = tm.lineCount
        return TM

    def SetTrimming(self, int granularity, unsigned int delimiter=0, unsigned int delimiterCount=0):
        cdef DWRITE_TRIMMING trimming
        trimming.granularity = <DWRITE_TRIMMING_GRANULARITY>granularity
        trimming.delimiter = delimiter
        trimming.delimiterCount = delimiterCount
        res = (<IDWriteTextLayout*>self.ptr).SetTrimming(&trimming, NULL)
        if FAILED(res):
            raise DirectWriteError(res)

    def HitTestPoint(self, float x, float y):
        cdef BOOL isTrailingHit = 0
        cdef BOOL isInside = 0
        cdef DWRITE_HIT_TEST_METRICS htm
        cdef HRESULT res = (<IDWriteTextLayout*>self.ptr).HitTestPoint(
            x, y, &isTrailingHit, &isInside, &htm)
        if FAILED(res):
            raise DirectWriteError(res)
        result = HIT_TEST_METRICS()
        result.textPosition = htm.textPosition
        result.length = htm.length
        result.left = htm.left
        result.top = htm.top
        result.width = htm.width
        result.height = htm.height
        result.bidiLevel = htm.bidiLevel
        result.isText = htm.isText
        result.isTrimmed = htm.isTrimmed
        return (<bint>isTrailingHit, <bint>isInside, result)

    def HitTestTextPosition(self, unsigned int position, bint isTrailingHit=False):
        cdef FLOAT pointX = 0.0
        cdef FLOAT pointY = 0.0
        cdef DWRITE_HIT_TEST_METRICS htm
        cdef HRESULT res = (<IDWriteTextLayout*>self.ptr).HitTestTextPosition(
            position, <BOOL>isTrailingHit, &pointX, &pointY, &htm)
        if FAILED(res):
            raise DirectWriteError(res)
        result = HIT_TEST_METRICS()
        result.textPosition = htm.textPosition
        result.length = htm.length
        result.left = htm.left
        result.top = htm.top
        result.width = htm.width
        result.height = htm.height
        result.bidiLevel = htm.bidiLevel
        result.isText = htm.isText
        result.isTrimmed = htm.isTrimmed
        return (pointX, pointY, result)

    def GetClusterMetrics(self):
        cdef UINT32 count = 0
        cdef HRESULT res = (<IDWriteTextLayout*>self.ptr).GetClusterMetrics(
            NULL, 0, &count)
        cdef _CLUSTER_METRICS_RAW *raw
        cdef UINT32 i
        cdef UINT16 flags
        cdef list result
        if count == 0:
            return []
        cdef DWRITE_CLUSTER_METRICS *cmetrics
        cmetrics = <DWRITE_CLUSTER_METRICS*>PyMem_Malloc(
            count * sizeof(DWRITE_CLUSTER_METRICS))
        if cmetrics == NULL:
            raise MemoryError()
        try:
            res = (<IDWriteTextLayout*>self.ptr).GetClusterMetrics(
                cmetrics, count, &count)
            if FAILED(res):
                raise DirectWriteError(res)
            result = []
            raw = <_CLUSTER_METRICS_RAW*>cmetrics
            for i in range(count):
                cm = CLUSTER_METRICS()
                cm.width = raw[i].width
                cm.length = raw[i].length
                flags = raw[i].flags
                cm.canWrapLineAfter = bool(flags & 1)
                cm.isWhitespace = bool(flags & 2)
                cm.isNewline = bool(flags & 4)
                cm.isSoftHyphen = bool(flags & 8)
                cm.isRightToLeft = bool(flags & 16)
                result.append(cm)
            return result
        finally:
            PyMem_Free(cmetrics)

    def GetLineMetrics(self):
        cdef UINT32 count = 0
        cdef HRESULT res = (<IDWriteTextLayout*>self.ptr).GetLineMetrics(
            NULL, 0, &count)
        if count == 0:
            return []
        cdef DWRITE_LINE_METRICS *lmetrics
        lmetrics = <DWRITE_LINE_METRICS*>PyMem_Malloc(
            count * sizeof(DWRITE_LINE_METRICS))
        if lmetrics == NULL:
            raise MemoryError()
        try:
            res = (<IDWriteTextLayout*>self.ptr).GetLineMetrics(
                lmetrics, count, &count)
            if FAILED(res):
                raise DirectWriteError(res)
            result = []
            for i in range(count):
                lm = LINE_METRICS()
                lm.length = lmetrics[i].length
                lm.trailingWhitespaceLength = lmetrics[i].trailingWhitespaceLength
                lm.newlineLength = lmetrics[i].newlineLength
                lm.height = lmetrics[i].height
                lm.baseline = lmetrics[i].baseline
                lm.isTrimmed = <bint>lmetrics[i].isTrimmed
                result.append(lm)
            return result
        finally:
            PyMem_Free(lmetrics)

    def SetUnderline(self, bint hasUnderline, unsigned int start=0, unsigned int length=0xFFFFFFFF):
        cdef DWRITE_TEXT_RANGE tr
        tr.startPosition = start
        tr.length = length
        cdef HRESULT res = (<IDWriteTextLayout*>self.ptr).SetUnderline(
            <BOOL>hasUnderline, tr)
        if FAILED(res):
            raise DirectWriteError(res)

    def SetStrikethrough(self, bint hasStrikethrough, unsigned int start=0, unsigned int length=0xFFFFFFFF):
        cdef DWRITE_TEXT_RANGE tr
        tr.startPosition = start
        tr.length = length
        cdef HRESULT res = (<IDWriteTextLayout*>self.ptr).SetStrikethrough(
            <BOOL>hasStrikethrough, tr)
        if FAILED(res):
            raise DirectWriteError(res)

class CLUSTER_METRICS:
    pass

class LINE_METRICS:
    pass

class HIT_TEST_METRICS:
    pass

class TEXT_METRICS:
    pass


cpdef nine_patch_draw(rt, bitmap, rect, margins, draw_flags=0):
    cdef int x, y, w, h, ml, mt, mr, mb
    cdef int img_w, img_h, cw, ch, dcw, dch
    cdef int sx, sy, sw, sh, dx, dy, dw, dh
    cdef bint tile_top, tile_left, tile_center, tile_right, tile_bottom

    x, y, w, h = rect
    ml, mt, mr, mb = margins

    img_w, img_h = bitmap.GetSize()
    cw = img_w - ml - mr
    if cw < 0: cw = 0
    ch = img_h - mt - mb
    if ch < 0: ch = 0
    dcw = w - ml - mr
    if dcw < 0: dcw = 0
    dch = h - mt - mb
    if dch < 0: dch = 0

    tile_top = (draw_flags // 10000) != 0
    tile_left = ((draw_flags // 1000) % 10) != 0
    tile_center = ((draw_flags // 100) % 10) != 0
    tile_right = ((draw_flags // 10) % 10) != 0
    tile_bottom = (draw_flags % 10) != 0

    if ml > 0 and mt > 0:
        rt.DrawBitmap(bitmap, x, y, x + ml, y + mt,
                      srcRect=(0, 0, ml, mt))
    if mr > 0 and mt > 0:
        rt.DrawBitmap(bitmap, x + w - mr, y, x + w, y + mt,
                      srcRect=(img_w - mr, 0, img_w, mt))
    if ml > 0 and mb > 0:
        rt.DrawBitmap(bitmap, x, y + h - mb, x + ml, y + h,
                      srcRect=(0, img_h - mb, ml, img_h))
    if mr > 0 and mb > 0:
        rt.DrawBitmap(bitmap, x + w - mr, y + h - mb, x + w, y + h,
                      srcRect=(img_w - mr, img_h - mb, img_w, img_h))
    if mt > 0 and cw > 0 and dcw > 0:
        if tile_top:
            _draw_tiled(rt, bitmap, ml, 0, cw, mt, x + ml, y, dcw, mt)
        else:
            rt.DrawBitmap(bitmap, x + ml, y, x + ml + dcw, y + mt,
                          srcRect=(ml, 0, ml + cw, mt))
    if mb > 0 and cw > 0 and dcw > 0:
        if tile_bottom:
            _draw_tiled(rt, bitmap, ml, img_h - mb, cw, mb, x + ml, y + h - mb, dcw, mb)
        else:
            rt.DrawBitmap(bitmap, x + ml, y + h - mb, x + ml + dcw, y + h,
                          srcRect=(ml, img_h - mb, ml + cw, img_h))
    if ml > 0 and ch > 0 and dch > 0:
        if tile_left:
            _draw_tiled(rt, bitmap, 0, mt, ml, ch, x, y + mt, ml, dch)
        else:
            rt.DrawBitmap(bitmap, x, y + mt, x + ml, y + mt + dch,
                          srcRect=(0, mt, ml, mt + ch))
    if mr > 0 and ch > 0 and dch > 0:
        if tile_right:
            _draw_tiled(rt, bitmap, img_w - mr, mt, mr, ch, x + w - mr, y + mt, mr, dch)
        else:
            rt.DrawBitmap(bitmap, x + w - mr, y + mt, x + w, y + mt + dch,
                          srcRect=(img_w - mr, mt, img_w, mt + ch))
    if cw > 0 and ch > 0 and dcw > 0 and dch > 0:
        if tile_center:
            _draw_tiled(rt, bitmap, ml, mt, cw, ch, x + ml, y + mt, dcw, dch)
        else:
            rt.DrawBitmap(bitmap, x + ml, y + mt, x + ml + dcw, y + mt + dch,
                          srcRect=(ml, mt, ml + cw, mt + ch))


cdef _draw_tiled(rt, bitmap, int sx, int sy, int sw, int sh, int dx, int dy, int dw, int dh):
    cdef int pos_x, pos_y, tile_w, tile_h
    pos_x = dx
    while pos_x < dx + dw:
        tile_w = sw
        if tile_w > dx + dw - pos_x:
            tile_w = dx + dw - pos_x
        pos_y = dy
        while pos_y < dy + dh:
            tile_h = sh
            if tile_h > dy + dh - pos_y:
                tile_h = dy + dh - pos_y
            rt.DrawBitmap(bitmap, pos_x, pos_y, pos_x + tile_w, pos_y + tile_h,
                          srcRect=(sx, sy, sx + tile_w, sy + tile_h))
            pos_y += sh
        pos_x += sw
