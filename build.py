"""Build Altertable Sans proofing fonts from original centerline sources."""
from pathlib import Path
import json
import math
import unicodedata

from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.basePen import BasePen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from shapely import affinity, set_precision
from shapely.geometry import LineString, Point, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from sources.figures import add_figures, features as figure_features
from sources.font_metadata import COPYRIGHT, VERSION, finish_metadata
from sources.ufo_export import export_ufo
from sources.italics import ITALIC_GLYPHS
from sources.latin import LATIN, extend_latin
from sources.marks import add_accents, features as mark_features
from sources.glyphs import GLYPHS, EXTRA, PATH_WEIGHTS
from sources.spacing import SIDEBEARINGS, KERNING, optical_weights, kerning_for_style
from sources.symbols import SYMBOLS, SYMBOL_WEIGHTS, SPACE_WIDTHS

ROOT = Path(__file__).resolve().parent
EPOCH = 3876940800
TEXT_STYLES = {300: ('Light', 74), 400: ('Regular', 90),
               500: ('Medium', 104), 600: ('SemiBold', 118), 700: ('Bold', 132)}


class FlattenPen(BasePen):
    def __init__(self):
        super().__init__(None)
        self.paths = []
        self.points = []

    def _moveTo(self, point):
        self.points = [point]
        self.start_control = None
        self.end_control = None

    def _lineTo(self, point):
        self.points.append(point)
        self.end_control = None

    def _curveToOne(self, p1, p2, p3):
        p0 = self.points[-1]
        if len(self.points) == 1:
            self.start_control = next((p for p in (p1, p2, p3) if p != p0), None)
        self.end_control = next((p for p in (p2, p1, p0) if p != p3), None)
        for step in range(1, 49):
            t = step / 48
            self.points.append(tuple(
                (1-t)**3*p0[i] + 3*(1-t)**2*t*p1[i]
                + 3*(1-t)*t*t*p2[i] + t**3*p3[i]
                for i in (0, 1)
            ))

    def _closePath(self):
        self.points.append(self.points[0])
        self._endPath()

    def _endPath(self):
        # A sampled chord only approximates a curve's endpoint tangent. Project
        # the adjacent sample onto the true tangent so open stroke caps keep
        # their intended angle (notably the vertical cut on the tail of y).
        if len(self.points) > 2 and self.points[0] != self.points[-1]:
            for endpoint, neighbor, control in ((0, 1, self.start_control),
                                                (-1, -2, self.end_control)):
                if control is None:
                    continue
                x, y = self.points[endpoint]
                dx, dy = control[0] - x, control[1] - y
                nx, ny = self.points[neighbor]
                amount = ((nx-x)*dx + (ny-y)*dy) / (dx*dx + dy*dy)
                self.points[neighbor] = (x + amount*dx, y + amount*dy)
        self.paths.append(self.points)
        self.points = []


def outline(path, stroke, path_weights=(), lower_loop_shift=0):
    pen = FlattenPen()
    parse_path(path, pen)
    horizontal_stroke = stroke * 0.92
    terminal_heights = {0: 0, 510: 540, 690: 720, 730: 760, -210: -220}

    def vertical_position(y):
        if y <= 510:
            return y * (540 - horizontal_stroke) / 510 + horizontal_stroke / 2
        return 540 - horizontal_stroke / 2 + y - 510

    shapes = []
    for path_index, points in enumerate(pen.paths):
        if len(points) < 2:
            continue
        if lower_loop_shift and path_index == 3:
            points = [(x, y - lower_loop_shift) for x, y in points]
        elif lower_loop_shift and path_index == 2:
            points = [(x, y - lower_loop_shift * (245 - y) / 220) for x, y in points]
        mapped = [(x, vertical_position(y)) for x, y in points]
        lower, upper = -10000, 10000
        if points[0] != points[-1]:
            for index, neighbor in ((0, 1), (-1, -2)):
                x, y = mapped[index]
                nx, ny = mapped[neighbor]
                source_y = points[index][1]
                target = terminal_heights.get(source_y)
                if target is None or abs(ny - y) < 0.001:
                    continue
                if (target - y) * (ny - y) >= 0:
                    continue
                mapped[index] = (x + (target - y) * (nx - x) / (ny - y), target)
                if all(py >= source_y for _, py in points):
                    lower = max(lower, target)
                if all(py <= source_y for _, py in points):
                    upper = min(upper, target)
        path_stroke = stroke * (path_weights[path_index] if path_index < len(path_weights) else 1)
        line = LineString([(x, y / 0.92) for x, y in mapped])
        shape = affinity.scale(line.buffer(path_stroke / 2, cap_style=2, join_style=2),
                               xfact=1, yfact=0.92, origin=(0, 0))
        shapes.append(shape.intersection(box(-10000, lower, 10000, upper)))
    return unary_union(shapes)


def glyph_name(char):
    return f'uni{ord(char[0]):04X}' + char[1:]


def tt_glyph(shape):
    pen = TTGlyphPen(None)
    # Quantize topology as a whole, not each vertex independently: rounding a
    # narrow corner pointwise can create self-intersections or reversed edges.
    shape = set_precision(shape, grid_size=1)
    if not shape.is_empty:
        polygons = [shape] if shape.geom_type == 'Polygon' else shape.geoms
        for polygon in polygons:
            polygon = orient(polygon, sign=-1)
            for ring in [polygon.exterior, *polygon.interiors]:
                points = []
                for x, y in ring.coords[:-1]:
                    point = (round(x), round(y))
                    if not points or point != points[-1]:
                        points.append(point)
                if len(set(points)) < 3:
                    raise ValueError('Degenerate contour after grid rounding')
                pen.moveTo(points[0])
                for point in points[1:]:
                    pen.lineTo(point)
                pen.closePath()
    return pen.glyph()


def build(optical, weight=400, italic=False):
    style, stroke = TEXT_STYLES[weight]
    if optical == 'Display':
        stroke = 86
    tracking = 12 if optical == 'Text' else 0
    alternates = ITALIC_GLYPHS if italic else {}
    drawings = {
        char: (width, outline(path, stroke, optical_weights(char, weight, italic,
                              () if char in alternates else (PATH_WEIGHTS | SYMBOL_WEIGHTS).get(char, ())),
                              max(0, (stroke - 90) * 1.1) if char == 'g' and not italic else 0))
        for char, (width, path) in (GLYPHS | EXTRA | SYMBOLS | LATIN | alternates).items()
    }
    width, one = drawings['1']
    drawings['1'] = (width, one.intersection(box(-10000, -10000, 10000, 720)))
    for char in 'VWvw':
        width, shape = drawings[char]
        drawings[char] = (width, shape.intersection(box(-10000, 0, 10000, 10000)))
    for char, (left, right) in SIDEBEARINGS.items():
        _, shape = drawings[char]
        shape = affinity.translate(shape, xoff=left - shape.bounds[0])
        drawings[char] = (round(shape.bounds[2] + right), shape)
    drawings['\u00a0'] = drawings[' ']
    drawings['\u2007'] = (drawings['0'][0], outline('', stroke))
    for char, width in SPACE_WIDTHS.items():
        drawings[char] = (width, outline('', stroke))
    for char in ('\u00ad', '\u2011'):
        drawings[char] = drawings['-']
    for char, radius in (('•', 55), ('●', 115)):
        drawings[char] = (350, Point(175, 300).buffer(radius, quad_segs=32))
    # The default zero remains tabular but gains an identifier dot.
    width, zero = drawings['0']
    drawings['0'] = (width, unary_union([zero, Point(width/2, 360).buffer(max(32, stroke*.3), quad_segs=16)]))
    extend_latin(drawings, outline, stroke)
    compositions = add_accents(drawings, outline, stroke)
    attachment_features = mark_features(drawings, compositions, italic, tracking, glyph_name)

    add_figures(drawings, outline, stroke)

    if italic:
        slope = math.tan(math.radians(10))
        drawings = {char: (width, affinity.affine_transform(shape, [1, slope, 0, 1, -270 * slope, 0]))
                    for char, (width, shape) in drawings.items()}

    missing_shape = outline('M90 0 V700 H510 V0 Z M90 0 L510 700', 55)
    glyphs = {'.notdef': tt_glyph(missing_shape)}
    metrics = {'.notdef': (600, round(missing_shape.bounds[0]))}
    for char, (width, shape) in drawings.items():
        shape = affinity.translate(shape, xoff=tracking / 2)
        name = glyph_name(char)
        glyphs[name] = tt_glyph(shape)
        metrics[name] = (width + tracking if width else 0, round(shape.bounds[0]) if not shape.is_empty else 0)

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(list(glyphs))
    encoded = {c: glyph_name(c) for c in drawings if len(c) == 1}
    fb.setupCharacterMap({ord(c): name for c, name in encoded.items()})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=1000, descent=-280, lineGap=0,
                             caretSlopeRise=1000, caretSlopeRun=176 if italic else 0)
    family = f'Altertable Sans {optical}'
    subfamily = ('Italic' if weight == 400 else f'{style} Italic') if italic else style
    filename_style = subfamily.replace(' ', '')
    legacy_style = ('Bold Italic' if weight == 700 else 'Italic') if italic else ('Bold' if weight == 700 else 'Regular')
    fb.setupNameTable({
        'familyName': family if weight in (400, 700) else f'{family} {style}',
        'styleName': legacy_style,
        **({'typographicFamily': family, 'typographicSubfamily': subfamily}
           if weight not in (400, 700) else {}),
        'uniqueFontIdentifier': f'{VERSION};ATBL;AltertableSans{optical}-{filename_style}',
        'fullName': f'{family} {subfamily}',
        'psName': f'AltertableSans{optical}-{filename_style}',
        'version': f'Version {VERSION}',
        'copyright': COPYRIGHT,
        'licenseDescription': ('This Font Software is licensed under the SIL Open Font License, '
                               'Version 1.1. This license is available with a FAQ at: '
                               'https://openfontlicense.org'),
        'licenseInfoURL': 'https://openfontlicense.org',
        'description': 'Original experimental proofing font. Not production-ready.',
    })
    # Win clipping bounds include two stacked marks; typographic line metrics stay fixed.
    fb.setupOS2(sTypoAscender=1000, sTypoDescender=-280, sTypoLineGap=0,
                usWinAscent=1250, usWinDescent=440, sxHeight=540, sCapHeight=720,
                version=4,
                usWeightClass=weight, usWidthClass=5, fsType=0,
                fsSelection=(0x81 | (0x20 if weight == 700 else 0)) if italic else (0xA0 if weight == 700 else 0xC0))
    fb.setupPost(italicAngle=-10 if italic else 0)
    fb.setupMaxp()
    # Propagate the seed pairs to their precomposed accented counterparts.
    groups = {}
    for char in drawings:
        base = unicodedata.normalize('NFD', char)[0]
        groups.setdefault(base, []).append(char)
    rules = []
    for (left, right), value in kerning_for_style(weight, italic).items():
        for lchar in groups[left]:
            for rchar in groups[right]:
                rules.append(f'pos {glyph_name(lchar)} {glyph_name(rchar)} {value};')
    feature_text = ('languagesystem DFLT dflt;\n'
                                 'languagesystem latn dflt;\nfeature kern {\nlookupflag IgnoreMarks;\n'
                                 + '\n'.join(rules) + '\n} kern;\n' + attachment_features + figure_features(glyph_name))
    addOpenTypeFeaturesFromString(fb.font, feature_text)
    fb.font.recalcTimestamp = False
    fb.font['head'].macStyle = (1 if weight == 700 else 0) | (2 if italic else 0)
    fb.font['head'].created = EPOCH
    fb.font['head'].modified = EPOCH
    finish_metadata(fb.font, optical, weight, style, italic)
    path = ROOT / 'fonts' / f'AltertableSans{optical}-{filename_style}.ttf'
    export_ufo(fb.font, feature_text, ROOT / 'sources' / 'ufo' / path.with_suffix('.ufo').name)
    fb.save(path)
    font = TTFont(path, recalcTimestamp=False)
    font.flavor = 'woff2'
    font.save(path.with_suffix('.woff2'))
    return {'style': optical, 'weight': weight, 'name': filename_style, 'italic': italic, 'characters': len(encoded), 'glyphs': len(glyphs),
            'seed_kerning_pairs': len(KERNING), 'kerning_pairs': len(rules), 'coverage': ''.join(sorted(encoded))}


if __name__ == '__main__':
    (ROOT / 'fonts').mkdir(exist_ok=True)
    report = [build('Text'), build('Display')]
    report.extend(build('Text', weight) for weight in TEXT_STYLES if weight != 400)
    report.extend(build('Text', weight, italic=True) for weight in TEXT_STYLES)
    (ROOT / 'fonts' / 'coverage.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    for entry in report:
        print(f"{entry['style']} {entry['weight']}: {entry['characters']} characters, {entry['seed_kerning_pairs']} seed pairs / {entry['kerning_pairs']} expanded kerning pairs")
