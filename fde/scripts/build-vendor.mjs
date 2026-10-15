// Bundles the two renderer libraries (marked, DOMPurify) into one IIFE file.
// The output lands at src/renderer/vendor.js and is git-ignored; the predev
// and prebuild hooks run this script, so a clean clone rebuilds it at once.
import esbuild from 'esbuild'

const entry = `
import { marked } from 'marked';
import DOMPurify from 'dompurify';
globalThis.fdeVendor = { marked, DOMPurify };
`

await esbuild.build({
  stdin: {
    contents: entry,
    resolveDir: new URL('..', import.meta.url).pathname,
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
