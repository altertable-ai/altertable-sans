"""Minimum optical constraints for small interface text."""
from pathlib import Path
import unittest
from fontTools.ttLib import TTFont
from shapely.geometry import Polygon
from test_latin import shape

ROOT = Path(__file__).resolve().parent


def counters(font, char):
    glyph = font['glyf'][font.getBestCmap()[ord(char)]]
    coordinates, ends, _ = glyph.getCoordinates(font['glyf'])
    result, start = [], 0
    for end in ends:
        polygon = Polygon(coordinates[start:end + 1])
        if polygon.exterior.is_ccw:
            result.append(polygon)
        start = end + 1
    return result


class Readability(unittest.TestCase):
    def test_upright_figures_have_cell_clearance(self):
        # Tabular metrics alone do not prevent a diagonal from crossing its cell.
        for path in (ROOT / 'fonts').glob('*.ttf'):
            font = TTFont(path)
            if font['OS/2'].fsSelection & 1:
                continue
            for char in '0123456789':
                name = font.getBestCmap()[ord(char)]
                glyph = font['glyf'][name]
                advance = font['hmtx'][name][0]
                self.assertGreaterEqual(glyph.xMin, 40, (path.name, char))
                self.assertGreaterEqual(advance - glyph.xMax, 40, (path.name, char))

    def test_text_rounds_have_small_size_clearance(self):
        font = TTFont(ROOT / 'fonts' / 'AltertableSansText-Regular.ttf')
        name = font.getBestCmap()[ord('o')]
        glyph = font['glyf'][name]
        self.assertGreaterEqual(font['hmtx'][name][0] - glyph.xMax + glyph.xMin, 96)

    def test_regular_g_has_room_in_upper_counter(self):
        font = TTFont(ROOT / 'fonts' / 'AltertableSansText-Regular.ttf')
        holes = counters(font, 'g')
        self.assertEqual(len(holes), 2)
        upper = max(holes, key=lambda hole: hole.centroid.y)
        self.assertGreaterEqual(upper.bounds[2] - upper.bounds[0], 220)

    def test_stem_letter_spacing_stays_balanced_across_weights(self):
        # Stem-to-stem whitespace must not collapse as strokes get heavier.
        # Compare the shipped outlines, not the builder's sidebearing table.
        regular = TTFont(ROOT / 'fonts' / 'AltertableSansText-Regular.ttf')
        for style in ['Light', 'Book', 'Medium', 'Semibold', 'Bold']:
            font = TTFont(ROOT / 'fonts' / f'AltertableSansText-{style}.ttf')
            for char in 'bhdmnpqu':
                with self.subTest(style=style, char=char):
                    spaces = []
                    for face in (regular, font):
                        name = face.getBestCmap()[ord(char)]
                        glyph = face['glyf'][name]
                        advance = face['hmtx'][name][0]
                        spaces.append((glyph.xMin, advance - glyph.xMax))
                    for baseline, actual in zip(*spaces):
                        self.assertGreaterEqual(actual, baseline * .85)
                        self.assertLessEqual(actual, baseline * 1.15)

    def test_one_aligns_with_flat_topped_figures(self):
        for path in (ROOT / 'fonts').glob('*.ttf'):
            font = TTFont(path)
            cmap = font.getBestCmap()
            one = font['glyf'][cmap[ord('1')]]
            four = font['glyf'][cmap[ord('4')]]
            self.assertEqual((one.yMin, one.yMax), (four.yMin, four.yMax), path.name)
            self.assertEqual((one.yMin, one.yMax), (0, 720), path.name)

    def test_proportional_and_tabular_figures(self):
        for path in (ROOT / 'fonts').glob('*.ttf'):
            def width(text, features):
                return sum(position[1] for position in shape(path, text, features))
            tabular = {'tnum': True}
            proportional = {'pnum': True}
            self.assertEqual(width('11,111', tabular), width('88,888', tabular), path.name)
            self.assertLess(width('11,111', proportional), width('88,888', proportional), path.name)
            self.assertLess(width('€1,234.56', proportional), width('€1,234.56', tabular), path.name)
            self.assertEqual(width('11,111', {'pnum': True, 'tnum': True}), width('11,111', tabular), path.name)
            font = TTFont(path)
            name = font.getBestCmap()[ord('1')]
            one, narrow = font['glyf'][name], font['glyf'][name + '.pnum']
            self.assertEqual((narrow.yMin, narrow.yMax), (0, 720), path.name)
            self.assertGreater(one.xMax - one.xMin, narrow.xMax - narrow.xMin, path.name)
            for char in '0123456789':
                glyph_name = font.getBestCmap()[ord(char)] + '.pnum'
                glyph = font['glyf'][glyph_name]
                if char == '1' and not font['OS/2'].fsSelection & 1:
                    self.assertGreaterEqual(font['hmtx'][glyph_name][0], glyph.xMax, path.name)

    def test_identifiers_have_structural_distinctions(self):
        for path in (ROOT / 'fonts').glob('*.ttf'):
            f = TTFont(path); cmap = f.getBestCmap()
            cap_i = f['glyf'][cmap[ord('I')]]
            # I has crossbars rather than relying on its height to differ from l.
            self.assertGreaterEqual(len(cap_i.coordinates), 12, path.name)
            # A dotted zero is structurally different from the capital O.
            self.assertEqual(f['glyf'][cmap[ord('0')]].numberOfContours, 3, path.name)

    def test_heavy_and_italic_f_spacing(self):
        # Crown/overhang clearance is tuned separately, not inherited from Regular.
        for style, pairs in {'Regular': {'ff':12, 'fi':10},
                             'Bold': {'ff':24, 'fi':20},
                             'Italic': {'ff':24, 'fi':18},
                             'BoldItalic': {'ff':32, 'fi':24}}.items():
            path = ROOT / 'fonts' / f'AltertableSansText-{style}.ttf'
            for pair, expected in pairs.items():
                natural = sum(sum(p[1] for p in shape(path, c)) for c in pair)
                self.assertEqual(sum(p[1] for p in shape(path, pair)) - natural, expected, f'{style}: {pair}')

    def test_heavy_lowercase_counters_remain_open(self):
        for style in ['Semibold', 'Bold']:
            font = TTFont(ROOT / 'fonts' / f'AltertableSansText-{style}.ttf')
            for char in 'ag':
                for counter in counters(font, char):
                    x0, y0, x1, y1 = counter.bounds
                    # At 12px, 125 units gives at least 1.5 pixels of counter height.
                    self.assertGreaterEqual(y1-y0, 125, f'{style} {char}')


if __name__ == '__main__':
    unittest.main()
