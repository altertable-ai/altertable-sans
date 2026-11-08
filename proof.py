"""Render actual TTFs at reading and display sizes for visual review."""
from pathlib import Path
from PIL import Image
from proof_render import draw_text

ROOT = Path(__file__).resolve().parent
SCALE = 2
image = Image.new('RGB', (1440 * SCALE, 1100 * SCALE), '#f5f3ed')


def line(text, y, size, optical='Text', color='#22221f'):
    path = ROOT / 'fonts' / f'AltertableSans{optical}-Regular.ttf'
    draw_text(image, path, text, 64, y + size, size, color, SCALE)


line('ALTERTABLE SANS / WEBSITE PROOF / 1.000', 25, 15, color='#66665e')
line('A quieter kind of clarity.', 72, 78, 'Display')
line('Regular Text', 200, 24)
line('Good typography makes room for the things we need to say.', 250, 30)
line('The shape of an idea becomes clearer when we put it into words.', 306, 22)
line('Review the details, compare the results, and follow the questions that matter.', 350, 18)
line('A useful interface gives every number, label, and sentence enough room to breathe.', 390, 14)
line('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 460, 38, 'Display')
line('abcdefghijklmnopqrstuvwxyz', 525, 44, 'Display')
line('0123456789  $ € £  + − × ÷ =  ( ) [ ] { }', 600, 38)
line('Hamburgefontsiv  ag eoc  rn m  Il1  O0', 675, 40)
line('À bientôt. Über Größe? Café, façade, mañana.', 750, 32)
line('AVATAR  WAY  To  Type  Vo  LY  “Quotes” …', 820, 32)
line('Regular Display', 908, 22)
line('Small details. Shared language.', 955, 60, 'Display')
rendered = image.resize((1440, 1100), Image.Resampling.LANCZOS)
rendered.save(ROOT / 'proof.png')
versioned = ROOT / 'proofs' / 'v1.000'
versioned.mkdir(parents=True, exist_ok=True)
rendered.save(versioned / 'proof.png')
print(ROOT / 'proof.png')
