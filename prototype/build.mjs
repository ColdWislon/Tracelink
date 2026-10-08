// Construit trace-prototype.html : un seul fichier autonome (bundle JS intégré au gabarit).
// src/app.js (+ seed.js, Tiptap, WaveDrom) → dist/bundle.js → inséré à la place de /*BUNDLE*/ dans src/template.html.
// « </script » est échappé pour ne pas fermer la balise <script> qui contient le bundle.
// Usage : npm install && npm run build
import { build } from 'esbuild'
import { readFileSync, writeFileSync } from 'fs'
await build({ entryPoints: ['src/app.js'], bundle: true, minify: true, format: 'iife', charset: 'utf8', outfile: 'dist/bundle.js' })
const js = readFileSync('dist/bundle.js', 'utf8').replaceAll('</script', '<\\/script')
const tpl = readFileSync('src/template.html', 'utf8')
if (tpl.split('/*BUNDLE*/').length !== 2) throw new Error('template.html doit contenir exactement un marqueur de bundle')
writeFileSync('trace-prototype.html', tpl.replace('/*BUNDLE*/', () => js))
console.log('trace-prototype.html généré')
