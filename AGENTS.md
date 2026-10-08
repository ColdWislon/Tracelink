# AGENTS.md — reprise du projet Trace par un agent ou un LLM

Ce fichier est le point d'entrée pour tout assistant de code (Claude Code, Copilot, Codex, Cursor…)
qui reprend ce dépôt. Lisez-le en entier avant de toucher au code. `CLAUDE.md` et
`.github/copilot-instructions.md` renvoient ici.

## 1. De quoi il s'agit

Trace est un outil web de **traçabilité des exigences** pour un SoC (circuit intégré numérique,
analogique et logiciel). Pour chaque exigence client, il doit montrer par quoi elle est raffinée,
par quoi elle est vérifiée, et avec quel résultat, afin de produire des **preuves contractuelles**.

Commanditaire : Bertrand Dosda, responsable méthodologie de vérification (équipe DV d'une vingtaine
d'ingénieurs, outils Cadence Xcelium / vManager / IMC, CI Jenkins, exigences dans Tuleap).

**L'application elle-même n'est pas encore écrite.** Le dépôt contient tout ce qu'il faut pour la
construire : la spécification, un prototype jetable, un design system et les maquettes des vues.

## 2. Deux types de missions possibles

Identifiez laquelle on vous confie avant de commencer.

| Mission | Point de départ | Ce qu'il faut produire |
| --- | --- | --- |
| **A. Construire l'application** | `SPEC.md`, en commençant par l'étape 0 (questions de cadrage) | Un nouveau code (React + TypeScript + API + PostgreSQL), livré par étapes, dans un dossier à créer (par ex. `app/`). Ne pas partir du code du prototype. |
| **B. Faire évoluer les supports** | `prototype/`, `maquettes/`, `design-system/` | Modifier la démo, les maquettes ou la spec, en gardant les trois cohérents. |

Pour la mission A, `SPEC.md` fait foi pour le **comportement**, les maquettes et le design system pour
l'**apparence**. En cas de contradiction, signalez-la au lieu de trancher seul.

## 3. Carte du dépôt

```
SPEC.md                    Spécification complète, rédigée comme un prompt pour un agent (« tu… »)
AGENTS.md                  Ce fichier
DECISIONS.md               Journal des décisions et de leurs raisons — à lire avant de remettre un choix en cause
README.md                  Présentation humaine et commandes
NOTICE.md                  Licences tierces
prototype/
  src/app.js               Toute la logique du prototype (index, statuts, nœuds Tiptap, panneau). Commenté.
  src/seed.js              Générateur déterministe des 9 182 exigences de démo et des résultats. Commenté.
  src/template.html        HTML + CSS du prototype ; le bundle y est injecté
  build.mjs, package.json  Build esbuild → trace-prototype.html (fichier unique, autonome)
  trace-prototype.html     Prototype construit, s'ouvre dans un navigateur
design-system/
  tokens.json              SOURCE des couleurs (clair/sombre), typo, espacements, rayons
  tokens.css               Variables CSS générées depuis tokens.json (ne pas éditer à la main)
  README.md                Règles d'usage (statuts, pastilles, typographie, rédaction)
  fonts/                   IBM Plex Sans/Serif en woff2 + fonts.css + licence OFL
maquettes/
  *.dc.html                14 maquettes (12 vues poste de travail + 2 téléphone), générées
  captures/*.png           Rendu des maquettes — à regarder en premier
  canvas.json              Disposition pour le canevas Claude Design
outils/
  extraire_donnees.mjs     seed.js → donnees.json (statuts calculés)
  generer_maquettes.py     donnees.json → maquettes/*.dc.html + canvas.json
  generer_tokens_css.py    design-system/tokens.json → tokens.css
```

## 4. Modèle métier en dix lignes

- **Niveaux** (préfixes d'ID) : spécifications ERS (client), SDS, DDS (numérique), ANS (analogique),
  FWS (firmware) ; plans de vérification VP (vPlan DV), ANV (analogique), FWT (tests FW), VAL (validation).
- **Sous-systèmes** : un document = un couple niveau × sous-système (`SDS|MEM`). Jamais tout un niveau.
- **ID** : `NIVEAU-SOUS_SYSTÈME-NNN`, ex. `ERS-IO-012`. Unique dans le projet, jamais réutilisé.
- **Liens** stockés côté enfant (`satisfies`). Même préfixe que le parent = « dérive de », sinon « satisfait ».
- **Métriques** sur les items de plan : `type:nom`. Types : DV `test assert cover` ; ANA `spec mc model` ;
  FW `utest itest codecov` ; VAL `proc mesure demo` (+ `carac` prévu par la spec, absent du prototype).
- **Statuts**, du pire au meilleur : Non tracée < Tracée < En échec < Planifiée < Prouvée.
  Item de plan = statut de ses métriques ; autre exigence = **pire statut de ses branches**.
- **Plans requis** : une ERS/SDS peut exiger des familles (ex. DV + VAL) ; famille requise sans item en aval ⇒ Non tracée.
- Les statuts sont **toujours recalculés**, jamais stockés comme vérité.
- **Résultats de référence** : une session par famille (DV, ANA, FW, VAL), figées ensemble dans une baseline.
- En cas de doute, un statut plus pessimiste vaut mieux qu'un faux « Prouvée » (preuve contractuelle).

L'implémentation de référence de ces règles est dans `prototype/src/app.js`, section
« vérification : calcul des statuts ».

## 5. Commandes

Prérequis : Node.js ≥ 20, Python ≥ 3.10, Playwright (uniquement pour les captures).

```bash
# Prototype
cd prototype && npm install && npm run build      # → trace-prototype.html

# Maquettes (après toute modification de seed.js, des règles de statut ou du générateur)
cd outils
node extraire_donnees.mjs                         # → donnees.json (ignoré par git)
python3 generer_maquettes.py                      # → ../maquettes/*.dc.html, canvas.json

# Captures PNG des maquettes (pip install playwright && playwright install chromium)
python3 - <<'EOF'
import glob, os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    for f in sorted(glob.glob('../maquettes/*.dc.html')):
        mob = 'Mobile' in f
        pg = b.new_page(viewport={'width': 390 if mob else 1440, 'height': 844 if mob else 900},
                        device_scale_factor=2 if mob else 1)
        pg.goto('file://' + os.path.abspath(f)); pg.wait_for_timeout(900)
        pg.screenshot(path='../maquettes/captures/' + os.path.basename(f).replace('.dc.html', '.png'),
                      full_page=not mob)
    b.close()
EOF
```

`design-system/tokens.css` est généré depuis `tokens.json` : `python3 outils/generer_tokens_css.py`.
Reportez aussi les couleurs dans le dict `C` de `outils/generer_maquettes.py`.

## 6. Règles de cohérence (le plus important pour la mission B)

Plusieurs choses sont dupliquées volontairement. Une modification à un endroit doit être propagée :

| Si vous modifiez… | …mettez aussi à jour |
| --- | --- |
| Les règles de statut (`evalMetric`, `planStatus`, `statusOf` dans app.js) | `outils/extraire_donnees.mjs` (copie compacte), puis régénérez les maquettes, et `SPEC.md` si la règle change |
| `prototype/src/seed.js` (même un seul appel au hasard) | Les IDs cités en dur dans `generer_maquettes.py` peuvent changer de sens ; régénérez et relisez les maquettes. Incrémentez `KEY` dans app.js |
| Le format JSON des documents | `KEY` dans app.js (sinon les navigateurs rechargent un ancien état) |
| `design-system/tokens.json` | `tokens.css` (script), le dict `C` du générateur, les variables `:root` de `template.html` |
| Une vue des maquettes | La section « Vues de l'application » de `SPEC.md` si le comportement change ; les captures PNG |
| `prototype/src/template.html` | Ne jamais recopier le marqueur de bundle (`/*BUNDLE*/`) ailleurs que dans la dernière balise `<script>` : build.mjs échoue s'il apparaît plus d'une fois |
| `SPEC.md` | Rien d'automatique : c'est la source. Gardez les marqueurs **À confirmer** tant que ce n'est pas tranché |

## 7. Conventions

- **Langue** : toute l'interface, la documentation et les commentaires sont en **français**.
  Les identifiants de code restent en anglais (`statusOf`, `satisfies`).
- **Libellés de statut** exacts : Prouvée, Planifiée, En échec, Tracée, Non tracée. Liens : « dérive de », « satisfait ».
- **Typographie** : apostrophe typographique ’ dans les textes affichés, guillemets « », espace avant `: ; ? !`
  comme en français. Pas de tiret cadratin pour relier deux idées.
- **Couleur jamais seule** : un statut s'affiche toujours avec son libellé ou sa forme (cercle vide = Tracée).
- **Pas de dépendance réseau** dans l'application finale (on-premise) : polices et bibliothèques servies localement.
  Le prototype charge Google Fonts et Mermaid depuis un CDN ; c'est toléré pour une démo, pas au-delà.
- **Données confidentielles** : les vrais fichiers client vont dans `exemples-prives/` (ignoré par git).
  Les données du dépôt sont fictives.

## 8. État d'avancement (au 8 octobre 2026)

Fait :
- `SPEC.md` complet (20 sections, livraison en 9 étapes, 14 questions de cadrage).
- Prototype fonctionnel à l'échelle d'un SoC : édition, liens, statuts, plans requis, 4 familles,
  2 sessions de résultats comparables, diagrammes WaveDrom/Mermaid, 11 sous-systèmes.
- Design system (tokens, règles, polices) et 14 maquettes générées sur les données de démo.

Pas fait dans le prototype (décrit dans la spec, à construire dans l'application) :
discussions et commentaires, revue et approbation, exigences paramétriques (tableau de paramètres),
historique et baselines, import Word/Excel, synchro Tuleap, refus des cycles à la saisie, exports.

Non tranché (marqué **À confirmer** dans `SPEC.md`) : format des exports ADE, types de liens Tuleap,
format vplanx et API vManager, versions de cellviews Virtuoso, règle post-layout, nettoyage HTML de
Tuleap, outils de la CI FW, double validation, SSO, charge (50 utilisateurs actifs), accès invité client,
notifications Teams/Slack, langage du backend (Node ou Python).

Prochaine étape prévue : réunir les réponses aux 14 questions et les fichiers d'exemple réels,
faire valider les maquettes par 5 ou 6 futurs utilisateurs, puis lancer l'étape 0 de la mission A.

## 9. Ressources hors dépôt

Ces pages existent sur claude.ai (privées, accessibles à Bertrand). Elles sont le **miroir** du contenu
du dépôt ; le dépôt fait foi s'il y a divergence.

- Prototype publié : https://claude.ai/artifact/R7WtEee4X1iDbqu58ZDghJ
- Design system (Claude Design) : https://claude.ai/artifact/WYKNughhFqUvRpwc1HURFo
- Maquettes (canevas Claude Design) : https://claude.ai/artifact/KDDxw5iU4wRfRxLfhnKJz5

## 10. Comment travailler ici

- Lisez `DECISIONS.md` avant de proposer un autre éditeur, framework ou stockage : ces choix ont été pesés.
- N'inventez jamais un format de fichier ou d'API externe (Tuleap, vManager, ADE, CI FW, bancs) :
  demandez un exemple réel. `SPEC.md` l'exige aussi.
- Après une modification du prototype : `npm run build`, ouvrez `trace-prototype.html`, vérifiez qu'il
  n'y a pas d'erreur console et que le chargement reste autour d'une seconde.
- Après une modification des maquettes : régénérez, refaites les captures, regardez-les.
- Petits commits, un par changement logique, message en français.
