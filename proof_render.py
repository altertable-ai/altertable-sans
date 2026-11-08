"""Render HarfBuzz glyph IDs and positions through FreeType (including marks)."""
from functools import lru_cache
from pathlib import Path

import freetype
from PIL import Image
import uharfbuzz as hb


@lru_cache(maxsize=32)
def load_font(path):
    return hb.Font(hb.Face(Path(path).read_bytes())), freetype.Face(str(path))


def draw_text(image, path, text, x, baseline, size, color='#22221f', scale=2):
    shaping_font, face = load_font(str(path))
    face.set_pixel_sizes(0, round(size * scale))
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(shaping_font, buffer)
    unit = size * scale / shaping_font.face.upem
    cursor = x * scale
    for info, position in zip(buffer.glyph_infos, buffer.glyph_positions):
        face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
        glyph = face.glyph
        bitmap = glyph.bitmap
        if bitmap.width and bitmap.rows:
            mask = Image.frombytes('L', (bitmap.pitch, bitmap.rows), bytes(bitmap.buffer))
            mask = mask.crop((0, 0, bitmap.width, bitmap.rows))
            left = round(cursor + position.x_offset * unit + glyph.bitmap_left)
            top = round(baseline * scale - position.y_offset * unit - glyph.bitmap_top)
            image.paste(color, (left, top), mask)
        cursor += position.x_advance * unit
    return cursor / scale
