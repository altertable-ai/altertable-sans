# Altertable Sans

An open-source sans-serif typeface for interfaces and the web, with broad
proportions, open counters, and tabular numerals. Available in six Text weights
with matching italics, plus a Regular Display style.

**Version 0.013 · Experimental · SIL Open Font License 1.1**

The family is in active development. You can use and modify it, but expect changes
to letterforms, spacing, and metrics before a stable release.

![Altertable Sans 0.013 specimen](proofs/v0.013/proof.png)

## Latest refinement

Version 0.013 gently opens Text spacing, redraws the upright double-storey `g`
and the numeral `2`, and centers the tabular figures within their cells. The
dotted zero, barred capital I, tailed lowercase l, and proportional-figure
features are retained. All styles have been rebuilt.

See [the before/after proof](refinement-proof.html) at 12, 14, and 16px, or
[the rendered comparison](proofs/refinement-after.png). The optional Suisse
International benchmark uses a local reference font that is not distributed.

## Get the fonts

The [fonts directory](fonts/) contains ready-to-use files:

- **TTF** for desktop applications. Download the styles you need and install them
  through your operating system's font manager.
- **WOFF2** for self-hosted websites.

To download the whole project, use GitHub's **Code → Download ZIP**, or clone it:

```sh
git clone https://github.com/altertable-ai/altertable-sans.git
cd altertable-sans
```

No build step is required to use the included fonts.

## Styles

| Family | Style | Weight | Upright | Italic |
| --- | --- | --- | --- | --- |
| Text | Light | 300 | ✓ | ✓ |
| Text | Regular | 400 | ✓ | ✓ |
| Text | Book | 450 | ✓ | ✓ |
| Text | Medium | 500 | ✓ | ✓ |
| Text | Semibold | 600 | ✓ | ✓ |
| Text | Bold | 700 | ✓ | ✓ |
| Display | Regular | 400 | ✓ | — |

Text has more spacing and slightly stronger strokes than Display. Capital I
has crossbars, lowercase l has an exit stroke, and zero has a dot. Heavy a/g
bowls have optical corrections, and heavy/italic f pairs have separate spacing. Italics use a
10° inclination with distinct single-storey `a` and `g` forms. All styles are
static fonts; there is no variable font yet.

## Use on the web

Copy [altertable-sans.css](altertable-sans.css), the `fonts/` directory, and
[OFL.txt](OFL.txt) into the same directory on your site. Load the stylesheet:

```html
<link rel="stylesheet" href="/fonts/altertable-sans/altertable-sans.css" />
```

```css
body {
  font-family: 'Altertable Sans', system-ui, sans-serif;
  font-weight: 400;
}

h1, h2 {
  font-weight: 500;
}

em {
  font-style: italic;
}
```

The stylesheet declares all twelve Text faces. Browsers fetch only the faces
needed by the page. It uses `font-display: optional`, so a slow first load may
retain the fallback font. You can change that policy to suit your site.

Display is supplied separately as `AltertableSansDisplay-Regular.woff2`; add an
`@font-face` declaration under a separate family name if you want to use it.
Keep a fallback stack for characters outside the font's coverage.

### Numeral spacing

Figures are tabular by default: every digit has the same advance for aligned
columns. The tabular `1` has a short base to balance its otherwise narrow shape.
Use proportional figures for running text; they include a narrower footless `1`
and optically spaced digits, periods, and commas.

```css
.price-in-text { font-variant-numeric: proportional-nums; }
.numeric-column { font-variant-numeric: tabular-nums; }
```

These use the font's `pnum` and `tnum` OpenType features. Compare the 0.011 default
with both 0.012 options in [figure-spacing-proof.html](figure-spacing-proof.html).

## Character coverage

Each style supports **374 Unicode characters**: printable ASCII, all letters in
Latin-1 and Latin Extended-A, Romanian comma-below letters, capital sharp S,
punctuation, currencies, arrows, mathematical symbols,
and spacing characters. Numerals are tabular by default, with a dotted zero for identifiers. Kerning includes
accented variants of the supported letter pairs.

See [coverage.json](fonts/coverage.json) for the exact character set in each style.
Coverage is not a claim of complete language support (for example, Vietnamese
and non-Latin scripts still require fallback). Fourteen zero-width combining
marks are supported: grave, acute, circumflex, tilde, macron, breve, dot above,
diaeresis, ring above, double acute, caron, comma below, cedilla, and ogonek.
OpenType `ccmp`, `mark`, and `mkmk` handle canonical compositions, dot removal
on accented i/j, and mark attachment/stacking. Windows clipping bounds allow
for two stacked marks while typographic line metrics remain unchanged;
arbitrary stacks still need suitable layout space.

## Preview

Serve the checkout locally:

```sh
python3 -m http.server 8768
```

Open <http://localhost:8768/specimen.html> to explore the current font:

- Editable headlines and paragraphs at reading and display sizes.
- All Text weights and italics, plus Regular Display.
- Proportional figures in text and tabular figures in aligned columns.
- Character coverage, accents, and combining marks.
- Altertable brand examples on light and dark surfaces, including metrics and
  interface labels.

The [static specimen](proof.png) is also included. Proofs render
HarfBuzz-shaped glyphs through FreeType, including substitutions and mark
offsets; they are not a substitute for browser/platform testing.

## Build from source

Use Python 3.12 with a virtual environment:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python build.py
python verify.py
python -m unittest test_latin test_readability -v
python proof.py
python proof_latin.py
python proof_readability.py
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` in
PowerShell instead of `source`.

The build writes TTF and WOFF2 files plus the coverage manifest into `fonts/`.
Verification checks character coverage, font metadata, metrics, contours,
clipping, kerning, and byte-identical rebuilds. GitHub Actions runs the build,
verification, and proof renderers on each push and pull request. The CI matrix
also loads the WOFF2 fonts in Chromium, Firefox, and WebKit on Linux, macOS, and
Windows, checking all Text weights/italics, canonical shaping, tabular numbers,
mobile/desktop overflow, light/dark presentation, and download-failure fallback.
Screenshots and measured widths are uploaded as workflow artifacts.
The tested font distribution is also uploaded as the `font-distribution` artifact.

### Releases

Push a version tag matching the font metadata (for example, `v0.009`) to publish
a GitHub Release. The tag runs the same build and tests on all three operating
systems; publication only proceeds when the entire matrix passes. A mismatched
tag fails verification. The release includes a ZIP of the tested TTF/WOFF2 fonts,
coverage manifest, stylesheet, license, and README, plus `SHA256SUMS`.

After updating the version in `build.py`, rebuilding the fonts, and committing
the release changes:

```sh
git tag -a v0.009 -m "Altertable Sans 0.009"
git push origin v0.009
```

Use the new version in place of `v0.009` for subsequent releases. Branch pushes,
pull requests, and manual workflow runs build and test without publishing.

Run the browser checks locally with:

```sh
npm ci
npx playwright install --with-deps chromium firefox webkit
npm run test:browser
```

[The interface proof](browser-proof.html) is a typography test fixture. It does
not replace an acceptance pass over every product screen. A local query-screen
Storybook pass is also used during this release's review.

Editable drawings live in [sources/](sources/): `glyphs.py` defines the base
letterforms, `italics.py` the italic alternates, `spacing.py` sidebearings and
kerning, and `symbols.py` additional symbols. `latin.py` supplies additional Latin
letters; `marks.py` constructs accents and OpenType attachment rules. The builder
expands these centerlines into flattened outlines. This is an experimental construction
method, not a finished set of Bézier masters.

## Contributing

[Issues](https://github.com/altertable-ai/altertable-sans/issues) and pull requests
are welcome. Useful reports include the text being rendered, style and weight,
font size, operating system, application or browser, and a screenshot.

For drawing or spacing changes, edit the sources, rebuild the fonts, run
`verify.py`, and include before-and-after specimens at both text and display
sizes. Include regenerated font files and the coverage manifest with your change.

Current priorities are optical refinement, broader Latin coverage, further
language-specific refinement, improved curve outlines, hinting, and cross-platform rendering.
The weights and italics still need individual refinement; passing the automated
checks does not establish production readiness.

## Design notes

Altertable Sans began as an exploration of broad grotesk proportions inspired
by Anthropic Sans. Its source drawings are original; no third-party font
outlines or metrics are imported into the build. This project is not affiliated
with Anthropic or BSPK, and no proprietary reference font is distributed.

## License

Fonts and project sources are licensed under the
[SIL Open Font License 1.1](OFL.txt). There are no Reserved Font Names.
Keep the copyright notice and license with redistributed font files; see the
license for the full terms.

Copyright 2026 The Altertable Sans Project Authors.
