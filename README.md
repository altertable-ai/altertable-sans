# Altertable Sans

An original open-source sans-serif prototype inspired by the broad proportions
and restrained grotesk character of Anthropic Sans. Working name; version 0.006.
This is a website design proof, **not a production font family**.

## Review

Run `python3 -m http.server 8768` and open
[the specimen](http://localhost:8768/specimen.html) in a browser. It loads the local WOFF2 fonts and has editable
headings and paragraphs. `proof.png` is a rendered TTF specimen at 14–78 px.
The family includes six Text weights in upright and italic, plus Regular Display.

## Build

From this directory, using Python 3.12 and uv:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python build.py
.venv/bin/python verify.py
.venv/bin/python proof.py
```

`build.py` writes six static Text weights (300, 400, 450, 500, 600, 700), each upright and italic, and Regular Display TTF/WOFF2 files to
`fonts/`, plus an exact coverage manifest. Timestamps are fixed for repeatable
font output. `proof.py` positions precomposed Latin with HarfBuzz and renders
the TTFs through Pillow/FreeType.

## Use on the web

Copy the `fonts/` directory and `altertable-sans.css` into your site, retain `OFL.txt`,
and load the stylesheet. Use `font-family: "Altertable Sans", system-ui, sans-serif`.
The stylesheet declares all six upright and italic weights; browsers fetch only
the faces used. Unsupported characters use your fallback font.

## Sources and scope

`sources/glyphs.py` contains original editable SVG-style centerline drawings in
font coordinates (positive Y points up). No third-party outlines or metrics are
imported into the build. The initial visual reference was the Sans specimen in
[the supplied article](https://gooova.com/en/anthropic-designed-its-own-type-family/).
Version 0.002 additionally compares actual browser-rendered glyphs against
Anthropic’s public webfont. The reference is only a proofing input; `build.py`
never reads it.

The build expands strokes, unions overlaps, and emits flattened polygon contours.
This is a fast proofing representation, not the intended production master format.
Text uses a 90-unit vertical stroke and 6 units of extra spacing; Display uses
an 86-unit vertical stroke without extra spacing. Horizontal strokes are 92% of
vertical stroke thickness. Cap height is 720, x-height 540, and ascenders 760. They are initial optical trials, not fully developed
optical masters. The prototype has 267 encoded characters, tabular default figures,
and 107 seed kerning pairs expanded to 1,267 pairs for supported accented forms.

Coverage includes printable ASCII, selected punctuation and currencies, and a
subset of precomposed Latin accents. It does **not** claim full language coverage.
Unsupported characters display a visible missing-glyph box; the browser may use
fallback fonts. Combining marks and NFD input are not yet supported.

## Letter comparison

Open `comparison.html` for every Latin uppercase/lowercase letter and digit at
48 px and 14 px, with three columns: Anthropic Sans, Altertable 0.004, and current
Altertable 0.006. The g proof includes 12, 14, 16, 20, and 28 px text, plus an enlarged
glyph. The reference is weight 400, optical size 16; the separate display sample
uses optical size 48. Earlier Altertable fonts live in `proofs/v0.001/`, `proofs/v0.002/`, `proofs/v0.003/`, and `proofs/v0.004/`.

Revision 0.002 addressed a pinched g waist, weak Text strokes, undersized i/j dots, and
rounded h/n/m shoulders. That revision redrew g, h, n, m, u, i, j, r, and k,
strengthened both optical trials, and reduced Text tracking slightly.
The new g has a rounder upper counter, a continuous closed lower loop, and a
clearer waist. `verify.py` guards its two counters and minimum central clearance.
The old Text g had only about 20 units of clearance at the same cross-section.

Revision 0.003 fixes an underlying endpoint error: the old build inset all
centerline endpoints by half a stroke, even when a vertical stroke had a flat
cap. This shortened H/I/l stems and lifted their baselines. The new construction
extends outward-facing flat terminals to their intended alignment and clips
angled terminal strokes flush with those boundaries. Curved endpoints pointing
inward are left alone. Regression checks cover H/I/N/l alignment and the r arm.

This pass redraws B/J/S/s, a/b/d/e/o/p/q, and 0/1/3/6/8/9, with stronger Display
strokes and modest horizontal/vertical contrast. The numeral 1 has no foot; 0
has straighter sides; 6 and 9 use diagonal extensions. Comparison cards now have
a minimum width to avoid labels and wide samples colliding.

Revision 0.004 refines c/f/j/r/t/y and C/G/Q terminals, applies per-path diagonal
weight corrections, and adjusts sidebearings explicitly in `sources/spacing.py`.
K/R/k arms are shorter; Z/z use separate bars and diagonal strokes to avoid
miter overhang; V/W/v/w have baseline-clipped vertices. Their underlying
centerlines retain pointed joins, with the final intersection setting the bottom
edge. Word space is 260 units before Text tracking. Kerning now covers common
capital/lowercase combinations, punctuation, quotes, and f/i/l combinations.
Verification checks the shaped advance and non-collision of every seed pair,
accent propagation, positive letter bearings, and the pointed-letter baselines.

See `review-0.004.md` for the letter-by-letter review and retained differences.
Remaining review items include detailed stroke modulation and curve editing,
particularly a/e/S/s and the proportions of B/P/R. Glyphs still use
flattened stroke geometry and need further optical correction and cross-platform
rasterization checks. This is a reviewed prototype, not a production release.

The local reference is `.reference/AnthropicSans-Roman.woff2`, excluded from Git
and **not covered by this project's OFL license**. It was retrieved on 8 November
2026 from the public font URL declared by [Anthropic’s website](https://www.anthropic.com):

```text
https://www.anthropic.com/_next/static/media/AnthropicSans_Roman_Web-s.p.1e3n6bt4oqimz.woff2
```

For another checkout, place the reference font at that local path to enable the
comparison. Without it the page reports the missing font and hides the reference
samples; the Altertable build and specimen work independently. Font metadata
identifies it as Anthropic Sans Web Text Regular, with weight 300–800 and optical
size 16–48. No proprietary font is included in the open-source deliverables.

## Website trial

To update an Altertable frontend checkout, run:

```sh
.venv/bin/python install_website.py /path/to/frontend
```

`install_website.py` copies the twelve Text WOFF2 files into
`src/styles/fonts/altertable-sans/` and the license into `public/fonts/altertable-sans/`.
The website-scoped font stack is declared in `src/styles/www.css`; font faces
live in `src/styles/altertable-sans-fonts.css`. The Vite build preloads Regular.
Font display remains optional, so a slow first load can retain the system fallback.

Revision 0.005 adds copyright, trademark, arrows, mathematical symbols, bullets,
and additional spaces. The website footer required ©. The six upright weights
cover the website's current 300–700 usage, including 450-weight buttons.
Heavier g outlines retain clearance between the two loops.
These weights are parametric prototypes, not individually finished masters.

Revision 0.006 introduces dedicated italic files with a ten-degree inclination,
original single-storey a/g alternates, a descending f, and an exit stroke on l.
Accented forms inherit those alternates. Remaining shapes use inclined upright
construction; these are experimental italics requiring optical refinement.
Italic metadata, caret angle, counters, clipping, and all seed kerning pairs are
verified alongside the upright family.

The website no longer uses IBM fonts: unsupported characters fall back to system
sans-serif and code text uses system monospace. App and documentation body fonts
remain system sans-serif, and their IBM Plex Mono is unchanged.
No synthetic bold or slant is enabled for the website. Coverage remains partial
Latin; these files do not provide arbitrary multilingual coverage.

## Before production

1. Refine the Regular design against text and display proofs. The first result is
   more geometric than the reference; review shoulders, bowls, terminals, the
   double-storey a/g, spacing, and small-size color before expanding the family.
2. Replace flattened geometry with carefully corrected Bezier contours in editable
   UFO/designspace masters. Tune joins, overshoots, stroke contrast, and spacing.
3. Refine the weight and italic masters; establish interpolation compatibility and
   develop a meaningful optical-size design rather than simply varying stroke width.
4. Define and complete a language coverage target, combining anchors, OpenType
   positioning, ligatures, proportional figures, and comprehensive kerning.
5. Build variable and static release fonts, run FontBakery and an OpenType sanitizer,
   and review shaping and rendering on Windows, macOS, iOS, Android, and browsers.
6. Review the family name and release metadata, then package a versioned release.

## License

The Altertable font sources, build scripts, specimen pages, and generated
Altertable fonts in this folder are provided under the SIL Open Font License 1.1 in `OFL.txt`. There are no
Reserved Font Names.

Copyright 2026 The Altertable Sans Project Authors. No affiliation with Anthropic
or BSPK; this is not a redistribution or relicensing of Anthropic's fonts.
