"""Quantization must not introduce invalid contours or backtracking spikes."""
from pathlib import Path
import unittest

from fontTools.ttLib import TTFont
from test_latin import contours
from build import FlattenPen, outline
from fontTools.svgLib.path import parse_path
from sources.glyphs import GLYPHS, PATH_WEIGHTS


class OutlineValidity(unittest.TestCase):
    def test_open_curve_caps_follow_endpoint_tangents(self):
        pen = FlattenPen()
        parse_path('M0 0 C100 0 100 100 200 100', pen)
        points = pen.paths[0]
        self.assertEqual(points[1][1], points[0][1])
        self.assertEqual(points[-2][1], points[-1][1])

    def test_y_tail_has_vertical_cut(self):
        # The horizontal tangent at the end of y needs a vertical butt cap.
        for stroke in (74, 86, 90, 104, 118, 132):
            form = outline(GLYPHS['y'][1], stroke, PATH_WEIGHTS['y'])
            points = list(form.exterior.coords)
            tail = [(a, b) for a, b in zip(points, points[1:])
                    if a[1] < 0 and b[1] < 0 and abs(a[1]-b[1]) > 50
                    and abs(a[0]-b[0]) < 2]
            self.assertEqual(len(tail), 1, stroke)
            self.assertAlmostEqual(tail[0][0][0], tail[0][1][0], places=7)

    def test_per_mille_circles_do_not_collide(self):
        for path in (Path(__file__).resolve().parent / 'fonts').glob('*.ttf'):
            with TTFont(path) as font:
                rings = contours(font, font.getBestCmap()[ord('‰')])
                self.assertEqual(sum(not ring.exterior.is_ccw for ring in rings), 4, path.name)
                self.assertEqual(sum(ring.exterior.is_ccw for ring in rings), 3, path.name)

    def test_grid_rounded_contours_are_valid(self):
        for path in (Path(__file__).resolve().parent / 'fonts').glob('*.ttf'):
            with TTFont(path) as font:
                for name in font.getGlyphOrder():
                    for contour in contours(font, name):
                        with self.subTest(font=path.name, glyph=name):
                            self.assertTrue(contour.is_valid)
                            self.assertGreater(contour.area, 0)
