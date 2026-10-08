# Trace

Outil de traçabilité des exigences pour un SoC : de l’exigence client aux résultats qui la prouvent (DV, analogique, FW, validation).

Vous reprenez ce projet avec un assistant de code (Claude Code, Copilot…) ? Il doit commencer par
[`AGENTS.md`](AGENTS.md), qui décrit l’état du projet, les règles de cohérence et les conventions ;
les choix déjà tranchés sont expliqués dans [`DECISIONS.md`](DECISIONS.md).

## Contenu du dépôt

| Dossier | Contenu |
| --- | --- |
| `SPEC.md` | Le prompt de création de l’application, à donner à Claude Code (« Lis SPEC.md et commence par l’étape 0 »). |
| `prototype/` | Prototype d’édition traçable : Tiptap, 9 182 exigences de démonstration sur 11 sous-systèmes. `trace-prototype.html` s’ouvre directement dans un navigateur. |
| `design-system/` | Design system Trace : `tokens.json` (source), `tokens.css` (variables CSS prêtes à l’emploi, thèmes clair et sombre), `fonts/` (IBM Plex servies localement) et `README.md` (règles d’usage). |
| `maquettes/` | Les 14 maquettes des vues. `captures/` contient leur rendu en PNG, à consulter en premier ; les fichiers `.dc.html` s’ouvrent aussi dans un navigateur et donnent le détail de la mise en page. |
| `outils/` | Scripts qui régénèrent les données de démo, les maquettes et `tokens.css`. |
| `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` | Consignes pour les assistants de code. |
| `DECISIONS.md` | Journal des décisions et de leurs raisons. |
| `NOTICE.md` | Licences des composants tiers. |

## Reconstruire le prototype

```bash
cd prototype
npm install
npm run build        # régénère trace-prototype.html
```

## Régénérer les maquettes

```bash
cd outils
node extraire_donnees.mjs          # écrit donnees.json depuis prototype/src/seed.js
python3 generer_maquettes.py       # réécrit ../maquettes/*.dc.html et canvas.json
```

Prérequis : Node.js 20 ou plus récent, Python 3.10 ou plus récent (pour les maquettes uniquement).

## Ce que le dépôt ne contient pas

Ces éléments sont propres à l’environnement de l’entreprise et doivent être fournis à l’équipe qui construit l’application avant l’étape 0 de `SPEC.md` :

- les réponses aux 14 questions de cadrage (fin de `SPEC.md`) ;
- des fichiers d’exemple réels : vPlan vManager, export ADE, rapport de la CI FW, résultats de banc, spécification client Word ou Excel ;
- les accès : API Tuleap et compte de service, SSO, serveur d’hébergement, accès réseau à vManager, Jenkins et la CI FW.

Ne commitez pas ces fichiers d’exemple s’ils sont confidentiels : placez-les dans un dossier `exemples-prives/`, déjà exclu par `.gitignore`.
