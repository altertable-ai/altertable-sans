"""Export the geometry builder's live font as editable, deterministic UFO 3."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.ufoLib import UFOWriter


def export_ufo(font, feature_text, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    name = lambda number: font['name'].getDebugName(number)
    os2, head, hhea = font['OS/2'], font['head'], font['hhea']
    version = (name(5) or str(head.fontRevision)).removeprefix('Version ').split()[0]
    major, _, minor = version.partition('.')
    info = SimpleNamespace(
        familyName=name(16) or name(1), styleName=name(17) or name(2),
        styleMapFamilyName=name(1), styleMapStyleName=name(2).lower(),
        unitsPerEm=head.unitsPerEm, ascender=os2.sTypoAscender,
        descender=os2.sTypoDescender, xHeight=os2.sxHeight, capHeight=os2.sCapHeight,
        italicAngle=font['post'].italicAngle, copyright=name(0),
        versionMajor=int(major), versionMinor=int(minor or 0),
        openTypeHeadCreated=(datetime(1904, 1, 1) + timedelta(seconds=head.created)).strftime('%Y/%m/%d %H:%M:%S'),
        openTypeNameUniqueID=name(3), openTypeNameVersion=name(5),
        openTypeNameDescription=name(10), openTypeNameLicense=name(13),
        openTypeNameLicenseURL=name(14), postscriptFontName=name(6),
        postscriptFullName=name(4), openTypeOS2WeightClass=os2.usWeightClass,
        openTypeOS2WidthClass=os2.usWidthClass, openTypeOS2VendorID=os2.achVendID,
        openTypeOS2Selection=[bit for bit in (7, 8, 9) if os2.fsSelection & (1 << bit)],
        openTypeOS2Type=[], openTypeOS2TypoAscender=os2.sTypoAscender,
        openTypeOS2TypoDescender=os2.sTypoDescender,
        openTypeOS2TypoLineGap=os2.sTypoLineGap,
        openTypeOS2WinAscent=os2.usWinAscent, openTypeOS2WinDescent=os2.usWinDescent,
        openTypeHheaAscender=hhea.ascent, openTypeHheaDescender=hhea.descent,
        openTypeHheaLineGap=hhea.lineGap, openTypeHheaCaretSlopeRise=hhea.caretSlopeRise,
        openTypeHheaCaretSlopeRun=hhea.caretSlopeRun,
        postscriptUnderlinePosition=font['post'].underlinePosition,
        postscriptUnderlineThickness=font['post'].underlineThickness,
    )
    # Preserve all explicit naming records, including legacy family/style mapping.
    info.openTypeNameRecords = [dict(nameID=r.nameID, platformID=r.platformID,
                                    encodingID=r.platEncID, languageID=r.langID,
                                    string=r.toUnicode()) for r in font['name'].names]
    reverse = {}
    for codepoint, glyph_name in font.getBestCmap().items():
        reverse.setdefault(glyph_name, []).append(codepoint)
    with UFOWriter(path, formatVersion=3) as writer:
        writer.writeInfo(info)
        writer.writeLib({'public.glyphOrder': font.getGlyphOrder(),
                         'public.postscriptNames': {n: n for n in font.getGlyphOrder()}})
        writer.writeFeatures(feature_text)
        glyph_set = writer.getGlyphSet()
        for stale_name in set(glyph_set.keys()) - set(font.getGlyphOrder()):
            glyph_set.deleteGlyph(stale_name)
        outlines = font.getGlyphSet()
        for glyph_name in font.getGlyphOrder():
            glyph = SimpleNamespace(width=font['hmtx'][glyph_name][0],
                                    unicodes=reverse.get(glyph_name, []))
            def draw(pen, outline=outlines[glyph_name]):
                outline.draw(SegmentToPointPen(pen))
            glyph_set.writeGlyph(glyph_name, glyph, draw, formatVersion=2)
        glyph_set.writeContents()
        writer.writeLayerContents()
