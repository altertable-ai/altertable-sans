"""Regression coverage for the Google Fonts Latin Core additions."""
import unittest
import unicodedata
from pathlib import Path
from fontTools.ttLib import TTFont
from test_latin import shape

REQUIRED = '¨¯´¸ˆˇ˘˙˚˛˜˝ẀẁẂẃẄẅỲỳ‚„‹›◌'
AUXILIARY = 'ǾǿʻǦǤȞǨƷǮǧǥȟǩʒǯǓǔẼẽǍǎ'

class GoogleFontsGlyphs(unittest.TestCase):
    def test_core_and_auxiliary_coverage(self):
        for path in Path('fonts').glob('*.ttf'):
            cmap = TTFont(path).getBestCmap()
            self.assertFalse(set(map(ord, REQUIRED + AUXILIARY)) - cmap.keys(), path.name)

    def test_added_canonical_equivalence(self):
        for path in Path('fonts').glob('*.ttf'):
            for char in REQUIRED + AUXILIARY:
                nfd = unicodedata.normalize('NFD', char)
                if len(nfd) == 2:
                    self.assertEqual(shape(path, char), shape(path, nfd), f'{path}: {char}')

    def test_dotted_circle_attaches_marks(self):
        for path in Path('fonts').glob('*.ttf'):
            result = shape(path, '◌\u0301')
            self.assertTrue(all(gid for gid, *_ in result), path.name)
            self.assertNotEqual(result[-1][2:], (0, 0), path.name)

    def test_math_widths(self):
        for path in Path('fonts').glob('*.ttf'):
            font = TTFont(path); cmap = font.getBestCmap()
            self.assertEqual(len({font['hmtx'][cmap[ord(c)]][0] for c in '<>+=−×÷'}), 1, path.name)

    def test_two_bottom_commas_fit_descent(self):
        for path in Path('fonts').glob('*.ttf'):
            font = TTFont(path)
            for gid, _, _, dy in shape(path, 'g\u0326\u0326'):
                self.assertGreaterEqual(font['glyf'][font.getGlyphName(gid)].yMin + dy,
                                        -440, path.name)

    def test_percent_counters_stay_separate(self):
        from build import outline
        from sources.glyphs import GLYPHS, PATH_WEIGHTS
        for stroke in (74, 90, 104, 118, 132):
            form = outline(GLYPHS['%'][1], stroke, PATH_WEIGHTS.get('%', ()))
            self.assertEqual(len(form.geoms), 3, stroke)
            self.assertEqual(sorted(len(p.interiors) for p in form.geoms), [0, 1, 1])

    def test_section_has_open_central_counter(self):
        from build import outline
        from sources.latin import LATIN
        for stroke in (74, 90, 104, 118, 132):
            form = outline(LATIN['§'][1], stroke)
            self.assertEqual(form.geom_type, 'Polygon')
            self.assertEqual(len(form.interiors), 1, stroke)

    def test_at_outer_bowl_stays_open(self):
        from build import outline
        from sources.glyphs import GLYPHS, PATH_WEIGHTS
        for stroke in (74, 86, 90, 104, 118, 132):
            form = outline(GLYPHS['@'][1], stroke, PATH_WEIGHTS.get('@', ()))
            self.assertEqual(form.geom_type, 'Polygon')
            self.assertEqual(len(form.interiors), 1, stroke)
