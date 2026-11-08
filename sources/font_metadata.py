"""Shared OpenType metadata for the static family."""
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import newTable
from fontTools.ttLib.tables.ttProgram import Program

VERSION = '1.000'
PROJECT_URL = 'https://github.com/altertable-ai/altertable-sans'
COPYRIGHT = f'Copyright 2026 The Altertable Sans Project Authors ({PROJECT_URL})'


def finish_metadata(font, optical, weight, style, italic):
    font['head'].fontRevision = float(VERSION)
    font['OS/2'].recalcCodePageRanges(font)
    font['OS/2'].achVendID = 'ATBL'
    axes = [{'tag': 'wght', 'name': 'Weight', 'values': [
        dict(value=weight, name=style, flags=2 if weight == 400 else 0)
    ]}]
    if optical == 'Text':
        value = dict(value=int(italic), name='Italic' if italic else 'Roman',
                     flags=0 if italic else 2)
        if not italic:
            value['linkedValue'] = 1
        axes.append(dict(tag='ital', name='Italic', values=[value]))
    buildStatTable(font, axes)
    # Enable smart dropout control for these deliberately unhinted outlines.
    font['prep'] = newTable('prep')
    font['prep'].program = Program()
    font['prep'].program.fromBytecode(b'\xb8\x01\xff\x85\xb0\x04\x8d')
    font['gasp'] = newTable('gasp')
    font['gasp'].version = 1
    font['gasp'].gaspRange = {65535: 15}
    font['meta'] = newTable('meta')
    font['meta'].data = {'dlng': 'Latn', 'slng': 'Latn'}
