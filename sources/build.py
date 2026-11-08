"""Compile the checked-in UFOs; never regenerate or overwrite editable sources.

Run: python sources/build.py [--output-dir fonts]
"""
import argparse
import os
from pathlib import Path
import sys

from fontmake.font_project import FontProject
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sources.font_metadata import finish_metadata


def rebuild(source, output):
    output.mkdir(parents=True, exist_ok=True)
    # The epoch matches the original geometry builder and fixes binary timestamps.
    previous_epoch = os.environ.get('SOURCE_DATE_EPOCH')
    try:
        os.environ['SOURCE_DATE_EPOCH'] = '1794096000'
        FontProject().run_from_ufos(
            [str(source)], output=('ttf',), output_dir=str(output),
            use_production_names=False, remove_overlaps=False, reverse_direction=False,
        )
    finally:
        if previous_epoch is None:
            os.environ.pop('SOURCE_DATE_EPOCH', None)
        else:
            os.environ['SOURCE_DATE_EPOCH'] = previous_epoch
    path = output / source.with_suffix('.ttf').name
    font = TTFont(path, recalcTimestamp=False)
    family = font['name'].getDebugName(16) or font['name'].getDebugName(1)
    italic = bool(font['head'].macStyle & 2)
    weight = font['OS/2'].usWeightClass
    weight_name = {300: 'Light', 400: 'Regular', 500: 'Medium',
                   600: 'SemiBold', 700: 'Bold'}[weight]
    revision = font['head'].fontRevision
    finish_metadata(font, 'Display' if 'Display' in family else 'Text',
                    weight, weight_name, italic)
    font['head'].fontRevision = revision
    font.save(path)
    font.flavor = 'woff2'
    font.save(path.with_suffix('.woff2'))
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'fonts')
    args = parser.parse_args()
    sources = sorted((ROOT / 'sources' / 'ufo').glob('*.ufo'))
    if not sources:
        parser.error('No UFO sources found in sources/ufo')
    for source in sources:
        rebuild(source, args.output_dir)
