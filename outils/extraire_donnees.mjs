/**
 * Extrait de prototype/src/seed.js les exigences et leurs statuts, vus avec les résultats du 4 octobre
 * (session n1004), et les écrit dans donnees.json pour generer_maquettes.py.
 *
 * Sortie : { reqs: [{ rid, doc, sub, sec, sat, metrics, goal, req, text, st, kids, metricsEv: [[métrique, ok|fail|short|missing, résultat]] }],
 *            subs: [{ code, nom }] }
 *
 * ATTENTION : ev() et st() sont une COPIE compacte de evalMetric/planStatus/statusOf de prototype/src/app.js.
 * Toute évolution de la règle de statut doit être reportée ici, sinon les maquettes et le prototype divergent.
 * (Duplication assumée pour garder ce script indépendant de Tiptap et du DOM.)
 */
import { SESSIONS, seedDocs, SUB_LIST } from '../prototype/src/seed.js'
const docs = seedDocs(), FAM = { VP: 'DV', ANV: 'ANA', FWT: 'FW', VAL: 'VAL' }
const textOf = n => n.type === 'text' ? n.text : n.type === 'reqRef' ? n.attrs.rid : (n.content || []).map(textOf).join(n.type === 'paragraph' ? '' : ' ')
const idx = new Map()
for (const [k, j] of Object.entries(docs)) { const [d, s] = k.split('|'); let h = ''; const walk = js => { for (const n of js.content || []) { if (n.type === 'heading' && n.attrs.level === 2) h = textOf(n); if (n.type === 'requirement') idx.set(n.attrs.rid, { rid: n.attrs.rid, doc: d, sub: s, sec: h, sat: n.attrs.satisfies, metrics: n.attrs.metrics, goal: n.attrs.goal, req: n.attrs.required || [], text: textOf(n).trim() }); else if (n.content) walk(n) } }; walk(j) }
const kids = new Map(); for (const r of idx.values()) for (const p of r.sat) { if (!kids.has(p)) kids.set(p, []); kids.get(p).push(r.rid) }
const res = SESSIONS.n1004.results, RANK = { untraced: 0, traced: 1, failing: 2, planned: 3, proven: 4 }
const ev = (m, g) => { const r = res[m], k = m.split(':')[0]; if (!r) return 'missing'; if (['test','utest','itest'].includes(k)) return r.fail ? 'fail' : 'ok'; if (k === 'assert') return r.ok ? 'ok' : 'fail'; if (k === 'cover' || k === 'codecov') return r.pct >= g ? 'ok' : 'short'; if (k === 'spec') return r.ok ? (r.view === 'schéma' ? 'short' : 'ok') : 'fail'; if (k === 'mc') return r.cpk >= 1.33 ? 'ok' : 'short'; if (k === 'model') return r.err <= 2 ? 'ok' : 'fail'; if (r.stale || r.pending) return 'short'; if (k === 'mesure') return r.val <= r.max ? 'ok' : 'fail'; return r.ok ? 'ok' : 'fail' }
const desc = rid => { const out = [], s = new Set([rid]), q = [rid]; while (q.length) for (const c of kids.get(q.shift()) || []) if (!s.has(c)) { s.add(c); out.push(c); q.push(c) } return out }
const memo = new Map()
const st = rid => { if (memo.has(rid)) return memo.get(rid); const r = idx.get(rid); let s; if (FAM[r.doc]) { if (!r.metrics.length) s = 'traced'; else { const e = r.metrics.map(m => ev(m, r.goal)); s = e.includes('fail') ? 'failing' : e.every(x => x === 'ok') ? 'proven' : 'planned' } } else { const k = kids.get(rid) || []; s = k.length ? k.map(st).reduce((a, b) => RANK[a] <= RANK[b] ? a : b) : 'untraced'; if (r.req.some(f => !desc(rid).some(x => FAM[idx.get(x).doc] === f))) s = 'untraced' } memo.set(rid, s); return s }
const out = [...idx.values()].map(r => ({ ...r, st: st(r.rid), kids: kids.get(r.rid) || [], metricsEv: r.metrics.map(m => [m, ev(m, r.goal), res[m] || null]) }))
import fs from 'fs'; fs.writeFileSync('donnees.json', JSON.stringify({ reqs: out, subs: SUB_LIST }))
console.log(out.length)
