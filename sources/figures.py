"""Tabular figures for aligned columns and proportional figures for text."""
from shapely import affinity
from shapely.ops import unary_union

FIGURES = '0123456789.,'


def add_figures(drawings, outline, stroke):
    # Keep every figure inside its tabular cell, including heavy diagonal joins.
    # Center the ink and compress only figures that exceed the available width.
    # One keeps its flag/stem placement; its separate foot is added below.
    for char in '023456789':
        width, shape = drawings[char]
        left, _, right, _ = shape.bounds
        scale = min(1, (width - 80) / (right - left))
        shape = affinity.scale(shape, xfact=scale, yfact=1, origin=(0, 0))
        left, _, right, _ = shape.bounds
        shape = affinity.translate(shape, xoff=(width - right - left) / 2)
        drawings[char] = (width, shape)
    for char in FIGURES:
        width, shape = drawings[char]
        bearing = 44
        ink_width = shape.bounds[2] - shape.bounds[0]
        if char != '1' and ink_width + 2 * bearing >= width:
            drawings[char + '.pnum'] = (width, shape)
        else:
            shifted = affinity.translate(shape, xoff=bearing - shape.bounds[0])
            drawings[char + '.pnum'] = (round(shifted.bounds[2] + bearing), shifted)
    width, one = drawings['1']
    foot = outline('M125 0 H515', stroke)
    drawings['1'] = (width, unary_union([one, foot]))


def features(glyph_name):
    proportional = '\n'.join(f'sub {glyph_name(c)} by {glyph_name(c + ".pnum")};' for c in FIGURES)
    tabular = '\n'.join(f'sub {glyph_name(c + ".pnum")} by {glyph_name(c)};' for c in FIGURES)
    return f'feature pnum {{\n{proportional}\n}} pnum;\nfeature tnum {{\n{tabular}\n}} tnum;\n'
