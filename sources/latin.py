"""Original additional Latin drawings and derived stroked/paired forms."""
from shapely import affinity
from shapely.geometry import Point
from shapely.ops import unary_union

LATIN = {
    'Æ': (900, 'M65 0 L385 690 H825 M385 690 V0 H825 M215 270 H385 M385 355 H770'),
    'æ': (900, 'M95 425 C130 510 370 585 420 365 V0 M420 285 C160 340 80 230 90 130 C100 -55 370 -55 420 160 M420 275 H815 C815 610 420 610 420 255 C420 -30 690 -85 810 95'),
    'Œ': (1000, 'M570 690 H325 C-15 690 -15 0 325 0 H570 V690 H930 M570 355 H870 M570 0 H930'),
    'œ': (960, 'M280 520 C15 520 15 -10 280 -10 C545 -10 545 520 280 520 Z M480 275 H875 C875 610 480 610 480 255 C480 -30 750 -85 870 95'),
    'Þ': (620, 'M100 0 V690 M100 540 H315 C620 540 620 185 315 185 H100'),
    'þ': (600, 'M100 -210 V730 M100 345 C100 455 185 520 300 520 C435 520 510 415 510 255 C510 95 435 -10 300 -10 C185 -10 100 65 100 175'),
    'ð': (580, 'M480 285 C480 570 340 680 190 730 M240 645 L410 755 M480 270 C480 605 85 605 85 255 C85 -100 480 -100 480 270 Z'),
    'Ŋ': (720, 'M100 0 V690 M100 690 L620 0 M620 690 V-60 C620 -185 560 -220 455 -220'),
    'ŋ': (580, 'M100 0 V510 M100 335 C100 445 185 520 300 520 C420 520 480 450 480 325 V-60 C480 -185 420 -220 315 -220'),
    'ĸ': (540, 'M100 0 V510 M440 510 L100 135 M260 305 L450 0'),
    'ẞ': (710, 'M100 0 V690 H390 L535 510 L360 345 C690 315 690 -75 355 20'),
    '¥': (640, 'M85 690 L320 335 L555 690 M320 335 V0 M100 300 H540 M100 150 H540'),
    '¤': (650, 'M325 560 C-10 560 -10 90 325 90 C660 90 660 560 325 560 Z M80 80 L160 160 M490 490 L570 570 M80 570 L160 490 M490 160 L570 80'),
    '¶': (620, 'M360 -130 V690 H270 C-25 690 -25 340 270 340 H360 M530 690 V-130'),
    '†': (500, 'M250 -100 V730 M55 480 H445'),
    '‡': (500, 'M250 -100 V730 M55 480 H445 M55 150 H445'),
    '§': (610, 'M495 600 C440 785 90 730 100 535 C110 380 520 375 510 200 C500 70 350 45 230 110 M115 90 C170 -95 520 -40 510 155 C500 310 90 315 100 490 C110 620 260 645 380 580'),
}


def extend_latin(drawings, outline, stroke):
    """Use original base forms for related letters without importing outlines."""
    for char, base, path in [
        ('Ø', 'O', 'M100 -30 L650 730'), ('ø', 'o', 'M65 -35 L510 550'),
        ('Ð', 'D', 'M30 355 H355'), ('Đ', 'D', 'M30 355 H355'),
        ('đ', 'd', 'M330 625 H650'), ('Ħ', 'H', 'M35 565 H675'),
        ('ħ', 'h', 'M35 625 H320'), ('Ł', 'L', 'M35 240 L350 480'),
        ('ł', 'l', 'M15 265 L240 440'), ('Ŧ', 'T', 'M125 355 H485'),
        ('ŧ', 't', 'M35 285 H325'), ('¢', 'c', 'M285 -100 V640'),
        ('µ', 'u', 'M100 -210 V160'),
    ]:
        width, base_shape = drawings[base]
        drawings[char] = (max(width, 35 + outline(path, stroke * .85).bounds[2]),
                          unary_union([base_shape, outline(path, stroke * .85)]))
    for char, base, path in [('ı', 'i', 'M125 0 V510'),
                             ('ȷ', 'j', 'M155 510 V-60 C155 -185 110 -240 25 -240')]:
        width, original = drawings[base]
        form = outline(path, stroke)
        form = affinity.translate(form, xoff=original.bounds[0] - form.bounds[0])
        drawings[char] = (width, form)
    # Long s follows the f crown without its crossbar.
    drawings['ſ'] = (355, outline('M135 0 V560 C135 680 200 730 285 730 H335', stroke))
    for char, left, right in [('Ĳ', 'I', 'J'), ('ĳ', 'i', 'j'), ('ŉ', '’', 'n')]:
        w1, a = drawings[left]; w2, b = drawings[right]
        drawings[char] = (w1 + w2, unary_union([a, affinity.translate(b, xoff=w1)]))
    for char, base in [('Ŀ', 'L'), ('ŀ', 'l')]:
        width, form = drawings[base]
        dot = Point(width + 55, 350).buffer(stroke / 2, quad_segs=16)
        drawings[char] = (width + 150, unary_union([form, dot]))
    for char, base in [('ª', 'a'), ('º', 'o')]:
        width, form = drawings[base]
        drawings[char] = (round(width * .65), affinity.translate(
            affinity.scale(form, .65, .65, origin=(0, 0)), yoff=370))
    for char, base in [('¡', '!'), ('¿', '?')]:
        width, form = drawings[base]
        # Inverted punctuation starts at x-height and descends below the baseline.
        form = affinity.rotate(form, 180, origin=(width / 2, 0))
        drawings[char] = (width, affinity.translate(form, yoff=540))
    for char, numerator, denominator in [('¼', '1', '4'), ('½', '1', '2'), ('¾', '3', '4')]:
        upper = affinity.translate(affinity.scale(drawings[numerator][1], .52, .52, origin=(0, 0)), yoff=365)
        lower = affinity.translate(affinity.scale(drawings[denominator][1], .52, .52, origin=(0, 0)), xoff=400)
        slash = outline('M220 -15 L530 710', stroke * .6)
        drawings[char] = (770, unary_union([upper, lower, slash]))
    width, percent = drawings['%']
    circle = affinity.translate(outline('M200 300 C30 300 30 0 200 0 C370 0 370 300 200 300 Z', stroke), xoff=780)
    drawings['‰'] = (1180, unary_union([percent, circle]))
