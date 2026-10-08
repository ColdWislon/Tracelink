"""
Génère les 14 maquettes statiques des vues de Trace (maquettes/*.dc.html) et l'index du canevas
(maquettes/canvas.json), à partir des données de démo réelles du prototype.

USAGE (depuis le dossier outils/)
    node extraire_donnees.mjs      # écrit donnees.json : exigences, statuts, métriques évaluées
    python3 generer_maquettes.py   # réécrit ../maquettes/*.dc.html, canvas.json et ds/trace/tokens.json
    Puis régénérer les captures PNG (voir AGENTS.md, section « Commandes »).

FORMAT DES FICHIERS .dc.html
    Format « design canvas » de Claude Design : un HTML dont le contenu visible est dans <x-dc>,
    les ressources de tête dans <helmet>, et un petit script <script type="text/x-dc"> qui déclare la
    taille d'aperçu ($preview). Ils s'ouvrent aussi tels quels dans un navigateur.
    Tout le style est EN LIGNE (attribut style) : c'est voulu, chaque maquette est autonome.

ORGANISATION
    En-tête : chargement des données, couleurs (C), petits composants HTML (dot, badge, fam, btn, card…),
    coquille commune (header, sidebar, page). Puis une section par vue, numérotée comme dans SPEC.md
    (« Vues de l'application »), qui remplit files['<Vue>.dc.html']. Enfin canvas.json (disposition).

DONNÉES RÉELLES OU INVENTÉES
    Réels (calculés depuis donnees.json) : compteurs, statuts, onglets et sommaire, matrice,
    explorateur, résultats analogiques du sous-système ALIM, familles, anomalies non tracées.
    Inventés mais cohérents : courbe d'évolution, baselines passées, file de synchro, conflit,
    import d'une révision D, fils de discussion, activité récente, personnes (Claire M., Hugo P.…).

PIÈGES
    - Les couleurs du dict C dupliquent design-system/tokens.json (thème clair seulement).
      Si les tokens changent, mettez C à jour.
    - Des IDs sont cités en dur (ERS-IO-020 pour le panneau et l'explorateur, SDS-IO-002, ERS-SYS-001…).
      Ils dépendent de l'ordre de génération de seed.js : après toute modification de seed.js,
      vérifiez qu'ils désignent toujours une exigence pertinente (ERS-IO-020 doit rester « en échec »).
    - Les hauteurs d'artboard (dict H en fin de fichier) doivent couvrir le contenu de chaque vue.
"""
import json, os, html, datetime, re
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
J = json.load(open('donnees.json')); D = J['reqs']; IDX = {r['rid']: r for r in D}; SUBS = J['subs']; CURSUB = 'IO'; SUBNAME = 'Sous-système d’E/S'
ROOT = '../maquettes'
os.makedirs(ROOT + '/ds/trace', exist_ok=True)
e = html.escape
# Couleurs du thème clair, copiées de design-system/tokens.json. SC : couleur par statut ; SB : fond de badge (13 % d'opacité).
C = dict(paper='#FAFAF7', sheet='#FFFFFF', req='#F2F4F8', rule='#DEDFD8', ink='#1C2230', muted='#5E6675',
         accent='#2F4FB5', ok='#2F7D55', danger='#B3261E', gap='#94600A', onacc='#FFFFFF')
SC = dict(proven=C['ok'], planned=C['accent'], failing=C['danger'], traced=C['muted'], untraced=C['gap'])
SB = dict(proven='rgba(47,125,85,.13)', planned='rgba(47,79,181,.12)', failing='rgba(179,38,30,.11)', traced='rgba(94,102,117,.12)', untraced='rgba(148,96,10,.13)')
LBL = dict(proven='Prouvée', planned='Planifiée', failing='En échec', traced='Tracée', untraced='Non tracée')
SANS = "'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif"
SERIF = "'IBM Plex Serif', Georgia, 'Times New Roman', serif"
FAMDOC = {'VP': 'DV', 'ANV': 'ANA', 'FWT': 'FW', 'VAL': 'VAL'}

# ---------- composants ----------
# Pastille de statut : disque plein, sauf « tracée » qui est un cercle vide (règle du design system).
def dot(st, s=8):
    if st == 'traced':
        return f'<span style="display: inline-block; width: {s-3}px; height: {s-3}px; border-radius: 50%; border: 1.5px solid {C["muted"]}; flex: none"></span>'
    return f'<span style="display: inline-block; width: {s}px; height: {s}px; border-radius: 50%; background: {SC[st]}; flex: none"></span>'
def badge(st, txt=None):
    return f'<span style="display: inline-block; font-size: 12px; line-height: 16px; font-weight: 600; padding: 2px 8px; border-radius: 4px; color: {SC[st]}; background: {SB[st]}; white-space: nowrap">{txt or LBL[st]}</span>'
# Pastille de famille DV/ANA/FW/VAL : pleine (statut), pointillée ambre (requise sans item) ou grisée (aucun item).
def fam(f, st=None, need=False):
    if st:
        if st == 'traced':
            return f'<span style="font-size: 10px; font-weight: 600; letter-spacing: .03em; padding: 3px 5px; border-radius: 4px; border: 1px solid {C["muted"]}; color: {C["muted"]}; min-width: 26px; text-align: center">{f}</span>'
        return f'<span style="font-size: 10px; font-weight: 600; letter-spacing: .03em; padding: 4px 6px; border-radius: 4px; background: {SC[st]}; color: #FFFFFF; min-width: 24px; text-align: center">{f}</span>'
    if need:
        return f'<span style="font-size: 10px; font-weight: 600; letter-spacing: .03em; padding: 3px 5px; border-radius: 4px; border: 1.5px dashed {C["gap"]}; color: {C["gap"]}; min-width: 24px; text-align: center">{f}</span>'
    return f'<span style="font-size: 10px; font-weight: 600; letter-spacing: .03em; padding: 3px 5px; border-radius: 4px; border: 1px solid {C["rule"]}; color: #8A909C; min-width: 26px; text-align: center">{f}</span>'
def btn(t, primary=False, aria=None, small=False):
    pad = '6px 12px' if small else '9px 16px'
    if primary:
        return f'<button type="button" style="font: 600 14px/20px {SANS}; padding: {pad}; border-radius: 6px; border: 1px solid {C["accent"]}; background: {C["accent"]}; color: #FFFFFF; cursor: pointer; min-height: 36px">{t}</button>'
    a = f' aria-label="{aria}"' if aria else ''
    return f'<button type="button"{a} style="font: 500 14px/20px {SANS}; padding: {pad}; border-radius: 6px; border: 1px solid {C["rule"]}; background: {C["sheet"]}; color: {C["ink"]}; cursor: pointer; min-height: 36px">{t}</button>'
def rid(r, size=14):
    return f'<span style="font-weight: 600; font-size: {size}px; color: {C["accent"]}; font-variant-numeric: tabular-nums; white-space: nowrap">{r}</span>'
def card(title, body, extra='', pad=20):
    h = f'<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 12px"><h2 style="margin: 0; font-size: 15px; line-height: 22px; font-weight: 600">{title}</h2>{extra}</div>' if title else ''
    return f'<section style="background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px; padding: {pad}px; display: flex; flex-direction: column; gap: 14px; min-width: 0">{h}{body}</section>'
def short(t, n=60): return t if len(t) <= n else t[:n-1].rstrip() + '…'
ICON_CHECK = f'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="{C["ok"]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8.5l3 3 7-7"/></svg>'
ICON_X = f'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="{C["danger"]}" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8"/></svg>'
ICON_SEARCH = f'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="{C["muted"]}" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5L14 14"/></svg>'

# ---------- coquille commune : en-tête, barre latérale, page ----------
NAV = [('Main.dc.html', 'Tableau de bord', ''), ('Document.dc.html', 'Documents', ''), ('Explorateur.dc.html', 'Explorateur', ''),
       ('Matrice.dc.html', 'Matrice de couverture', ''), ('Resultats.dc.html', 'Résultats', ''), ('Anomalies.dc.html', 'Anomalies', '@@NANOM@@'),
       ('Discussions.dc.html', 'Discussions', '9'), ('Import.dc.html', 'Import', ''), ('Synchro.dc.html', 'Synchronisation', '4'),
       ('Baselines.dc.html', 'Baselines', ''), ('Administration.dc.html', 'Administration', '')]

def header():
    return f'''<header style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap; padding: 10px 20px; background: {C["sheet"]}; border-bottom: 1px solid {C["rule"]}">
<a href="Main.dc.html" style="font-weight: 600; font-size: 18px; letter-spacing: -.01em; color: {C["ink"]}; text-decoration: none">Trace</a>
<button type="button" style="font: 500 14px/20px {SANS}; padding: 6px 10px; border-radius: 6px; border: 1px solid {C["rule"]}; background: {C["sheet"]}; color: {C["ink"]}; cursor: pointer">SoC de démonstration ▾</button><span style="font-size: 13px; color: {C["muted"]}">9 182 exigences · 11 sous-systèmes</span>
<label style="flex: 1 1 260px; max-width: 460px; display: flex; align-items: center; gap: 8px; padding: 7px 10px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["paper"]}">{ICON_SEARCH}<span style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0)">Rechercher une exigence</span><input type="search" placeholder="Rechercher une exigence par ID ou texte" style="flex: 1; min-width: 0; border: 0; background: transparent; font: 14px/20px {SANS}; color: {C["ink"]}; outline: none"><span style="font-size: 12px; color: {C["muted"]}; border: 1px solid {C["rule"]}; border-radius: 4px; padding: 0 5px">Ctrl K</span></label>
<div style="margin-left: auto; display: flex; align-items: center; gap: 10px; flex-wrap: wrap">
<span style="font-size: 13px; color: {C["muted"]}">Résultats de référence : <strong style="color: {C["ink"]}; font-weight: 600">4 octobre</strong></span>
<button type="button" aria-label="Aide" style="width: 36px; height: 36px; border-radius: 50%; border: 1px solid {C["rule"]}; background: {C["sheet"]}; font: 600 15px {SANS}; color: {C["ink"]}; cursor: pointer">?</button>
<button type="button" aria-label="Compte de Bertrand" style="width: 36px; height: 36px; border-radius: 50%; border: 0; background: {C["ink"]}; color: {C["paper"]}; font: 600 13px {SANS}; cursor: pointer">BD</button>
</div>
</header>'''

def sidebar(active):
    items = []
    for f, t, n in NAV:
        on = f == active
        cnt = f'<span style="font-size: 12px; font-weight: 600; color: {C["gap"] if t=="Anomalies" else C["muted"]}; font-variant-numeric: tabular-nums">{n}</span>' if n else ''
        items.append(f'<a href="{f}" style="display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 9px 12px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: {600 if on else 500}; color: {C["ink"] if on else "#3A4150"}; background: {C["req"] if on else "transparent"}">{t}{cnt}</a>')
    return f'''<nav aria-label="Vues" style="flex: 1 1 200px; max-width: 232px; padding: 16px 12px; display: flex; flex-direction: column; gap: 2px; border-right: 1px solid {C["rule"]}; background: {C["sheet"]}">
{''.join(items)}
<div style="margin-top: 20px; padding: 12px; border-top: 1px solid {C["rule"]}; font-size: 12px; line-height: 16px; color: {C["muted"]}">Synchronisé avec Tuleap il y a 2 min<br>4 modifications en attente</div>
</nav>'''

# Enveloppe une vue poste de travail (1440 px de large, hauteur h) au format .dc.html.
def page(fname, title, body, h, active=None, wide=False):
    return f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{e(title)}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&amp;family=IBM+Plex+Serif:wght@400;600&amp;display=swap">
<style>
body{{margin:0}}
a{{color:{C["accent"]}}}a:hover{{color:#223C8C}}
</style>
</helmet>
<div style="min-height: {h}px; background: {C["paper"]}; color: {C["ink"]}; font-family: {SANS}; font-size: 15px; line-height: 22px; display: flex; flex-direction: column">
{header()}
<div style="display: flex; flex-wrap: wrap; flex: 1; align-items: stretch">
{sidebar(active or fname)}
<main style="flex: 999 1 560px; min-width: 0; padding: 24px 28px 40px; display: flex; flex-direction: column; gap: 20px">
{body}
</main>
</div>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1440,"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>'''

def title_row(t, sub, right=''):
    return f'<div style="display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap"><div><h1 style="margin: 0; font-size: 27px; line-height: 32px; font-weight: 600; letter-spacing: -.015em">{t}</h1><p style="margin: 4px 0 0; color: {C["muted"]}; font-size: 14px">{sub}</p></div><div style="display: flex; gap: 8px; flex-wrap: wrap">{right}</div></div>'

ERS = [r for r in D if r['doc'] == 'ERS']
cnt = {k: sum(1 for r in ERS if r['st'] == k) for k in LBL}
def famstats(doc):
    it = [r for r in D if r['doc'] == doc]
    return [len(it), sum(r['st']=='proven' for r in it), sum(r['st']=='planned' for r in it), sum(r['st']=='failing' for r in it), sum(r['st']=='traced' for r in it)]
FS = {'DV': famstats('VP'), 'ANA': famstats('ANV'), 'FW': famstats('FWT'), 'VAL': famstats('VAL')}
def desc(r0):
    out, seen, q = [], {r0}, [r0]
    while q:
        for c in IDX[q.pop(0)]['kids']:
            if c not in seen: seen.add(c); out.append(c); q.append(c)
    return out
def famst(r0, f):
    WORST = ['untraced', 'traced', 'failing', 'planned', 'proven']
    its = [IDX[x]['st'] for x in desc(r0) if FAMDOC.get(IDX[x]['doc']) == f]
    return min(its, key=WORST.index) if its else None
def segbar(counts, total, h=10):
    order = ['proven', 'planned', 'failing', 'traced', 'untraced']
    segs = ''.join(f'<span style="flex: {counts[k]} 1 0; background: {SC[k] if k!="traced" else "#B8BDC6"}"></span>' for k in order if counts.get(k))
    return f'<div style="display: flex; gap: 2px; height: {h}px; border-radius: 3px; overflow: hidden">{segs}</div>'
def legend(counts):
    order = ['proven', 'planned', 'failing', 'traced', 'untraced']
    return '<div style="display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 13px; color: ' + C['muted'] + '">' + ''.join(f'<span style="display: inline-flex; align-items: center; gap: 6px">{dot(k)}<span><strong style="color: {C["ink"]}; font-weight: 600">{counts[k]}</strong> {LBL[k].lower()}{"s" if counts[k]>1 and k!="failing" else ""}</span></span>' for k in order if counts.get(k)) + '</div>'

# Résultats analogiques réels du sous-système Alimentations et références
def anvrow(x):
    m, ev, res = x['metricsEv'][0] if x['metricsEv'] else (None, None, None)
    if not m: return None
    kind, name = m.split(':', 1)
    crit = re.search(r'critère (.+?)\.$', x['text']); crit = crit.group(1) if crit else ('Cpk ≥ 1,33' if kind == 'mc' else 'écart ≤ 2 %')
    if res is None: return (x['rid'], x['sat'][0], kind, name, crit, '—', 'absent des résultats', '—', '—', 'planned')
    if kind == 'spec':
        val = 'tient sur les 27 coins' if res['ok'] else 'hors limite'
        mg = (f"+{res['margin']} %" if res['ok'] else f"{res['margin']} %")
        return (x['rid'], x['sat'][0], kind, name, crit, res['corner'], val, mg, 'Schéma' if res['view'] == 'schéma' else 'Post-layout', x['st'])
    if kind == 'mc': return (x['rid'], x['sat'][0], kind, name, crit, '500 tirages', f"Cpk {str(res['cpk']).replace('.', ',')}", f"{res['cpk'] - 1.33:+.2f}".replace('.', ','), 'Post-layout', x['st'])
    return (x['rid'], x['sat'][0], kind, name, crit, 'tt · 1,10 V · 25 °C', f"écart {str(res['err']).replace('.', ',')} %", f"{2 - res['err']:+.1f} pt".replace('.', ','), 'Post-layout', x['st'])
ALIMV = [r for r in D if r['doc'] == 'ANV' and r['sub'] == 'ALIM']
_rows = [anvrow(x) for x in ALIMV]; _rows = [x for x in _rows if x]
ANV = [x for x in _rows if x[9] == 'failing'][:2] + [x for x in _rows if x[9] == 'planned'][:2] + [x for x in _rows if x[9] == 'proven' and x[2] == 'spec'][:5] + [x for x in _rows if x[2] in ('mc', 'model') and x[9] == 'proven'][:2]
ANVSTATS = {k: sum(1 for x in ALIMV if x['st'] == k) for k in LBL}
files = {}
# ---------- 1. Tableau de bord ----------
FINAL = sum(1 for x in D if x['doc'] == 'ERS' and x['st'] == 'proven')
spark = [round(FINAL * (0.42 + 0.58 * (i / 29) ** 0.8) + (5 if i % 4 == 1 else -3 if i % 5 == 2 else 0)) for i in range(29)] + [FINAL]
SMAX = len(ERS)
pts = ' '.join(f'{12 + i * 19.3:.1f},{150 - v * 120 / SMAX:.1f}' for i, v in enumerate(spark))
fam_rows = ''.join(f'<tr><th scope="row" style="text-align: left; padding: 8px 6px; font-weight: 600; border-top: 1px solid {C["rule"]}">{n}</th>' + ''.join(f'<td style="text-align: right; padding: 8px 6px; border-top: 1px solid {C["rule"]}; color: {col}; font-variant-numeric: tabular-nums">{v}</td>' for v, col in zip([FS[k][0], FS[k][1], FS[k][3]], [C['ink'], C['ok'], C['danger']])) + '</tr>' for k, n in [('DV', 'vPlan DV'), ('ANA', 'Analogique'), ('FW', 'Tests FW'), ('VAL', 'Validation')])
STALE = sum(1 for r in D for m, s, res in r['metricsEv'] if res and res.get('stale'))
PEND = sum(1 for r in D for m, s, res in r['metricsEv'] if res and res.get('pending'))
MISS = sum(1 for r in D for m, s, res in r['metricsEv'] if s == 'missing')
anoms = [('Exigences client non tracées', cnt['untraced'], 'untraced'), ('Plan requis sans item', 4, 'untraced'), ('Métriques absentes des résultats', MISS, 'untraced'),
         ('Résultats à rejouer', STALE, 'untraced'), ('Fils bloquants ouverts', 2, 'failing'), ('Conflits de synchro', 1, 'failing'), ('Questions client sans réponse', 2, 'planned')]
anom_list = ''.join(f'<li style="display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 9px 0; border-top: 1px solid {C["rule"]}"><a href="Anomalies.dc.html" style="display: flex; align-items: center; gap: 10px; color: {C["ink"]}; text-decoration: none; font-size: 14px">{dot(s)}{t}</a><span style="font-weight: 600; font-variant-numeric: tabular-nums">{n}</span></li>' for t, n, s in anoms)

def substats(code):
    se = [x for x in ERS if x['sub'] == code]
    return se, {k: sum(1 for x in se if x['st'] == k) for k in LBL}
def subrow(sb):
    se, c = substats(sb['code'])
    td = lambda v, col: f'<td style="text-align: right; padding: 7px 6px; border-top: 1px solid {C["rule"]}; color: {col}; font-variant-numeric: tabular-nums">{v}</td>'
    return f'<tr><th scope="row" style="text-align: left; padding: 7px 6px; font-weight: 500; border-top: 1px solid {C["rule"]}"><a href="Matrice.dc.html" style="color: {C["ink"]}; text-decoration: none">{e(sb["nom"])}</a></th>' + td(len(se), C['ink']) + td(c['proven'], C['ok']) + td(c['failing'], C['danger']) + td(c['untraced'], C['gap']) + f'<td style="padding: 7px 6px 7px 14px; border-top: 1px solid {C["rule"]}; width: 30%">{segbar(c, len(se), 8)}</td></tr>'
_th = lambda t, a='right': f'<th style="text-align: {a}; padding: 0 6px 6px; font-weight: 500">{t}</th>'
SUBTBL = '<div style="overflow-x: auto"><table style="width: 100%; border-collapse: collapse; font-size: 14px"><thead><tr style="color: ' + C['muted'] + '; font-size: 12px">' + _th('Sous-système', 'left') + _th('ERS') + _th('Prouvées') + _th('En échec') + _th('Non tracées') + _th('') + '</tr></thead><tbody>' + ''.join(subrow(sb) for sb in SUBS) + '</tbody></table></div>'
REFS = f'''<dl style="margin: 0; display: grid; grid-template-columns: auto 1fr; gap: 8px 14px; font-size: 14px">
<dt style="color: {C["muted"]}">DV</dt><dd style="margin: 0">reg_nightly_20261004_0215</dd>
<dt style="color: {C["muted"]}">ANA</dt><dd style="margin: 0">Campagne ADE-14, post-layout</dd>
<dt style="color: {C["muted"]}">FW</dt><dd style="margin: 0">fw-ci #1490 (4f0d7b9)</dd>
<dt style="color: {C["muted"]}">VAL</dt><dd style="margin: 0">VAL-08, silicium A0, {PEND} en attente de double validation</dd></dl>'''

body = title_row('Tableau de bord', 'SoC de démonstration, révision D de la spécification client, 11 sous-systèmes', btn('Créer une baseline') + btn('Exporter le rapport de preuve', True))
body += f'''<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px">
{card('Exigences client', f'<div style="display: flex; align-items: baseline; gap: 10px"><span style="font-size: 44px; line-height: 48px; font-weight: 600; letter-spacing: -.02em; font-variant-numeric: tabular-nums">{cnt["proven"]}</span><span style="color: {C["muted"]}">prouvées sur {len(ERS)}</span></div>' + segbar(cnt, len(ERS), 12) + legend(cnt))}
{card('Évolution sur 30 régressions', f'<svg viewBox="0 0 600 170" style="width: 100%; height: auto" role="img" aria-label="Exigences client prouvées, de {spark[0]} à {FINAL} sur les 30 dernières régressions"><line x1="0" y1="150" x2="600" y2="150" stroke="{C["rule"]}"/><line x1="0" y1="30" x2="600" y2="30" stroke="{C["rule"]}" stroke-dasharray="3 4"/><text x="4" y="24" font-size="12" fill="{C["muted"]}" font-family="IBM Plex Sans">{SMAX} exigences client</text><polyline points="{pts}" fill="none" stroke="{C["ok"]}" stroke-width="2.5" stroke-linejoin="round"/><circle cx="{12+29*19.3:.1f}" cy="{150-FINAL*120/SMAX:.1f}" r="4.5" fill="{C["ok"]}"/></svg><p style="margin: 0; font-size: 13px; color: {C["muted"]}">De {spark[0]} à {FINAL} exigences client prouvées depuis la nightly du 5 septembre.</p>', f'<span style="font-size: 13px; color: {C["muted"]}">Prouvées</span>')}
{card('Anomalies', f'<ul style="list-style: none; margin: -9px 0 0; padding: 0">{anom_list}</ul>', '<a href="Anomalies.dc.html" style="font-size: 13px">Tout voir</a>')}
</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px">
<div style="grid-column: span 2; min-width: 0">{card('Couverture par sous-système', SUBTBL, '<a href="Matrice.dc.html" style="font-size: 13px">Matrice</a>')}</div>
{card('Items de vérification par famille', f'<div style="overflow-x: auto"><table style="width: 100%; border-collapse: collapse; font-size: 14px"><thead><tr style="color: {C["muted"]}; font-size: 12px"><th style="text-align: left; padding: 0 6px 6px; font-weight: 500">Famille</th><th style="text-align: right; padding: 0 6px 6px; font-weight: 500">Items</th><th style="text-align: right; padding: 0 6px 6px; font-weight: 500">Prouvés</th><th style="text-align: right; padding: 0 6px 6px; font-weight: 500">En échec</th></tr></thead><tbody>{fam_rows}</tbody></table></div>')}
</div>
<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px">
{card('Résultats de référence', REFS)}
{card('Synchronisation Tuleap', f'<p style="margin: 0; display: flex; align-items: center; gap: 8px">{dot("proven")}9 trackers synchronisés il y a 2 min</p><p style="margin: 0; display: flex; align-items: center; gap: 8px">{dot("planned")}4 modifications en attente d’écriture</p><p style="margin: 0; display: flex; align-items: center; gap: 8px">{dot("failing")}1 conflit à résoudre sur SDS-IO-040</p>', '<a href="Synchro.dc.html" style="font-size: 13px">Ouvrir</a>')}
{card('Dernières baselines', ''.join(f'<div style="display: flex; justify-content: space-between; gap: 10px; padding-top: 10px; border-top: 1px solid {C["rule"]}"><div><div style="font-weight: 600">{a}</div><div style="font-size: 13px; color: {C["muted"]}">{b}</div></div><span style="font-size: 13px; color: {C["muted"]}; white-space: nowrap">{c}</span></div>' for a, b, c in [('BL-07 · Jalon 2, revue client', f'{round(FINAL*0.86)} prouvées sur {len(ERS)-3}', '28 sept.'), ('BL-06 · Revue interne SDS', f'{round(FINAL*0.71)} prouvées sur {len(ERS)-12}', '12 sept.'), ('BL-05 · Gel de la révision C', f'{round(FINAL*0.52)} prouvées sur {len(ERS)-12}', '29 août')]), '<a href="Baselines.dc.html" style="font-size: 13px">Toutes</a>')}
{card('Activité récente', ''.join(f'<div style="font-size: 14px; padding-top: 10px; border-top: 1px solid {C["rule"]}"><strong style="font-weight: 600">{a}</strong> {b}<div style="font-size: 13px; color: {C["muted"]}">{c}</div></div>' for a, b, c in [('Claire M.', 'a proposé une modification de ERS-IO-020', 'il y a 12 min'), ('Jenkins', 'a importé reg_nightly_20261004_0215', 'ce matin, 06:41'), ('Hugo P.', 'a validé 6 résultats de la campagne VAL-08', 'hier, 17:20'), ('Bertrand D.', 'a importé ERS_client_revD.docx', 'hier, 09:05')]))}
</div>'''
files['Main.dc.html'] = page('Main.dc.html', 'Trace, tableau de bord', body, 1240)

# ---------- 2. Document ----------
sds = [r for r in D if r['doc'] == 'SDS' and r['sub'] == CURSUB][:6]
def reqblock(r, active=False, disc=0, extra=''):
    der = [p for p in r['sat'] if p.split('-')[0] == r['rid'].split('-')[0]]; sat = [p for p in r['sat'] if p not in der]
    links = '<br>'.join(x for x in [('dérive de ' + ', '.join(der)) if der else '', ('satisfait ' + ', '.join(sat)) if sat else ''] if x)
    dc = f'<span style="font-size: 11px; font-weight: 600; color: {C["accent"]}; background: {C["req"]}; border-radius: 4px; padding: 0 5px; margin-top: 4px">{disc} fils</span>' if disc else ''
    return f'''<div style="display: grid; grid-template-columns: 132px minmax(0, 1fr); column-gap: 16px; margin: 0 0 18px">
<div style="display: flex; flex-direction: column; align-items: flex-end; padding-top: 4px; text-align: right"><span style="display: inline-flex; align-items: center; gap: 6px">{dot(r["st"])}{rid(r["rid"])}</span><span style="font-size: 12px; line-height: 16px; color: {C["muted"]}; margin-top: 3px">{links}</span>{dc}</div>
<div style="border-left: 2px solid {C["accent"] if active else C["rule"]}; background: {C["req"] if active else "transparent"}; padding: 4px 12px 4px 14px; border-radius: 0 4px 4px 0; font-family: {SERIF}; font-size: 17px; line-height: 28px">{e(r["text"])}{extra}</div></div>'''
fsm = f'''<div style="margin-top: 10px; border: 1px solid {C["rule"]}; border-radius: 6px; overflow: hidden; font-family: {SANS}"><div style="display: flex; justify-content: space-between; padding: 4px 10px; background: {C["req"]}; font-size: 12px; color: {C["muted"]}"><span>Diagramme Mermaid</span><a href="#" style="font-size: 12px">Modifier le code</a></div><div style="background: #FFFFFF; padding: 14px; display: flex; justify-content: center"><svg viewBox="0 0 460 120" width="460" height="120" role="img" aria-label="Machine d’état IDLE, ARMED, ACTIVE, ERROR"><g font-family="IBM Plex Sans" font-size="12" fill="{C["ink"]}"><rect x="10" y="45" width="70" height="30" rx="6" fill="#F2F4F8" stroke="#5E6675"/><text x="45" y="64" text-anchor="middle">IDLE</text><rect x="130" y="45" width="76" height="30" rx="6" fill="#F2F4F8" stroke="#5E6675"/><text x="168" y="64" text-anchor="middle">ARMED</text><rect x="256" y="45" width="80" height="30" rx="6" fill="#F2F4F8" stroke="#5E6675"/><text x="296" y="64" text-anchor="middle">ACTIVE</text><rect x="384" y="45" width="70" height="30" rx="6" fill="#F2F4F8" stroke="#5E6675"/><text x="419" y="64" text-anchor="middle">ERROR</text></g><g stroke="#5E6675" fill="none" stroke-width="1.2"><path d="M80 60H128"/><path d="M206 60H254"/><path d="M336 60H382"/><path d="M419 45C419 10 45 10 45 43"/></g><g font-family="IBM Plex Sans" font-size="10" fill="{C["muted"]}"><text x="104" y="54" text-anchor="middle">EN = 1</text><text x="230" y="54" text-anchor="middle">dma_req</text><text x="359" y="54" text-anchor="middle">SLVERR</text><text x="232" y="20" text-anchor="middle">ERRACK</text></g></svg></div></div>'''
doc_tabs = ''.join(f'<a href="Document.dc.html" style="padding: 8px 12px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: {600 if t=="SDS" else 500}; color: {C["ink"] if t=="SDS" else C["muted"]}; background: {C["req"] if t=="SDS" else "transparent"}; white-space: nowrap">{t} <span style="font-size: 12px; color: {C["muted"]}">{n}</span></a>' for t, n in [(lab, sum(1 for x in D if x['doc'] == lv and x['sub'] == CURSUB)) for lv, lab in [('ERS', 'ERS client'), ('SDS', 'SDS'), ('DDS', 'DDS'), ('ANS', 'Spéc. ANA'), ('FWS', 'Spéc. FW'), ('VP', 'vPlan DV'), ('ANV', 'Plan ANA'), ('FWT', 'Tests FW'), ('VAL', 'Validation')]])
WORSTL = ['untraced', 'traced', 'failing', 'planned', 'proven']
_sds = [x for x in D if x['doc'] == 'SDS' and x['sub'] == CURSUB]
TOC = [(sec, len(L), min((x['st'] for x in L), key=WORSTL.index)) for sec in dict.fromkeys(x['sec'] for x in _sds) for L in [[x for x in _sds if x['sec'] == sec]]]
toc = ''.join(f'<a href="#" style="display: flex; justify-content: space-between; align-items: center; gap: 6px; padding: 6px 8px; border-radius: 6px; text-decoration: none; font-size: 13px; color: {C["ink"]}; background: {C["req"] if i==0 else "transparent"}"><span style="display: inline-flex; align-items: center; gap: 8px">{dot(s)}{t}</span><span style="color: {C["muted"]}; font-variant-numeric: tabular-nums">{n}</span></a>' for i, (t, n, s) in enumerate(TOC))
toolbar = ''.join(f'<button type="button" style="font: 500 13px/18px {SANS}; padding: 6px 9px; border: 0; border-radius: 6px; background: transparent; color: {C["ink"]}; cursor: pointer">{t}</button>' for t in ['Annuler', 'T1', 'T2', 'G', 'I', 'Liste', 'Tableau']) + f'<span style="width: 1px; height: 20px; background: {C["rule"]}"></span>' + btn('Nouvelle exigence', True, small=True) + ''.join(f'<button type="button" style="font: 500 13px/18px {SANS}; padding: 6px 9px; border: 0; border-radius: 6px; background: transparent; color: {C["ink"]}; cursor: pointer">{t}</button>' for t in ['Citer', 'Chronogramme', 'Diagramme', 'Paramètres'])
a = IDX['SDS-IO-002']
docpanel = f'''<aside aria-label="Panneau de l’exigence" style="flex: 0 1 360px; min-width: 300px; background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px; padding: 18px; display: flex; flex-direction: column; gap: 14px; align-self: flex-start">
<div style="display: flex; gap: 2px; border-bottom: 1px solid {C["rule"]}; margin: -4px -4px 0; flex-wrap: wrap">{''.join(f'<button type="button" style="font: {600 if i==0 else 500} 13px {SANS}; padding: 8px 8px; border: 0; border-bottom: 2px solid {C["accent"] if i==0 else "transparent"}; background: transparent; color: {C["ink"] if i==0 else C["muted"]}; cursor: pointer">{t}</button>' for i, t in enumerate(['Traçabilité', 'Vérification', 'Historique', 'Synchro', 'Discussion 2']))}</div>
<div style="display: flex; align-items: baseline; gap: 10px">{rid('SDS-IO-002', 24)}<span style="font-size: 13px; color: {C["muted"]}">SDS · numérique</span></div>
<p style="margin: 0; font-family: {SERIF}; font-size: 15px; line-height: 24px">{e(a["text"])}</p>
<div style="background: {SB[a["st"]]}; border-radius: 0 6px 6px 0; border-left: 3px solid {SC[a["st"]]}; padding: 10px 12px; display: flex; flex-direction: column; gap: 6px">{badge(a["st"])}<span style="font-size: 14px">Toutes les branches sont prouvées, résultats du 4 octobre.</span></div>
<div style="display: flex; flex-direction: column; gap: 6px">{''.join(f'<div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px; padding-top: 6px; border-top: 1px solid {C["rule"]}"><span>{n}</span>{badge(famst("SDS-IO-002", f)) if famst("SDS-IO-002", f) else f"<span style=\'font-size: 13px; color: {C['muted']}\'>aucun item</span>"}</div>' for f, n in [('DV', 'vPlan DV'), ('ANA', 'Analogique'), ('FW', 'Tests FW'), ('VAL', 'Validation')])}</div>
<h3 style="margin: 4px 0 0; font-size: 13px; font-weight: 600; color: {C["muted"]}">Satisfait</h3>
<div style="display: flex; gap: 10px; font-size: 14px; padding: 8px 0; border-top: 1px solid {C["rule"]}">{rid(a["sat"][0])}<span style="color: {C["muted"]}">{short(IDX[a["sat"][0]]["text"], 70)}</span></div>
<h3 style="margin: 4px 0 0; font-size: 13px; font-weight: 600; color: {C["muted"]}">Raffinée ou vérifiée par</h3>
{''.join(f'<div style="display: flex; gap: 10px; align-items: center; font-size: 14px; padding: 8px 0; border-top: 1px solid {C["rule"]}">{rid(k)}<span style="color: {C["muted"]}; flex: 1">{short(IDX[k]["text"], 46)}</span>{dot(IDX[k]["st"])}</div>' for k in a["kids"][:4])}
</aside>'''
docbody = ''.join(reqblock(r, r['rid'] == 'SDS-IO-002', 2 if r['rid'] in ('SDS-IO-002', 'SDS-IO-005') else 0, fsm if r['rid'] == 'SDS-IO-001' else '') for r in sds)
body = f'''<div style="display: flex; gap: 4px; flex-wrap: wrap; border-bottom: 1px solid {C["rule"]}; padding-bottom: 8px">{doc_tabs}</div>
<div style="display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 6px; background: {SB["planned"]}; font-size: 14px">{dot("planned")}<span>2 modifications de ce document attendent leur écriture dans Tuleap.</span><a href="Synchro.dc.html" style="margin-left: auto; font-size: 13px">Voir la file</a></div>
<div style="display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-start">
<nav aria-label="Sommaire" style="flex: 0 1 200px; min-width: 180px; display: flex; flex-direction: column; gap: 2px"><div style="font-size: 12px; font-weight: 600; color: {C["muted"]}; padding: 0 8px 6px">Sommaire</div>{toc}<div style="font-size: 12px; font-weight: 600; color: {C["muted"]}; padding: 16px 8px 6px">Afficher</div>{''.join(f'<label style="display: flex; gap: 8px; align-items: center; font-size: 13px; padding: 4px 8px"><input type="checkbox"{" checked" if i==0 else ""}>{t}</label>' for i, t in enumerate(['Prose et exigences', 'Exigences seules', 'Anomalies seules']))}</nav>
<article style="flex: 1 1 520px; min-width: 0; background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px">
<div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center; padding: 6px 10px; border-bottom: 1px solid {C["rule"]}">{toolbar}</div>
<div style="padding: 28px 28px 28px 8px">
<h1 style="margin: 0 0 4px 148px; font-size: 26px; line-height: 32px; font-weight: 600">SDS · Sous-système d’E/S</h1>
<p style="margin: 0 0 22px 148px; font-family: {SERIF}; font-size: 17px; line-height: 28px; color: {C["muted"]}">Spécification de conception, branches numérique, analogique et logicielle.</p>
<h2 style="margin: 0 0 6px 148px; font-size: 18px; font-weight: 600">Contrôleur DMA</h2><h3 style="margin: 0 0 12px 148px; font-size: 15px; font-weight: 600; color: {C["muted"]}">Matériel</h3>
{docbody}
</div></article>
{docpanel}
</div>'''
files['Document.dc.html'] = page('Document.dc.html', 'Trace, document SDS', body, 1240)
json.dump({k: len(v) for k, v in files.items()}, open('/tmp/sizes.json', 'w'))
import pickle; pickle.dump(files, open('/tmp/files1.pkl', 'wb'))

# ---------- 3. Panneau d'une exigence ----------
def tabs(active, items):
    return f'<div style="display: flex; gap: 2px; border-bottom: 1px solid {C["rule"]}; flex-wrap: wrap">' + ''.join(f'<button type="button" style="font: {600 if t==active else 500} 13px {SANS}; padding: 8px 8px; border: 0; border-bottom: 2px solid {C["accent"] if t==active else "transparent"}; background: transparent; color: {C["ink"] if t==active else C["muted"]}; cursor: pointer">{t}</button>' for t in items) + '</div>'
PT = ['Traçabilité', 'Vérification', 'Historique', 'Synchro', 'Discussion']
def phead(r, sub):
    return f'<div style="display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap">{rid(r, 24)}<span style="font-size: 13px; color: {C["muted"]}">{sub}</span></div>'
def lrow(k, extra=''):
    return f'<div style="display: flex; gap: 10px; align-items: center; font-size: 14px; padding: 8px 0; border-top: 1px solid {C["rule"]}">{rid(k)}<span style="color: {C["muted"]}; flex: 1; min-width: 0">{short(IDX[k]["text"], 52)}</span>{extra}</div>'
def h3(t): return f'<h3 style="margin: 4px 0 0; font-size: 13px; font-weight: 600; color: {C["muted"]}">{t}</h3>'
r8 = IDX['ERS-IO-020']
weak = [k for k in r8['kids'] if IDX[k]['st'] == 'failing']
p1 = f'''{tabs('Traçabilité', PT)}{phead('ERS-IO-020', 'ERS client · approuvée')}
<p style="margin: 0; font-family: {SERIF}; font-size: 15px; line-height: 24px">{e(r8["text"])}</p>
<div style="background: {SB["failing"]}; border-left: 3px solid {C["danger"]}; border-radius: 0 6px 6px 0; padding: 10px 12px; display: flex; flex-direction: column; gap: 6px">{badge("failing")}<span style="font-size: 14px">Au moins une métrique est en échec dans les résultats du 4 octobre.</span><span style="font-size: 13px">Branche à traiter : {" ".join(rid(k, 13) for k in weak)}</span></div>
<div style="display: flex; flex-direction: column; gap: 6px">{''.join(f'<div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px; padding-top: 6px; border-top: 1px solid {C["rule"]}"><span>{n}{" <span style=\'font-size: 11px; color: " + C["muted"] + "; border: 1px solid " + C["rule"] + "; border-radius: 4px; padding: 0 4px; margin-left: 4px\'>requis</span>" if f in r8["req"] else ""}</span>{badge(famst("ERS-IO-020", f)) if famst("ERS-IO-020", f) else "<span style=\'font-size: 13px; color: " + C["muted"] + "\'>aucun item</span>"}</div>' for f, n in [('DV', 'vPlan DV'), ('ANA', 'Analogique'), ('FW', 'Tests FW'), ('VAL', 'Validation')])}</div>
{h3('Plans requis')}<div style="display: flex; gap: 6px; flex-wrap: wrap">{''.join(f'<button type="button" aria-pressed="{"true" if f in r8["req"] else "false"}" style="font: 500 13px {SANS}; padding: 6px 12px; border-radius: 999px; border: 1px solid {C["accent"] if f in r8["req"] else C["rule"]}; background: {C["accent"] if f in r8["req"] else C["paper"]}; color: {"#FFFFFF" if f in r8["req"] else C["ink"]}; cursor: pointer">{n}</button>' for f, n in [('DV', 'DV'), ('ANA', 'Analogique'), ('FW', 'FW'), ('VAL', 'Validation')])}</div>
{h3('Liens amont')}<p style="margin: 0; font-size: 14px; color: {C["muted"]}">Exigence racine</p>
{h3('Raffinée ou vérifiée par')}{''.join(lrow(k, dot(IDX[k]["st"])) for k in r8["kids"])}'''
vp = next(IDX[x] for x in desc('ERS-IO-020') if IDX[x]['doc'] in FAMDOC and IDX[x]['st'] == 'failing')
MKOPTS = ''.join(f'<option>{o}</option>' for o in {'VP': ['Test', 'Assertion', 'Couverture'], 'FWT': ['Test unitaire', 'Test d’intégration', 'Couv. de code'], 'VAL': ['Procédure', 'Mesure', 'Démonstration']}[vp['doc']])
SRC = {'VP': 'reg_nightly_20261004_0215, importée ce matin à 06:41', 'FWT': 'fw-ci #1490 (4f0d7b9), importé hier à 22:10', 'VAL': 'campagne VAL-08, silicium A0'}[vp['doc']]
VPSUB = {'VP': 'vPlan DV · simulation', 'FWT': 'Tests FW · intégration', 'VAL': 'Validation · banc'}[vp['doc']]
def mrow(m, s, res):
    kind, name = m.split(':', 1)
    KN = dict(test='Test', assert_='Assertion', cover='Couverture', utest='Test unitaire', itest='Test d’intégration', codecov='Couv. de code', proc='Procédure', mesure='Mesure', demo='Démonstration')
    kn = KN.get(kind, KN.get(kind + '_', kind))
    if res is None: txt, col = 'absent des résultats', C['gap']
    elif kind in ('test', 'utest', 'itest'): txt, col = (f'{res["fail"]} en échec sur {res["pass"]+res["fail"]}', C['danger']) if res['fail'] else (f'{res["pass"]} passés', C['ok'])
    elif kind == 'assert': txt, col = ('jamais violée, couverte', C['ok']) if res['ok'] else ('violée', C['danger'])
    elif res.get('stale'): txt, col = 'à rejouer, version antérieure', C['gap']
    elif res.get('pending'): txt, col = 'en attente de double validation', C['accent']
    elif kind == 'mesure': txt, col = (f'{str(res["val"]).replace(".", ",")} {res["unit"]}, max {res["max"]} {res["unit"]}', C['ok'] if s == 'ok' else C['danger'])
    elif kind in ('proc', 'demo'): txt, col = ('réussie', C['ok']) if s == 'ok' else ('échouée', C['danger'])
    else: txt, col = (f'{res["pct"]} %', C['ok']) if s == 'ok' else (f'{res["pct"]} % pour 100 %', C['accent'])
    bc = {'ok': C['ok'], 'fail': C['danger'], 'short': C['accent'], 'missing': C['gap']}[s]
    return f'<div style="display: grid; grid-template-columns: 96px minmax(0, 1fr); column-gap: 8px; padding: 8px 0 8px 10px; border-top: 1px solid {C["rule"]}; border-left: 3px solid {bc}"><span style="font-size: 12px; color: {C["muted"]}">{kn}</span><span style="font-size: 14px; overflow-wrap: anywhere">{name}</span><span></span><span style="font-size: 13px; color: {col}">{txt}</span></div>'
p2 = f'''{tabs('Vérification', PT)}{phead(vp["rid"], VPSUB)}
<p style="margin: 0; font-family: {SERIF}; font-size: 15px; line-height: 24px">{e(vp["text"])}</p>
<div>{badge("failing")}</div>
{h3('Métriques')}<div>{''.join(mrow(*x) for x in vp["metricsEv"])}</div>
<div style="display: flex; gap: 8px"><label style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0)" for="mk">Type</label><select id="mk" style="font: 14px {SANS}; padding: 7px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["paper"]}; color: {C["ink"]}">{MKOPTS}</select><label style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0)" for="mn">Nom</label><input id="mn" placeholder="nom proposé par autocomplétion" style="flex: 1; min-width: 0; font: 14px {SANS}; padding: 7px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["paper"]}; color: {C["ink"]}">{btn('Ajouter', small=True)}</div>
<label style="display: flex; align-items: center; gap: 8px; font-size: 14px; color: {C["muted"]}">Objectif de couverture <input value="100" inputmode="numeric" style="width: 56px; font: 14px {SANS}; padding: 5px 7px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["paper"]}; color: {C["ink"]}"> %</label>
<p style="margin: 0; font-size: 13px; color: {C["muted"]}">Source : {SRC}.</p>
{h3('Satisfait')}{''.join(lrow(k, dot(IDX[k]["st"])) for k in vp["sat"])}'''
hist = [('v4', 'Claire M.', 'il y a 12 min', 'Proposition acceptée', 'Les erreurs de parité, de trame et de débordement doivent être détectées <del style="color: ' + C['danger'] + '">et signalées</del> <ins style="color: ' + C['ok'] + '; text-decoration: none; background: rgba(47,125,85,.12)">, signalées par interruption et comptées</ins>.'),
        ('v3', 'Bertrand D.', 'hier, 09:05', 'Import ERS_client_revD.docx', 'Plans requis : DV, Validation.'),
        ('v2', 'Synchro Tuleap', '14 sept.', 'Changeset Tuleap #88213', 'Lien « satisfait » ajouté depuis SDS-IO-043.'),
        ('v1', 'Bertrand D.', '29 août', 'Import ERS_client_revC.docx', 'Création.')]
p3 = f'''{tabs('Historique', PT)}{phead('ERS-IO-020', 'Historique des versions')}
<div style="display: flex; gap: 8px; align-items: center; font-size: 14px"><span style="color: {C["muted"]}">Comparer</span><select aria-label="Version de départ" style="font: 14px {SANS}; padding: 5px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["paper"]}; color: {C["ink"]}"><option>v3</option></select><span>à</span><select aria-label="Version d’arrivée" style="font: 14px {SANS}; padding: 5px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["paper"]}; color: {C["ink"]}"><option>v4</option></select></div>
{''.join(f'<div style="display: grid; grid-template-columns: 34px minmax(0, 1fr); gap: 10px; padding: 10px 0; border-top: 1px solid {C["rule"]}"><span style="font-weight: 600; font-size: 13px; color: {C["accent"]}">{v}</span><div style="display: flex; flex-direction: column; gap: 4px"><span style="font-size: 14px"><strong style="font-weight: 600">{w}</strong> · {o}</span><span style="font-size: 12px; color: {C["muted"]}">{d}</span><span style="font-family: {SERIF}; font-size: 14px; line-height: 22px">{c}</span></div></div>' for v, w, d, o, c in hist)}
<div style="padding: 10px 12px; border-radius: 6px; background: {C["req"]}; font-size: 13px">Version approuvée : <strong>v3</strong> par Hugo P. La v4 repasse l’exigence en revue.</div>'''
pan = lambda inner: f'<section style="background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px; padding: 18px; display: flex; flex-direction: column; gap: 14px; min-width: 0">{inner}</section>'
body = title_row('Panneau d’une exigence', 'Le même panneau s’ouvre depuis toutes les vues. Trois onglets montrés ici sur deux exigences.')
body += f'<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; align-items: start">{pan(p1)}{pan(p2)}{pan(p3)}</div>'
files['Panneau.dc.html'] = page('Panneau.dc.html', 'Trace, panneau d’une exigence', body, 1180, active='Document.dc.html')

# ---------- 4. Explorateur ----------
root = 'ERS-IO-020'
NP = lambda L: [k for k in L if IDX[k]['st'] != 'proven']
cols = [[root], NP(IDX[root]['kids'])[:5], [], [], []]
for p in cols[1]:
    cols[2] += [k for k in NP(IDX[p]['kids']) if k not in cols[2]]
cols[2] = cols[2][:6]
for p in cols[2]:
    cols[3] += [k for k in NP(IDX[p]['kids']) if k not in cols[3]]
cols[3] = cols[3][:6]
planc = [k for k in cols[3] if IDX[k]['doc'] in FAMDOC]
mets = [(k, m, s_) for k in planc for m, s_, res in IDX[k]['metricsEv'] if s_ != 'ok'][:5]
HIDDEN = len(desc(root)) - sum(len(c) for c in cols[1:4])
BH, GAP, TOP = 70, 14, 30
def ypos(i): return TOP + i * (BH + GAP) + BH / 2
def box(k):
    r = IDX[k]
    return f'<div style="height: {BH}px; box-sizing: border-box; background: {C["sheet"]}; border: 1px solid {C["accent"] if k==root else C["rule"]}; border-radius: 6px; padding: 8px 10px; display: flex; flex-direction: column; gap: 2px; box-shadow: {"0 0 0 2px rgba(47,79,181,.18)" if k==root else "none"}"><span style="display: flex; align-items: center; gap: 6px">{dot(r["st"])}{rid(k, 13)}<span style="margin-left: auto; font-size: 11px; color: {C["muted"]}">{LBL[r["st"]]}</span></span><span style="font-size: 12px; line-height: 16px; color: {C["muted"]}; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical">{e(r["text"])}</span></div>'
def mbox(k, m, s):
    kind, name = m.split(':', 1)
    col = {'fail': C['danger'], 'short': C['accent'], 'missing': C['gap']}[s]
    t = {'fail': 'en échec', 'short': 'objectif non atteint', 'missing': 'absent des résultats'}[s]
    return f'<div style="height: {BH}px; box-sizing: border-box; background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-left: 3px solid {col}; border-radius: 6px; padding: 8px 10px; display: flex; flex-direction: column; gap: 2px"><span style="font-size: 12px; color: {C["muted"]}">{kind} · {k}</span><span style="font-size: 13px; overflow-wrap: anywhere">{name}</span><span style="font-size: 12px; color: {col}">{t}</span></div>'
colsH = max(len(c) for c in cols[:4] + [mets]) * (BH + GAP) + TOP + 10
def links(a, b, pairs):
    paths = ''.join(f'<path d="M0 {ypos(i):.0f} C 28 {ypos(i):.0f}, 28 {ypos(j):.0f}, 56 {ypos(j):.0f}" fill="none" stroke="#9AA1AE" stroke-width="1.3"/>' for i, j in pairs)
    return f'<svg width="56" height="{colsH}" viewBox="0 0 56 {colsH}" aria-hidden="true" style="flex: none">{paths}</svg>'
def pairs(A, B):
    out = []
    for j, k in enumerate(B):
        for i, p in enumerate(A):
            if p in IDX[k]['sat']: out.append((i, j))
    return out
def pairsm(A, M):
    return [(A.index(k), j) for j, (k, m, s) in enumerate(M)]
heads = ['Exigence client', 'Enfants directs', 'Niveau suivant', 'Niveau suivant', 'Métriques à traiter']
colw = 220
def column(i, inner):
    return f'<div style="width: {colw}px; flex: none; display: flex; flex-direction: column; gap: {GAP}px; padding-top: {TOP}px; position: relative"><span style="position: absolute; top: 0; left: 0; font-size: 12px; font-weight: 600; color: {C["muted"]}">{heads[i]}</span>{inner}</div>'
def pairs_any(A, B):
    return [(i, j) for j, k in enumerate(B) for i, p in enumerate(A) if p in IDX[k]['sat']]
graph = column(0, box(root)) + links(0, 1, [(0, j) for j in range(len(cols[1]))]) + column(1, ''.join(box(k) for k in cols[1])) + links(1, 2, pairs_any(cols[1], cols[2])) + column(2, ''.join(box(k) for k in cols[2])) + links(2, 3, pairs_any(cols[2], cols[3])) + column(3, ''.join(box(k) for k in cols[3])) + links(3, 4, [(cols[3].index(k), j) for j, (k, m, s_) in enumerate(mets)]) + column(4, ''.join(mbox(*x) for x in mets))
body = title_row('Explorateur de traçabilité', f'Centré sur ERS-IO-020, {len(desc(root))} exigences en aval. Seules les branches non prouvées sont dépliées.', btn('Exporter en SVG') + btn('Ouvrir le panneau', True))
body += f'''<div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center; font-size: 14px"><span style="color: {C["muted"]}">Afficher</span>{''.join(f'<label style="display: inline-flex; gap: 6px; align-items: center; padding: 5px 10px; border: 1px solid {C["rule"]}; border-radius: 999px; background: {C["sheet"]}"><input type="checkbox" checked>{t}</label>' for t in ['DV', 'Analogique', 'FW', 'Validation'])}<label style="display: inline-flex; gap: 6px; align-items: center; margin-left: 12px"><input type="checkbox">Branches prouvées</label></div>
<div style="overflow-x: auto; background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px; padding: 20px"><div style="display: flex; align-items: flex-start; min-width: max-content">{graph}</div></div>
<p style="margin: 0; font-size: 13px; color: {C["muted"]}">{HIDDEN} exigences prouvées ou plus profondes sont repliées. Les ancêtres s’affichent à gauche quand l’exigence centrale n’est pas une exigence racine.</p>'''
files['Explorateur.dc.html'] = page('Explorateur.dc.html', 'Trace, explorateur de traçabilité', body, 1000)

# ---------- 5. Matrice ----------
def ers_tree():
    ids = [r['rid'] for r in ERS if r['sub'] == CURSUB]; out, seen = [], set()
    def visit(k, d):
        if k in seen: return
        seen.add(k); out.append((k, d))
        for c in IDX[k]['kids']:
            if IDX[c]['doc'] == 'ERS': visit(c, d + 1)
    for k in ids:
        if not any(p in ids for p in IDX[k]['sat']): visit(k, 0)
    return out
def cell(lst):
    if not lst: return f'<span style="color: #9AA1AE">—</span>'
    s = ' '.join(lst[:1]) + (f' <span style="color: {C["muted"]}">+{len(lst)-1}</span>' if len(lst) > 1 else '')
    return f'<span style="font-variant-numeric: tabular-nums">{s}</span>'
th = lambda t, a='left': f'<th scope="col" style="text-align: {a}; padding: 10px 8px; font-size: 12px; font-weight: 600; color: {C["muted"]}; border-bottom: 1px solid {C["rule"]}; position: sticky; top: 0; background: {C["sheet"]}; white-space: nowrap">{t}</th>'
rows = ''
for k, d in ers_tree()[:36]:
    r = IDX[k]; ds = desc(k)
    by = lambda doc: [x for x in ds if IDX[x]['doc'] == doc]
    anscell = by('ANS')
    plans = by('VP') + by('ANV') + by('FWT') + by('VAL')
    fams = ''.join(fam(f, famst(k, f), f in r['req']) for f in ['DV', 'ANA', 'FW', 'VAL'])
    rows += f'<tr style="background: {SB["failing"] if k=="ERS-IO-020" else "transparent"}"><td style="padding: 9px 8px; border-bottom: 1px solid {C["rule"]}; white-space: nowrap"><span style="display: inline-flex; align-items: center; gap: 8px; padding-left: {d*18}px">{dot(r["st"])}{rid(k, 13)}</span></td><td style="padding: 9px 8px; border-bottom: 1px solid {C["rule"]}; max-width: 300px; color: {C["ink"]}">{e(short(r["text"], 58))}</td>' + ''.join(f'<td style="padding: 9px 8px; border-bottom: 1px solid {C["rule"]}; font-size: 13px; white-space: nowrap">{cell(x)}</td>' for x in [by('SDS'), by('DDS'), anscell, by('FWS'), plans]) + f'<td style="padding: 9px 8px; border-bottom: 1px solid {C["rule"]}"><span style="display: inline-flex; gap: 3px">{fams}</span></td><td style="padding: 9px 8px; border-bottom: 1px solid {C["rule"]}; text-align: right">{badge(r["st"])}</td></tr>'
sel = lambda lab, opts: f'<label style="display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: {C["muted"]}">{lab}<select style="font: 14px {SANS}; padding: 7px 8px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["sheet"]}; color: {C["ink"]}; min-width: 150px">{"".join(f"<option>{o}</option>" for o in opts)}</select></label>'
NIO = sum(1 for x in ERS if x['sub'] == CURSUB)
body = title_row('Matrice de couverture', f'Sous-système d’E/S : {NIO} exigences client sur {len(ERS)} pour le SoC, résultats du 4 octobre', btn('Exporter XLSX') + btn('Exporter CSV'))
body += f'''<div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end">{sel('Sous-système', [SUBNAME] + [x['nom'] for x in SUBS if x['code'] != CURSUB] + ['Tout le SoC'])}{sel('Niveau', ['ERS client', 'SDS'])}{sel('Statut', ['Tous les statuts', 'Non prouvées'])}{sel('Branche', ['Toutes', 'Numérique', 'Analogique', 'FW'])}{sel('Famille', ['Toutes', 'DV', 'Analogique', 'FW', 'Validation'])}{sel('Résultats', ['4 octobre', '3 octobre', 'BL-07'])}<label style="display: flex; align-items: center; gap: 8px; font-size: 14px; padding: 8px 0"><input type="checkbox">Comparer avec BL-07</label><label style="flex: 1 1 200px; display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: {C["muted"]}">Texte<input type="search" placeholder="Filtrer par texte" style="font: 14px {SANS}; padding: 7px 8px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["sheet"]}; color: {C["ink"]}"></label></div>
<div style="display: flex; gap: 20px; align-items: center; flex-wrap: wrap">{legend({k: sum(1 for x in ERS if x['sub'] == CURSUB and x['st'] == k) for k in LBL})}<span style="font-size: 13px; color: {C["muted"]}; display: inline-flex; gap: 6px; align-items: center">{fam("VAL", need=True)} plan requis sans item</span></div>
<div style="overflow-x: auto; background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px"><table style="width: 100%; border-collapse: collapse; font-size: 14px"><thead><tr>{th('ID')}{th('Énoncé')}{th('SDS')}{th('DDS')}{th('Spéc. ANA')}{th('Spéc. FW')}{th('Plans')}{th('Familles')}{th('Statut', 'right')}</tr></thead><tbody>{rows}</tbody></table></div><div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px; color: {C["muted"]}"><span>Lignes 1 à 36 sur {NIO}</span><div style="display: flex; gap: 8px">{btn('Précédent', small=True)}{btn('Suivant', small=True)}</div></div>'''
files['Matrice.dc.html'] = page('Matrice.dc.html', 'Trace, matrice de couverture', body, 1960)

# ---------- 6. Résultats ----------
rtabs = f'<div style="display: flex; gap: 4px; border-bottom: 1px solid {C["rule"]}; flex-wrap: wrap">' + ''.join(f'<button type="button" style="font: {600 if t=="Analogique" else 500} 14px {SANS}; padding: 10px 14px; border: 0; border-bottom: 2px solid {C["accent"] if t=="Analogique" else "transparent"}; background: transparent; color: {C["ink"] if t=="Analogique" else C["muted"]}; cursor: pointer">{t} <span style="font-size: 12px; color: {C["muted"]}">{n}</span></button>' for t, n in [('DV', FS['DV'][0]), ('Analogique', FS['ANA'][0]), ('FW', FS['FW'][0]), ('Validation', FS['VAL'][0])]) + '</div>'
KM = {'spec': 'Performance', 'mc': 'Monte-Carlo', 'model': 'Corrélation modèle'}
arows = ''.join(f'<tr><td style="padding: 11px 8px; border-bottom: 1px solid {C["rule"]}; white-space: nowrap"><span style="display: inline-flex; gap: 8px; align-items: center">{dot(st)}{rid(i, 13)}</span><div style="font-size: 12px; color: {C["muted"]}; padding-left: 16px">{a}</div></td><td style="padding: 11px 8px; border-bottom: 1px solid {C["rule"]}"><div style="font-size: 12px; color: {C["muted"]}">{KM[k]}</div><div style="font-size: 14px">{n}</div></td><td style="padding: 11px 8px; border-bottom: 1px solid {C["rule"]}; white-space: nowrap; font-variant-numeric: tabular-nums">{b}</td><td style="padding: 11px 8px; border-bottom: 1px solid {C["rule"]}; white-space: nowrap; font-size: 13px">{w}</td><td style="padding: 11px 8px; border-bottom: 1px solid {C["rule"]}; white-space: nowrap; font-weight: 600; font-variant-numeric: tabular-nums; color: {SC[st]}">{v}</td><td style="padding: 11px 8px; border-bottom: 1px solid {C["rule"]}; white-space: nowrap; font-variant-numeric: tabular-nums">{mg}</td><td style="padding: 11px 8px; border-bottom: 1px solid {C["rule"]}; white-space: nowrap"><span style="font-size: 12px; font-weight: 600; padding: 2px 7px; border-radius: 4px; border: 1px solid {C["rule"]}; color: {C["gap"] if view=="Schéma" else C["ink"]}">{view}</span></td><td style="padding: 11px 8px; border-bottom: 1px solid {C["rule"]}; text-align: right">{badge(st)}</td></tr>' for i, a, k, n, b, w, v, mg, view, st in ANV)
body = title_row('Résultats de vérification', f'Analogique · Alimentations et références : {len(ALIMV)} items, campagne ADE-14 du 3 octobre, PDK 1.4.2, 27 coins', btn('Ouvrir l’export ADE') + btn('Importer une campagne', True))
body += rtabs + f'''<div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end">{sel('Campagne affichée', ['ADE-14 · 3 octobre', 'ADE-13 · 26 septembre'])}{sel('Comparer avec', ['ADE-13 · 26 septembre', 'Aucune'])}{sel('Sous-système', ['Alimentations et références', 'Conversion et capteurs', 'Mémoires'])}{sel('Vue simulée', ['Toutes', 'Post-layout', 'Schéma'])}</div>
<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px">{''.join(card('', f'<div style="font-size: 13px; color: {C["muted"]}">{t}</div><div style="font-size: 28px; line-height: 32px; font-weight: 600; color: {col}; font-variant-numeric: tabular-nums">{n}</div><div style="font-size: 13px; color: {C["muted"]}">{s}</div>', pad=16) for t, n, s, col in [('Prouvés', str(ANVSTATS['proven']), f'sur {len(ALIMV)} items', C['ok']), ('En échec', str(ANVSTATS['failing']), 'hors limite au pire coin', C['danger']), ('Planifiés', str(ANVSTATS['planned']), 'schéma seul ou Cpk insuffisant', C['accent']), ('Sans métrique', str(ANVSTATS['traced']), 'à compléter', C['muted'])])}</div>
<div style="overflow-x: auto; background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px"><table style="width: 100%; border-collapse: collapse; font-size: 14px"><thead><tr>{th('Item')}{th('Métrique')}{th('Critère')}{th('Pire coin')}{th('Résultat')}{th('Marge')}{th('Vue')}{th('Statut', 'right')}</tr></thead><tbody>{arows}</tbody></table></div>
<p style="margin: 0; font-size: 13px; color: {C["muted"]}">Une performance n’est atteinte que si elle tient sur tous les coins du jeu demandé. Les résultats importés ne sont jamais modifiés.</p>'''
files['Resultats.dc.html'] = page('Resultats.dc.html', 'Trace, résultats de vérification', body, 980)
pickle.dump(files, open('/tmp/files2.pkl', 'wb'))
print({k: len(v) for k, v in files.items()})

# ---------- 7. Anomalies ----------
untr = [r for r in ERS if r['st'] == 'untraced']
def reason(r):
    miss = [f for f in r['req'] if not famst(r['rid'], f)]
    if miss: return 'Plan requis sans item : ' + ', '.join({'DV': 'DV', 'FW': 'FW', 'VAL': 'Validation'}[f] for f in miss)
    if not r['kids']: return 'Aucune exigence dérivée'
    return 'Une branche s’arrête avant les plans de vérification'
stale = [(r['rid'], m) for r in D for m, s, res in r['metricsEv'] if res and res.get('stale')][:3]
missing = [(r['rid'], m) for r in D for m, s, res in r['metricsEv'] if s == 'missing'][:3]
def arow(lead, txt, actions, who=''):
    w = f'<span style="font-size: 13px; color: {C["muted"]}; white-space: nowrap">{who}</span>' if who else f'<button type="button" style="font: 500 13px {SANS}; padding: 5px 10px; border-radius: 6px; border: 1px dashed {C["rule"]}; background: transparent; color: {C["muted"]}; cursor: pointer">Assigner</button>'
    return f'<div style="display: flex; align-items: center; gap: 12px; padding: 10px 0; border-top: 1px solid {C["rule"]}; flex-wrap: wrap"><span style="min-width: 90px">{lead}</span><span style="flex: 1 1 280px; font-size: 14px; color: {C["ink"]}">{txt}</span>{w}{"".join(btn(a, small=True) for a in actions)}</div>'
def acat(t, n, st, rows, open_=True):
    return f'<section style="background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px; padding: 14px 18px"><div style="display: flex; align-items: center; gap: 10px">{dot(st, 10)}<h2 style="margin: 0; font-size: 15px; font-weight: 600">{t}</h2><span style="font-weight: 600; color: {C["muted"]}; font-variant-numeric: tabular-nums">{n}</span><button type="button" aria-expanded="{"true" if open_ else "false"}" style="margin-left: auto; font: 500 13px {SANS}; border: 0; background: transparent; color: {C["accent"]}; cursor: pointer">{"Replier" if open_ else "Déplier"}</button></div>{"<div style=\'margin-top: 8px\'>" + rows + "</div>" if open_ else ""}</section>'
NANOM = 2 + 1 + len(untr) + STALE + MISS + 2 + 3
body = title_row('Anomalies', f'{NANOM} points à traiter sur le SoC, du plus bloquant au moins urgent', sel('Assignées à', ['Tout le monde', 'Moi', 'Non assignées']))
body += acat('Fils bloquants ouverts', 2, 'failing', arow(rid('ERS-IO-020'), 'Claire M. : « Le débordement doit-il aussi lever une interruption ? » Bloque l’approbation de la v4.', ['Ouvrir le fil'], 'Bertrand D.') + arow(rid('SDS-SYS-035'), 'Hugo P. : la séquence d’acquittement contredit FWS-SYS-010.', ['Ouvrir le fil']))
body += acat('Conflits de synchro', 1, 'failing', arow(rid('SDS-IO-040'), 'Modifiée dans Tuleap (changeset #88540) pendant votre édition.', ['Résoudre']))
body += acat('Exigences client non tracées', len(untr), 'untraced', ''.join(arow(rid(r['rid']), f'{e(short(r["text"], 70))} <span style="color: {C["gap"]}; font-size: 13px">· {reason(r)}</span>', ['Ouvrir']) for r in untr[:5]))
body += acat('Résultats à rejouer', STALE, 'untraced', ''.join(arow(rid(k), f'<code style="font-size: 13px">{m}</code> obtenu sur silicium A0, la baseline en cours vise A1.', ['Voir le résultat']) for k, m in stale))
body += acat('Métriques absentes des résultats', MISS, 'untraced', ''.join(arow(rid(k), f'<code style="font-size: 13px">{m}</code> n’apparaît pas dans les résultats de référence.', ['Corriger le nom']) for k, m in missing))
body += acat('Questions client sans réponse depuis 10 jours', 2, 'planned', '', False)
body += acat('Exigences approuvées puis modifiées', 3, 'planned', '', False)
files['Anomalies.dc.html'] = page('Anomalies.dc.html', 'Trace, anomalies', body, 1500)

# ---------- 8. Import ----------
steps = ['Fichier et modèle', 'Correspondance', 'Aperçu', 'Validation']
stepper = '<ol style="list-style: none; margin: 0; padding: 0; display: flex; gap: 8px; flex-wrap: wrap">' + ''.join(f'<li style="display: flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px; font-size: 14px; font-weight: {600 if i==2 else 500}; background: {C["accent"] if i==2 else C["sheet"]}; color: {"#FFFFFF" if i==2 else (C["ink"] if i<2 else C["muted"])}; border: 1px solid {C["accent"] if i==2 else C["rule"]}"><span style="font-variant-numeric: tabular-nums">{i+1}</span>{t}</li>' for i, t in enumerate(steps)) + '</ol>'
summary = [('Nouvelles', 3, C['ok']), ('Modifiées', 4, C['accent']), ('Inchangées', len(ERS) - 8, C['muted']), ('Absentes du fichier', 1, C['gap']), ('Erreurs', 2, C['danger'])]
def diffrow(k, old, new, tag):
    return f'<div style="display: grid; grid-template-columns: 100px minmax(0, 1fr) auto; gap: 14px; padding: 12px 0; border-top: 1px solid {C["rule"]}; align-items: start"><span>{rid(k)}</span><div style="font-family: {SERIF}; font-size: 15px; line-height: 24px">{old}{new}</div>{tag}</div>'
DEL = lambda t: f'<del style="color: {C["danger"]}; background: rgba(179,38,30,.08)">{t}</del>'
INS = lambda t: f'<ins style="color: {C["ok"]}; background: rgba(47,125,85,.12); text-decoration: none">{t}</ins>'
body = title_row('Importer des exigences', 'ERS_client_revD.docx · modèle « Spécification client » · SHA-256 3f9a07…c21e', btn('Annuler'))
body += stepper
body += f'<div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px">' + ''.join(card('', f'<div style="font-size: 13px; color: {C["muted"]}">{t}</div><div style="font-size: 28px; line-height: 32px; font-weight: 600; color: {c}; font-variant-numeric: tabular-nums">{n}</div>', pad=14) for t, n, c in summary) + '</div>'
body += card('Modifiées', diffrow('ERS-IO-020', 'Les erreurs de parité, de trame et de débordement doivent être détectées ', DEL('et signalées') + ' ' + INS('et signalées par interruption') + '.', badge('planned', '3 aval à revoir')) + diffrow('ERS-SYS-001', 'Le sous-système doit offrir ', DEL('4') + INS('6') + ' timers 32 bits à rechargement automatique.', badge('planned', '4 aval à revoir')) + diffrow('ERS-PWR-013', 'Le sous-système doit supporter un mode veille avec une consommation inférieure à ', DEL('50 µA') + INS('40 µA') + '.', badge('planned', '4 aval à revoir')), f'<span style="font-size: 13px; color: {C["muted"]}">et 1 autre</span>')
body += f'<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px">' + card('Nouvelles', ''.join(f'<div style="display: flex; gap: 12px; padding: 10px 0; border-top: 1px solid {C["rule"]}">{rid(k)}<span style="font-family: {SERIF}; font-size: 15px; line-height: 24px">{t}</span></div>' for k, t in [('ERS-IO-070', 'Le contrôleur DMA doit supporter les transferts en liste chaînée.'), ('ERS-SYS-056', 'Chaque timer doit offrir un mode capture sur front externe.'), ('ERS-IO-071', 'Le maître SPI doit supporter le mode quad en lecture.')])) + card('Erreurs et absentes', f'<div style="display: flex; gap: 10px; padding: 10px 0; border-top: 1px solid {C["rule"]}">{ICON_X}<span style="font-size: 14px">Ligne 41 : lien « Satisfait : ERS-IO-099 » vers un ID inconnu.</span></div><div style="display: flex; gap: 10px; padding: 10px 0; border-top: 1px solid {C["rule"]}">{ICON_X}<span style="font-size: 14px">ERS-SYS-012 apparaît deux fois (pages 6 et 11).</span></div><div style="display: flex; gap: 10px; align-items: center; padding: 10px 0; border-top: 1px solid {C["rule"]}; flex-wrap: wrap">{dot("untraced")}<span style="font-size: 14px; flex: 1">ERS-IO-036 n’apparaît plus dans la révision D.</span><label style="display: flex; gap: 6px; align-items: center; font-size: 14px"><input type="checkbox">Retirer</label></div>') + '</div>'
body += f'<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; padding: 14px 18px; background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px"><span style="font-size: 14px">11 exigences aval passeront « à revoir ». Corrigez les 2 erreurs ou excluez leurs lignes pour continuer.</span><div style="display: flex; gap: 8px">{btn("Retour à la correspondance")}{btn("Valider l’import", True)}</div></div>'
files['Import.dc.html'] = page('Import.dc.html', 'Trace, import d’une spécification', body, 1260)

# ---------- 9. Synchro ----------
LVN = lambda lv: sum(1 for x in D if x['doc'] == lv)
trk = [('ERS client', 'exigences-client', LVN('ERS'), 'il y a 2 min', 0, 0), ('SDS', 'sds-soc', LVN('SDS'), 'il y a 2 min', 2, 1), ('DDS', 'dds-soc', LVN('DDS'), 'il y a 3 min', 0, 0), ('Spéc. analogique', 'ans-soc', LVN('ANS'), 'il y a 3 min', 0, 0), ('Spéc. FW', 'fws-soc', LVN('FWS'), 'il y a 2 min', 1, 0), ('vPlan DV', 'vplan-soc', LVN('VP'), 'il y a 2 min', 1, 0), ('Plan analogique', 'anv-soc', LVN('ANV'), 'il y a 3 min', 0, 0), ('Tests FW', 'fwt-soc', LVN('FWT'), 'il y a 4 min', 0, 0), ('Validation', 'val-soc', LVN('VAL'), 'il y a 4 min', 0, 0)]
trows = ''.join(f'<tr><td style="padding: 10px 8px; border-bottom: 1px solid {C["rule"]}; font-weight: 600">{a}</td><td style="padding: 10px 8px; border-bottom: 1px solid {C["rule"]}"><code style="font-size: 13px">{b}</code></td><td style="padding: 10px 8px; border-bottom: 1px solid {C["rule"]}; text-align: right; font-variant-numeric: tabular-nums">{c}</td><td style="padding: 10px 8px; border-bottom: 1px solid {C["rule"]}; color: {C["muted"]}">{d}</td><td style="padding: 10px 8px; border-bottom: 1px solid {C["rule"]}; text-align: right; font-variant-numeric: tabular-nums; color: {C["accent"] if f else C["muted"]}">{f}</td><td style="padding: 10px 8px; border-bottom: 1px solid {C["rule"]}; text-align: right">{badge("failing", "1 conflit") if g else ""}</td></tr>' for a, b, c, d, f, g in trk)
body = title_row('Synchronisation Tuleap', 'Synchro entrante toutes les minutes, 30 appels par minute au plus', btn('Synchroniser maintenant'))
body += f'<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px">' + ''.join(card('', f'<div style="font-size: 13px; color: {C["muted"]}">{t}</div><div style="font-size: 28px; line-height: 32px; font-weight: 600; color: {c}">{n}</div><div style="font-size: 13px; color: {C["muted"]}">{s}</div>', pad=16) for t, n, s, c in [('En attente d’écriture', '4', 'la plus ancienne depuis 3 min', C['accent']), ('Conflits', '1', 'SDS-IO-040', C['danger']), ('Erreurs', '0', 'aucune depuis hier 18:02', C['ok'])]) + '</div>'
body += card('Trackers', f'<div style="overflow-x: auto"><table style="width: 100%; border-collapse: collapse; font-size: 14px"><thead><tr>{th("Niveau")}{th("Tracker")}{th("Artefacts", "right")}{th("Dernière synchro")}{th("En attente", "right")}{th("État", "right")}</tr></thead><tbody>{trows}</tbody></table></div>')
L = 'Les données reçues sur RX doivent être échantillonnées au milieu du bit, avec un filtrage majoritaire sur 3 échantillons.'
R = 'Les données reçues sur RX doivent être échantillonnées au milieu du bit, avec un filtrage majoritaire sur 5 échantillons.'
side = lambda t, who, txt, hl: f'<div style="flex: 1 1 300px; min-width: 0; border: 1px solid {C["rule"]}; border-radius: 6px; padding: 14px; display: flex; flex-direction: column; gap: 8px"><div style="font-size: 13px; font-weight: 600">{t}</div><div style="font-size: 12px; color: {C["muted"]}">{who}</div><p style="margin: 0; font-family: {SERIF}; font-size: 15px; line-height: 24px">{txt}</p></div>'
body += card('Conflit sur SDS-IO-040', f'<p style="margin: 0; font-size: 14px">Quelqu’un a modifié l’artefact dans Tuleap pendant que Claire M. éditait SDS-IO-040. Rien n’a été écrasé.</p><div style="display: flex; gap: 14px; flex-wrap: wrap">{side("Version locale", "Claire M. · aujourd’hui 10:14 · basée sur le changeset #88497", L.replace("3 échantillons", INS("3 échantillons")), 0)}{side("Version Tuleap", "Marc T. · aujourd’hui 10:16 · changeset #88540", R.replace("5 échantillons", DEL("5 échantillons")), 0)}</div><div style="display: flex; gap: 8px; flex-wrap: wrap">{btn("Garder la mienne")}{btn("Prendre celle de Tuleap")}{btn("Fusionner à la main", True)}</div>', badge('failing', 'En conflit'))
files['Synchro.dc.html'] = page('Synchro.dc.html', 'Trace, synchronisation Tuleap', body, 1180)

# ---------- 10. Baselines ----------
BLT = len(ERS)
bl = [('BL-07', 'Jalon 2, revue client', '28 sept. 2026', 'Bertrand D.', {'proven': round(FINAL*0.86), 'planned': 70, 'failing': 74, 'traced': 30, 'untraced': BLT - 3 - round(FINAL*0.86) - 174}), ('BL-06', 'Revue interne SDS', '12 sept. 2026', 'Hugo P.', {'proven': round(FINAL*0.71), 'planned': 82, 'failing': 69, 'traced': 41, 'untraced': BLT - 12 - round(FINAL*0.71) - 192}), ('BL-05', 'Gel de la révision C', '29 août 2026', 'Bertrand D.', {'proven': round(FINAL*0.52), 'planned': 96, 'failing': 77, 'traced': 52, 'untraced': BLT - 12 - round(FINAL*0.52) - 225})]
brows = ''.join(f'<tr><td style="padding: 12px 8px; border-bottom: 1px solid {C["rule"]}"><input type="checkbox" aria-label="Sélectionner {a}"{" checked" if a in ("BL-07", "BL-06") else ""}></td><td style="padding: 12px 8px; border-bottom: 1px solid {C["rule"]}; white-space: nowrap">{rid(a)}</td><td style="padding: 12px 8px; border-bottom: 1px solid {C["rule"]}; font-weight: 600">{b}</td><td style="padding: 12px 8px; border-bottom: 1px solid {C["rule"]}; color: {C["muted"]}; white-space: nowrap">{c}</td><td style="padding: 12px 8px; border-bottom: 1px solid {C["rule"]}; white-space: nowrap">{d}</td><td style="padding: 12px 8px; border-bottom: 1px solid {C["rule"]}; width: 26%">{segbar(s, 30, 8)}<div style="font-size: 12px; color: {C["muted"]}; margin-top: 4px">{s["proven"]} prouvées sur {sum(s.values())}</div></td><td style="padding: 12px 8px; border-bottom: 1px solid {C["rule"]}; text-align: right; white-space: nowrap">{btn("Rapport de preuve", small=True)}</td></tr>' for a, b, c, d, s in bl)
chk = lambda ok, t: f'<div style="display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-top: 1px solid {C["rule"]}; font-size: 14px">{ICON_CHECK if ok else ICON_X}<span>{t}</span></div>'
body = title_row('Baselines', 'Une baseline fige exigences, plans, résultats de référence, discussions et approbations. Elle est immuable.', btn('Comparer la sélection') + btn('Créer une baseline', True))
body += card('', f'<div style="overflow-x: auto"><table style="width: 100%; border-collapse: collapse; font-size: 14px"><thead><tr>{th("")}{th("ID")}{th("Nom")}{th("Date")}{th("Auteur")}{th("Exigences client")}{th("")}</tr></thead><tbody>{brows}</tbody></table></div>', pad=12)
body += f'<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; align-items: start">'
body += card('Nouvelle baseline', f'<label style="display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: {C["muted"]}">Nom<input value="Jalon 3, revue client" style="font: 15px {SANS}; padding: 8px 10px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["paper"]}; color: {C["ink"]}"></label><div style="font-size: 13px; font-weight: 600; color: {C["muted"]}">Contrôles préalables</div>{chk(True, "Résultats de référence choisis : DV 4 octobre, ADE-14, fw-ci #1490, VAL-08")}{chk(False, "4 modifications attendent leur écriture dans Tuleap, dont 1 en conflit")}{chk(False, "2 fils bloquants ouverts (ERS-IO-020, SDS-SYS-035)")}{chk(True, "Aucun résultat en attente de double validation dans le périmètre")}<div style="display: flex; justify-content: flex-end">{btn("Créer la baseline", True)}</div>')
body += card('BL-06 → BL-07', ''.join(f'<div style="display: flex; justify-content: space-between; padding: 8px 0; border-top: 1px solid {C["rule"]}; font-size: 14px"><span>{t}</span><strong style="font-weight: 600; font-variant-numeric: tabular-nums; color: {c}">{n}</strong></div>' for t, n, c in [('Exigences ajoutées', '+2', C['ok']), ('Exigences modifiées', '7', C['accent']), ('Exigences retirées', '0', C['muted']), ('Devenues prouvées', '+4', C['ok']), ('Devenues en échec', '+1', C['danger'])]) + f'<div style="display: flex; gap: 10px; padding: 8px 0; border-top: 1px solid {C["rule"]}; font-size: 14px; flex-wrap: wrap">{rid("ERS-CPU-015")}<span style="color: {C["muted"]}">Prouvée</span><span>→</span>{badge("planned")}<span style="color: {C["muted"]}">couverture ERRCODE à 94 %</span></div>')
body += '</div>'
files['Baselines.dc.html'] = page('Baselines.dc.html', 'Trace, baselines', body, 1080)

# ---------- 11. Administration ----------
lv = [('ERS client', 'ERS', 'exigences-client', '—', 'ERS'), ('SDS', 'SDS', 'sds-ioss', 'ERS', 'SDS'), ('DDS', 'DDS', 'dds-ioss', 'SDS', 'DDS'), ('Spéc. analogique', 'ANS', 'ans-ioss', 'SDS', 'ANS'), ('Spéc. FW', 'FWS', 'fws-drivers', 'SDS', 'FWS'), ('vPlan DV', 'VP', 'vplan-ioss', 'DDS, SDS, ERS', '—'), ('Plan analogique', 'ANV', 'anv-ioss', 'ANS, SDS', '—'), ('Tests FW', 'FWT', 'fwt-drivers', 'FWS, SDS', '—'), ('Validation', 'VAL', 'val-ioss', 'ERS, SDS', '—')]
inp = lambda v, w=120, lab='': f'<input aria-label="{lab}" value="{v}" style="width: {w}px; font: 14px {SANS}; padding: 6px 8px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["paper"]}; color: {C["ink"]}">'
lrows = ''.join(f'<tr><td style="padding: 8px; border-bottom: 1px solid {C["rule"]}; font-weight: 600">{a}</td><td style="padding: 8px; border-bottom: 1px solid {C["rule"]}">{inp(b, 70, "Préfixe de " + a)}</td><td style="padding: 8px; border-bottom: 1px solid {C["rule"]}">{inp(c, 160, "Tracker de " + a)}</td><td style="padding: 8px; border-bottom: 1px solid {C["rule"]}; color: {C["muted"]}">{d}</td><td style="padding: 8px; border-bottom: 1px solid {C["rule"]}; color: {C["muted"]}">{f}</td></tr>' for a, b, c, d, f in lv)
tog = lambda t, on: f'<label style="display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 0; border-top: 1px solid {C["rule"]}; font-size: 14px"><span>{t}</span><input type="checkbox"{" checked" if on else ""} style="width: 18px; height: 18px"></label>'
body = title_row('Administration du projet', 'Sous-système d’E/S · réservé aux administrateurs du projet', btn('Enregistrer', True))
body += card('Niveaux et trackers', f'<div style="overflow-x: auto"><table style="width: 100%; border-collapse: collapse; font-size: 14px"><thead><tr>{th("Niveau")}{th("Préfixe")}{th("Tracker Tuleap")}{th("Satisfait")}{th("Dérive de")}</tr></thead><tbody>{lrows}</tbody></table></div><p style="margin: 0; font-size: 13px; color: {C["muted"]}">Types de liens Tuleap : « derives_from » pour dérive de, « satisfies » pour satisfait.</p>')
body += f'<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; align-items: start">'
body += card('Plans requis par défaut', ''.join(f'<div style="padding: 10px 0; border-top: 1px solid {C["rule"]}"><div style="font-size: 14px; margin-bottom: 8px">{t}</div><div style="display: flex; gap: 6px; flex-wrap: wrap">' + ''.join(f'<button type="button" aria-pressed="{"true" if f in on else "false"}" style="font: 500 13px {SANS}; padding: 5px 11px; border-radius: 999px; border: 1px solid {C["accent"] if f in on else C["rule"]}; background: {C["accent"] if f in on else C["paper"]}; color: {"#FFFFFF" if f in on else C["ink"]}; cursor: pointer">{f}</button>' for f in ['DV', 'Analogique', 'FW', 'Validation']) + '</div></div>' for t, on in [('Exigence client numérique', ['DV', 'Validation']), ('Exigence client analogique', ['Analogique', 'Validation']), ('Exigence SDS', [])]))
body += card('Analogique', f'{tog("Exiger le post-layout pour qu’un résultat compte comme preuve", True)}<div style="padding: 10px 0; border-top: 1px solid {C["rule"]}"><div style="font-size: 14px; margin-bottom: 6px">Jeu de coins par défaut</div><select aria-label="Jeu de coins par défaut" style="width: 100%; font: 14px {SANS}; padding: 7px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["paper"]}; color: {C["ink"]}"><option>Nominal + étendu (27 coins)</option></select><div style="font-size: 13px; color: {C["muted"]}; margin-top: 6px">Process tt, ss, ff · 0,99 V, 1,10 V, 1,21 V · -40 °C, 25 °C, 125 °C</div></div><div style="padding: 10px 0; border-top: 1px solid {C["rule"]}; font-size: 14px">Objectif Monte-Carlo par défaut : Cpk ≥ 1,33</div>')
body += card('Rôles et revue', ''.join(f'<div style="display: flex; justify-content: space-between; padding: 9px 0; border-top: 1px solid {C["rule"]}; font-size: 14px"><span>{t}</span><span style="color: {C["muted"]}; font-variant-numeric: tabular-nums">{n} personnes</span></div>' for t, n in [('Administrateurs', 3), ('Approbateurs', 14), ('Rédacteurs', 61), ('Lecteurs', 148)]) + tog('Un fil bloquant empêche la création d’une baseline', True) + tog('Double validation des résultats de validation', True))
body += '</div>'
files['Administration.dc.html'] = page('Administration.dc.html', 'Trace, administration du projet', body, 1180)

# ---------- 12. Discussions ----------
threads = [('ERS-IO-020', 'Question client', 'Le débordement doit-il aussi lever une interruption ?', 'Claire M.', 'il y a 12 min', 'planned', True), ('SDS-SYS-035', 'Bloquant', 'La séquence d’acquittement contredit FWS-SYS-010.', 'Hugo P.', 'il y a 2 h', 'failing', False),
           ('ERS-SYS-001', 'Proposition', 'Passer à 6 timers, conformément à la révision D.', 'Bertrand D.', 'hier', 'planned', False), ('ANS-ALIM-042', 'Question', 'Le courant de repos inclut-il le comparateur de réveil ?', 'Inès R.', 'hier', 'planned', False), ('VP-IO-001', 'Commentaire', 'Le covergroup cg_burst ne couvre pas les longueurs impaires.', 'Marc T.', '2 oct.', 'traced', False)]
tlist = ''.join(f'<a href="#" style="display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; border-top: 1px solid {C["rule"]}; text-decoration: none; color: {C["ink"]}; background: {C["req"] if act else "transparent"}"><span style="display: flex; gap: 8px; align-items: center">{rid(k, 13)}{badge(st, ty)}<span style="margin-left: auto; font-size: 12px; color: {C["muted"]}">{d}</span></span><span style="font-size: 14px">{t}</span><span style="font-size: 12px; color: {C["muted"]}">{w}</span></a>' for k, ty, t, w, d, st, act in threads)
filt = ''.join(f'<button type="button" aria-pressed="{"true" if i==0 else "false"}" style="font: 500 13px {SANS}; padding: 6px 12px; border-radius: 999px; border: 1px solid {C["accent"] if i==0 else C["rule"]}; background: {C["accent"] if i==0 else C["sheet"]}; color: {"#FFFFFF" if i==0 else C["ink"]}; cursor: pointer">{t} <span style="opacity: .8">{n}</span></button>' for i, (t, n) in enumerate([('Mes mentions', 3), ('Mes revues à faire', 5), ('Questions client', 2), ('Bloquants', 2), ('Tous les fils ouverts', 9)]))
msg = lambda who, when, txt, extra='': f'<div style="display: grid; grid-template-columns: 36px minmax(0, 1fr); gap: 12px; padding: 14px 0; border-top: 1px solid {C["rule"]}"><span style="width: 36px; height: 36px; border-radius: 50%; background: {C["req"]}; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; color: {C["ink"]}">{"".join(x[0] for x in who.split()[:2])}</span><div style="display: flex; flex-direction: column; gap: 6px"><span style="font-size: 14px"><strong style="font-weight: 600">{who}</strong> <span style="color: {C["muted"]}; font-size: 13px">{when}</span></span><span style="font-size: 15px; line-height: 23px">{txt}</span>{extra}</div></div>'
prop = f'<div style="border: 1px solid {C["rule"]}; border-radius: 6px; padding: 12px; display: flex; flex-direction: column; gap: 8px; background: {C["paper"]}"><span style="font-size: 12px; font-weight: 600; color: {C["muted"]}">Proposition de modification de l’énoncé</span><p style="margin: 0; font-family: {SERIF}; font-size: 15px; line-height: 24px">Les erreurs de parité, de trame et de débordement doivent être détectées {DEL("et signalées")} {INS(", signalées par interruption et comptées")}.</p><div style="display: flex; gap: 8px">{btn("Appliquer", True, small=True)}{btn("Refuser", small=True)}</div></div>'
thread = f'''<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap">{rid("ERS-IO-020", 20)}{badge("planned", "Question client")}<span style="font-size: 13px; color: {C["muted"]}">Sur le passage « et signalées » · version v3</span><div style="margin-left: auto; display: flex; gap: 8px">{btn("Exporter pour le client", small=True)}{btn("Résoudre", small=True)}</div></div>
<blockquote style="margin: 0; padding: 10px 14px; border-left: 3px solid {C["accent"]}; background: {C["req"]}; font-family: {SERIF}; font-size: 15px; line-height: 24px">Les erreurs de parité, de trame et de débordement doivent être détectées <mark style="background: rgba(47,79,181,.18); color: {C["ink"]}">et signalées</mark>.</blockquote>
{msg("Claire M.", "il y a 2 jours", "« Signalées » reste ambigu : interruption, bit de statut, ou les deux ? Le débordement doit-il aussi lever une interruption ? <a href='#'>@Bertrand</a>, peux-tu le poser au client ?")}
{msg("Bertrand D.", "hier", "Posé au client dans le lot de questions du 5 octobre. Réponse : interruption pour les trois erreurs, avec compteurs consultables par le logiciel.")}
{msg("Claire M.", "il y a 12 min", "Je propose de reformuler en conséquence.", prop)}
<label style="display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: {C["muted"]}">Répondre<textarea rows="3" placeholder="Votre réponse, @mention, citation d’exigence…" style="font: 15px/22px {SANS}; padding: 10px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["sheet"]}; color: {C["ink"]}; resize: vertical"></textarea></label>
<div style="display: flex; justify-content: flex-end; gap: 8px">{btn("Proposer une modification")}{btn("Envoyer", True)}</div>'''
body = title_row('Discussions', '9 fils ouverts sur le projet', '')
body += f'<div style="display: flex; gap: 8px; flex-wrap: wrap">{filt}</div>'
body += f'<div style="display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-start"><section aria-label="Fils" style="flex: 1 1 340px; max-width: 420px; background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px; overflow: hidden">{tlist}</section><section aria-label="Fil ouvert" style="flex: 999 1 520px; min-width: 0; background: {C["sheet"]}; border: 1px solid {C["rule"]}; border-radius: 6px; padding: 18px 22px; display: flex; flex-direction: column; gap: 12px">{thread}</section></div>'
files['Discussions.dc.html'] = page('Discussions.dc.html', 'Trace, discussions', body, 1120)

# ---------- Mobiles ----------
def mobile(title, inner, h=844):
    return f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{e(title)}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&amp;family=IBM+Plex+Serif:wght@400;600&amp;display=swap">
<style>
body{{margin:0}}
a{{color:{C["accent"]}}}a:hover{{color:#223C8C}}
</style>
</helmet>
<div style="width: 390px; height: {h}px; box-sizing: border-box; overflow: hidden; position: relative; background: {C["paper"]}; color: {C["ink"]}; font-family: {SANS}; font-size: 15px; line-height: 22px; display: flex; flex-direction: column">
<header style="display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: {C["sheet"]}; border-bottom: 1px solid {C["rule"]}"><button type="button" aria-label="Menu" style="width: 44px; height: 44px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["sheet"]}; cursor: pointer; display: flex; align-items: center; justify-content: center"><svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="{C["ink"]}" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M3 5h12M3 9h12M3 13h12"/></svg></button><span style="font-weight: 600; font-size: 17px">Trace</span><span style="font-size: 13px; color: {C["muted"]}">Sous-système d’E/S</span><button type="button" aria-label="Rechercher" style="margin-left: auto; width: 44px; height: 44px; border: 1px solid {C["rule"]}; border-radius: 6px; background: {C["sheet"]}; cursor: pointer; display: flex; align-items: center; justify-content: center">{ICON_SEARCH}</button></header>
{inner}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":390,"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>'''
m1 = f'''<div style="padding: 16px; display: flex; flex-direction: column; gap: 14px; overflow: hidden">
<h1 style="margin: 0; font-size: 22px; line-height: 28px; font-weight: 600">Tableau de bord</h1>
{card('Exigences client', f'<div style="display: flex; align-items: baseline; gap: 8px"><span style="font-size: 36px; line-height: 40px; font-weight: 600">{cnt["proven"]}</span><span style="color: {C["muted"]}">prouvées sur {len(ERS)}</span></div>' + segbar(cnt, len(ERS), 10) + legend(cnt), pad=16)}
{card('Par famille', ''.join(f'<div style="display: grid; grid-template-columns: 82px 1fr 52px; gap: 10px; align-items: center; font-size: 14px"><span>{n}</span>{segbar({"proven": FS[k][1], "planned": FS[k][2], "failing": FS[k][3], "traced": FS[k][4]}, FS[k][0], 8)}<span style="text-align: right; color: {C["muted"]}; font-variant-numeric: tabular-nums">{FS[k][1]}/{FS[k][0]}</span></div>' for k, n in [('DV', 'DV'), ('ANA', 'Analogique'), ('FW', 'FW'), ('VAL', 'Validation')]), pad=16)}
{card('Anomalies', f'<ul style="list-style: none; margin: -9px 0 0; padding: 0">' + ''.join(f'<li style="display: flex; justify-content: space-between; align-items: center; min-height: 44px; border-top: 1px solid {C["rule"]}"><a href="Mobile-Exigence.dc.html" style="display: flex; align-items: center; gap: 10px; color: {C["ink"]}; text-decoration: none; font-size: 14px">{dot(s)}{t}</a><span style="font-weight: 600">{n}</span></li>' for t, n, s in anoms[:5]) + '</ul>', pad=16)}
</div>'''
files['Mobile-Tableau.dc.html'] = mobile('Trace mobile, tableau de bord', m1)
m2 = f'''<div style="padding: 16px 16px 0; display: flex; flex-direction: column; gap: 4px; filter: saturate(.9)">
<div style="font-size: 13px; color: {C["muted"]}">ERS client · UART</div>
<div style="display: flex; align-items: center; gap: 8px; margin-top: 10px">{dot(IDX["ERS-IO-019"]["st"])}{rid("ERS-IO-019")}</div>
<p style="margin: 0 0 12px; font-family: {SERIF}; font-size: 16px; line-height: 26px">{e(IDX["ERS-IO-019"]["text"])}</p>
<div style="display: flex; align-items: center; gap: 8px">{dot("failing")}{rid("ERS-IO-020")}<span style="font-size: 11px; font-weight: 600; color: {C["accent"]}; background: {C["req"]}; border-radius: 4px; padding: 0 5px">2 fils</span></div>
<p style="margin: 0; font-family: {SERIF}; font-size: 16px; line-height: 26px; background: {C["req"]}; border-left: 2px solid {C["accent"]}; padding: 2px 10px">{e(r8["text"])}</p>
</div>
<div role="dialog" aria-label="Panneau de ERS-IO-020" style="position: absolute; left: 0; right: 0; bottom: 0; height: 560px; background: {C["sheet"]}; border-radius: 12px 12px 0 0; box-shadow: 0 -8px 28px rgba(28,34,48,.16); border-top: 1px solid {C["rule"]}; display: flex; flex-direction: column">
<div style="display: flex; justify-content: center; padding: 8px"><span style="width: 40px; height: 4px; border-radius: 2px; background: {C["rule"]}"></span></div>
<div style="padding: 0 16px 16px; display: flex; flex-direction: column; gap: 12px; overflow: hidden">
<div style="display: flex; align-items: baseline; gap: 8px">{rid("ERS-IO-020", 22)}<span style="font-size: 13px; color: {C["muted"]}">ERS client</span><button type="button" aria-label="Fermer le panneau" style="margin-left: auto; width: 44px; height: 44px; border: 0; background: transparent; font-size: 22px; color: {C["muted"]}; cursor: pointer">×</button></div>
{tabs('Traçabilité', ['Traçabilité', 'Vérification', 'Historique', 'Discussion'])}
<div style="background: {SB["failing"]}; border-left: 3px solid {C["danger"]}; border-radius: 0 6px 6px 0; padding: 10px 12px; display: flex; flex-direction: column; gap: 6px">{badge("failing")}<span style="font-size: 14px">Au moins une métrique est en échec dans les résultats du 4 octobre.</span></div>
<div style="display: flex; gap: 6px; flex-wrap: wrap">{''.join(fam(f, famst("ERS-IO-020", f), f in r8["req"]) for f in ["DV", "ANA", "FW", "VAL"])}</div>
{h3('Raffinée ou vérifiée par')}{''.join(f'<a href="#" style="display: flex; gap: 10px; align-items: center; min-height: 44px; border-top: 1px solid {C["rule"]}; text-decoration: none; font-size: 14px">{rid(k)}<span style="color: {C["muted"]}; flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{e(IDX[k]["text"])}</span>{dot(IDX[k]["st"])}</a>' for k in r8["kids"][:4])}
</div></div>'''
files['Mobile-Exigence.dc.html'] = mobile('Trace mobile, panneau d’une exigence', m2)

# ---------- canvas.json + ds ----------
# Disposition du canevas : 3 colonnes d'artboards de 1440 px, puis les deux écrans téléphone dessous.
# H : hauteur de chaque artboard (à ajuster si une vue s'allonge).
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
H = {'Main.dc.html': 1240, 'Document.dc.html': 1240, 'Panneau.dc.html': 1180, 'Explorateur.dc.html': 1000, 'Matrice.dc.html': 1960, 'Resultats.dc.html': 980, 'Anomalies.dc.html': 1500, 'Discussions.dc.html': 1120, 'Import.dc.html': 1260, 'Synchro.dc.html': 1180, 'Baselines.dc.html': 1080, 'Administration.dc.html': 1180}
TITLES = {'Main.dc.html': '1. Tableau de bord', 'Document.dc.html': '2. Document', 'Panneau.dc.html': '3. Panneau d’une exigence', 'Explorateur.dc.html': '4. Explorateur de traçabilité', 'Matrice.dc.html': '5. Matrice de couverture', 'Resultats.dc.html': '6. Résultats de vérification', 'Anomalies.dc.html': '7. Anomalies', 'Import.dc.html': '8. Import', 'Synchro.dc.html': '9. Synchronisation', 'Baselines.dc.html': '10. Baselines', 'Administration.dc.html': '11. Administration', 'Discussions.dc.html': '12. Discussions'}
order = list(TITLES)
boards, y, rowmax = {}, 0, 0
for i, f in enumerate(order):
    c = i % 3
    if c == 0 and i: y += rowmax + 120; rowmax = 0
    boards[f] = {'x': c * 1520, 'y': y, 'w': 1440, 'h': H[f], 'title': TITLES[f], 'expand': 'fill', 'is_interactive': True}
    rowmax = max(rowmax, H[f])
my = y + rowmax + 420
boards['Mobile-Tableau.dc.html'] = {'x': 0, 'y': my, 'w': 390, 'h': 844, 'title': 'Téléphone · tableau de bord', 'is_interactive': True}
boards['Mobile-Exigence.dc.html'] = {'x': 470, 'y': my, 'w': 390, 'h': 844, 'title': 'Téléphone · panneau d’une exigence', 'is_interactive': True}
order += ['Mobile-Tableau.dc.html', 'Mobile-Exigence.dc.html']
canvas = {'v': 3, 'createdOnFiles': {'v': 1, 'at': now}, 'title': 'Trace, maquettes des vues', 'launch': {'view': 'canvas'}, 'pages': [], 'boards': boards, 'order': order,
          'notes': {'desk': {'x': 0, 'y': -300, 'text': 'Poste de travail : les douze vues', 'kind': 'title1', 'maxW': 4400}, 'phone': {'x': 0, 'y': my - 300, 'text': 'Téléphone', 'kind': 'title1', 'maxW': 860}},
          'designSystems': [{'title': 'Trace', 'namespace': 'trace', 'artifact': 'https://claude.ai/artifact/WYKNughhFqUvRpwc1HURFo', 'version': None, 'copiedAt': now}]}
for f, s in files.items():
    open(f'{ROOT}/{f}', 'w').write(s.replace('@@NANOM@@', str(NANOM)))
json.dump(canvas, open(f'{ROOT}/canvas.json', 'w'), ensure_ascii=False, indent=1)
# Copie du design system à côté des maquettes : le canevas Claude Design le lit dans ds/<namespace>/.
import shutil; shutil.copy(os.path.join(HERE, '..', 'design-system', 'tokens.json'), f'{ROOT}/ds/trace/tokens.json')
print({k: len(v) for k, v in files.items()})
