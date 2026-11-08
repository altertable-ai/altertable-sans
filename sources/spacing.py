"""Optical sidebearings and seed kerning pairs, in font units."""

# Text adds six units to each advance; these are the underlying Display bearings.
SIDEBEARINGS = {
    'A': (28, 28), 'C': (52, 48), 'G': (52, 52), 'I': (50, 50),
    'P': (55, 30), 'J': (36, 52), 'K': (55, 42), 'O': (42, 42), 'Q': (42, 38),
    'R': (55, 42), 'S': (40, 40), 'V': (26, 26), 'W': (26, 26),
    'X': (32, 32), 'Y': (25, 25), 'Z': (44, 44),
    # Preserve stem/round spacing as stroke expansion changes the ink width.
    'b': (55, 45), 'd': (45, 55), 'h': (55, 55), 'm': (55, 55),
    'n': (55, 55), 'p': (55, 45), 'q': (45, 55), 'u': (55, 55),
    'c': (42, 38), 'e': (42, 42), 'f': (32, 18), 'i': (68, 68),
    'j': (25, 62), 'k': (55, 38), 'l': (55, 40), 'o': (42, 42),
    'r': (55, 30), 's': (36, 36), 't': (32, 30), 'v': (24, 24),
    'w': (24, 24), 'x': (28, 28), 'y': (24, 24), 'z': (38, 38),
}

KERNING = {
    'AV': -60, 'AW': -45, 'AY': -60, 'AT': -45,
    'VA': -60, 'WA': -45, 'YA': -60, 'TA': -45,
    'AC': -12, 'AG': -12, 'AO': -12, 'AQ': -12, 'AU': -8,
    'CA': -12, 'GA': -12, 'OA': -12, 'QA': -12,
    'To': -55, 'Ta': -50, 'Te': -55, 'Tc': -55, 'Ts': -35,
    'Tu': -25, 'Tr': -20, 'Tw': -20, 'Ty': -25,
    'Yo': -50, 'Ya': -50, 'Ye': -50, 'Yc': -50,
    'Yu': -35, 'Yr': -30, 'Ys': -35,
    'Vo': -30, 'Va': -30, 'Ve': -30, 'Vc': -30, 'Vu': -15,
    'Wa': -20, 'Wo': -20, 'We': -20, 'Wc': -20,
    'LT': -40, 'LV': -35, 'LW': -25, 'LY': -45,
    'FA': -35, 'Fo': -20, 'Fa': -20, 'Fe': -20,
    'PA': -30, 'Pa': -20, 'Po': -15, 'Pe': -15,
    'Ko': -15, 'Ke': -15, 'Kc': -15, 'KO': -12,
    'Ro': -8, 'Re': -8, 'RV': -10, 'RY': -15,
    'xo': -10, 'xe': -10, 'xc': -10, 'ox': -10, 'ex': -10,
    'vo': -8, 've': -8, 'va': -8, 'ov': -8,
    'wo': -6, 'we': -6, 'wa': -6,
    'yo': -8, 'ye': -8, 'ya': -8, 'oy': -8,
    'ff': 12, 'fi': 10, 'fl': 10,
    'r.': -22, 'r,': -22, 'v.': -30, 'v,': -30,
    'w.': -20, 'w,': -20, 'y.': -25, 'y,': -25,
    'T.': -55, 'T,': -55, 'V.': -50, 'V,': -50,
    'W.': -35, 'W,': -35, 'Y.': -55, 'Y,': -55,
    'F.': -35, 'F,': -35, 'P.': -45, 'P,': -45,
    'A’': -35, 'A”': -35, 'L’': -35, 'L”': -35,
    '‘A': -30, '“A': -30,
}


def optical_weights(char, weight, italic, defaults):
    """Ease heavy a/g bowls independently of their stems and connecting strokes."""
    amount = max(0, weight - 400) / 300
    if not italic and char == 'a':
        return (1, 1 - .14 * amount)
    if not italic and char == 'g':
        return (1 - .14 * amount, 1, 1 - .1 * amount, 1 - .30 * amount)
    return defaults


def kerning_for_style(weight, italic):
    """Reserve more crown clearance for heavy/italic f and ease heavy diagonals."""
    pairs = dict(KERNING)
    amount = max(0, weight - 400) / 300
    if italic:
        pairs.update(ff=round(24 + 8*amount), fi=round(18 + 6*amount), fl=round(16 + 6*amount))
        pairs.update({'r.': -16, 'r,': -16})
    else:
        pairs.update(ff=round(12 + 12*amount), fi=round(10 + 10*amount), fl=round(10 + 8*amount))
    for pair in ['AV', 'AW', 'AY', 'AT', 'VA', 'WA', 'YA', 'TA']:
        pairs[pair] += round(8*amount)
    return pairs
