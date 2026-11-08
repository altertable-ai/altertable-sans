"""Regression checks against shipped fonts, independent of builder geometry."""
import unicodedata
from io import BytesIO
from functools import lru_cache
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont
import uharfbuzz as hb
from shapely.geometry import Polygon, LineString

ROOT = Path(__file__).resolve().parent
MARKS = '\u0300\u0301\u0302\u0303\u0304\u0306\u0307\u0308\u030a\u030b\u030c\u0326\u0327\u0328'


@lru_cache(maxsize=32)
def shaping_font(path):
    data = path.read_bytes()
    if path.suffix == '.woff2':
        font_file = TTFont(path)
        font_file.flavor = None
        stream = BytesIO()
        font_file.save(stream)
        data = stream.getvalue()
    return hb.Font(hb.Face(data))


def shape(path, text, features=None):
    font = shaping_font(path)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def contours(font, glyph_name):
    glyph = font['glyf'][glyph_name]
    coordinates, ends, _ = glyph.getCoordinates(font['glyf'])
    polygons, start = [], 0
    for end in ends:
        polygons.append(Polygon(coordinates[start:end + 1]))
        start = end + 1
    return polygons


class LatinRegression(unittest.TestCase):
    def setUp(self):
        self.paths = sorted((ROOT / 'fonts').glob('*.ttf')) + sorted((ROOT / 'fonts').glob('*.woff2'))

    def test_latin_coverage(self):
        required = {n for n in range(0xA0, 0x180) if unicodedata.category(chr(n)).startswith('L')}
        required |= set(map(ord, '¡¿ȘșȚțẞ¥¢¤§¶†‡‰µ¼½¾' + MARKS))
        for path in self.paths:
            missing = required - TTFont(path).getBestCmap().keys()
            self.assertFalse(missing, f'{path.name}: missing {"".join(map(chr, sorted(missing)))}')

    def test_canonical_equivalence(self):
        for path in self.paths:
            cmap = TTFont(path).getBestCmap()
            for cp in [*range(0xC0, 0x180), *range(0x218, 0x21C)]:
                char = chr(cp)
                nfd = unicodedata.normalize('NFD', char)
                if len(nfd) == 2:
                    self.assertIn(ord(nfd[1]), cmap, f'{path.name}: {char} mark missing')
                    self.assertEqual(shape(path, char), shape(path, nfd), f'{path.name}: {char}')

    def test_free_marks_and_stacking(self):
        for path in self.paths:
            f = TTFont(path); cmap = f.getBestCmap()
            for mark in MARKS:
                self.assertIn(ord(mark), cmap)
                self.assertEqual(f['hmtx'][cmap[ord(mark)]][0], 0)
            for text in ['q\u0301', 'x\u0308\u0301', 'i\u030b', 'j\u030b']:
                result = shape(path, text)
                self.assertTrue(all(gid for gid, *_ in result), f'{path.name}: {text}')
                self.assertEqual(sum(p[1] for p in result), sum(p[1] for p in shape(path, text[0])))
                self.assertNotEqual(result[-1][2:], (0, 0), f'{path.name}: unpositioned {text}')
            for base, dotless in [('i', 'ı'), ('j', 'ȷ')]:
                gid = shape(path, base + '\u030b')[0][0]
                self.assertEqual(f.getGlyphName(gid), cmap[ord(dotless)], path.name)
            stacked = shape(path, 'x\u0308\u0301')
            self.assertGreater(stacked[-1][3], stacked[-2][3], path.name)

    def test_kerning_skips_combining_marks(self):
        for path in self.paths:
            self.assertEqual(sum(p[1] for p in shape(path, 'A\u030bV')),
                             sum(p[1] for p in shape(path, 'AV')), path.name)

    def test_stacked_marks_fit_clipping_metrics(self):
        for path in self.paths:
            f = TTFont(path)
            order = f.getGlyphOrder()
            for text in ['A\u0304\u0301', 'g\u0326\u0326']:
                for gid, advance, dx, dy in shape(path, text):
                    glyph = f['glyf'][order[gid]]
                    self.assertLessEqual(glyph.yMax + dy, f['OS/2'].usWinAscent, f'{path.name}: {text}')
                    self.assertGreaterEqual(glyph.yMin + dy, -f['OS/2'].usWinDescent, f'{path.name}: {text}')

    def test_ogoneks_are_attached(self):
        for path in self.paths:
            f = TTFont(path); cmap = f.getBestCmap()
            for char in 'ĄąĘęĮįŲų':
                base = unicodedata.normalize('NFD', char)[0]
                self.assertEqual(f['glyf'][cmap[ord(char)]].numberOfContours,
                                 f['glyf'][cmap[ord(base)]].numberOfContours,
                                 f'{path.name}: detached {char}')

    def test_caron_follows_upper_stem(self):
        for path in self.paths:
            f = TTFont(path); cmap = f.getBestCmap()
            for char in 'Ľľ':
                outer = [p for p in contours(f, cmap[ord(char)]) if not p.exterior.is_ccw]
                base, accent = sorted(outer, key=lambda p: p.area, reverse=True)
                section = base.intersection(LineString([(-1000, accent.centroid.y), (2000, accent.centroid.y)]))
                self.assertLess(accent.bounds[0] - section.bounds[2], 100, f'{path.name}: {char}')

    def test_eth_has_only_one_counter(self):
        for path in self.paths:
            f = TTFont(path)
            holes = [p for p in contours(f, f.getBestCmap()[ord('ð')]) if p.exterior.is_ccw]
            self.assertEqual(len(holes), 1, path.name)

    def test_soft_dots_through_below_marks(self):
        for path in self.paths:
            f = TTFont(path)
            for text in ['i\u0326\u030b', 'j\u0326\u0301', 'į\u0301', 'į\u0307\u0301']:
                result = shape(path, text)
                base = f['glyf'][f.getGlyphName(result[0][0])]
                self.assertLess(base.yMax, 600, f'{path.name}: retained intrinsic dot in {text}')

    def test_caron_separation(self):
        for path in self.paths:
            f = TTFont(path); cmap = f.getBestCmap()
            for char in 'ďťľ':
                g = f['glyf'][cmap[ord(char)]]
                # A detached right-side caron adds one contour to the base.
                base = unicodedata.normalize('NFD', char)[0]
                expected = f['glyf'][cmap[ord(base)]].numberOfContours + 1
                self.assertEqual(g.numberOfContours, expected, f'{path.name}: {char} accent fused to stem')


if __name__ == '__main__':
    unittest.main()
