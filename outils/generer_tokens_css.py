"""
Génère design-system/tokens.css à partir de design-system/tokens.json (la source).

    python3 outils/generer_tokens_css.py

Produit : variables CSS (--paper, --ok, --font-sans, --space-2, --radius-md…) en thème clair sur :root,
thème sombre sous prefers-color-scheme (sauf si data-theme="light" est forcé) et sous data-theme="dark",
plus une classe .t-<style> par style de texte (.t-title, .t-req-id, .t-prose…).
"""
import json, os
DS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'design-system')
t = json.load(open(os.path.join(DS, 'tokens.json')))
L = ['/* Trace — généré depuis tokens.json par outils/generer_tokens_css.py. Ne pas modifier à la main. */',
     '@import "./fonts/fonts.css";', '', ':root {']
L += [f"  --{c['name']}: {c['value']['light']};" for c in t['color']['tokens']]
L += [f"  --font-{k}: {v};" for k, v in t['type']['families'].items()]
L += [f"  --{x['name']}: {x['value']};" for k in ('spacing', 'radius') for x in t[k]['tokens']]
L += ['}', '@media (prefers-color-scheme: dark) {', '  :root:not([data-theme="light"]) {']
L += [f"    --{c['name']}: {c['value']['dark']};" for c in t['color']['tokens']]
L += ['  }', '}', ':root[data-theme="dark"] {']
L += [f"  --{c['name']}: {c['value']['dark']};" for c in t['color']['tokens']]
L += ['}']
L += [f".t-{s['name']} {{ font-family: var(--font-{g['family']}); font-size: {s['fontSize']}; line-height: {s['lineHeight']}; font-weight: {s['fontWeight']}; }}"
      for g in t['type']['groups'] for s in g['styles']]
open(os.path.join(DS, 'tokens.css'), 'w').write('\n'.join(L) + '\n')
print('design-system/tokens.css généré')
