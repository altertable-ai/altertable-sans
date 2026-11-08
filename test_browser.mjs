// Cross-engine/OS checks against actual WOFF2 faces and interface-sized layouts.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium, firefox, webkit } from 'playwright';

const root = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(root, 'browser-results', process.platform);
await mkdir(out, { recursive: true });
const mime = { '.html':'text/html', '.css':'text/css', '.woff2':'font/woff2' };
const server = createServer(async (request, response) => {
  const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
  const file = path.resolve(root, '.' + pathname);
  if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
  try {
    const bytes = await readFile(file);
    response.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
    response.end(bytes);
  } catch { response.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const url = `http://127.0.0.1:${server.address().port}/browser-proof.html`;
const results = [];
try {
  for (const [name, engine] of Object.entries({ chromium, firefox, webkit })) {
    const browser = await engine.launch();
    try {
      for (const width of [1280, 390]) for (const colorScheme of ['light', 'dark']) {
        const page = await browser.newPage({ viewport: { width, height: 1000 }, colorScheme });
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', message => {
          if (message.type() === 'error') console.error(`${name}/${width}: ${message.text()}`);
        });
        page.on('requestfailed', request => console.error(`${name}/${width}: ${request.url()} ${request.failure()?.errorText}`));
        // Exercise optional-font timeouts as well as fast local downloads.
        if (width === 390 && colorScheme === 'dark') {
          await page.route('**/*.woff2', async route => {
            await new Promise(resolve => setTimeout(resolve, 200));
            await route.continue();
          });
        }
        await page.goto(url);
        const metrics = await page.evaluate(async () => {
          const canvas = document.createElement('canvas');
          const context = canvas.getContext('2d');
          // The shipped CSS intentionally uses optional loading. Use a fresh block
          // face for optical screenshots so a first-load fallback cannot masquerade
          // as a successful font review; test the shipped declarations separately.
          const manifest = await fetch('fonts/coverage.json').then(r => r.json());
          const rules = [...document.styleSheets].flatMap(sheet => [...sheet.cssRules])
            .filter(rule => rule.type === CSSRule.FONT_FACE_RULE);
          for (const entry of manifest.filter(e => e.style === 'Text')) {
            const style = entry.italic ? 'italic' : 'normal';
            const matches = rules.filter(rule => rule.style.fontWeight === String(entry.weight)
              && rule.style.fontStyle === style);
            if (matches.length !== 1) throw new Error(`Missing or duplicate CSS face: ${entry.name}`);
            const declaration = matches[0].style;
            if (declaration.fontDisplay !== 'optional'
              || !declaration.getPropertyValue('src').includes(`AltertableSansText-${entry.name}.woff2`)) {
              throw new Error(`Incorrect CSS face: ${entry.name}`);
            }
            const face = new FontFace('Proof Sans', declaration.getPropertyValue('src'),
              {weight:String(entry.weight), style:entry.italic?'italic':'normal', display:'block'});
            try { document.fonts.add(await face.load()); }
            catch (error) { throw new Error(`Cannot load ${entry.name}: ${error.message}`); }
          }
          document.body.style.fontFamily = '"Proof Sans", system-ui, sans-serif';
          const measurements = [];
          for (const weight of [300,400,450,500,600,700]) for (const style of ['normal','italic']) {
            const font = `${style} ${weight} 16px "Proof Sans"`;
            const loaded = await document.fonts.load(font);
            if (loaded.length !== 1 || loaded[0].status !== 'loaded') throw new Error(`Face failed: ${font}`);
            context.font = `${style} ${weight} 16px "Proof Sans"`;
            const nfc = 'Café naïve Ångström Ąą Ęę Ľľ';
            const nfd = nfc.normalize('NFD');
            const digits = [...'0123456789'].map(c => context.measureText(c).width);
            function numericWidth(text, variant) {
              const span = document.createElement('span');
              span.style.cssText = `position:absolute;visibility:hidden;white-space:pre;font:${style} ${weight} 16px "Proof Sans";font-variant-numeric:${variant}`;
              span.textContent = text;
              document.body.append(span);
              const width = span.getBoundingClientRect().width;
              span.remove();
              return width;
            }
            const proportionalSaving = numericWidth('11,111', 'tabular-nums') - numericWidth('11,111', 'proportional-nums');
            const tabularDifference = numericWidth('11,111', 'tabular-nums') - numericWidth('88,888', 'tabular-nums');
            measurements.push({ weight, style, proportionalSaving, tabularDifference, nfc:context.measureText(nfc).width,
              nfd:context.measureText(nfd).width, digitSpread:Math.max(...digits)-Math.min(...digits) });
          }
          await document.fonts.ready;
          const probe = document.querySelector('#identifier-probe');
          context.font = getComputedStyle(probe).font;
          const probeDifference = Math.abs(probe.getBoundingClientRect().width - context.measureText(probe.textContent).width);
          return { measurements, probeDifference, overflow:document.documentElement.scrollWidth > innerWidth,
            clipped:[...document.querySelectorAll('[data-fit]')].filter(e => e.scrollWidth > e.clientWidth || e.scrollHeight > e.clientHeight).map(e=>e.textContent) };
        });
        assert.deepEqual(errors, [], `${name}: browser errors`);
        assert.ok(metrics.probeDifference < .1, `${name}: visible text stayed in fallback after font load`);
        assert.equal(metrics.overflow, false, `${name}/${width}: page overflow`);
        assert.deepEqual(metrics.clipped, [], `${name}/${width}: clipped controls`);
        for (const m of metrics.measurements) {
          assert.ok(Math.abs(m.nfc-m.nfd) < .05, `${name}: NFC/NFD differ (${m.weight} ${m.style})`);
          assert.ok(m.digitSpread < .05, `${name}: digits not tabular`);
          assert.ok(m.proportionalSaving > 10, `${name}: proportional figures did not narrow repeated ones`);
          assert.ok(Math.abs(m.tabularDifference) < .05, `${name}: tabular rows do not align`);
        }
        await page.screenshot({ path:path.join(out,`${name}-${width}-${colorScheme}.png`), fullPage:true });
        results.push({ engine:name, width, colorScheme, ...metrics });
        await page.close();
      }
      // Review the actual repository specimens as well as the interface fixture.
      for (const width of [1280, 390]) {
        const review = await browser.newPage({ viewport:{width,height:1000} });
        await review.goto(url.replace('browser-proof.html', 'comparison.html'));
        await review.waitForFunction(() => document.querySelector('#revision-status')
          .textContent.startsWith('Both revisions loaded'));
        assert.equal(await review.locator('.revision-pair').count(), 12);
        const spacing = await review.evaluate(() => {
          const context = document.createElement('canvas').getContext('2d');
          const measurements = [];
          // Linux rounds advances at text sizes, hiding small spacing revisions.
          // Compare design-scale metrics; the page still renders its 14–24px proofs.
          for (const weight of [300,400,450,500,600,700]) for (const style of ['normal','italic']) {
            const widths = ['Revision Before','Revision After'].map(family => {
              context.font = `${style} ${weight} 1000px "${family}"`;
              return context.measureText('minimum rhythm').width / 1000;
            });
            measurements.push({weight,style,before:widths[0],after:widths[1],
              faces:[...document.fonts].filter(face=>face.family.includes('Revision')).map(face=>({family:face.family,weight:face.weight,style:face.style,status:face.status}))});
          }
          return {measurements,overflow:document.documentElement.scrollWidth>innerWidth};
        });
        assert.equal(spacing.overflow, false, `${name}/${width}: comparison overflow`);
        for (const m of spacing.measurements) {
          if (m.weight === 300) assert.ok(m.after < m.before, `${name}: Light spacing unchanged ${JSON.stringify(m)}`);
          else if (m.weight === 400) assert.ok(Math.abs(m.after-m.before)<.0001, `${name}: Regular spacing changed ${JSON.stringify(m)}`);
          else assert.ok(m.after > m.before, `${name}: heavy spacing unchanged ${JSON.stringify(m)}`);
        }
        await review.screenshot({path:path.join(out,`${name}-${width}-comparison.png`),fullPage:true});
        await review.goto(url.replace('browser-proof.html', 'specimen.html'));
        await review.evaluate(() => document.fonts.ready);
        assert.equal(await review.evaluate(() => document.documentElement.scrollWidth>innerWidth),
          false, `${name}/${width}: specimen overflow`);
        await review.screenshot({path:path.join(out,`${name}-${width}-specimen.png`),fullPage:true});
        await review.close();
      }
      // A failed download must leave usable fallback text and controls.
      const fallback = await browser.newPage({ viewport:{width:390,height:900} });
      await fallback.route('**/*.woff2', route => route.abort());
      await fallback.goto(url);
      await fallback.evaluate(() => document.fonts.ready);
      assert.equal(await fallback.locator('h1').isVisible(), true);
      assert.ok(await fallback.locator('button').evaluate(e => e.getBoundingClientRect().width) > 40);
      await fallback.close();
      console.log(`PASS ${name}: all Text faces, shaping, digits, desktop/mobile, light/dark, fallback`);
    } finally { await browser.close(); }
  }
  await writeFile(path.join(out,'metrics.json'), JSON.stringify(results,null,2)+'\n');
} finally { await new Promise(resolve => server.close(resolve)); }
