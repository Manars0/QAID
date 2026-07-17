/**
 * Generate PNG exports from QAID SVG logos using sharp.
 * Usage: node scripts/generate-logo-pngs.mjs
 */
import sharp from 'sharp';
import { readFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const src = join(root, 'artifacts/qaid/public/logo');
const out = join(root, 'artifacts/qaid/public/logo');

mkdirSync(out, { recursive: true });

const jobs = [
  // [input_svg, output_name, width, height, background]
  ['icon.svg',          'icon-256.png',        256, 256, { r:0, g:0, b:0, alpha:0 }],
  ['icon.svg',          'icon-128.png',        128, 128, { r:0, g:0, b:0, alpha:0 }],
  ['icon.svg',          'icon-64.png',          64,  64, { r:0, g:0, b:0, alpha:0 }],
  ['favicon.svg',       'favicon-32.png',       32,  32, null],
  ['favicon.svg',       'favicon-64.png',       64,  64, null],
  ['app-icon.svg',      'app-icon-1024.png',  1024,1024, null],
  ['app-icon.svg',      'app-icon-512.png',    512, 512, null],
  ['app-icon.svg',      'app-icon-192.png',    192, 192, null],
  ['logo-light.svg',    'logo-light.png',      680, 204, { r:255, g:255, b:255, alpha:255 }],
  ['logo-dark.svg',     'logo-dark.png',       680, 204, { r:13,  g:17,  b:23,  alpha:255 }],
  ['logo-ar-light.svg', 'logo-ar-light.png',   656, 208, { r:255, g:255, b:255, alpha:255 }],
  ['logo-ar-dark.svg',  'logo-ar-dark.png',    656, 208, { r:13,  g:17,  b:23,  alpha:255 }],
  ['logo-mono.svg',     'logo-mono.png',       688, 208, { r:255, g:255, b:255, alpha:255 }],
  ['brand-preview.svg', 'brand-preview.png',   960, 640, { r:240, g:244, b:248, alpha:255 }],
];

let ok = 0, fail = 0;

for (const [svg, png, w, h, bg] of jobs) {
  try {
    const svgBuf = readFileSync(join(src, svg));
    let s = sharp(svgBuf, { density: 300 }).resize(w, h);
    if (bg) {
      s = s.flatten({ background: bg });
    }
    await s.png({ compressionLevel: 8 }).toFile(join(out, png));
    console.log(`✓  ${png}  (${w}×${h})`);
    ok++;
  } catch (e) {
    console.error(`✗  ${png}: ${e.message}`);
    fail++;
  }
}

console.log(`\n${ok} generated, ${fail} failed → ${out}`);
