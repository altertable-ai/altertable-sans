"""Render an article specimen within Google Fonts' image-size limits."""
from pathlib import Path
from PIL import Image
from proof_render import draw_text

ROOT = Path(__file__).resolve().parent
image = Image.new('RGB', (1440 * 2, 720 * 2), '#f5f3ed')
text = ROOT / 'fonts' / 'AltertableSansText-Regular.ttf'
display = ROOT / 'fonts' / 'AltertableSansDisplay-Regular.ttf'
for font, words, y, size in [
    (display, 'Altertable Sans', 130, 90),
    (text, 'Good questions deserve clear answers.', 240, 40),
    (text, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 340, 40),
    (text, 'abcdefghijklmnopqrstuvwxyz', 420, 48),
    (text, '0123456789  € £ $  Il1 O0  Ąą Ęę Ŵŵ Ỳỳ', 530, 36),
    (text, 'Text and Display · Original open-source letterforms', 635, 24),
]:
    draw_text(image, font, words, 64, y, size, '#22221f', 2)
output = ROOT / 'fonts' / 'article' / 'specimen.png'
output.parent.mkdir(parents=True, exist_ok=True)
image.resize((1440, 720), Image.Resampling.LANCZOS).save(output, optimize=True)
print(output)
