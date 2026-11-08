"""Check prototype coverage, metrics, contours, packaging, and repeatability."""
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

from fontTools.ttLib import TTFont
import uharfbuzz as hb
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from shapely.affinity import translate
from sources.spacing import kerning_for_style
import string
import json

def glyph_geometry(font, char):
    glyph = font['glyf'][font.getBestCmap()[ord(char)]]
    coordinates, endpoints, _ = glyph.getCoordinates(font['glyf'])
    outer, counters = [], []
    start = 0
    for end in endpoints:
        polygon = Polygon(coordinates[start:end + 1])
        (counters if polygon.exterior.is_ccw else outer).append(polygon)
        start = end + 1
    return unary_union(outer).difference(unary_union(counters)), len(counters)


ROOT = Path(__file__).resolve().parent
fonts = sorted((ROOT / 'fonts').glob('*.*tf')) + sorted((ROOT / 'fonts').glob('*.woff2'))
manifest = json.loads((ROOT / 'fonts' / 'coverage.json').read_text(encoding='utf-8'))
assert len(fonts) == 2 * len(manifest), 'Expected TTF and WOFF2 for each style'
expected_coverage = set(map(ord, manifest[0]['coverage']))
required = set(range(32, 127)) | {ord(c) for c in 'ÀÜberGrößeCaféfaçadamañana€£“”…−©®™•●←→↑↓↔↗✓✕⨯°±≤≥≠∞«»'}
for path in fonts:
    font = TTFont(path)
    cmap = font.getBestCmap()
    italic = bool(font['OS/2'].fsSelection & 1)
    kerning = kerning_for_style(font['OS/2'].usWeightClass, italic)
    assert bool(font['head'].macStyle & 2) == italic
    assert font['post'].italicAngle == (-10 if italic else 0)
    assert font['hhea'].caretSlopeRun == (176 if italic else 0)
    assert required <= cmap.keys(), f'{path.name}: missing proof characters'
    assert set(cmap) == expected_coverage
    for char in "\u200b\u2060\ufeff":
        assert font['hmtx'][cmap[ord(char)]][0] == 0, 'Invisible formatting characters must not add spacing'
    assert font['OS/2'].fsType == 0
    assert font['OS/2'].version >= 4
    assert 'GPOS' in font
    assert font['name'].getDebugName(13).startswith('This Font Software is licensed under the SIL')
    for char in 'HIN':
        stem = font['glyf'][cmap[ord(char)]]
        assert (stem.yMin, stem.yMax) == (0, 720), f'{char}: flat terminals miss baseline/cap height'
    ascender = font['glyf'][cmap[ord('l')]]
    assert (ascender.yMin, ascender.yMax) == (0, 760), 'l: inconsistent ascender alignment'
    shoulder = font['glyf'][cmap[ord('r')]]
    assert italic or shoulder.xMax < font['hmtx'][cmap[ord('r')]][0], 'r: curve terminal extrapolated beyond its advance'
    for char in string.ascii_letters:
        glyph = font['glyf'][cmap[ord(char)]]
        advance, left = font['hmtx'][cmap[ord(char)]]
        assert italic or (left >= 0 and advance >= glyph.xMax), f'{char}: negative sidebearing'
    for char in 'VWvw':
        glyph = font['glyf'][cmap[ord(char)]]
        assert glyph.yMin == 0, f'{char}: diagonal join extends below baseline'
    digits = [font['hmtx'][cmap[ord(c)]][0] for c in '0123456789']
    assert len(set(digits)) == 1, 'Tabular numerals must have equal advance'
    for name in font.getGlyphOrder():
        glyph = font['glyf'][name]
        if glyph.numberOfContours:
            assert glyph.yMax <= font['OS/2'].usWinAscent, f'{name}: top clipping'
            assert glyph.yMin >= -font['OS/2'].usWinDescent, f'{name}: bottom clipping'
            assert glyph.xMin == font['hmtx'][name][1], f'{name}: incorrect left bearing'
    if italic:
        for char in 'ag':
            shape, counters = glyph_geometry(font, char)
            assert counters == 1, f'{char}: italic alternate must retain one open counter'
        assert font['glyf'][cmap[ord('f')]].yMin < 0, 'Italic f needs a descender'
        assert font['hmtx'][cmap[ord('l')]][0] < 400, 'Italic l exit stroke must not extrapolate'
        assert ascender.xMax - ascender.xMin < 400, 'Italic l is unexpectedly wide'
    else:
        shape, counters = glyph_geometry(font, 'g')
        assert counters == 2, 'The double-storey g must retain two counters'
        center = shape.intersection(LineString([(280, -280), (280, 600)]))
        strokes = sorted((part.bounds[1], part.bounds[3]) for part in center.geoms)
        assert len(strokes) == 4, 'Expected top and bottom strokes for both g bowls'
        waist = strokes[2][0] - strokes[1][1]
        assert waist >= 60, f'g waist collapses at reading sizes: {waist:.1f} units'
        print(f'PASS {path.name}: g has two counters and a {waist:.1f}-unit open waist')
    if path.suffix == '.ttf':
        shaping_font = hb.Font(hb.Face(path.read_bytes()))
        shapes = {c: glyph_geometry(font, c)[0] for c in set(''.join(kerning))}
        for pair, adjustment in kerning.items():
            left, right = pair
            left_advance = font['hmtx'][cmap[ord(left)]][0]
            right_advance = font['hmtx'][cmap[ord(right)]][0]
            buffer = hb.Buffer()
            buffer.add_str(pair)
            buffer.guess_segment_properties()
            hb.shape(shaping_font, buffer, {'kern': True})
            actual = sum(position.x_advance for position in buffer.glyph_positions)
            assert actual == left_advance + right_advance + adjustment, f'{pair}: incorrect kerning'
            overlap = shapes[left].intersection(translate(shapes[right], xoff=left_advance + adjustment))
            assert overlap.area < 0.5, f'{pair}: kerned outlines collide'
        for pair, adjustment in {'ÁV': kerning['AV'], 'Tó': kerning['To'], 'Yé': kerning['Ye']}.items():
            buffer = hb.Buffer()
            buffer.add_str(pair)
            buffer.guess_segment_properties()
            hb.shape(shaping_font, buffer)
            actual = sum(position.x_advance for position in buffer.glyph_positions)
            expected = sum(font['hmtx'][cmap[ord(c)]][0] for c in pair) + adjustment
            assert actual == expected, f'{pair}: accented kerning was not propagated'
        print(f'PASS {len(kerning)} seed pairs: shaping values and no outline collisions')
    print(f'PASS {path.name}: coverage, metrics, contours, licensing, kerning table')

before = {p.name: sha256(p.read_bytes()).hexdigest() for p in fonts}
subprocess.run([sys.executable, str(ROOT / 'build.py')], check=True)
after = {p.name: sha256(p.read_bytes()).hexdigest() for p in fonts}
assert before == after, 'Font output changed across identical builds'
print(f'PASS byte-identical rebuild of all {len(fonts)} fonts')
