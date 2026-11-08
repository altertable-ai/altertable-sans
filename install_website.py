"""Copy reviewed Text webfonts and their license into the website asset tree."""
from pathlib import Path
import shutil
import json
import argparse

from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('frontend', type=Path, help='Path to the Altertable frontend checkout')
REPOSITORY = parser.parse_args().frontend.resolve()
if not (REPOSITORY / 'src' / 'styles' / 'www.css').is_file():
    parser.error('frontend must contain src/styles/www.css')
DESTINATION = REPOSITORY / 'src' / 'styles' / 'fonts' / 'altertable-sans'
LICENSE_DIRECTORY = REPOSITORY / 'public' / 'fonts' / 'altertable-sans'

sources = []
for entry in json.loads((ROOT / 'fonts' / 'coverage.json').read_text()):
    if entry['style'] != 'Text':
        continue
    weight, style = entry['weight'], entry['name']
    source = ROOT / 'fonts' / f'AltertableSansText-{style}.woff2'
    font = TTFont(source)
    assert font['OS/2'].usWeightClass == weight
    assert font['name'].getDebugName(5) == 'Version 0.006'
    assert ord('©') in font.getBestCmap()
    sources.append(source)

DESTINATION.mkdir(parents=True, exist_ok=True)
LICENSE_DIRECTORY.mkdir(parents=True, exist_ok=True)
for source in sources:
    shutil.copyfile(source, DESTINATION / source.name)
shutil.copyfile(ROOT / 'OFL.txt', LICENSE_DIRECTORY / 'OFL.txt')
print(f'Installed {len(sources)} webfonts and OFL license')
