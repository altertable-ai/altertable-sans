"""Distribution-level metadata regressions, independent of the builder."""
from pathlib import Path
import unittest

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
STYLES = {300: 'Light', 400: 'Regular', 500: 'Medium', 600: 'SemiBold', 700: 'Bold'}


class FontMetadata(unittest.TestCase):
    def test_metadata(self):
        for path in sorted((ROOT / 'fonts').glob('*.ttf')):
            with self.subTest(font=path.name), TTFont(path) as font:
                names, os2 = font['name'], font['OS/2']
                version = float(names.getDebugName(5).removeprefix('Version '))
                self.assertGreaterEqual(version, 1)
                self.assertAlmostEqual(font['head'].fontRevision, version, places=4)
                self.assertTrue(os2.ulCodePageRange1 & 1, 'Windows Latin codepage')
                self.assertIn('https://github.com/altertable-ai/altertable-sans', names.getDebugName(0))
                italic = bool(font['head'].macStyle & 2)
                bold = os2.usWeightClass == 700
                self.assertEqual(bool(os2.fsSelection & 0x40), not (italic or bold))
                self.assertEqual(bool(os2.fsSelection & 1), italic)
                self.assertEqual(bool(os2.fsSelection & 0x20), bold)
                self.assertEqual(font['gasp'].gaspRange, {65535: 15})
                self.assertIn(b'\xb8\x01\xff\x85\xb0\x04\x8d', font['prep'].program.getBytecode())
                self.assertEqual(font['meta'].data['dlng'], 'Latn')
                self.assertEqual(font['meta'].data['slng'], 'Latn')
                self.assertIn(os2.usWeightClass, STYLES)
                self.assertEqual(names.getDebugName(16) is None, os2.usWeightClass in (400, 700))
                axes = {axis.AxisTag: i for i, axis in enumerate(font['STAT'].table.DesignAxisRecord.Axis)}
                values = font['STAT'].table.AxisValueArray.AxisValue
                self.assertTrue(any(value.AxisIndex == axes['wght'] and value.Value == os2.usWeightClass
                                    for value in values))
                if 'Text' in path.name:
                    self.assertTrue(any(value.AxisIndex == axes['ital'] and value.Value == int(italic)
                                        for value in values))


if __name__ == '__main__':
    unittest.main()
