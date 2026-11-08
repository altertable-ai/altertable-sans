"""Reading-size identifier, weight and spacing proof for every shipped style."""
from pathlib import Path
from PIL import Image
from proof_render import draw_text

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'proofs' / 'v0.013'
OUT.mkdir(parents=True, exist_ok=True)
paths = sorted((ROOT / 'fonts').glob('*.ttf'))
height = 190*len(paths)+30
image = Image.new('RGB', (1400*2, height*2), '#f5f3ed')
y = 30
for path in paths:
    draw_text(image, ROOT/'fonts'/'AltertableSansText-Regular.ttf', path.stem, 32, y, 16, '#66665e'); y += 35
    for size in [12,16,28]:
        draw_text(image, path, 'g2 2026 Il1 O0 rn m · Minimum revenue · office affinity · AVATAR To Type · Ąą Ęę Ľľ ð', 32, y, size)
        y += size+18
    y += 15
image.resize((1400,height), Image.Resampling.LANCZOS).save(OUT/'readability.png')
print(OUT/'readability.png')
