"""Shape and render the Latin regression corpus in every released style."""
from pathlib import Path
import unicodedata
from PIL import Image
from proof_render import draw_text

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'proofs' / 'v0.012'
OUT.mkdir(parents=True, exist_ok=True)
SCALE = 2
regular = ROOT / 'fonts' / 'AltertableSansText-Regular.ttf'


def line(image, path, text, y, size, color='#22221f'):
    draw_text(image, path, text, 32, y, size, color, SCALE)


samples = [
    'ď ť ľ Ľ   Ģ ģ Ķ ķ Ļ ļ Ņ ņ Ŗ ŗ   Ș ș Ț ț',
    'Æ æ Œ œ Ø ø Ð ð Þ þ Đ đ Ħ ħ Ł ł Ŋ ŋ Ŧ ŧ ẞ',
    'Ā ā Ă ă Ą ą Ė ė Ę ę Ğ ğ İ ı Ĳ ĳ ĸ Ŀ ŀ ŉ ſ',
    'Ī ī Į į Ő ő Ű ű Ų ų Ż ż   ¥ ¢ ¤ § ¶ † ‡ ‰ µ ¼ ½ ¾ ª º ¡¿',
    'Cœur, œuvre, smørrebrød. Łódź. İstanbul. Þór. Știință.',
    'Café naïve Ångström  |  ' + unicodedata.normalize('NFD', 'Café naïve Ångström'),
    'q\u0301 x\u0308\u0301 i\u0326\u030b j\u0326\u0301 į\u0301 į\u0307\u0301 A\u0304\u0301',
]
image = Image.new('RGB', (1500*SCALE, 1540*SCALE), '#f5f3ed')
y = 38
for style in ['Regular', 'Bold', 'Italic', 'BoldItalic']:
    path = ROOT / 'fonts' / f'AltertableSansText-{style}.ttf'
    line(image, regular, '0.012 / ' + style + ' / Latin and mark proof', y, 18, '#66665e'); y += 47
    for sample in samples:
        line(image, path, sample, y, 30); y += 40
    line(image, path, samples[4], y, 13); y += 44
image.resize((1500,1540), Image.Resampling.LANCZOS).save(OUT / 'latin.png')

paths = sorted((ROOT / 'fonts').glob('*.ttf'))
image = Image.new('RGB', (1500*SCALE, (len(paths)*175+30)*SCALE), 'white')
y = 30
for path in paths:
    line(image, regular, path.stem, y, 16, '#66665e'); y += 40
    line(image, path, samples[0], y, 30); y += 40
    line(image, path, samples[4], y, 24); y += 30
    line(image, path, samples[5] + '  q\u0301 x\u0308\u0301 i\u030b j\u030b', y, 13); y += 65
image.resize((1500,len(paths)*175+30), Image.Resampling.LANCZOS).save(OUT / 'all-styles.png')
print(OUT)
