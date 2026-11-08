"""Measured accent construction and OpenType attachment for Latin marks."""
import math
import unicodedata
from shapely import affinity
from shapely.ops import unary_union
from shapely.geometry import LineString, Point, box
from sources.glyphs import ACCENTS

MARK_PATHS = ACCENTS | {
    '\u0304': 'M-140 650 H140',
    '\u0306': 'M-135 700 C-115 570 115 570 135 700',
    '\u0307': 'M0 620 V700',
    '\u030b': 'M-140 600 L-40 730 M40 600 L140 730',
    '\u0326': 'M20 -35 V-90 L-25 -165',
    # A vertical entry joins baseline stems without a diagonal hairline wedge.
    '\u0328': 'M45 0 C45 -90 -80 -205 65 -155',
}
GAP = 45
BOTTOM_GAP = 20


def mark_class(char):
    return {'\u0326': 'bottom', '\u0327': 'cedilla', '\u0328': 'ogonek'}.get(char, 'top')


def normalized_mark(path, outline, stroke, below=False, attached=False):
    form = outline(path, stroke * .62)
    x0, y0, x1, y1 = form.bounds
    # Compact accents retain clearance above capitals inside the existing metrics.
    if y1 - y0 > 160:
        form = affinity.scale(form, yfact=160 / (y1-y0), origin=(0, 0))
    x0, y0, x1, y1 = form.bounds
    center = (x0+x1)/2
    if attached:
        center = form.intersection(LineString([(-1000, y1-5), (1000, y1-5)])).centroid.x
    return affinity.translate(form, xoff=-center, yoff=-y1 if below else -y0)


def base_anchor(width, form, kind):
    x0, y0, x1, y1 = form.bounds
    if kind == 'top':
        return ((x0+x1)/2, y1+GAP)
    if kind == 'ogonek':
        # Bury the vertical entry inside the lower-right ink. The deeper overlap
        # also clears the curved baseline of U/e without a narrow notch.
        y = y0 + 50
        section = form.intersection(LineString([(x0-1, y), (x1+1, y)]))
        return (section.bounds[2]-30, y)
    return ((x0+x1)/2, y0-BOTTOM_GAP if kind == 'bottom' else y0+12)


def add_accents(drawings, outline, stroke):
    marks = {c: normalized_mark(p, outline, stroke, mark_class(c) != 'top',
                                mark_class(c) in ('cedilla', 'ogonek'))
             for c, p in MARK_PATHS.items()}
    # Below-base commas need the compact proportions of a diacritic, rather
    # than the height of a punctuation comma. This also keeps stacks legible.
    comma = marks['\u0326']
    marks['\u0326'] = affinity.scale(comma, xfact=.75,
                                      yfact=min(1, 65/(comma.bounds[3]-comma.bounds[1])),
                                      origin=(0, 0))
    compositions = []
    for code in [*range(0xC0, 0x180), 0x1CD, 0x1CE, 0x1D3, 0x1D4, 0x1E6, 0x1E7,
                 0x1E8, 0x1E9, 0x1EE, 0x1EF, 0x1FE, 0x1FF, 0x21E, 0x21F,
                 *range(0x218, 0x21C), *range(0x1E80, 0x1E86), 0x1EBC, 0x1EBD, 0x1EF2, 0x1EF3]:
        char = chr(code)
        parts = unicodedata.normalize('NFD', char)
        if len(parts) != 2 or parts[0] not in drawings or parts[1] not in marks:
            continue
        base, accent = parts
        width, form = drawings[base]
        if base in 'ij' and mark_class(accent) == 'top':
            form = drawings['ı' if base == 'i' else 'ȷ'][1]
        mark = marks[accent]
        kind = mark_class(accent)
        x, y = base_anchor(width, form, kind)
        if char in 'ďťľĽ':
            # Slovak/Czech use a raised comma to the right of these stems.
            mark = normalized_mark('M20 160 V95 L-20 15', outline, stroke)
            y = form.bounds[3] - mark.bounds[3]
            section = form.intersection(box(-1000, y, 2000, form.bounds[3]+1))
            x = section.bounds[2] + GAP - mark.bounds[0]
            width = max(width, x + mark.bounds[2] + 35)
        elif char in 'ĢģĶķĻļŅņŖŗ':
            mark = marks['\u0326']
            if char == 'ģ':
                mark = affinity.rotate(mark, 180, origin=(0, 0))
                x, y = base_anchor(width, form, 'top')
            else:
                x, y = base_anchor(width, form, 'bottom')
        drawings[char] = (round(width), unary_union([form, affinity.translate(mark, xoff=x, yoff=y)]))
        compositions.append((base, accent, char))
        if char == 'į':
            dotless = drawings['ı'][1]
            x, y = base_anchor(width, dotless, kind)
            drawings['į.nodot'] = (round(width), unary_union([
                dotless, affinity.translate(mark, xoff=x, yoff=y)]))
    # Spacing accents share the combining drawings at their traditional heights.
    for char, combining in zip('¨¯´¸ˆˇ˘˙˚˛˜˝',
                               '\u0308\u0304\u0301\u0327\u0302\u030c\u0306\u0307\u030a\u0328\u0303\u030b'):
        form = marks[combining]
        width = max(300, math.ceil(form.bounds[2] - form.bounds[0] + 100))
        drawings[char] = (width, affinity.translate(form, xoff=width/2,
                                                   yoff=600 if mark_class(combining) == 'top' else 0))
    # A dotted circle makes isolated marks visible and provides ordinary anchors.
    dots = [Point(300 + 220*math.cos(a*math.pi/6), 255 + 220*math.sin(a*math.pi/6))
            .buffer(stroke*.30, quad_segs=8) for a in range(12)]
    drawings['◌'] = (600, unary_union(dots))
    for char, form in marks.items():
        drawings[char] = (0, form)
    return compositions


def features(drawings, compositions, italic, tracking, name):
    """Apply the same coordinate transform to outlines and attachment anchors."""
    slope = math.tan(math.radians(10)) if italic else 0

    def anchor(x, y):
        return f'<anchor {round(x + slope*(y-270) + tracking/2)} {round(y)}>'

    above = [c for c in MARK_PATHS if mark_class(c) == 'top']
    lines = ['@Above = [' + ' '.join(map(name, above)) + '];', 'feature ccmp {']
    for base, accent, composed in compositions:
        lines.append(f'sub {name(base)} {name(accent)} by {name(composed)};')
    lines.extend(['lookup RemoveSoftDot {', 'lookupflag UseMarkFilteringSet @Above;',
                  f"sub {name('i')}' @Above by {name('ı')};",
                  f"sub {name('j')}' @Above by {name('ȷ')};",
                  f"sub {name('į')}' @Above by {name('į.nodot')};",
                  '} RemoveSoftDot;', '} ccmp;'])
    for char in MARK_PATHS:
        lines.append(f'markClass {name(char)} {anchor(0, 0)} @MC_{mark_class(char)};')
    lines.append('feature mark {')
    for char, (width, form) in drawings.items():
        if (not unicodedata.category(char[0]).startswith('L') and char != '◌') or form.is_empty:
            continue
        anchors = ' '.join(f'{anchor(*base_anchor(width, form, kind))} mark @MC_{kind}'
                           for kind in ['top', 'bottom', 'cedilla', 'ogonek'])
        lines.append(f'pos base {name(char)} {anchors};')
    lines.append('} mark;')
    lines.append('feature mkmk {')
    for char in MARK_PATHS:
        form = drawings[char][1]
        kind = mark_class(char)
        y = form.bounds[3]+GAP if kind == 'top' else form.bounds[1]-(BOTTOM_GAP if kind == 'bottom' else GAP)
        lines.append(f'pos mark {name(char)} {anchor(0, y)} mark @MC_{kind};')
    lines.append('} mkmk;')
    return '\n'.join(lines)
