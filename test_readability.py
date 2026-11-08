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
