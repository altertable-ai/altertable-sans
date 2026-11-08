"""Editable source export and independent rebuild regression tests."""
import tempfile
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont
from sources.ufo_export import export_ufo


class UFOSourcesTest(unittest.TestCase):
    def test_export_preserves_editable_outlines_names_and_metrics(self):
        from fontTools.ufoLib import UFOReader
        font = TTFont('fonts/AltertableSansText-Regular.ttf')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'Regular.ufo'
            export_ufo(font, 'languagesystem DFLT dflt;\n', path)
            reader = UFOReader(path)
            glyphs = reader.getGlyphSet()
            self.assertEqual(set(glyphs.keys()), set(font.getGlyphOrder()))
            self.assertEqual(reader.readLib()['public.glyphOrder'], font.getGlyphOrder())
            from types import SimpleNamespace
            glyph = SimpleNamespace()
            glyphs.readGlyph(font.getBestCmap()[65], glyph)
            self.assertEqual(glyph.width, font['hmtx'][font.getBestCmap()[65]][0])
            self.assertEqual(glyph.unicodes, [65])
            self.assertEqual(reader.readFeatures(), 'languagesystem DFLT dflt;\n')
            before = {p.relative_to(path): p.read_bytes() for p in path.rglob('*') if p.is_file()}
            export_ufo(font, 'languagesystem DFLT dflt;\n', path)
            after = {p.relative_to(path): p.read_bytes() for p in path.rglob('*') if p.is_file()}
            self.assertEqual(before, after)


    def test_fontmake_rebuild_reads_source_edits_and_preserves_shaping(self):
        import importlib.util
        if importlib.util.find_spec('fontmake') is None:
            self.skipTest('Install requirements-source.txt for the UFO compiler test')
        from sources.build import rebuild
        import xml.etree.ElementTree as ET
        from fontTools.ufoLib import UFOReader
        from fontTools.pens.recordingPen import RecordingPen
        font = TTFont('fonts/AltertableSansText-Regular.ttf')
        font['head'].fontRevision = 1.001
        for record in font['name'].names:
            if record.nameID == 5:
                record.string = 'Version 1.001'.encode(record.getEncoding())
        left, right = (font.getBestCmap()[ord(c)] for c in 'AV')
        features = f'languagesystem DFLT dflt; feature kern {{ pos {left} {right} -71; }} kern;'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'AltertableSansText-Regular.ufo'
            export_ufo(font, features, path)
            reader = UFOReader(path)
            filename = reader.getGlyphSet().contents[left]
            glif = path / 'glyphs' / filename
            tree = ET.parse(glif)
            tree.getroot().find('advance').set('width', '777')
            tree.write(glif, encoding='utf-8', xml_declaration=True)
            result = TTFont(rebuild(path, root / 'output'))
            self.assertAlmostEqual(result['head'].fontRevision, 1.001, places=4)
            self.assertEqual(result['name'].getDebugName(5), 'Version 1.001')
            self.assertEqual(result.getGlyphOrder(), font.getGlyphOrder())
            self.assertEqual(result.getBestCmap(), font.getBestCmap())
            self.assertEqual(result['hmtx'][left][0], 777)
            self.assertEqual(result['name'].getDebugName(6), font['name'].getDebugName(6))
            original, compiled = RecordingPen(), RecordingPen()
            font.getGlyphSet()[left].draw(original)
            result.getGlyphSet()[left].draw(compiled)
            self.assertEqual(original.value, compiled.value)
            pair = result['GPOS'].table.LookupList.Lookup[0].SubTable[0]
            self.assertEqual(pair.PairSet[0].PairValueRecord[0].Value1.XAdvance, -71)


    def test_all_production_sources_rebuild_with_identical_outlines_and_shaping(self):
        import importlib.util
        if importlib.util.find_spec('fontmake') is None:
            self.skipTest('Install requirements-source.txt for the UFO compiler test')
        import uharfbuzz as hb
        from fontTools.pens.recordingPen import RecordingPen
        from sources.build import rebuild

        def shape(path, text, features):
            face = hb.Face(path.read_bytes())
            buffer = hb.Buffer()
            buffer.add_str(text)
            buffer.guess_segment_properties()
            hb.shape(hb.Font(face), buffer, features)
            return [(i.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
                    for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)]

        sources = sorted(Path('sources/ufo').glob('*.ufo'))
        self.assertEqual(len(sources), 11)
        texts = ['AVATAR To Wa 0123456789', 'A\u0301 a\u0308\u0301 fi ffi',
                 'ÁçÉøÞ ÐŁŒ ß ¹₂₃']
        with tempfile.TemporaryDirectory() as directory:
            for source in sources:
                original_path = Path('fonts') / source.with_suffix('.ttf').name
                compiled_path = rebuild(source, Path(directory))
                original, compiled = TTFont(original_path), TTFont(compiled_path)
                with self.subTest(font=source.name):
                    self.assertEqual(original.getGlyphOrder(), compiled.getGlyphOrder())
                    self.assertEqual(original.getBestCmap(), compiled.getBestCmap())
                    self.assertEqual(original['hmtx'].metrics, compiled['hmtx'].metrics)
                    original_glyphs, compiled_glyphs = original.getGlyphSet(), compiled.getGlyphSet()
                    for name in original.getGlyphOrder():
                        before, after = RecordingPen(), RecordingPen()
                        original_glyphs[name].draw(before)
                        compiled_glyphs[name].draw(after)
                        self.assertEqual(before.value, after.value, name)
                    for text in texts:
                        for features in [{}, {'tnum': 1}, {'pnum': 1}, {'zero': 1},
                                         {'ccmp': 1, 'mark': 1, 'mkmk': 1}]:
                            self.assertEqual(shape(original_path, text, features),
                                             shape(compiled_path, text, features),
                                             (text, features))
                original.close()
                compiled.close()


if __name__ == '__main__':
    unittest.main()
