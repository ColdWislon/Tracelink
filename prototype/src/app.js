/**
 * Trace — prototype d'édition traçable (point d'entrée du bundle).
 *
 * RÔLE
 *   Démontrer l'ergonomie visée par SPEC.md : un éditeur de type document (Tiptap)
 *   où chaque exigence est un bloc typé avec un ID, des liens amont, et un statut
 *   de preuve calculé en direct à partir de résultats de vérification fictifs.
 *   Ce fichier n'est PAS la base de code de l'application finale : SPEC.md demande
 *   de repartir de zéro (React + TypeScript + API + PostgreSQL). Il sert de
 *   référence pour les règles de statut et l'ergonomie.
 *
 * ARCHITECTURE (tout tient dans ce fichier, sans framework)
 *   seed.js ──seedDocs()──► state.json  { "NIVEAU|SOUS-SYSTÈME": JSON Tiptap }
 *                                │
 *          setDoc(L, S) charge UN document dans l'éditeur (jamais tout le SoC)
 *                                │
 *   index()  ── parcourt tous les documents ─► Map rid → entrée, + map.kids (liens inverses)
 *   statusOf() ── calcule le statut de chaque exigence (pire branche, mémoïsé)
 *   afterChange() ── repeint pastilles, onglets, panneau ; déclenche save()
 *
 * SECTIONS
 *   index · vérification (statuts) · nœuds Tiptap · diagrammes · état/persistance ·
 *   rendu (onglets, panneau) · barre d'outils · sélecteur de référence · événements · démarrage
 *
 * INVARIANTS À NE PAS CASSER
 *   - Un ID d'exigence est unique dans tout le projet (tous documents confondus).
 *     Le plugin appendTransaction du nœud Requirement réattribue tout ID vide,
 *     dupliqué dans le document, ou déjà utilisé dans un AUTRE document.
 *   - Les liens amont sont stockés uniquement côté enfant (attribut `satisfies`).
 *     « dérive de » et « satisfait » ne sont PAS deux attributs : le type de lien
 *     se déduit du préfixe (même préfixe = dérive de, sinon satisfait), cf. relLabel().
 *   - Les statuts ne sont jamais stockés : ils sont recalculés à chaque changement.
 *   - Règle de statut dupliquée dans outils/extraire_donnees.mjs : toute
 *     modification de evalMetric/planStatus/statusOf doit y être reportée.
 *
 * PIÈGES CONNUS
 *   - Changer le format JSON stocké => incrémenter KEY, sinon les navigateurs
 *     rechargent d'anciens documents incompatibles depuis localStorage.
 *   - Mermaid est chargé par CDN dans template.html (asynchrone) : renderDiagram()
 *     met les rendus en attente tant que window.mermaid n'existe pas.
 *     WaveDrom, lui, est bundlé (import npm).
 *   - Les performances à ~9 000 exigences reposent sur trois choix : un seul
 *     document dans l'éditeur, index recalculé seulement pour le document modifié
 *     (cache `entries`), statuts mémoïsés par passe de rendu (`memo`).
 */
import { Editor, Node, mergeAttributes } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import Placeholder from '@tiptap/extension-placeholder'
import { Plugin, EditorState } from '@tiptap/pm/state'
import { SESSIONS, seedDocs, SUB_LIST } from './seed.js'
import WaveDrom from 'wavedrom'

/* ---------- configuration des niveaux ----------
 * Un niveau = un type de document. `upstream` liste les niveaux qu'une exigence de ce
 * niveau a le droit de citer dans `satisfies` (le panneau ne propose que ceux-là).
 * `fam` n'existe que pour les plans de vérification : DV, ANA, FW ou VAL.
 * Dans l'application finale, cette table devient de la configuration par projet. */
const DOCS = [
  { key: 'ERS', label: 'ERS client', prefix: 'ERS', upstream: ['ERS'] },
  { key: 'SDS', label: 'SDS', prefix: 'SDS', upstream: ['ERS', 'SDS'] },
  { key: 'DDS', label: 'DDS', prefix: 'DDS', upstream: ['SDS', 'DDS'] },
  { key: 'ANS', label: 'Spéc. ANA', prefix: 'ANS', upstream: ['SDS', 'ANS'] },
  { key: 'FWS', label: 'Spéc. FW', prefix: 'FWS', upstream: ['SDS', 'FWS'] },
  { key: 'VP', label: 'vPlan DV', prefix: 'VP', upstream: ['DDS', 'SDS', 'ERS'], fam: 'DV' },
  { key: 'ANV', label: 'Plan ANA', prefix: 'ANV', upstream: ['ANS', 'SDS'], fam: 'ANA' },
  { key: 'FWT', label: 'Tests FW', prefix: 'FWT', upstream: ['FWS', 'SDS'], fam: 'FW' },
  { key: 'VAL', label: 'Validation', prefix: 'VAL', upstream: ['ERS', 'SDS'], fam: 'VAL' },
]
const FAMS = [['DV', 'DV'], ['ANA', 'Analogique'], ['FW', 'FW'], ['VAL', 'Validation']]
const FAM_LABEL = Object.fromEntries(FAMS)
// Types de métriques autorisés par famille. Une métrique est stockée « type:nom », ex. « test:uart_overflow_test ».
const KINDS = { DV: ['test', 'assert', 'cover'], ANA: ['spec', 'mc', 'model'], FW: ['utest', 'itest', 'codecov'], VAL: ['proc', 'mesure', 'demo'] }
const KIND = { spec: 'Performance', mc: 'Monte-Carlo', model: 'Corrélation', test: 'Test', assert: 'Assertion', cover: 'Couverture', utest: 'Test unitaire', itest: 'Test d’intégration', codecov: 'Couv. de code', proc: 'Procédure', mesure: 'Mesure', demo: 'Démonstration' }
const docOf = k => DOCS.find(d => d.key === k)
const famOf = k => docOf(k)?.fam
const isPlan = k => !!famOf(k)
// Clé localStorage. À incrémenter dès que le format des documents ou de l'état sauvegardé change.
const KEY = 'trace-proto-v7'
const $ = s => document.querySelector(s)
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))
const fr = n => String(n).replace('.', ',')
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches

// État global.
//   state   : { json: {clé document → JSON Tiptap}, edited: {clé → 1 si modifié}, cur: [niveau, sous-système], session }
//   curL/curS/curKey : niveau, sous-système et clé ("SDS|IO") du document ouvert dans l'éditeur
//   active  : ID de l'exigence sélectionnée (panneau en mode détail), ou null (vue d'ensemble)
let state, curL, curS, curKey, active = null
const SUBS = SUB_LIST
const dkey = (L, S) => L + '|' + S
// Caches de l'index.
//   entries    : clé document → liste d'entrées extraites ; seul le document courant est réextrait (collect)
//   idxCache   : dernier index complet ; invalidé par `dirty` à chaque frappe
//   otherIdSet : IDs présents dans les AUTRES documents, figé à l'ouverture d'un document (sert au contrôle d'unicité)
let entries = {}, idxCache = null, dirty = true, otherIdSet = new Set()

/* ---------- index ----------
 * Transforme les JSON Tiptap en une table d'exigences : Map rid → { rid, doc (niveau), sub,
 * dk (clé document), satisfies, metrics, goal, required, text, node }.
 * idx.kids : Map rid parent → entrées enfants (liens inverses), reconstruite à chaque index(). */
function textOf(n) {
  if (n.type === 'text') return n.text
  if (n.type === 'reqRef') return n.attrs.rid
  return (n.content || []).map(textOf).join(n.type === 'paragraph' ? '' : ' ')
}
function walk(json, doc, cb, sub, dk) {
  for (const n of json.content || []) {
    if (n.type === 'requirement') cb({ rid: n.attrs.rid, doc, sub, dk, satisfies: n.attrs.satisfies || [], metrics: n.attrs.metrics || [], goal: n.attrs.goal ?? 100, required: n.attrs.required || [], text: textOf(n).trim(), node: n })
    else if (n.content) walk(n, doc, cb, sub, dk)
  }
}
function collect(dk) { const [L, S] = dk.split('|'), out = []; walk(state.json[dk] || {}, L, x => out.push(x), S, dk); entries[dk] = out }
function index() {
  if (!dirty && idxCache) return idxCache
  syncCurrent()
  const m = new Map()
  for (const dk in state.json) { if (!entries[dk]) collect(dk); for (const x of entries[dk]) m.set(x.rid, x) }
  const kids = new Map()
  for (const r of m.values()) for (const p of r.satisfies) { if (!kids.has(p)) kids.set(p, []); kids.get(p).push(r) }
  m.kids = kids
  idxCache = m; dirty = false
  return m
}
const childrenOf = (rid, idx) => idx.kids.get(rid) || []
function descendants(rid, idx) {
  const out = [], seen = new Set([rid]), q = [rid]
  while (q.length) for (const c of childrenOf(q.shift(), idx)) if (!seen.has(c.rid)) { seen.add(c.rid); out.push(c); q.push(c.rid) }
  return out
}
const pre = rid => String(rid).split('-')[0]
const relLabel = (rid, parent) => (pre(rid) === pre(parent) ? 'dérive de' : 'satisfait')
function otherIds() { return otherIdSet }
// Prochain ID libre du document courant : « PRÉFIXE-SOUS-SYSTÈME-NNN », max + 1.
// Un ID n'est jamais réutilisé tant qu'il existe ; dans l'outil final, la règle « jamais réutilisé,
// même après suppression » sera garantie côté serveur par une séquence.
function nextId(pmDoc, seen) {
  const p = docOf(curL).prefix + '-' + curS
  let max = 0
  const consider = r => { const m = r && r.match(/^(.+)-(\d+)$/); if (m && m[1] === p) max = Math.max(max, +m[2]) }
  pmDoc.descendants(n => { if (n.type.name === 'requirement') consider(n.attrs.rid) })
  seen.forEach(consider)
  return p + '-' + String(max + 1).padStart(3, '0')
}

/* ---------- vérification : calcul des statuts ----------
 * C'est le cœur métier, à transposer fidèlement dans l'application finale (et à tester).
 * Ordre du pire au meilleur : untraced < traced < failing < planned < proven.
 *   - Item de plan (VP, ANV, FWT, VAL) : statut de ses métriques (planStatus).
 *   - Autre exigence : pire statut de ses enfants (« pire branche »), sans enfant => untraced.
 *   - Plans requis : si une famille requise n'a aucun item en aval => untraced, quel que soit le reste.
 * Le statut d'une métrique (evalMetric) vaut ok | fail | short | missing ; « short » et « missing »
 * rendent l'item « planned » (pas encore prouvé, mais pas en échec). */
const RANK = { untraced: 0, traced: 1, failing: 2, planned: 3, proven: 4 }
const LABEL = { untraced: 'Non tracée', traced: 'Tracée', failing: 'En échec', planned: 'Planifiée', proven: 'Prouvée' }
const worst = (a, b) => (RANK[a] <= RANK[b] ? a : b)
// Évalue une métrique contre la session de résultats sélectionnée (state.session).
// Seuils codés en dur ici (Cpk ≥ 1,33, écart modèle ≤ 2 %) : paramètres de projet dans l'outil final.
// Un résultat analogique « schéma » ne prouve rien quand le post-layout est exigé => short.
function evalMetric(m, goal) {
  const [kind, ...rest] = m.split(':'), name = rest.join(':')
  const r = SESSIONS[state.session]?.results[m]
  const base = { kind, name }
  if (!r) return { ...base, st: 'missing', txt: 'absent des résultats' }
  if (kind === 'test' || kind === 'utest' || kind === 'itest') return r.fail ? { ...base, st: 'fail', txt: `${r.fail} en échec sur ${r.pass + r.fail}` } : { ...base, st: 'ok', txt: `${r.pass} passés` }
  if (kind === 'assert') return r.ok ? { ...base, st: 'ok', txt: 'jamais violée, couverte' } : { ...base, st: 'fail', txt: 'violée' }
  if (kind === 'cover' || kind === 'codecov') return r.pct >= goal ? { ...base, st: 'ok', txt: `${r.pct} %` } : { ...base, st: 'short', txt: `${r.pct} % pour un objectif de ${goal} %` }
  if (kind === 'spec') return r.ok ? (r.view === 'schéma' ? { ...base, st: 'short', txt: `tient sur tous les coins, schéma seul (post-layout exigé)` } : { ...base, st: 'ok', txt: `marge ${r.margin} % au pire coin (${r.corner})` }) : { ...base, st: 'fail', txt: `hors limite de ${-r.margin} % au coin ${r.corner}` }
  if (kind === 'mc') return r.cpk >= 1.33 ? { ...base, st: 'ok', txt: `Cpk ${fr(r.cpk)} sur ${r.n} tirages` } : { ...base, st: 'short', txt: `Cpk ${fr(r.cpk)} pour un objectif de 1,33` }
  if (kind === 'model') return r.err <= 2 ? { ...base, st: 'ok', txt: `écart ${fr(r.err)} %` } : { ...base, st: 'fail', txt: `écart ${fr(r.err)} % pour 2 % maximum` }
  if (r.stale) return { ...base, st: 'short', txt: 'à rejouer, obtenu sur une version antérieure' }
  if (r.pending) return { ...base, st: 'short', txt: 'en attente de double validation' }
  if (kind === 'mesure') {
    const ok = r.val >= r.min && r.val <= r.max
    return { ...base, st: ok ? 'ok' : 'fail', txt: `${fr(r.val)} ${r.unit}, borne max ${r.max} ${r.unit}` }
  }
  return r.ok ? { ...base, st: 'ok', txt: kind === 'demo' ? 'démontrée' : 'réussie' } : { ...base, st: 'fail', txt: 'échouée' }
}
function planStatus(r) {
  if (!r.metrics.length) return 'traced'
  const ev = r.metrics.map(m => evalMetric(m, r.goal))
  if (ev.some(e => e.st === 'fail')) return 'failing'
  return ev.every(e => e.st === 'ok') ? 'proven' : 'planned'
}
const missingFams = (r, idx) => r.required.filter(f => !descendants(r.rid, idx).some(x => famOf(x.doc) === f))
// `memo` : cache par passe de rendu (créé dans afterChange) ; `stack` : protection contre un cycle
// éventuel dans les données (le prototype ne refuse pas encore les cycles à la saisie, l'outil final doit le faire).
function statusOf(rid, idx, memo = new Map(), stack = new Set()) {
  if (memo.has(rid)) return memo.get(rid)
  const r = idx.get(rid); if (!r) return 'untraced'
  let s
  if (isPlan(r.doc)) s = planStatus(r)
  else {
    const kids = childrenOf(rid, idx).filter(k => !stack.has(k.rid))
    stack.add(rid)
    s = kids.length ? kids.map(k => statusOf(k.rid, idx, memo, stack)).reduce(worst) : 'untraced'
    stack.delete(rid)
    if (missingFams(r, idx).length) s = 'untraced'
  }
  memo.set(rid, s); return s
}
// Statut le plus faible des items d'une famille en aval ; null si la famille n'a aucun item (pastilles DV/ANA/FW/VAL).
function famStatus(rid, fam, idx, memo) {
  const items = descendants(rid, idx).filter(x => famOf(x.doc) === fam)
  return items.length ? items.map(x => statusOf(x.rid, idx, memo)).reduce(worst) : null
}
const badge = s => `<span class="badge s-${s}">${LABEL[s]}</span>`

/* ---------- nœuds Tiptap ----------
 * Trois nœuds sur mesure :
 *   requirement : bloc d'exigence. Attributs rid, satisfies[], metrics[], required[], goal.
 *                 Contenu : paragraphes, listes, diagrammes (pas d'exigence imbriquée).
 *                 La « gouttière » (ID + liens amont) est rendue hors du contenu éditable.
 *   reqRef      : citation en ligne d'une autre exigence par son ID (barrée si la cible disparaît).
 *   diagram     : bloc atomique WaveDrom ou Mermaid ; seule la source texte est stockée. */
const listAttr = (name, data) => ({
  default: [],
  parseHTML: e => (e.getAttribute(data) || '').split(',').map(s => s.trim()).filter(Boolean),
  renderHTML: a => ({ [data]: (a[name] || []).join(',') }),
})
const Requirement = Node.create({
  name: 'requirement', group: 'block', content: '(paragraph|bulletList|orderedList|diagram)+', defining: true, isolating: true,
  addAttributes() {
    return {
      rid: { default: null, parseHTML: e => e.getAttribute('data-rid') || null, renderHTML: a => ({ 'data-rid': a.rid }) },
      satisfies: listAttr('satisfies', 'data-sat'),
      metrics: listAttr('metrics', 'data-metrics'),
      required: listAttr('required', 'data-required'),
      goal: { default: 100, parseHTML: e => +(e.getAttribute('data-goal') || 100), renderHTML: a => ({ 'data-goal': a.goal }) },
    }
  },
  parseHTML() { return [{ tag: 'div[data-type="requirement"]' }] },
  renderHTML({ HTMLAttributes }) { return ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'requirement' }), 0] },
  addNodeView() {
    return ({ node }) => {
      const dom = document.createElement('div'); dom.className = 'req'
      const gut = document.createElement('div'); gut.className = 'req-gutter'; gut.contentEditable = 'false'
      const id = document.createElement('button'); id.type = 'button'; id.className = 'req-id'
      const sat = document.createElement('span'); sat.className = 'req-sat'
      gut.append(id, sat)
      const body = document.createElement('div'); body.className = 'req-body'
      dom.append(gut, body)
      let rid
      const paint = n => {
        rid = n.attrs.rid; dom.dataset.rid = rid || ''
        id.textContent = rid || '…'
        const s = n.attrs.satisfies || []
        const der = s.filter(p => pre(p) === pre(rid)), sats = s.filter(p => pre(p) !== pre(rid))
        sat.textContent = [der.length ? 'dérive de ' + der.join(', ') : '', sats.length ? 'satisfait ' + sats.join(', ') : ''].filter(Boolean).join('\n') || (curL === 'ERS' ? '' : 'sans lien amont')
        sat.classList.toggle('none', !s.length && curL !== 'ERS')
        dom.classList.toggle('is-active', rid === active)
      }
      paint(node)
      id.addEventListener('click', () => { active = rid; openPanel(); afterChange() })
      return {
        dom, contentDOM: body,
        update: n => { if (n.type.name !== 'requirement') return false; paint(n); return true },
        stopEvent: e => gut.contains(e.target),
        ignoreMutation: m => gut.contains(m.target) || (m.type === 'attributes' && m.target === dom),
      }
    }
  },
  // Garantit l'unicité des IDs après chaque transaction : collage d'une exigence copiée,
  // nouvelle exigence (rid null), ou ID déjà pris dans un autre document => nouvel ID.
  addProseMirrorPlugins() {
    return [new Plugin({
      appendTransaction(trs, _old, st) {
        if (!trs.some(t => t.docChanged)) return null
        const seen = new Set(), ext = otherIds()
        let tr = null
        st.doc.descendants((n, pos) => {
          if (n.type.name !== 'requirement') return
          let r = n.attrs.rid
          if (!r || seen.has(r) || ext.has(r)) {
            r = nextId(st.doc, seen)
            tr = tr || st.tr
            tr.setNodeMarkup(pos, undefined, { ...n.attrs, rid: r })
          }
          seen.add(r)
          return false
        })
        return tr
      },
    })]
  },
})

/* ---------- diagrammes décrits en texte ----------
 * Choix de SPEC.md : dans le contenu contractuel, privilégier des diagrammes dont la source est du
 * texte (diff lisible, baseline exacte). Le rendu est fait à l'affichage et n'est jamais stocké.
 * Mermaid tourne en securityLevel 'strict'. Dans l'outil final, le rendu des exports se fait côté serveur. */
const DG = {
  wavedrom: { label: 'Chronogramme WaveDrom', def: '{"signal": [\n {"name": "clk", "wave": "p......"},\n {"name": "req", "wave": "0.1..0."},\n {"name": "ack", "wave": "0..1.0."}\n]}' },
  mermaid: { label: 'Diagramme Mermaid', def: 'stateDiagram-v2\n  [*] --> IDLE\n  IDLE --> ACTIVE: start\n  ACTIVE --> IDLE: done' },
}
let dgSeq = 0, openNextDiagram = false
const mermaidWaiters = new Set()
function mermaidReady() {
  if (!window.mermaid || window.__mmdInit) return !!window.mermaid
  const dark = matchMedia('(prefers-color-scheme: dark)').matches
  window.mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: dark ? 'dark' : 'neutral', fontFamily: 'IBM Plex Sans, system-ui, sans-serif' })
  window.__mmdInit = true
  return true
}
const flushMermaid = () => { mermaidWaiters.forEach(f => f()); mermaidWaiters.clear() }
document.getElementById('mmd-js')?.addEventListener('load', flushMermaid)
// WaveDrom accepte un JSON « relâché » (clés sans guillemets, quotes simples, virgules finales) : on tente
// d'abord JSON.parse, puis une normalisation minimale.
function parseWave(src) {
  try { return JSON.parse(src) } catch (e) {}
  return JSON.parse(src.replace(/'/g, '"').replace(/([{,]\s*)([A-Za-z_]\w*)\s*:/g, '$1"$2":').replace(/,(\s*[}\]])/g, '$1'))
}
async function renderDiagram(lang, src, el) {
  const id = 'dg' + (++dgSeq)
  try {
    if (lang === 'wavedrom') {
      el.innerHTML = WaveDrom.onml.stringify(WaveDrom.renderAny(dgSeq, parseWave(src), WaveDrom.waveSkin))
    } else {
      if (!mermaidReady()) { el.innerHTML = '<p class="dg-msg">Chargement du moteur de diagrammes…</p>'; mermaidWaiters.add(() => renderDiagram(lang, src, el)); return }
      await window.mermaid.parse(src)
      const { svg } = await window.mermaid.render(id, src)
      el.innerHTML = svg
    }
  } catch (e) {
    document.getElementById('d' + id)?.remove()
    el.innerHTML = `<p class="dg-msg dg-err">Syntaxe invalide : ${esc(String(e.message || e).split('\n')[0].slice(0, 160))}</p>`
  }
}
const Diagram = Node.create({
  name: 'diagram', group: 'block', atom: true, selectable: true,
  addAttributes() {
    return {
      lang: { default: 'mermaid', parseHTML: e => e.getAttribute('data-lang') || 'mermaid', renderHTML: a => ({ 'data-lang': a.lang }) },
      src: { default: '', parseHTML: e => e.textContent, renderHTML: () => ({}) },
    }
  },
  parseHTML() { return [{ tag: 'pre[data-diagram]' }] },
  renderHTML({ node, HTMLAttributes }) { return ['pre', mergeAttributes(HTMLAttributes, { 'data-diagram': '' }), node.attrs.src] },
  addNodeView() {
    return ({ node, getPos, editor: ed }) => {
      let cur = node, t
      const dom = document.createElement('div'); dom.className = 'diagram'; dom.contentEditable = 'false'
      const bar = document.createElement('div'); bar.className = 'dg-bar'
      const lab = document.createElement('span'); lab.className = 'dg-label'
      const btn = document.createElement('button'); btn.type = 'button'; btn.className = 'dg-btn'
      bar.append(lab, btn)
      const view = document.createElement('div'); view.className = 'dg-render'
      const ta = document.createElement('textarea'); ta.className = 'dg-code'; ta.spellcheck = false; ta.setAttribute('aria-label', 'Code du diagramme')
      dom.append(bar, view, ta)
      const setOpen = o => { dom.classList.toggle('editing', o); btn.textContent = o ? 'Fermer le code' : 'Modifier le code'; if (o) { ta.value = cur.attrs.src; ta.focus() } }
      const paint = () => { lab.textContent = (DG[cur.attrs.lang] || DG.mermaid).label; renderDiagram(cur.attrs.lang, cur.attrs.src, view) }
      btn.addEventListener('click', () => setOpen(!dom.classList.contains('editing')))
      ta.addEventListener('input', () => {
        clearTimeout(t)
        t = setTimeout(() => { const pos = getPos(); if (typeof pos === 'number') ed.view.dispatch(ed.state.tr.setNodeMarkup(pos, undefined, { ...cur.attrs, src: ta.value })) }, 350)
      })
      paint(); setOpen(openNextDiagram); openNextDiagram = false
      return {
        dom,
        update: n => { if (n.type.name !== 'diagram') return false; const changed = n.attrs.src !== cur.attrs.src || n.attrs.lang !== cur.attrs.lang; cur = n; if (changed) { if (document.activeElement !== ta) ta.value = n.attrs.src; paint() } return true },
        stopEvent: e => e.target === ta || e.target === btn,
        ignoreMutation: () => true,
        selectNode: () => dom.classList.add('selected'),
        deselectNode: () => dom.classList.remove('selected'),
      }
    }
  },
})

const ReqRef = Node.create({
  name: 'reqRef', group: 'inline', inline: true, atom: true, selectable: true,
  addAttributes() { return { rid: { default: null, parseHTML: e => e.getAttribute('data-ref'), renderHTML: a => ({ 'data-ref': a.rid }) } } },
  parseHTML() { return [{ tag: 'span[data-ref]' }] },
  renderHTML({ node, HTMLAttributes }) { return ['span', mergeAttributes(HTMLAttributes, { class: 'ref' }), node.attrs.rid] },
  renderText({ node }) { return node.attrs.rid },
})

const extensions = [
  StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
  Table.configure({ resizable: false }), TableRow, TableHeader, TableCell,
  Placeholder.configure({ includeChildren: true, showOnlyCurrent: false, placeholder: 'Énoncé de l’exigence' }),
  Requirement, ReqRef, Diagram,
]

/* ---------- état et persistance ----------
 * Les documents de démo sont régénérés à l'identique depuis seed.js à chaque chargement (générateur
 * déterministe) ; seuls les documents MODIFIÉS (state.edited) sont sauvegardés dans localStorage,
 * pour rester sous le quota du navigateur avec ~9 000 exigences. */
const seedState = () => ({ json: seedDocs(), edited: {}, cur: ['ERS', 'IO'], session: 'n1004' })
function load() {
  const s = seedState()
  try { const saved = JSON.parse(localStorage.getItem(KEY)); if (saved) { Object.entries(saved.docs || {}).forEach(([k, v]) => { if (s.json[k]) { s.json[k] = v; s.edited[k] = 1 } }); if (saved.cur) s.cur = saved.cur; if (saved.session) s.session = saved.session } } catch (e) {}
  return s
}
let saveT
function save() {
  clearTimeout(saveT)
  saveT = setTimeout(() => { try { const docs = {}; Object.keys(state.edited).forEach(k => { docs[k] = state.json[k] }); localStorage.setItem(KEY, JSON.stringify({ docs, cur: [curL, curS], session: state.session })) } catch (e) {} }, 600)
}

const editor = new Editor({ element: $('#doc'), extensions, content: '' })
// Recopie le contenu de l'éditeur dans state.json et réindexe ce seul document (appelé par index()).
function syncCurrent() { if (curKey && dirty) { state.json[curKey] = editor.getJSON(); collect(curKey) } }

// Ouvre le document (niveau L, sous-système S). On remplace l'EditorState entier (et non setContent)
// pour repartir d'un historique d'annulation vide propre à ce document.
function setDoc(L, S) {
  index()
  curL = L; curS = S || curS; curKey = dkey(curL, curS)
  otherIdSet = new Set([...idxCache.keys()].filter(id => idxCache.get(id).dk !== curKey))
  const st = EditorState.create({ schema: editor.schema, doc: editor.schema.nodeFromJSON(state.json[curKey]), plugins: editor.state.plugins })
  editor.view.updateState(st)
  $('#doc-scroll').scrollTop = 0
  afterChange()
}
function findPos(rid) {
  let p = null
  editor.state.doc.descendants((n, pos) => {
    if (p !== null) return false
    if (n.type.name === 'requirement' && n.attrs.rid === rid) { p = pos; return false }
  })
  return p
}
function setAttrs(rid, attrs) {
  const pos = findPos(rid); if (pos === null) return
  const n = editor.state.doc.nodeAt(pos)
  editor.view.dispatch(editor.state.tr.setNodeMarkup(pos, undefined, { ...n.attrs, ...attrs }))
}
function goto(rid) {
  const r = index().get(rid); if (!r) return
  if (r.dk !== curKey) setDoc(r.doc, r.sub)
  active = rid
  const pos = findPos(rid)
  if (pos !== null) {
    const el = editor.view.nodeDOM(pos)
    if (el && el.scrollIntoView) el.scrollIntoView({ block: 'center', behavior: reduceMotion ? 'auto' : 'smooth' })
  }
  afterChange()
}
function reqAtSelection() {
  const sel = editor.state.selection
  if (sel.node && sel.node.type.name === 'requirement') return sel.node.attrs.rid
  const $f = sel.$from
  for (let d = $f.depth; d > 0; d--) if ($f.node(d).type.name === 'requirement') return $f.node(d).attrs.rid
  return null
}

/* ---------- rendu ----------
 * afterChange() est l'unique point de rafraîchissement : appelé (avec anti-rebond de 150 ms) après
 * chaque frappe, et directement après chaque action du panneau. Il ne reconstruit pas l'éditeur :
 * il pose data-status sur les blocs .req (le CSS dessine la pastille) et régénère le panneau en HTML. */
let renderT
function afterChange() {
  const idx = index(), memo = new Map()
  if (active && !idx.has(active)) active = null
  editor.view.dom.querySelectorAll('.req').forEach(el => {
    el.classList.toggle('is-active', el.dataset.rid === active)
    if (idx.has(el.dataset.rid)) { const st = statusOf(el.dataset.rid, idx, memo); el.dataset.status = st; el.querySelector('.req-id').title = LABEL[st] }
  })
  editor.view.dom.querySelectorAll('[data-ref]').forEach(el => el.classList.toggle('broken', !idx.has(el.dataset.ref)))
  renderTabs(idx); renderPanel(idx, memo); renderToolbar(); save()
}

let tabsKey = ''
function renderTabs(idx) {
  const k = curKey + idx.size
  if (k === tabsKey) return
  tabsKey = k
  const counts = {}, subCount = {}
  for (const r of idx.values()) { if (r.sub === curS) counts[r.doc] = (counts[r.doc] || 0) + 1; subCount[r.sub] = (subCount[r.sub] || 0) + 1 }
  $('#tabs').innerHTML = DOCS.map(d => `<button type="button" role="tab" aria-selected="${d.key === curL}" data-doc="${d.key}">${d.label}<span class="count">${counts[d.key] || 0}</span></button>`).join('')
  $('#subsel').innerHTML = SUBS.map(s => `<option value="${s.code}"${s.code === curS ? ' selected' : ''}>${esc(s.nom)} (${subCount[s.code] || 0})</option>`).join('')
  $('#total').textContent = `SoC complet, ${idx.size.toLocaleString('fr-FR')} exigences`
}

const row = (r, extra = '') => `<li class="row"><button type="button" class="row-main" data-goto="${esc(r.rid)}"><span class="rid">${esc(r.rid)}</span><span class="txt">${esc(r.text || 'Énoncé vide')}</span></button>${extra}</li>`

function upSection(r, parents, editable, cands) {
  const unlink = p => editable ? `<button type="button" class="x" data-unlink="${esc(p.rid)}" aria-label="Retirer le lien vers ${esc(p.rid)}">×</button>` : ''
  const der = parents.filter(p => pre(p.rid) === pre(r.rid)), sats = parents.filter(p => pre(p.rid) !== pre(r.rid))
  let h = ''
  if (der.length) h += `<h3>Dérive de</h3><ul class="rows">${der.map(p => row(p, unlink(p))).join('')}</ul>`
  if (sats.length) h += `<h3>Satisfait</h3><ul class="rows">${sats.map(p => row(p, unlink(p))).join('')}</ul>`
  if (!parents.length) h += `<h3>Liens amont</h3>` + (r.doc === 'ERS' ? `<p class="p-note">Exigence racine</p>` : `<p class="p-note gap-text">Aucun lien amont</p>`)
  if (editable && cands.length) h += `<div class="add"><label class="sr" for="add-sel">Exigence amont</label><select id="add-sel">${cands.map(c => `<option value="${esc(c.rid)}">${relLabel(r.rid, c.rid)} ${esc(c.rid)}, ${esc(c.text.slice(0, 40))}</option>`).join('')}</select><button type="button" class="btn" data-act="link">Lier</button></div>`
  return h
}
function ersTree(ers) {
  const set = new Set(ers.map(x => x.rid)), out = [], seen = new Set()
  const visit = (x, d) => { if (seen.has(x.rid)) return; seen.add(x.rid); out.push([x, d]); ers.filter(c => c.satisfies.includes(x.rid)).forEach(c => visit(c, d + 1)) }
  ers.filter(x => !x.satisfies.some(p => set.has(p))).forEach(x => visit(x, 0))
  ers.forEach(x => visit(x, 0))
  return out
}
const famDots = (rid, idx, memo, req) => `<span class="fams">${FAMS.map(([f, l]) => {
  const s = famStatus(rid, f, idx, memo), need = req.includes(f)
  return `<span class="fam ${s ? 's-' + s : need ? 'need' : 'none'}" title="${l} : ${s ? LABEL[s] : need ? 'requis, aucun item' : 'aucun item'}">${f}</span>`
}).join('')}</span>`

// Panneau de droite, deux modes :
//   active == null : vue d'ensemble (couverture par sous-système, matrice ERS du sous-système, familles)
//   active == rid  : détail d'une exigence (statut et raison, liens amont/aval, métriques si item de plan)
// Les actions sont des data-attributes (data-goto, data-unlink, data-act…) gérés par délégation plus bas.
function renderPanel(idx, memo) {
  const body = $('#panel-body'), summary = $('#panel-summary')
  const st = rid => statusOf(rid, idx, memo)
  const ses = SESSIONS[state.session]
  const sessionSel = `<label class="ses"><span>Résultats</span><select id="ses-sel">${Object.entries(SESSIONS).map(([k, v]) => `<option value="${k}"${k === state.session ? ' selected' : ''}>${v.label.replace('Résultats du ', '')}</option>`).join('')}</select></label>`
  const allErs = [...idx.values()].filter(x => x.doc === 'ERS')
  const ers = allErs.filter(x => x.sub === curS)
  const proven = allErs.filter(x => st(x.rid) === 'proven').length
  const subName = (SUBS.find(s => s.code === curS) || {}).nom || ''
  if (!active) {
    summary.textContent = `Exigences client prouvées : ${proven} sur ${allErs.length}`
    const subRows = SUBS.map(s => { const se = allErs.filter(x => x.sub === s.code), c = k => se.filter(x => st(x.rid) === k).length; return `<tr class="${s.code === curS ? 'cur' : ''}"><th scope="row"><button type="button" class="sub-link" data-sub="${s.code}">${esc(s.nom)}</button></th><td>${se.length}</td><td class="c-ok">${c('proven')}</td><td class="c-fail">${c('failing')}</td><td class="c-gap">${c('untraced')}</td></tr>` }).join('')
    const counts = Object.keys(RANK).reverse().map(k => [k, ers.filter(x => st(x.rid) === k).length]).filter(([, n]) => n)
    const famRows = FAMS.map(([f, l]) => {
      const items = [...idx.values()].filter(x => famOf(x.doc) === f), by = k => items.filter(x => st(x.rid) === k).length
      return `<tr><th scope="row">${l}</th><td>${items.length}</td><td class="c-ok">${by('proven')}</td><td class="c-pl">${by('planned')}</td><td class="c-fail">${by('failing')}</td><td class="c-tr">${by('traced')}</td></tr>`
    }).join('')
    const orphans = [...idx.values()].filter(x => x.sub === curS && x.doc !== 'ERS' && !x.satisfies.length)
    body.innerHTML = `
      ${sessionSel}
      <p class="ses-ids">DV ${esc(ses.ids.DV)}<br>${esc(ses.ids.ANA)}<br>FW ${esc(ses.ids.FW)}<br>${esc(ses.ids.VAL)}</p>
      <h2 class="p-title">Couverture par sous-système</h2>
      <div class="tbl"><table class="fam-tbl sub-tbl"><thead><tr><th></th><th>ERS</th><th>Prouvées</th><th>En échec</th><th>Non tracées</th></tr></thead><tbody>${subRows}</tbody></table></div>
      <h2 class="p-title" style="margin-top:1.4rem">${esc(subName)}</h2>
      <p class="meter" aria-hidden="true">${ers.map(x => `<span class="s-${st(x.rid)}"></span>`).join('')}</p>
      <p class="counts">${counts.map(([k, n]) => `<span><i class="dot s-${k}"></i>${n} ${LABEL[k].toLowerCase()}${n > 1 && k !== 'failing' ? 's' : ''}</span>`).join('')}</p>
      <ul class="matrix">${ersTree(ers).map(([x, depth]) => {
        const s = st(x.rid)
        return `<li style="--depth:${depth}"><button type="button" data-goto="${esc(x.rid)}"><span class="dot s-${s}" aria-hidden="true"></span><span class="rid">${esc(x.rid)}</span><span class="m-txt">${esc(x.text)}</span>${famDots(x.rid, idx, memo, x.required)}</button></li>`
      }).join('')}</ul>
      <p class="p-note">Pastilles DV, ANA, FW et VAL : statut le plus faible des items de chaque famille en aval. Cadre pointillé : famille requise sans aucun item.</p>
      <h3>Items de vérification par famille</h3>
      <div class="tbl"><table class="fam-tbl"><thead><tr><th></th><th>Items</th><th>Prouvés</th><th>Planifiés</th><th>En échec</th><th>Sans métrique</th></tr></thead><tbody>${famRows}</tbody></table></div>
      ${orphans.length ? `<h3>Sans lien amont</h3><ul class="rows">${orphans.slice(0, 12).map(r => row(r)).join('')}</ul>` : ''}
      <p class="p-hint">Placez le curseur dans une exigence pour voir sa chaîne de traçabilité.</p>`
    return
  }
  const r = idx.get(active), d = docOf(r.doc), editable = r.dk === curKey, s = st(r.rid), fam = d.fam
  const parents = r.satisfies.map(p => idx.get(p) || { rid: p, text: 'Exigence introuvable', missing: true })
  const kids = childrenOf(r.rid, idx)
  const below = new Set([r.rid, ...descendants(r.rid, idx).map(x => x.rid)])
  const cands = [...idx.values()].filter(x => x.sub === r.sub && d.upstream.includes(x.doc) && !r.satisfies.includes(x.rid) && !below.has(x.rid))
  summary.textContent = `${r.rid}, ${LABEL[s].toLowerCase()}`
  let verif = ''
  if (fam) {
    const ev = r.metrics.map(m => ({ m, ...evalMetric(m, r.goal) }))
    verif = `<h3>Métriques</h3>
      ${ev.length ? `<ul class="metrics">${ev.map(e => `<li class="mt-${e.st}"><span class="mk">${KIND[e.kind] || e.kind}</span><span class="mn">${esc(e.name)}</span><span class="mr">${esc(e.txt)}</span>${editable ? `<button type="button" class="x" data-unmetric="${esc(e.m)}" aria-label="Retirer ${esc(e.name)}">×</button>` : ''}</li>`).join('')}</ul>`
        : `<p class="p-note gap-text">Aucune métrique : l’item est tracé mais rien ne le prouve encore.</p>`}
      ${editable ? `<div class="add add-metric"><label class="sr" for="mk-sel">Type</label><select id="mk-sel">${KINDS[fam].map(k => `<option value="${k}">${KIND[k]}</option>`).join('')}</select><label class="sr" for="mn-in">Nom</label><input id="mn-in" placeholder="nom de la métrique" autocomplete="off"><button type="button" class="btn" data-act="metric">Ajouter</button></div>
      ${fam !== 'VAL' && fam !== 'ANA' ? `<label class="goal">Objectif de couverture <input id="goal-in" type="number" min="1" max="100" value="${r.goal}"> %</label>` : ''}` : ''}
      <p class="p-note">Source : ${esc(ses.ids[fam])}.</p>`
  } else {
    const miss = missingFams(r, idx)
    const weak = kids.filter(k => st(k.rid) === s && s !== 'proven')
    const why = {
      proven: `Toutes les branches sont prouvées, ${esc(ses.label.toLowerCase())}.`,
      planned: `Les métriques existent mais n’atteignent pas toutes leur objectif, ou des résultats attendent une validation.`,
      failing: `Au moins une métrique est en échec, ${esc(ses.label.toLowerCase())}.`,
      traced: `Une branche atteint un plan de vérification, mais sans métrique associée.`,
      untraced: miss.length ? `Plan requis sans aucun item : ${miss.map(f => FAM_LABEL[f]).join(', ')}.` : kids.length ? `Une branche s’arrête avant les plans de vérification.` : `Aucune exigence dérivée.`,
    }[s]
    const famGrid = FAMS.map(([f, l]) => { const fs = famStatus(r.rid, f, idx, memo); return `<div class="fg"><span class="fg-l">${l}${r.required.includes(f) ? ' <em>requis</em>' : ''}</span>${fs ? badge(fs) : `<span class="p-note">${r.required.includes(f) ? '<span class="gap-text">aucun item</span>' : 'aucun item'}</span>`}</div>` }).join('')
    const reqCtl = (r.doc === 'ERS' || r.doc === 'SDS') ? `<h3>Plans requis</h3><div class="chips">${FAMS.map(([f, l]) => `<button type="button" class="chip" aria-pressed="${r.required.includes(f)}" data-req="${f}"${editable ? '' : ' disabled'}>${l}</button>`).join('')}</div>` : ''
    verif = `<div class="status s-${s}">${badge(s)}<span>${why}</span></div>
      ${weak.length ? `<p class="p-note">Branche à traiter : ${weak.slice(0, 6).map(w => `<button type="button" class="inl" data-goto="${esc(w.rid)}">${esc(w.rid)}</button>`).join(', ')}</p>` : ''}
      <div class="famgrid">${famGrid}</div>${reqCtl}`
  }
  const nodeJson = JSON.stringify({ type: 'requirement', attrs: r.node.attrs, text: r.text }, null, 2)
  const kd = k => row(k, `<span class="dot s-${st(k.rid)}" title="${LABEL[st(k.rid)]}"></span>`)
  const dk = kids.filter(k => k.doc === r.doc), ok = kids.filter(k => k.doc !== r.doc)
  body.innerHTML = `
    <div class="d-head"><span class="d-id">${esc(r.rid)}</span><span class="d-doc">${esc(d.label)}</span>${fam ? badge(s) : ''}</div>
    <p class="d-text">${esc(r.text || 'Énoncé vide')}</p>
    ${!fam ? verif : ''}
    ${!editable ? `<button type="button" class="btn" data-goto="${esc(r.rid)}">Ouvrir dans ${esc(d.label)}</button>` : ''}
    ${upSection(r, parents, editable, cands)}
    ${fam ? verif : (dk.length ? `<h3>Exigences dérivées</h3><ul class="rows">${dk.map(kd).join('')}</ul>` : '')
      + `<h3>Raffinée ou vérifiée par</h3>` + (ok.length ? `<ul class="rows">${ok.map(kd).join('')}</ul>` : `<p class="p-note">Rien en aval pour l’instant</p>`)}
    <details><summary>Ce qui est stocké</summary><pre>${esc(nodeJson)}</pre></details>
    <button type="button" class="link" data-act="overview">Revenir à la couverture</button>`
}

// Barre d'outils : [commande, état actif ?, action]. Les boutons sont déclarés dans template.html (data-cmd).
const TB = [
  ['h1', () => editor.isActive('heading', { level: 1 }), c => c.toggleHeading({ level: 1 })],
  ['h2', () => editor.isActive('heading', { level: 2 }), c => c.toggleHeading({ level: 2 })],
  ['bold', () => editor.isActive('bold'), c => c.toggleBold()],
  ['italic', () => editor.isActive('italic'), c => c.toggleItalic()],
  ['list', () => editor.isActive('bulletList'), c => c.toggleBulletList()],
  ['table', () => editor.isActive('table'), c => c.insertTable({ rows: 3, cols: 3, withHeaderRow: true })],
]
function renderToolbar() {
  for (const [k, isOn] of TB) { const b = document.querySelector(`[data-cmd="${k}"]`); if (b) b.setAttribute('aria-pressed', isOn() ? 'true' : 'false') }
  const u = $('[data-cmd="undo"]'), rd = $('[data-cmd="redo"]')
  if (u) u.disabled = !editor.can().undo()
  if (rd) rd.disabled = !editor.can().redo()
}
// Insère une exigence vide (rid null => ID attribué par le plugin) après le bloc courant,
// ou à la place d'un paragraphe vide pour ne pas laisser de ligne blanche.
function insertRequirement() {
  const node = { type: 'requirement', attrs: { rid: null, satisfies: [], metrics: [], required: [], goal: curL === 'FWT' ? 85 : 100 }, content: [{ type: 'paragraph' }] }
  const $f = editor.state.selection.$from
  if ($f.depth < 1) { editor.chain().focus().insertContent(node).run(); return }
  const top = $f.node(1)
  if (top.type.name === 'paragraph' && top.content.size === 0) {
    const from = $f.before(1)
    editor.chain().focus().insertContentAt({ from, to: $f.after(1) }, node).setTextSelection(from + 2).run()
  } else {
    const p = $f.after(1)
    editor.chain().focus().insertContentAt(p, node).setTextSelection(p + 2).run()
  }
}

/* ---------- sélecteur de référence (bouton « Citer ») ----------
 * Dialogue natif <dialog> ; la position du curseur est mémorisée avant ouverture car le focus part dans la recherche. */
let savedPos = 0
function openPicker() {
  savedPos = editor.state.selection.from
  const dlg = $('#picker'); $('#pick-q').value = ''; fillPicker('')
  dlg.showModal(); $('#pick-q').focus()
}
function fillPicker(q) {
  q = q.toLowerCase()
  const items = [...index().values()].filter(x => !q || x.rid.toLowerCase().includes(q) || x.text.toLowerCase().includes(q)).slice(0, 80)
  $('#pick-list').innerHTML = items.length
    ? items.map(x => `<li><button type="button" data-pick="${esc(x.rid)}"><span class="rid">${esc(x.rid)}</span><span class="txt">${esc(x.text)}</span></button></li>`).join('')
    : `<li class="p-note">Aucune exigence ne correspond à « ${esc(q)} »</li>`
}

const panel = $('#panel')
function openPanel() { panel.classList.add('open'); $('#panel-toggle').setAttribute('aria-expanded', 'true') }

/* ---------- événements ----------
 * Toute modification d'attribut passe par setAttrs() => transaction Tiptap => annulable (Ctrl+Z). */
editor.on('update', () => { dirty = true; if (curKey) state.edited[curKey] = 1; clearTimeout(renderT); renderT = setTimeout(afterChange, 150) })
editor.on('selectionUpdate', () => {
  const r = reqAtSelection()
  if (r && r !== active) { active = r; afterChange() } else renderToolbar()
})
$('#tabs').addEventListener('click', e => { const b = e.target.closest('[data-doc]'); if (b && b.dataset.doc !== curL) setDoc(b.dataset.doc, curS) })
$('#subsel').addEventListener('change', e => { active = null; setDoc(curL, e.target.value) })
$('#toolbar').addEventListener('click', e => {
  const b = e.target.closest('[data-cmd]'); if (!b) return
  const k = b.dataset.cmd
  if (k === 'req') return insertRequirement()
  if (k === 'ref') return openPicker()
  if (k === 'wave' || k === 'mmd') { const lang = k === 'wave' ? 'wavedrom' : 'mermaid'; openNextDiagram = true; return editor.chain().focus().insertContent({ type: 'diagram', attrs: { lang, src: DG[lang].def } }).run() }
  if (k === 'undo') return editor.chain().focus().undo().run()
  if (k === 'redo') return editor.chain().focus().redo().run()
  const t = TB.find(x => x[0] === k); if (t) t[2](editor.chain().focus()).run()
})
panel.addEventListener('click', e => {
  const g = e.target.closest('[data-goto]'); if (g) return goto(g.dataset.goto)
  const sb = e.target.closest('[data-sub]'); if (sb) { active = null; return setDoc('ERS', sb.dataset.sub) }
  const um = e.target.closest('[data-unmetric]')
  if (um) { const r = index().get(active); setAttrs(active, { metrics: r.metrics.filter(x => x !== um.dataset.unmetric) }); return }
  const u = e.target.closest('[data-unlink]')
  if (u) { const r = index().get(active); setAttrs(active, { satisfies: r.satisfies.filter(x => x !== u.dataset.unlink) }); return }
  const rq = e.target.closest('[data-req]')
  if (rq && !rq.disabled) { const r = index().get(active), f = rq.dataset.req; setAttrs(active, { required: r.required.includes(f) ? r.required.filter(x => x !== f) : [...r.required, f] }); return }
  const a = e.target.closest('[data-act]'); if (!a) return
  if (a.dataset.act === 'overview') { active = null; afterChange() }
  if (a.dataset.act === 'metric') {
    const n = $('#mn-in').value.trim(), r = index().get(active); if (!n) return $('#mn-in').focus()
    const m = $('#mk-sel').value + ':' + n
    if (!r.metrics.includes(m)) setAttrs(active, { metrics: [...r.metrics, m] })
  }
  if (a.dataset.act === 'link') { const v = $('#add-sel').value, r = index().get(active); if (v) setAttrs(active, { satisfies: [...r.satisfies, v] }) }
})
panel.addEventListener('change', e => {
  if (e.target.id === 'ses-sel') { state.session = e.target.value; afterChange() }
  if (e.target.id === 'goal-in') { const g = Math.min(100, Math.max(1, +e.target.value || 100)); setAttrs(active, { goal: g }) }
})
panel.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.id === 'mn-in') { e.preventDefault(); panel.querySelector('[data-act="metric"]').click() } })
$('#panel-toggle').addEventListener('click', () => {
  const o = panel.classList.toggle('open'); $('#panel-toggle').setAttribute('aria-expanded', String(o))
})
$('#pick-q').addEventListener('input', e => fillPicker(e.target.value))
$('#pick-list').addEventListener('click', e => {
  const b = e.target.closest('[data-pick]'); if (!b) return
  $('#picker').close()
  editor.chain().focus().insertContentAt(savedPos, { type: 'reqRef', attrs: { rid: b.dataset.pick } }).run()
})
$('#pick-close').addEventListener('click', () => $('#picker').close())
$('#reset').addEventListener('click', () => {
  try { localStorage.removeItem(KEY) } catch (e) {}
  state = seedState(); curKey = undefined; entries = {}; dirty = true; active = null; setDoc('ERS', 'IO')
})

/* ---------- démarrage ---------- */
state = load()
if (!SESSIONS[state.session]) state.session = 'n1004'
setDoc(DOCS.some(d => d.key === state.cur[0]) ? state.cur[0] : 'ERS', SUBS.some(s => s.code === state.cur[1]) ? state.cur[1] : 'IO')
