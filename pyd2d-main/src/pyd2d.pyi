# This file is a type stub for the native _pyd2d extension module.
"""
pyd2d - A Python wrapper for the Windows Direct2D and DirectWrite APIs.

This module provides a Pythonic interface to Direct2D and DirectWrite,
which are part of the Windows API.
"""

from typing import Optional, Tuple

from _pyd2d_const import (
    ALPHA_MAX,
    ALPHA_MODE,
    ANTIALIAS_MODE,
    ARC_SIZE,
    BITMAP_INTERPOLATION_MODE,
    BREAK_CONDITION,
    CAP_STYLE,
    COMBINE_MODE,
    COMPATIBLE_RENDER_TARGET_OPTIONS,
    D2D_FACTORY_TYPE,
    DASH_STYLE,
    DC_INITIALIZE_MODE,
    DEBUG_LEVEL,
    DRAW_TEXT_OPTIONS,
    DWRITE_FACTORY_TYPE,
    DXGI_FORMAT,
    EXTEND_MODE,
    FEATURE_LEVEL,
    FIGURE_BEGIN,
    FIGURE_END,
    FILL_MODE,
    FLOW_DIRECTION,
    FONT_FACE_TYPE,
    FONT_FEATURE_TAG,
    FONT_FILE_TYPE,
    FONT_SIMULATIONS,
    FONT_STRETCH,
    FONT_STYLE,
    FONT_WEIGHT,
    GAMMA,
    GEOMETRY_RELATION,
    GEOMETRY_SIMPLIFICATION_OPTION,
    INFORMATIONAL_STRING_ID,
    INTERPOLATION_MODE_DEFINITION,
    LAYER_OPTIONS,
    LINE_JOIN,
    LINE_SPACING_METHOD,
    MEASURING_MODE,
    NUMBER_SUBSTITUTION_METHOD,
    OPACITY_MASK_CONTENT,
    PARAGRAPH_ALIGNMENT,
    PATH_SEGMENT,
    PIXEL_GEOMETRY,
    PRESENT_OPTIONS,
    READING_DIRECTION,
    RENDER_TARGET_TYPE,
    RENDER_TARGET_USAGE,
    RENDERING_MODE,
    SCRIPT_SHAPES,
    SWEEP_DIRECTION,
    TEXT_ALIGNMENT,
    TEXT_ANTIALIAS_MODE,
    TEXTURE_TYPE,
    TRIMMING_GRANULARITY,
    WINDOW_STATE,
    WORD_WRAPPING,
)

__all__ = [
    "ALPHA_MAX",
    "ALPHA_MODE",
    "ANTIALIAS_MODE",
    "ARC_SIZE",
    "BITMAP_INTERPOLATION_MODE",
    "BREAK_CONDITION",
    "CAP_STYLE",
    "COMBINE_MODE",
    "COMPATIBLE_RENDER_TARGET_OPTIONS",
    "D2D_FACTORY_TYPE",
    "DASH_STYLE",
    "DC_INITIALIZE_MODE",
    "DEBUG_LEVEL",
    "DRAW_TEXT_OPTIONS",
    "DWRITE_FACTORY_TYPE",
    "DXGI_FORMAT",
    "EXTEND_MODE",
    "FEATURE_LEVEL",
    "FIGURE_BEGIN",
    "FIGURE_END",
    "FILL_MODE",
    "FLOW_DIRECTION",
    "FONT_FACE_TYPE",
    "FONT_FEATURE_TAG",
    "FONT_FILE_TYPE",
    "FONT_SIMULATIONS",
    "FONT_STRETCH",
    "FONT_STYLE",
    "FONT_WEIGHT",
    "GAMMA",
    "GEOMETRY_RELATION",
    "GEOMETRY_SIMPLIFICATION_OPTION",
    "INFORMATIONAL_STRING_ID",
    "INTERPOLATION_MODE_DEFINITION",
    "LAYER_OPTIONS",
    "LINE_JOIN",
    "LINE_SPACING_METHOD",
    "MEASURING_MODE",
    "NUMBER_SUBSTITUTION_METHOD",
    "OPACITY_MASK_CONTENT",
    "PARAGRAPH_ALIGNMENT",
    "PATH_SEGMENT",
    "PIXEL_GEOMETRY",
    "PRESENT_OPTIONS",
    "READING_DIRECTION",
    "RENDERING_MODE",
    "RENDER_TARGET_TYPE",
    "RENDER_TARGET_USAGE",
    "SCRIPT_SHAPES",
    "SWEEP_DIRECTION",
    "TEXTURE_TYPE",
    "TEXT_ALIGNMENT",
    "TEXT_ANTIALIAS_MODE",
    "TEXT_METRICS",
    "TRIMMING_GRANULARITY",
    "WINDOW_STATE",
    "WORD_WRAPPING",
    "Bitmap",
    "BitmapBrush",
    "Brush",
    "COMError",
    "COMObject",
    "D2DFactory",
    "DCRenderTarget",
    "DWriteFactory",
    "DWriteFactory",
    "Direct2DError",
    "DirectWriteError",
    "FontFace",
    "Geometry",
    "GeometrySink",
    "GetD2DFactory",
    "GetDWriteFactory",
    "HWNDRenderTarget",
    "Image",
    "InitializeCOM",
    "PathGeometry",
    "RenderTarget",
    "Resource",
    "SimplifiedGeometrySink",
    "SolidColorBrush",
    "StrokeStyle",
    "TextFormat",
    "TextLayout",
]

class COMError(OSError):
    """
    Base class for COM errors.
    """

    hresult: int
    def __init__(self, hresult: int) -> None: ...

class Direct2DError(COMError):
    """
    Base class for Direct2D errors.
    """

def InitializeCOM(options: int = 0) -> None:
    """
    Initializes COM for the current thread by calling CoInitializeEx.
    """

def UninitializeCOM() -> None:
    """
    Uninitializes COM for the current thread by calling CoUninitialize.
    """

class COMObject:
    """
    Base class for COM objects.
    Use the factory functions to create instances of COMObject subclasses.
    """

    def Release(self) -> None:
        """
        Releases the COM object. The object can no longer be used after this call.
        Objects are automatically released when they are garbage collected.
        """

def GetD2DFactory() -> "D2DFactory":
    """
    Returns the Direct2D factory object, creating it on the first call.
    """

class D2DFactory(COMObject):
    """
    Creates Direct2D resources.
    """
    def __init__(self, factoryType: int = 0, debugLevel: int = 0) -> None:
        """
        Creates the Direct2D factory object.
        """
    def CreateHwndRenderTarget(
        self,
        hwnd: int,
        width: int,
        height: int,
        presentOptions: int = 0,
        rtType: int = 0,
        pixelFormat: int = 0,
        alphaMode: int = 0,
        dpiX: float = 0,
        dpiY: float = 0,
        usage: int = 0,
        featureLevel: int = 0,
    ) -> "HWNDRenderTarget":
        """
        Creates a HwndRenderTarget.
        """
    def CreateDCRenderTarget(
        self,
        rtType: int = 0,
        pixelFormat: int = 0,
        alphaMode: int = 0,
        dpiX: float = 0,
        dpiY: float = 0,
        usage: int = 0,
        featureLevel: int = 0,
    ) -> "DCRenderTarget":
        """
        Creates a DCRenderTarget.
        """
    def CreatePathGeometry(self) -> "PathGeometry":
        """
        Creates a PathGeometry.
        """
    def CreateStrokeStyle(
        self,
        startCap: int = 0,
        endCap: int = 0,
        dashCap: int = 0,
        lineJoin: int = 0,
        miterLimit: float = 10.0,
        dashStyle: int = 0,
        dashOffset: float = 0.0,
    ) -> "StrokeStyle":
        """
        Creates a StrokeStyle.
        """
    def CreateBitmap(
        self, width: int, height: int, guidFormat: Optional[bytes] = None
    ) -> "Bitmap":
        """
        Creates a Bitmap.
        """
    def CreateBitmapFromWicBitmap(
        self,
        source: "COMObject",
        dxgiFormat: int = 0,
        alphaMode: int = 1,
        dpiX: float = 96.0,
        dpiY: float = 96.0,
    ) -> "Bitmap":
        """
        Creates a D2D Bitmap from a WIC bitmap source.
        """

class Resource(COMObject):
    """
    Base class representing a Direct2D drawing resource.
    """

class RenderTarget(Resource):
    """
    Base class representing an object that can receive drawing commands.

    Classes that inherit from RenderTarget render the drawing commands they receive
    in different ways.
    """
    def BeginDraw(self) -> None:
        """
        Initiates drawing on this render target.
        """
    def Clear(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        """
        Clears the drawing area to the specified color.
        """
    def CreateSolidColorBrush(
        self, r: float, g: float, b: float, a: float = 1.0, opacity: float = 1.0
    ) -> "SolidColorBrush":
        """
        Creates a SolidColorBrush.
        """
    def CreateBitmapBrush(
        self,
        bitmap: "Bitmap",
        extendModeX: int = 0,
        extendModeY: int = 0,
        interpolationMode: int = 1,
        opacity: float = 1.0,
    ) -> "BitmapBrush":
        """
        Creates a BitmapBrush.
        """
    def CreateCompatibleRenderTarget(
        self,
        width: float = 0,
        height: float = 0,
        pixelWidth: int = 0,
        pixelHeight: int = 0,
        pixelFormat: int = 87,
        alphaMode: int = 0,
        options: int = 0,
    ) -> "BitmapRenderTarget":
        """
        Creates a bitmap render target for use as an intermediate surface.
        """
    def DrawBitmap(
        self,
        bitmap: "Bitmap",
        l: float,
        t: float,
        r: float,
        b: float,
        opacity: float = 1.0,
        interpolationMode: int = 1,
        srcRect: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        """
        Draws the specified bitmap after scaling it to the size of the specified
        rectangle.
        """
    def DrawEllipse(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        brush: "Brush",
        strokeWidth: float = 1.0,
        strokeStyle: Optional["StrokeStyle"] = None,
    ) -> None:
        """
        Draws the outline of the specified ellipse using the specified stroke style.
        """
    def DrawGeometry(
        self,
        geometry: "Geometry",
        brush: "Brush",
        strokeWidth: float = 1.0,
        strokeStyle: Optional["StrokeStyle"] = None,
    ) -> None:
        """
        Draws the outline of the specified geometry using the specified stroke style.
        """
    def DrawLine(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        brush: "Brush",
        strokeWidth: float = 1.0,
        strokeStyle: Optional["StrokeStyle"] = None,
    ) -> None:
        """
        Draws a line between the specified points using the specified stroke style.
        """
    def DrawRectangle(
        self,
        l: float,
        t: float,
        r: float,
        b: float,
        brush: "Brush",
        strokeWidth: float = 1.0,
        strokeStyle: Optional["StrokeStyle"] = None,
    ) -> None:
        """
        Draws the outline of a rectangle that has the specified dimensions and stroke
        style.
        """
    def DrawText(
        self,
        text: str,
        textFormat: "TextFormat",
        l: float,
        t: float,
        r: float,
        b: float,
        brush: "Brush",
        options: int = 0,
        measuringMode: int = 0,
    ) -> None:
        """
        Draws the specified text using the format information provided by a TextFormat
        object.
        """
    def DrawTextLayout(
        self,
        x: float,
        y: float,
        textLayout: "TextLayout",
        brush: "Brush",
        options: int = 0,
    ) -> None:
        """
        Draws the formatted text described by the specified TextLayout object.
        """
    def EndDraw(self) -> None:
        """
        Ends drawing operations on the render target and indicates the current error
        state and associated tags.
        """
    def FillEllipse(
        self, cx: float, cy: float, rx: float, ry: float, brush: "Brush"
    ) -> None:
        """
        Paints the interior of the specified ellipse.
        """
    def FillGeometry(self, geometry: "Geometry", brush: "Brush") -> None:
        """
        Paints the interior of the specified geometry.
        """
    def FillRectangle(
        self, l: float, t: float, r: float, b: float, brush: "Brush"
    ) -> None:
        """
        Paints the interior of the specified rectangle.
        """
    def GetTransform(self) -> Tuple[float, float, float, float, float, float]:
        """
        Gets the current transform of the render target.
        """
    def SetAntialiasMode(self, mode: int) -> None:
        """
        Sets the antialiasing mode of the render target.
        The antialiasing mode applies to all subsequent drawing operations,
        excluding text and glyph drawing operations.
        """
    def SetTransform(
        self,
        m11: float = 1,
        m12: float = 0,
        m21: float = 0,
        m22: float = 1,
        dx: float = 0,
        dy: float = 0,
    ) -> None:
        """
        Applies the specified transform to the render target,
        replacing the existing transformation.
        All subsequent drawing operations occur in the transformed space.
        """

class HWNDRenderTarget(RenderTarget):
    """
    Renders drawing instructions to a window.
    """
    def Resize(self, width: int, height: int) -> None:
        """
        Changes the size of the render target to the specified pixel size.
        """

class DCRenderTarget(RenderTarget):
    """
    Renders drawing instructions to a GDI device context.
    """
    def BindDC(self, hdc: int, left: int = 0, top: int = 0, right: int = 0, bottom: int = 0) -> None:
        """
        Binds the render target to the device context to which it issues drawing commands.
        """

class BitmapRenderTarget(RenderTarget):
    """
    Renders to an intermediate bitmap for use as a pattern or caching.
    """
    def GetBitmap(self) -> "Bitmap":
        """
        Retrieves the bitmap for this render target.
        """

class Brush(Resource):
    """
    Base class representing an object that paints an area.
    Classes that derive from Brush describe how the area is painted.
    """
    def GetOpacity(self) -> float:
        """
        Gets the degree of opacity of this brush.
        """

class SolidColorBrush(Brush):
    """
    Paints an area with a solid color.
    """
    def SetColor(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        """
        Specifies the color of this solid color brush.
        """

class BitmapBrush(Brush):
    """
    Paints an area with a bitmap.
    """

class StrokeStyle(Resource):
    """
    Describes the caps, miter limit, line join, and dash information for a stroke.
    """

class Geometry(Resource):
    """
    Base class representing a geometry resource.
    Defines a set of helper methods for manipulating and measuring geometric shapes.
    Classes that inherit from Geometry define specific shapes.
    """

    def FillContainsPoint(
        self, x: float, y: float, tolerance: float = 0.0
    ) -> bool:
        """
        Indicates whether the area filled by the geometry would contain
        the specified point given the specified flattening tolerance.
        """

    def StrokeContainsPoint(
        self,
        x: float,
        y: float,
        strokeWidth: float = 1.0,
        strokeStyle: Optional[StrokeStyle] = None,
        tolerance: float = 0.0,
    ) -> bool:
        """
        Determines whether the geometry's stroke contains the specified point.
        """

    def GetBounds(self) -> Tuple[float, float, float, float]:
        """
        Retrieves the bounds of the geometry.
        Returns (left, top, right, bottom).
        """

    def GetWidenedBounds(
        self,
        strokeWidth: float = 1.0,
        strokeStyle: Optional[StrokeStyle] = None,
        tolerance: float = 0.0,
    ) -> Tuple[float, float, float, float]:
        """
        Gets the bounds of the geometry after it has been widened by the
        specified stroke width and style.
        Returns (left, top, right, bottom).
        """

    def CombineWithGeometry(
        self,
        other: Geometry,
        combineMode: int,
        tolerance: float = 0.0,
    ) -> Geometry:
        """
        Combines this geometry with the specified geometry and stores the
        result in an output geometry.

        combineMode: COMBINE_MODE.UNION(0) / INTERSECT(1) / XOR(2) / EXCLUDE(3)
        """

    def ComputeArea(self, tolerance: float = 0.0) -> float:
        """
        Computes the area of the geometry after it has been transformed.
        """

    def CompareWithGeometry(
        self, other: Geometry, tolerance: float = 0.0
    ) -> int:
        """
        Describes the intersection between this geometry and the specified
        geometry. Returns a GEOMETRY_RELATION value.
        """

class PathGeometry(Geometry):
    """
    Represents a complex shape that may be composed of arcs, curves, and lines.
    """
    def Open(self) -> "GeometrySink":
        """
        Retrieves the GeometrySink that is used to populate the path geometry with
        figures and segments.
        """

class SimplifiedGeometrySink(COMObject):
    """
    Describes a geometric path that does not contain quadratic bezier curves or arcs.
    """
    def BeginFigure(self, x: float, y: float, figureBegin: int = 0) -> None:
        """
        Starts a new figure at the specified point.
        """
    def Close(self) -> None:
        """
        Closes the geometry sink, indicates whether it is in an error state, and resets
        the sink's error state.
        """
    def EndFigure(self, figureEnd: int = 0) -> None:
        """
        Ends the current figure; optionally, closes it.
        """
    def SetFillMode(self, fillMode: int) -> None:
        """
        Specifies the method used to determine which pointsare inside
        the geometry described by this geometry sink and which points are outside.
        """

class GeometrySink(SimplifiedGeometrySink):
    """
    Describes a geometric path that can contain lines, arcs,
    cubic Bezier curves, and quadratic Bezier curves.
    """
    def AddArc(
        self,
        x: float,
        y: float,
        rx: float,
        ry: float,
        rotationAngle: float,
        sweepDirection: int,
        arcSize: int,
    ) -> None:
        """
        Adds a single arc to the path geometry.
        """
    def AddBezier(
        self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float
    ) -> None:
        """
        Creates a cubic Bezier curve between the current point and the specified end
        point.
        """
    def AddLine(self, x: float, y: float) -> None:
        """
        Creates a line segment between the current point and the specified end point
        and adds it to the geometry sink.
        """
    def AddQuadraticBezier(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """
        Creates a quadratic Bezier curve between the current point and the specified end
        point.
        """

class Image(Resource):
    """
    Base class representing a producer of pixels that can fill an arbitrary 2D plane.
    """

class Bitmap(Image):
    """
    Represents a bitmap that has been bound to a RenderTarget.
    """

def GetDWriteFactory() -> "DWriteFactory":
    """
    Returns the DirectWrite factory object, creating it on the first call.
    """

class DirectWriteError(COMError):
    """
    Base class for DirectWrite errors.
    """

class DWriteFactory(COMObject):
    """
    Creates DirectWrite resources.
    """
    def __init__(self, factoryType: int = 0) -> None:
        """
        Creates the DirectWrite factory object.
        """
    def CreateTextFormat(
        self,
        familyName: str,
        size: float,
        weight: int = 500,
        style: int = 0,
        stretch: int = 5,
    ) -> "TextFormat":
        """
        Creates a text format object used for text layout.
        """
    def CreateTextLayout(
        self, text: str, textFormat: "TextFormat", maxWidth: float, maxHeight: float
    ) -> "TextLayout":
        """
        Takes a string, text format, and associated constraints,
        and produces an object that represents the fully analyzed and formatted result.
        """

class FontFace(COMObject):
    """
    Exposes various font data such as metrics, names, and glyph outlines.
    Contains font face type, appropriate file references, and face identification data.
    """

class TextFormat(COMObject):
    """
    Describes the font and paragraph properties used to format text,
    and describes locale information.
    """
    def SetWordWrapping(self, wrapping: int) -> None:
        """
        Set word wrapping mode (0=WRAP, 1=NO_WRAP, 2=EMERGENCY_BREAK).
        """

class TextLayout(TextFormat):
    """
    Represents a block of text after it has been fully analyzed and formatted.
    """
    def GetMaxWidth(self) -> float:
        """
        Gets the layout maximum width.
        """
    def GetMetrics(self) -> "TEXT_METRICS":
        """
        Retrieves overall metrics for the formatted string.
        """

class TEXT_METRICS:
    """
    Contains the metrics associated with text after layout.
    All coordinates are in device independent pixels (DIPs).
    """

    left: float
    top: float
    width: float
    widthIncludingTrailingWhitespace: float
    height: float
    layoutWidth: float
    layoutHeight: float
    maxBidiReorderingDepth: int
    lineCount: int
