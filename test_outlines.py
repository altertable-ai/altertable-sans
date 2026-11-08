"""Quantization must not introduce invalid contours or backtracking spikes."""
from pathlib import Path
import unittest

from fontTools.ttLib import TTFont
from test_latin import contours


class OutlineValidity(unittest.TestCase):
    def test_grid_rounded_contours_are_valid(self):
        for path in (Path(__file__).resolve().parent / 'fonts').glob('*.ttf'):
            with TTFont(path) as font:
                for name in font.getGlyphOrder():
                    for contour in contours(font, name):
                        with self.subTest(font=path.name, glyph=name):
                            self.assertTrue(contour.is_valid)
                            self.assertGreater(contour.area, 0)
