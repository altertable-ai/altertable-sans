"""Tabular figures for aligned columns and proportional figures for text."""
from shapely import affinity
from shapely.ops import unary_union

FIGURES = '0123456789.,'


def add_figures(drawings, outline, stroke):
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
