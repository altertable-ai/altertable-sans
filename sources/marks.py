"""Measured accent construction and OpenType attachment for Latin marks."""
import math
import unicodedata
from shapely import affinity
from shapely.ops import unary_union
from sources.glyphs import ACCENTS

MARK_PATHS = ACCENTS | {
    '\u0304': 'M-140 650 H140',
    '\u0306': 'M-135 700 C-115 570 115 570 135 700',
    '\u0307': 'M0 620 V700',
    '\u030b': 'M-140 600 L-40 730 M40 600 L140 730',
    '\u0326': 'M20 -35 V-90 L-25 -165',
    '\u0328': 'M45 0 C-105 -90 -80 -205 65 -155',
}
GAP = 45


def mark_class(char):
    return {'\u0326': 'bottom', '\u0327': 'cedilla', '\u0328': 'ogonek'}.get(char, 'top')


def normalized_mark(path, outline, stroke, below=False):
    form = outline(path, stroke * .62)
    x0, y0, x1, y1 = form.bounds
    # Compact accents retain clearance above capitals inside the existing metrics.
    if y1 - y0 > 160:
        form = affinity.scale(form, yfact=160 / (y1-y0), origin=(0, 0))
    x0, y0, x1, y1 = form.bounds
    return affinity.translate(form, xoff=-(x0+x1)/2, yoff=-y1 if below else -y0)


def base_anchor(width, form, kind):
    x0, y0, x1, y1 = form.bounds
    if kind == 'top':
        return ((x0+x1)/2, y1+GAP)
    if kind == 'ogonek':
        return (x1-25, y0+12)
    return ((x0+x1)/2, y0-GAP if kind == 'bottom' else y0+12)


def add_accents(drawings, outline, stroke):
    marks = {c: normalized_mark(p, outline, stroke, mark_class(c) != 'top')
             for c, p in MARK_PATHS.items()}
    compositions = []
    for code in [*range(0xC0, 0x180), *range(0x218, 0x21C)]:
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
            x = form.bounds[2] + GAP - mark.bounds[0]
            y = form.bounds[3] - mark.bounds[3]
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
    lines.extend([f"sub {name('i')}' @Above by {name('ı')};",
                  f"sub {name('j')}' @Above by {name('ȷ')};", '} ccmp;'])
    for char in MARK_PATHS:
        lines.append(f'markClass {name(char)} {anchor(0, 0)} @MC_{mark_class(char)};')
    lines.append('feature mark {')
    for char, (width, form) in drawings.items():
        if not unicodedata.category(char).startswith('L') or form.is_empty:
            continue
        anchors = ' '.join(f'{anchor(*base_anchor(width, form, kind))} mark @MC_{kind}'
                           for kind in ['top', 'bottom', 'cedilla', 'ogonek'])
        lines.append(f'pos base {name(char)} {anchors};')
    lines.append('} mark;')
    lines.append('feature mkmk {')
    for char in MARK_PATHS:
        form = drawings[char][1]
        kind = mark_class(char)
        y = form.bounds[3]+GAP if kind == 'top' else form.bounds[1]-GAP
        lines.append(f'pos mark {name(char)} {anchor(0, y)} mark @MC_{kind};')
    lines.append('} mkmk;')
    return '\n'.join(lines)
