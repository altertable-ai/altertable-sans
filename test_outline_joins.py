"""Joined source strokes must not leave hairline wedges or close counters."""
import math
import unittest
from shapely import affinity

from build import outline, TEXT_STYLES
from sources.glyphs import GLYPHS, EXTRA, PATH_WEIGHTS
from sources.latin import LATIN, extend_latin
from sources.marks import add_accents


def corner_angles(form):
    """Interior angle between incident segments, independent of ring direction."""
    polygons = [form] if form.geom_type == 'Polygon' else form.geoms
    for polygon in polygons:
        for ring in [polygon.exterior, *polygon.interiors]:
            points = list(ring.coords)[:-1]
            for index, point in enumerate(points):
                before, after = points[index-1], points[(index+1) % len(points)]
                a = (before[0]-point[0], before[1]-point[1])
                b = (after[0]-point[0], after[1]-point[1])
                cosine = sum(x*y for x, y in zip(a, b)) / (math.hypot(*a)*math.hypot(*b))
                yield math.degrees(math.acos(max(-1, min(1, cosine))))


def drawings_at(stroke):
    drawings = {char: (width, outline(path, stroke, PATH_WEIGHTS.get(char, ())))
                for char, (width, path) in (GLYPHS | EXTRA | LATIN).items()}
    extend_latin(drawings, outline, stroke)
    add_accents(drawings, outline, stroke)
    return drawings


def counter_count(form):
    return sum(len(p.interiors) for p in ([form] if form.geom_type == 'Polygon' else form.geoms))


class OutlineJoins(unittest.TestCase):
    def test_joined_strokes_have_no_hairline_wedges(self):
        for stroke in [86, *(stroke for _, stroke in TEXT_STYLES.values())]:
            drawings = drawings_at(stroke)
            for char in '@§ĄąĘęĮįŲų':
                with self.subTest(stroke=stroke, char=char):
                    form = drawings[char][1]
                    self.assertTrue(form.is_valid)
                    self.assertEqual(form.geom_type, 'MultiPolygon' if char == 'į' else 'Polygon')
                    # The section sign's central lens has deliberate pointed
                    # ends; the narrow overlapping-arm notches were <14°.
                    for italic in (False, True):
                        transformed = affinity.skew(form, xs=10, origin=(0, 270)) if italic else form
                        with self.subTest(italic=italic):
                            self.assertGreater(min(corner_angles(transformed)), 15)

    def test_ogonek_keeps_base_counters_and_advance(self):
        for stroke in [86, *(stroke for _, stroke in TEXT_STYLES.values())]:
            drawings = drawings_at(stroke)
            for base, composed in zip('AaEeIiUu', 'ĄąĘęĮįŲų'):
                with self.subTest(stroke=stroke, char=composed):
                    self.assertEqual(drawings[base][0], drawings[composed][0])
                    self.assertEqual(counter_count(drawings[base][1]),
                                     counter_count(drawings[composed][1]))
                    self.assertLess(drawings[composed][1].bounds[1], 0)
            self.assertEqual(len(drawings['§'][1].interiors), 1)
            self.assertEqual(len(drawings['@'][1].interiors), 1)
