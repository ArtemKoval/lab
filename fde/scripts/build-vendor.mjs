// Bundles the renderer: the two libraries (marked, DOMPurify) into vendor.js
// and the application entry plus logic modules into app.bundle.js. Both
// outputs are git-ignored; the predev and prebuild hooks run this script, so
// a clean clone rebuilds them at once.
import esbuild from 'esbuild'

const root = new URL('..', import.meta.url).pathname

const vendorEntry = `
import { marked } from 'marked';
import DOMPurify from 'dompurify';
globalThis.fdeVendor = { marked, DOMPurify };
`

await esbuild.build({
  stdin: {
    contents: vendorEntry,
    resolveDir: root,
    sourcefile: 'vendor-entry.js',
    loader: 'js',
  },
  bundle: true,
  format: 'iife',
  minify: true,
  sourcemap: false,
  target: ['chrome120'],
  outfile: 'src/renderer/vendor.js',
  logLevel: 'info',
})

await esbuild.build({
  entryPoints: ['src/renderer/app.js'],
  bundle: true,
  format: 'iife',
  minify: true,
  sourcemap: false,
  target: ['chrome120'],
  outfile: 'src/renderer/app.bundle.js',
  logLevel: 'info',
})

