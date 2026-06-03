import pyd2d

def make_rect(factory, l, t, r, b):
    geo = factory.CreatePathGeometry()
    sink = geo.Open()
    sink.BeginFigure(float(l), float(t), pyd2d.FIGURE_BEGIN.FILLED)
    sink.AddLine(float(r), float(t))
    sink.AddLine(float(r), float(b))
    sink.AddLine(float(l), float(b))
    sink.EndFigure(pyd2d.FIGURE_END.CLOSED)
    sink.Close()
    return geo

# --- 24.5 Outline / Simplify / Tessellate ---

def test_outline():
    factory = pyd2d.GetD2DFactory()
    geo = make_rect(factory, 0, 0, 100, 50)
    outline = geo.Outline(0.0)
    assert type(outline).__name__ == 'PathGeometry', f'Expected PathGeometry, got {type(outline).__name__}'
    assert hasattr(outline, 'Open'), 'Outline should have Open method'
    bounds = outline.GetBounds()
    assert abs(bounds[0]) < 1.0 and abs(bounds[1]) < 1.0
    assert abs(bounds[2] - 100.0) < 1.0 and abs(bounds[3] - 50.0) < 1.0
    print('test_outline OK')

def test_simplify():
    factory = pyd2d.GetD2DFactory()
    geo = make_rect(factory, 0, 0, 100, 50)
    simple = geo.Simplify(pyd2d.GEOMETRY_SIMPLIFICATION_OPTION.CUBICS_AND_LINES, 0.0)
    assert type(simple).__name__ == 'PathGeometry'
    bounds = simple.GetBounds()
    assert abs(bounds[2] - 100.0) < 1.0 and abs(bounds[3] - 50.0) < 1.0
    print('test_simplify OK')

def test_tessellate():
    factory = pyd2d.GetD2DFactory()
    geo = make_rect(factory, 0, 0, 100, 50)
    tri = geo.Tessellate(0.0)
    assert type(tri).__name__ == 'PathGeometry'
    print('test_tessellate OK')

# --- 24.1 FillContainsPoint ---

def test_fill_contains_point_inside():
    factory = pyd2d.GetD2DFactory()
    rect = make_rect(factory, 10, 10, 90, 90)
    assert rect.FillContainsPoint(50, 50) is True, 'center should be inside'
    assert rect.FillContainsPoint(5, 50) is False, 'left edge should be outside'
    assert rect.FillContainsPoint(95, 50) is False, 'right edge should be outside'
    print('test_fill_contains_point_inside OK')

def test_fill_contains_point_with_tolerance():
    factory = pyd2d.GetD2DFactory()
    rect = make_rect(factory, 10, 10, 90, 90)
    assert rect.FillContainsPoint(10.0, 10.0) is True, 'top-left corner should be inside'
    print('test_fill_contains_point_with_tolerance OK')

# --- 24.2 StrokeContainsPoint ---

def test_stroke_contains_point_on_edge():
    factory = pyd2d.GetD2DFactory()
    rect = make_rect(factory, 10, 10, 90, 90)
    assert rect.StrokeContainsPoint(50, 10, 2.0) is True, 'top edge with 2px stroke'
    assert rect.StrokeContainsPoint(50, 50, 1.0) is False, 'center not on stroke'
    print('test_stroke_contains_point_on_edge OK')

# --- 24.3 GetBounds + GetWidenedBounds ---

def test_get_bounds():
    factory = pyd2d.GetD2DFactory()
    rect = make_rect(factory, 10, 20, 90, 80)
    l, t, r, b = rect.GetBounds()
    assert abs(l - 10) < 0.01, f'left={l}'
    assert abs(t - 20) < 0.01, f'top={t}'
    assert abs(r - 90) < 0.01, f'right={r}'
    assert abs(b - 80) < 0.01, f'bottom={b}'
    print('test_get_bounds OK')

def test_get_widened_bounds():
    factory = pyd2d.GetD2DFactory()
    rect = make_rect(factory, 10, 20, 90, 80)
    l, t, r, b = rect.GetWidenedBounds(3.0)
    assert l < 10, f'Widened left should be < 10 (stroke expansion), got {l}'
    assert r > 90, f'Widened right should be > 90, got {r}'
    print('test_get_widened_bounds OK')

# --- 24.4 CombineWithGeometry ---

def test_combine_union():
    factory = pyd2d.GetD2DFactory()
    r1 = make_rect(factory, 0, 0, 60, 60)
    r2 = make_rect(factory, 40, 40, 100, 100)
    union = r1.CombineWithGeometry(r2, pyd2d.COMBINE_MODE.UNION)
    bounds = union.GetBounds()
    assert abs(bounds[0]) < 0.01, f'Union left={bounds[0]}'
    assert abs(bounds[1]) < 0.01, f'Union top={bounds[1]}'
    assert abs(bounds[2] - 100) < 0.01, f'Union right={bounds[2]}'
    assert abs(bounds[3] - 100) < 0.01, f'Union bottom={bounds[3]}'
    print('test_combine_union OK')

def test_combine_intersect():
    factory = pyd2d.GetD2DFactory()
    r1 = make_rect(factory, 0, 0, 60, 60)
    r2 = make_rect(factory, 40, 40, 100, 100)
    inter = r1.CombineWithGeometry(r2, pyd2d.COMBINE_MODE.INTERSECT)
    bounds = inter.GetBounds()
    assert abs(bounds[0] - 40) < 0.01, f'Intersect left={bounds[0]}'
    assert abs(bounds[1] - 40) < 0.01, f'Intersect top={bounds[1]}'
    assert abs(bounds[2] - 60) < 0.01, f'Intersect right={bounds[2]}'
    assert abs(bounds[3] - 60) < 0.01, f'Intersect bottom={bounds[3]}'
    print('test_combine_intersect OK')

def test_combine_xor():
    factory = pyd2d.GetD2DFactory()
    r1 = make_rect(factory, 0, 0, 60, 60)
    r2 = make_rect(factory, 40, 40, 100, 100)
    xor = r1.CombineWithGeometry(r2, pyd2d.COMBINE_MODE.XOR)
    bounds = xor.GetBounds()
    assert abs(bounds[0]) < 0.01, f'XOR left={bounds[0]}'
    assert abs(bounds[2] - 100) < 0.01, f'XOR right={bounds[2]}'
    union = r1.CombineWithGeometry(r2, pyd2d.COMBINE_MODE.UNION)
    u_area = union.ComputeArea()
    x_area = xor.ComputeArea()
    assert x_area < u_area, f'XOR area ({x_area}) should be < union area ({u_area})'
    print('test_combine_xor OK')

# --- 24.6 ComputeArea + CompareWithGeometry ---

def test_compute_area():
    factory = pyd2d.GetD2DFactory()
    rect = make_rect(factory, 10, 10, 90, 60)
    area = rect.ComputeArea()
    expected = 80 * 50
    assert abs(area - expected) < 1.0, f'Area should be {expected}, got {area}'
    print('test_compute_area OK')

def test_compare_geometry_equal():
    factory = pyd2d.GetD2DFactory()
    r1 = make_rect(factory, 10, 10, 90, 60)
    r2 = make_rect(factory, 10, 10, 90, 60)
    rel = r1.CompareWithGeometry(r2)
    assert rel in (2, 3), f'Identical rects should be IS_CONTAINED(2) or CONTAINS(3), got {rel}'
    print('test_compare_geometry_equal OK')

# --- Run ---
test_outline()
test_simplify()
test_tessellate()
test_fill_contains_point_inside()
test_fill_contains_point_with_tolerance()
test_stroke_contains_point_on_edge()
test_get_bounds()
test_get_widened_bounds()
test_combine_union()
test_combine_intersect()
test_combine_xor()
test_compute_area()
test_compare_geometry_equal()
print()
print('ALL 24.x TESTS PASSED')