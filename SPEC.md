# Prompt de création de l'outil de traçabilité

Oct 5, 2026 · @Bertrand

## Mode d'emploi

Ce prompt est destiné à Claude Code, lancé à la racine d'un dépôt vide. Le plus simple est de l'exporter en Markdown, de l'enregistrer sous `SPEC.md`, puis de demander : « Lis SPEC.md et commence par l'étape 0 ». Tout ce qui suit est écrit à l'adresse de l'agent. Les points marqués **À confirmer** sont des hypothèses à valider avant de coder la partie concernée.

## Ressources fournies dans le dépôt

Le dépôt contient, en plus de ce fichier, des ressources à lire avant l'étape 0. Elles font foi pour l'ergonomie et l'apparence ; ce fichier fait foi pour le comportement. En cas de contradiction entre les deux, signale-la au lieu de choisir seul.

| Chemin | Rôle | Comment l'utiliser |
| --- | --- | --- |
| `prototype/trace-prototype.html` | Prototype fonctionnel : éditeur Tiptap, exigences avec ID, liens, statuts, diagrammes, 9 182 exigences de démo | L'ouvrir dans un navigateur pour comprendre l'ergonomie attendue. Ce n'est pas une base de code à reprendre telle quelle. |
| `prototype/src/seed.js` | Générateur du jeu de démo (11 sous-systèmes, 45 blocs, résultats fictifs des quatre familles) | Réutiliser pour les données de démo de l'étape 1, le projet bac à sable et les tests de charge. |
| `prototype/src/app.js` | Logique du prototype : calcul des statuts, plans requis, nœuds Tiptap | Référence pour les règles de statut ; la réécrire proprement, typée et testée. |
| `design-system/` | Tokens (couleurs de statut en thème clair et sombre, typographie, espacements, rayons), règles d'usage, polices IBM Plex | Utiliser ces valeurs exactes dans le front. Servir les polices localement, jamais depuis Google Fonts. |
| `maquettes/` | Les 14 maquettes validées : douze vues sur poste de travail, deux sur téléphone | Les captures PNG dans `maquettes/captures/` montrent le rendu attendu ; les fichiers `.dc.html` donnent les détails de mise en page. |
| `outils/` | Scripts qui régénèrent les données de démo et les maquettes | À ne modifier que si la démo change. |

Mermaid, WaveDrom et toutes les autres bibliothèques sont installées par npm et servies par l'application : rien n'est chargé depuis Internet en production.

## Rôle et contexte

Tu es l'ingénieur logiciel principal d'un outil web de traçabilité des exigences pour plus de 200 utilisateurs répartis sur plusieurs équipes et projets, issus de plusieurs métiers : conception et vérification numérique (SystemVerilog, UVM), analogique, logiciel embarqué, validation et gestion de projet. L'outil sert d'abord à produire des **preuves de vérification pour un contrat client** : pour chaque exigence client, montrer par quoi elle est raffinée, par quoi elle est vérifiée, et avec quel résultat. Il n'y a pas de norme de sûreté formelle à respecter, mais les preuves doivent être reproductibles et datées.

Environnement existant :

- **Tuleap** : les exigences vivent dans un ou plusieurs trackers. Tuleap est lent ; l'outil ne doit jamais faire attendre l'utilisateur sur lui.
- **Cadence vManager, Xcelium et IMC** : régressions, vPlans, couverture et simulation mixte (Xcelium AMS) ; Virtuoso, ADE et Spectre pour l'analogique (à confirmer).
- **Jenkins** : CI qui lance les régressions nocturnes.

Chaîne documentaire : ERS/MRS (exigences client) → SDS, puis trois branches. Côté numérique, SDS → DDS → vPlan (vérification DV). Côté analogique, SDS → spécification analogique → plan de vérification analogique (simulations électriques). Côté logiciel, SDS → spécification FW → plan de test FW. Un plan de validation (FPGA, émulation, silicium, banc système, caractérisation) vérifie de bout en bout les exigences ERS et SDS. Les exigences client sont raffinées en exigences internes.

Un prototype a validé l'expérience d'édition : un éditeur type document où les exigences sont des blocs structurés avec ID, un panneau de traçabilité et une vue de couverture. Tu repars de zéro, mais l'ergonomie doit en reprendre les principes.

## Modèle de traçabilité

Le cœur de l'outil est un graphe d'exigences orienté et acyclique. Tout le reste (éditeur, synchro, rapports) le sert.

**Niveaux.** Chaque document appartient à un niveau configurable. Les niveaux par défaut sont ERS, SDS, DDS, ANS et FWS pour les spécifications, VP, ANV, FWT et VAL pour les plans de vérification ; ils sont détaillés dans les sections suivantes. Chaque exigence a une branche optionnelle : numérique, analogique ou FW. La liste des niveaux et leur ordre se configurent par projet, sans code.

**Sous-systèmes.** Un projet de SoC compte typiquement une dizaine de sous-systèmes (grappe processeur, mémoires, sécurité, E/S, analogique…) et environ 10 000 exigences. Un document correspond donc à un couple niveau × sous-système (par exemple le SDS du sous-système Mémoires), jamais à un niveau entier. La liste des sous-systèmes se configure par projet. Les liens peuvent traverser les sous-systèmes, mais le menu d'ajout de lien propose d'abord le sous-système courant.

**Identifiants.** Chaque exigence a un ID lisible et stable, attribué automatiquement et jamais réutilisé. Un collage qui duplique une exigence crée un nouvel ID. Proposition, reprise du prototype : niveau, sous-système puis rang (`ERS-IO-012`, `SDS-MEM-034`). Le format exact est **À confirmer**.

**Deux types de liens amont**, distincts dans le modèle et dans l'interface :

| Lien | Sens | Exemple |
| --- | --- | --- |
| dérive de | même niveau | ERS-006 dérive de ERS-003 |
| satisfait | niveau supérieur | SDS-005 satisfait ERS-006 |

Une exigence peut porter les deux. Un item de plan de vérification satisfait une exigence de spécification ; les niveaux autorisés sont donnés dans les tableaux des sections suivantes. Tout lien qui créerait un cycle est refusé à la saisie.

**Items de plan de vérification.** En plus de l'énoncé et des liens, chaque item porte une méthode (simulation, formel, mesure, revue), une liste de métriques typées dont les types dépendent de la famille du plan (section suivante) et un objectif (100 % par défaut).

**Statuts calculés**, du pire au meilleur :

1. Non tracée : au moins une branche s'arrête avant un plan de vérification, ou un plan requis n'a aucun item en aval.
2. Tracée : la branche atteint un item de plan sans métrique.
3. En échec : une métrique échoue dans les résultats de référence.
4. Planifiée : les métriques existent mais n'atteignent pas toutes leur objectif, sont absentes des résultats, attendent une double validation, sont à rejouer, ou ne sont prouvées que sur schéma quand le post-layout est exigé.
5. Prouvée : toutes les métriques atteignent leur objectif.

Le statut d'une exigence est le **pire statut de ses branches**, exigences dérivées comprises. Une exigence sans aucun lien aval est non tracée. Les statuts sont toujours recalculés, jamais stockés comme vérité.

**Règles de refus.** Une exigence sans ID ne peut pas être enregistrée. Une exigence hors racine sans lien amont est signalée en anomalie. Une référence vers un ID inexistant est signalée en anomalie.

## Spécification FW, validation et familles de plans

La chaîne couvre aussi le logiciel embarqué et la validation, avec le même modèle de nœuds, de liens et de statuts que la branche numérique.

**Niveaux ajoutés.**

| Niveau | Préfixe proposé | Satisfait | Rôle |
| --- | --- | --- | --- |
| Spécification FW | FWS | SDS (branche FW) | Équivalent du DDS côté logiciel : comportement du firmware, API, séquences d'initialisation, gestion d'erreurs |
| Plan de test FW | FWT | FWS, SDS | Items vérifiables du firmware |
| Plan de validation | VAL | ERS, SDS | Items vérifiés sur cible réelle ou proche : FPGA, émulation, silicium, banc système |

Les préfixes et la liste des niveaux restent configurables par projet. Une FWS peut dériver d'une autre FWS, comme partout ailleurs.

**Quatre familles de plans de vérification.** vPlan DV, plan de vérification analogique, plan de test FW et plan de validation partagent le même modèle d'item (énoncé, liens amont, méthode, métriques, objectif) et les mêmes règles de statut. Ils diffèrent par leurs types de métriques et la source de leurs résultats :

| Plan | Types de métriques | Source des résultats |
| --- | --- | --- |
| vPlan DV | `test:`, `assert:`, `cover:` (y compris les tests mixtes Xcelium AMS) | vManager via Jenkins |
| Plan de vérification analogique | `spec:` (performance simulée avec bornes), `mc:` (Monte-Carlo, rendement ou Cpk), `model:` (corrélation d'un modèle comportemental avec le transistor) | Exports ADE Assembler ou Maestro (**À confirmer**) |
| Plan de test FW | `utest:` (test unitaire), `itest:` (test d'intégration sur modèle ou cible), `codecov:` (couverture de code, en %) | CI FW (rapports JUnit XML et couverture de code, **À confirmer**) |
| Plan de validation | `proc:` (procédure de test, réussie ou non), `mesure:` (valeur avec bornes min et max), `carac:` (caractérisation silicium sur plusieurs échantillons et températures), `demo:` (démonstration ou revue) | Saisie par l'opérateur ou import Excel ou CSV depuis le banc ; Tuleap Test Management si l'équipe l'utilise (**À confirmer**) |

**Statut.** Le statut d'une exigence reste le pire statut de toutes ses branches, quel que soit le plan qui les termine. En plus, chaque exigence ERS ou SDS peut déclarer les **plans requis** (par exemple DV et validation) : elle n'est prouvée que si chaque plan requis contient au moins un item prouvé en aval. Par défaut, aucun plan n'est requis ; la règle se règle par projet et par exigence.

**Contexte d'exécution.** Un résultat FW ou de validation n'a de valeur qu'avec ses versions. Chaque exécution enregistre : version du firmware (hash Git), version du matériel (RTL, bitstream FPGA ou révision de silicium), banc ou environnement, date et opérateur. Un résultat obtenu sur une version antérieure à la baseline en cours est signalé « à rejouer ».

**Résultats de validation saisis à la main.** L'opérateur saisit le résultat, les valeurs mesurées et joint ses preuves (logs, captures d'oscilloscope, photos). Proposition, **À confirmer** : le résultat ne compte comme preuve qu'après validation par une seconde personne, et devient alors immuable ; une correction crée une nouvelle exécution.

## Analogique et mixte

Le produit contient des blocs analogiques (références, régulateurs, convertisseurs, PLL, entrées-sorties). Leurs exigences sont paramétriques et leur vérification repose sur des simulations électriques, pas sur des régressions de tests.

**Niveaux ajoutés.**

| Niveau | Préfixe proposé | Satisfait | Rôle |
| --- | --- | --- | --- |
| Spécification analogique | ANS | SDS (branche analogique) | Performances de chaque bloc analogique, conditions de fonctionnement, interfaces avec le numérique |
| Plan de vérification analogique | ANV | ANS, SDS | Simulations par coins, Monte-Carlo, pré et post-layout, corrélation des modèles |

Les branches deviennent : numérique, analogique et FW. Les tests mixtes (Xcelium AMS, modèles real-number) restent dans le vPlan DV, puisqu'ils passent par vManager.

**Exigences paramétriques.** Une exigence ERS, SDS ou ANS peut porter un tableau de paramètres structuré, en plus de son énoncé : paramètre, symbole, conditions (tension, température, charge), minimum, typique, maximum, unité. Ce tableau est un nœud de l'éditeur, pas un tableau libre : chaque ligne a un identifiant (par exemple `ANS-012/VOS`), et une métrique `spec:`, `mc:`, `mesure:` ou `carac:` peut viser une ligne précise. L'outil reprend alors automatiquement les bornes de la ligne au lieu de les ressaisir.

**Évaluation des métriques analogiques.**

- `spec:` est atteinte si la performance tient dans les bornes sur **tous** les coins du jeu de coins demandé. L'outil affiche le pire coin et la marge restante.
- `mc:` est atteinte si le rendement ou le Cpk atteint l'objectif de l'item (par exemple Cpk ≥ 1,33), avec le nombre de tirages.
- `model:` est atteinte si l'écart entre le modèle comportemental et la simulation transistor reste sous le seuil fixé. Elle garantit que les tests mixtes du vPlan DV portent sur un modèle fidèle.
- `carac:` est atteinte si la moyenne et la dispersion mesurées sur les échantillons respectent les bornes, avec le Cpk et le nombre d'échantillons.

**Contexte d'exécution analogique.** Chaque résultat enregistre : version du PDK, jeu de coins, vue simulée (schéma ou extraction post-layout), version des cellviews Virtuoso (ou référence du système de gestion de conception, **À confirmer**), outil et version du simulateur. Un résultat devient « à rejouer » si le schéma, le layout ou le PDK a changé depuis. Par projet ou par exigence, on peut exiger des résultats post-layout pour qu'une métrique compte comme preuve ; un résultat sur schéma seul reste alors « planifié ».

**Plans requis.** La famille analogique (ANA) s'ajoute aux plans requis : une exigence client sur une performance analogique exige typiquement ANA et validation.

## Discussions sur les exigences

Chaque exigence et chaque item de plan a ses fils de discussion, pour la relecture interne comme pour les clarifications avec le client. Une discussion fait partie de la preuve : elle explique pourquoi une exigence a été écrite ou modifiée ainsi.

**Ancrage.** Un fil s'attache à l'exigence entière, à un passage surligné de l'énoncé, à une ligne d'un tableau de paramètres ou à un diagramme. L'ancre suit le texte quand l'énoncé change ; si le passage disparaît, le fil reste sur l'exigence avec la mention « passage modifié ».

**Types de fils.**

| Type | Usage | Effet |
| --- | --- | --- |
| Commentaire | Remarque, précision | Aucun |
| Question | Point à clarifier, en interne ou avec le client | Reste en attente tant qu'aucune réponse n'est acceptée |
| Proposition de modification | Nouveau texte proposé pour l'énoncé ou un paramètre | Un clic l'applique et crée une nouvelle version de l'exigence |
| Bloquant | Désaccord ou défaut à corriger | Empêche l'approbation de l'exigence et la création d'une baseline (règle configurable par projet) |

**Contenu.** Texte simple avec mise en forme légère, mentions `@personne`, références d'exigences (comme dans l'éditeur) et pièces jointes.

**Cycle de vie.** Un fil est ouvert puis résolu, avec un résumé de la décision prise ; il peut être rouvert. Chaque message enregistre la version de l'exigence à laquelle il répond, et l'historique de l'exigence entrelace versions et discussions. Les messages sont append-only : une modification reste visible (« modifié », avec l'ancien texte consultable) et une suppression masque le message sans l'effacer.

**Revue et approbation.** Chaque exigence a un statut de revue : brouillon, en revue, approuvée, à reprendre. Le rédacteur demande une revue à des relecteurs nommés ; l'approbation est enregistrée avec son auteur et la version approuvée. Toute modification ultérieure de l'énoncé repasse l'exigence en revue. Les règles exactes (nombre d'approbateurs, rôles autorisés) sont **À confirmer**.

**Échanges avec le client.** Un fil peut être marqué « client ». Les questions client ouvertes s'exportent en liste de questions-réponses (XLSX ou DOCX) à envoyer, et les réponses se réimportent avec l'assistant d'import. Option à étudier : un accès invité limité au projet, en lecture et commentaire seulement (**À confirmer**).

**Notifications.** En direct dans l'application, plus un e-mail récapitulatif paramétrable. On peut s'abonner à une exigence, à un document ou seulement à ses mentions. Teams ou Slack en option (**À confirmer**).

**Tuleap.** Les discussions sont stockées dans l'outil. En option, la décision d'un fil résolu est recopiée en commentaire de suivi de l'artefact Tuleap, pour que l'information reste visible côté Tuleap (**À confirmer**).

**Dans l'interface.**

- Dans la marge du document, un compteur de fils ouverts à côté de l'ID, et les passages commentés surlignés.
- Dans le panneau d'une exigence, un onglet Discussion avec les fils, leur type et leur statut.
- Une douzième vue, **Discussions** : mes mentions, mes revues à faire, fils ouverts par document, questions client en attente, avec filtres par type, auteur et ancienneté.
- Dans les anomalies : fils bloquants ouverts, questions client sans réponse depuis un délai configurable, exigences approuvées puis modifiées.

**Baselines.** Une baseline fige aussi l'état des discussions et des approbations. Le rapport de preuve peut inclure, en annexe, les décisions prises sur les exigences du périmètre.

## Architecture et stack

L'outil lit et écrit dans sa propre base ; Tuleap et les sources de résultats (vManager, exports ADE, CI FW, bancs) sont synchronisés en arrière-plan. Aucune action utilisateur n'attend un appel externe.

Composants :

- **Front** : application web TypeScript, éditeur Tiptap v3, React, avec Vite comme outil de build et serveur de développement.
- **API** : backend TypeScript (Node) ou Python, au choix, justifié en une phrase.
- **Base** : PostgreSQL. Tables append-only pour les versions d'exigences et de documents ; vues ou requêtes récursives pour le graphe. Les fichiers (images, pièces jointes, fichiers importés, exports) sont stockés hors base, adressés par leur empreinte, sur disque ou sur un stockage objet compatible S3 on-premise.
- **Workers** : un worker de synchro Tuleap (entrant et sortant), un worker d'import des résultats des quatre familles et un worker de rendu (diagrammes, exports DOCX et PDF). File de tâches persistée en base pour commencer, sans brique supplémentaire.
- **Déploiement** : on-premise, `docker compose` (front, API, workers, PostgreSQL). Pas de service cloud tiers.

Authentification : chaque utilisateur agit avec ses propres droits Tuleap (jeton personnel ou OAuth2, **À confirmer** selon l'instance). L'outil ne doit jamais permettre de lire ou modifier un artefact que l'utilisateur ne pourrait pas lire ou modifier dans Tuleap.

**Montée en charge.** L'application doit servir plus de 200 utilisateurs sur plusieurs projets, dont environ 50 actifs en même temps (hypothèse **À confirmer**). Conçois-la pour cela dès l'étape 1 :

- **Cibles de temps de réponse** (95e centile, sous charge) : ouverture d'un document de 500 exigences en moins de 1 s, enregistrement local en moins de 200 ms, vue de couverture d'un projet de 5 000 exigences en moins de 1 s.
- **API sans état**, plusieurs instances derrière un répartiteur de charge ; les workers tournent en instances séparées et se partagent la file sans traiter deux fois la même tâche.
- **Statuts en cache** par projet et par régression, recalculés de façon incrémentale à chaque changement ; jamais le graphe complet à chaque requête.
- **Mises à jour en direct** (SSE ou WebSocket) : verrous de section avec le nom de leur détenteur, modifications faites par d'autres, fin de synchro, nouvelle régression importée.
- **Synchro Tuleap mutualisée** : une seule synchro entrante par tracker pour tous les utilisateurs, via un compte de service en lecture (**À confirmer**), avec un débit d'appels plafonné et configurable pour ne pas aggraver la lenteur de Tuleap. Les droits de lecture de chaque utilisateur restent appliqués à partir des permissions Tuleap mises en cache par tracker. Les écritures partent toujours avec le jeton de l'utilisateur.
- **Isolation par projet** : données, configuration et administration séparées ; un utilisateur ne voit que les projets auxquels il a accès.
- **Connexion** par le SSO de l'entreprise (LDAP ou OIDC, **À confirmer**), avec quatre rôles applicatifs par projet (lecteur, rédacteur, approbateur, administrateur) qui s'ajoutent aux droits Tuleap.
- **Tâches lourdes en arrière-plan** : imports, exports et générations de vplanx, avec notification à la fin.
- **Exploitation** : journal d'audit des actions d'administration, métriques et alertes (temps de réponse, profondeur des files, erreurs de synchro), sauvegardes quotidiennes avec restauration testée.

**Enseignements du prototype à 9 000 exigences.** Trois choix ont été nécessaires pour garder l'édition fluide ; reprends-les côté serveur comme côté navigateur :

- l'éditeur ne charge qu'un document niveau × sous-système à la fois (600 exigences au plus) ;
- l'index de traçabilité n'est recalculé que pour le document modifié, le reste restant en cache ;
- les statuts sont calculés avec mémorisation sur tout le graphe, et la vue de couverture affiche un sous-système à la fois, avec un tableau de synthèse par sous-système au-dessus.

Qualité : typage strict, tests unitaires sur le calcul des statuts et la détection de cycles, tests d'intégration sur la synchro avec un faux serveur Tuleap, tests de bout en bout sur l'éditeur (Playwright).

## Éditeur

L'édition doit être proche de Word dans une page web : titres, gras, italique, listes, tableaux, images, annuler et rétablir, collage propre depuis Word. Utilise Tiptap v3 (licence MIT) et uniquement des extensions open source.

Le document est stocké en JSON structuré, jamais en HTML ou en blob. Il contient trois sortes de contenus :

- **Prose libre** : titres, paragraphes, tableaux, images et diagrammes. Elle est versionnée par l'outil.
- **Nœud exigence** : bloc qui contient l'énoncé (paragraphes, listes, images, diagrammes et, si besoin, un tableau de paramètres structuré) et porte en attributs l'ID, la branche, les liens amont, les plans requis, le statut de revue et, pour un item de plan, la méthode, les métriques et l'objectif. Il référence l'artefact Tuleap correspondant.
- **Référence** : nœud en ligne qui cite une autre exigence par son ID. Il s'affiche barré si la cible n'existe plus.

Comportements attendus :

- L'ID de chaque exigence est affiché dans la marge gauche, précédé d'une pastille de statut, avec ses liens amont en dessous.
- Un bouton « Nouvelle exigence » insère un bloc après le bloc courant avec un ID attribué.
- Un bouton « Citer » ouvre une recherche par ID ou par texte.
- Une exigence ne peut pas contenir une autre exigence.
- Les ID sont uniques dans tout le projet, contrôlés dans l'éditeur et côté serveur.
- Sur mobile, la marge passe au-dessus du bloc et le panneau devient un tiroir en bas d'écran.

Pas de coédition temps réel dans le MVP : un verrou par section, posé à l'ouverture en édition et libéré après inactivité.

## Dessins et diagrammes

Une exigence peut contenir des dessins, au même titre que la prose libre. Trois types de blocs sont prévus :

| Bloc | Usage | Stockage | Diff dans l'historique |
| --- | --- | --- | --- |
| Chronogramme WaveDrom | Signaux, horloges, bus, latences | Source JSON dans le document | Lisible, sur le code source |
| Diagramme Mermaid | Machines d'état, séquences, flux | Source texte dans le document | Lisible, sur le code source |
| Image | Captures, schémas existants, reprise de documents Word | Fichier PNG, JPEG ou SVG identifié par son empreinte SHA-256 | Avant et après côte à côte |

Dans le contenu contractuel d'une exigence, privilégie les diagrammes décrits en texte : chaque modification y est un diff lisible et une baseline fige exactement le dessin. Les images servent surtout à reprendre l'existant. Le dessin libre éditable (draw.io, Excalidraw) reste réservé à la prose libre (**À confirmer**).

**Édition.** Les diagrammes sont rendus à l'affichage. « Modifier le code » ouvre un éditeur avec aperçu en direct ; une erreur de syntaxe s'affiche sans perdre le code. La barre d'outils a deux boutons, Chronogramme et Diagramme ; les images s'ajoutent par collage, glisser-déposer ou bouton, avec une légende facultative.

**Versionnement.** Modifier le code d'un diagramme ou remplacer une image crée une nouvelle version de l'exigence. L'historique montre le diff du code et les deux rendus. Les fichiers ne sont jamais écrasés.

**Tuleap.** Les images partent en pièces jointes de l'artefact (champ fichier) et sont référencées dans la description. Pour un diagramme, la description porte le rendu (SVG, ou PNG si le nettoyage HTML de Tuleap retire le SVG, **À confirmer**) et le code source est conservé en pièce jointe ou dans un champ texte dédié, pour qu'un aller-retour ne perde rien.

**Import Word.** Les images situées dans une exigence sont extraites et rattachées à cette exigence ; les autres vont dans la prose libre.

**Export.** Les diagrammes sont rendus côté serveur, en SVG pour le PDF et en PNG haute résolution pour le DOCX, avec leur légende. Le rendu ne dépend jamais du navigateur de l'utilisateur.

**Sécurité.** Mermaid tourne en mode strict, et les SVG importés sont nettoyés (aucun script ni lien externe).

## Import depuis Word et Excel

L'outil doit charger des exigences depuis un fichier Word (.docx) ou Excel (.xlsx, .csv), typiquement une spécification client. Un import ne crée jamais d'exigence sans ID : la prose sans ID est importée comme prose libre ou ignorée, jamais transformée en exigence.

**Excel et CSV.** Un assistant fait correspondre les colonnes du fichier aux champs de l'outil : ID, énoncé, niveau, branche, liens « dérive de » et « satisfait », et pour un plan de vérification méthode, métriques et objectif. La correspondance est enregistrée par modèle de fichier pour être réutilisée. Un fichier modèle vierge est téléchargeable.

**Word.** Les exigences sont repérées par une règle configurable par modèle de document :

- un ID en début de paragraphe, selon une expression régulière (par exemple `^[A-Z]{2,4}-\d{3}`) ;
- ou un style Word dédié (par exemple « Exigence ») ;
- ou un tableau dont une colonne porte l'ID.

L'énoncé va jusqu'au prochain ID ou au prochain titre. Les titres, la prose, les tableaux et les images hors exigences deviennent de la prose libre, pour que le document importé garde sa structure. Les liens amont écrits dans le texte (par exemple « Satisfait : ERS-003 ») sont reconnus selon un motif configurable.

**Aperçu avant validation.** Aucun import n'écrit directement. L'outil montre d'abord, par rapport à l'existant : exigences nouvelles, modifiées (avec diff de l'énoncé), inchangées, et absentes du fichier. Il liste aussi les erreurs ligne par ligne : ID en double, lien vers un ID inconnu, cycle, colonne obligatoire vide. Les absentes ne sont jamais retirées automatiquement : l'utilisateur décide.

**Réimport d'une nouvelle révision.** Quand le client envoie une révision (par exemple C puis D), la comparaison se fait par ID. Les exigences dont l'énoncé a changé créent une nouvelle version, et toutes les exigences aval sont signalées « à revoir » jusqu'à ce que quelqu'un confirme ou modifie leurs liens.

**Traçabilité de l'import.** Le fichier source est conservé avec son empreinte SHA-256, son nom, sa révision déclarée, l'auteur et la date. Chaque version d'exigence créée par un import pointe vers lui. Les exigences validées partent ensuite vers Tuleap par l'écriture différée, comme une saisie manuelle.

## Intégration Tuleap

Tuleap est la référence pour les exigences ; l'outil travaille sur un miroir local et se synchronise en arrière-plan. Tuleap est lent : aucun écran ne doit appeler son API en direct.

**Correspondance.** Chaque niveau est rattaché à un ou plusieurs trackers, configurés par projet. Une exigence correspond à un artefact : son titre porte l'ID lisible (ou un champ dédié, **À confirmer**), sa description porte l'énoncé en HTML. Les liens « dérive de » et « satisfait » sont deux types de liens d'artefacts Tuleap distincts, à créer côté Tuleap (noms **À confirmer**). Les sections de prose libre restent dans la base de l'outil.

**Synchro entrante.**

1. Import complet paginé à la première configuration d'un tracker.
2. Puis incrémental : seuls les artefacts modifiés depuis la dernière synchro, toutes les minutes ou sur webhook Tuleap si l'instance en propose.
3. Le miroir stocke pour chaque artefact l'ID du dernier changeset connu.

**Écriture différée.** Une modification est enregistrée immédiatement en local et placée dans une file. Le worker la pousse vers Tuleap avec le jeton de l'utilisateur. Chaque exigence affiche son état : synchronisée, en attente, en conflit ou en erreur.

**Conflits.** Avant d'écrire, le worker vérifie que le dernier changeset Tuleap est celui sur lequel l'utilisateur a travaillé. Sinon, l'exigence passe en conflit et l'interface montre les deux versions côte à côte ; l'utilisateur choisit. Jamais d'écrasement silencieux.

**Robustesse.** Reprise automatique avec délai croissant, aucune perte si Tuleap est indisponible, journal de synchro consultable par exigence.

Avant de coder : mesure les temps de réponse de l'API REST de l'instance réelle (lecture d'un artefact, page de 100 artefacts, écriture) et vérifie ce que le nettoyage HTML de Tuleap conserve dans une description (tableaux, listes imbriquées, images).

## Création des plans de vérification

Les quatre familles de plans se créent de la même façon ; le vPlan DV sert d'exemple ci-dessous. Un plan est un document de son niveau dont les blocs sont des items vérifiables. L'outil propose trois façons de le créer, combinables dans un même document.

**Squelette depuis les exigences.** Depuis un document de spécification (SDS, DDS, ANS ou FWS), l'action « Préparer le plan » crée un brouillon dans le plan correspondant (vPlan DV, plan analogique ou plan de test FW) ; depuis l'ERS ou le SDS, elle prépare aussi le plan de validation :

- un item par exigence feuille qui n'a encore aucun item de ce plan en aval, déjà lié en « satisfait » ;
- l'énoncé pré-rempli avec celui de l'exigence, marqué « à reformuler » tant que personne ne l'a modifié ;
- des sections calquées sur celles du document source, par bloc fonctionnel et par branche.

Lancée à nouveau plus tard, l'action ne crée des items que pour les exigences encore sans item en aval ; elle ne touche jamais aux items existants. L'utilisateur peut ensuite découper un item en plusieurs, ou lier un même item à plusieurs exigences.

**Import ponctuel d'un vPlan existant.** Pour un projet en cours, l'outil importe une fois un vPlan vManager (vplanx) ou un tableau Excel (via l'assistant d'import). Les items arrivent avec leurs métriques et sans lien amont ; la vue Anomalies les liste pour que l'équipe les relie. Après cet import, l'outil devient la seule source du vPlan.

**Saisie manuelle.** Dans l'éditeur, pour les items qui ne découlent pas directement d'une exigence (robustesse, scénarios croisés), à lier ensuite à l'exigence la plus proche.

**Complétion d'un item.** Le panneau Vérification guide la saisie de la méthode, des métriques et de l'objectif :

- les noms de métriques (tests, assertions, covergroups, performances, procédures) sont proposés en autocomplétion à partir des résultats déjà importés (sessions vManager, exports ADE, builds FW, campagnes de validation) ; un nom inconnu reste possible mais est signalé ;
- un objectif inférieur à 100 % exige une justification écrite, conservée dans l'historique ;
- un item sans métrique reste au statut « tracée », visible dans les anomalies.

**Relecture et publication.** Un vPlan se publie vers vManager seulement depuis une version relue : l'outil génère alors le fichier vplanx (section suivante), et la baseline enregistre quelle version du vPlan a servi à quelle session.

## Boucle vPlan, vManager et Jenkins

Le vPlan est rédigé dans l'outil, qui en est la seule source. vManager reçoit un plan généré et renvoie des résultats.

**Aller.** L'outil génère le fichier vPlan que vManager charge (vplanx), avec pour chaque item ses métriques associées. Le format exact et la syntaxe d'association des tests, assertions et covergroups sont **À confirmer** sur la version de vManager utilisée : demande un vPlan réel de l'équipe comme référence avant d'écrire le générateur.

**Retour.** Après chaque régression, un job Jenkins appelle un point d'entrée de l'outil avec l'identifiant de session vManager. Le worker récupère les résultats (API vManager ou rapport exporté, **À confirmer**) et les enregistre par métrique :

| Métrique | Donnée enregistrée | Atteinte si |
| --- | --- | --- |
| test | nombre de runs passés et en échec | aucun échec et au moins un passage |
| assert | violée ou non, couverte ou non | jamais violée et couverte |
| cover | pourcentage | supérieur ou égal à l'objectif de l'item |

Une métrique absente des résultats compte comme non atteinte et est signalée.

**Régression de référence.** Chaque projet a une régression de référence (par défaut la dernière nightly complète). L'utilisateur peut afficher les statuts selon n'importe quelle session importée, pour comparer deux régressions.

Les sessions importées ne sont jamais modifiées : elles font partie des preuves.

## Résultats analogiques, FW et validation

Les plans analogique, FW et de validation se créent comme le vPlan (section Création des plans de vérification). Seule la remontée des résultats diffère.

**Firmware.** Après chaque build de la CI FW, un job appelle l'outil avec l'identifiant du build et le hash Git. Le worker importe les rapports de tests (JUnit XML) et de couverture de code, puis les rattache aux métriques `utest:`, `itest:` et `codecov:` par nom. Les outils et formats exacts de la CI FW sont **À confirmer**.

**Validation.** Une campagne de validation regroupe des exécutions sur un même contexte (versions FW et matériel, banc). Les résultats arrivent par saisie dans l'outil, ou par import d'un fichier Excel ou CSV produit par le banc, avec l'assistant d'import et une correspondance de colonnes enregistrée. Une campagne se clôture explicitement ; ses résultats validés deviennent immuables.

**Simulations analogiques.** Après une campagne de simulation, l'export ADE (CSV ou rapport, **À confirmer**) est importé par l'assistant d'import ou déposé par un job Jenkins. Chaque ligne donne une performance, son coin, sa valeur et la vue simulée ; l'outil la rattache aux métriques `spec:`, `mc:` et `model:` par nom, avec le contexte d'exécution analogique.

**Résultats de référence.** La notion de régression de référence s'étend aux quatre familles : chaque projet désigne une session DV, une campagne de simulation analogique, un build FW et une campagne de validation de référence, affichés ensemble et figés ensemble dans une baseline.

## Historique, baselines et export

**Historique append-only.** Rien n'est jamais modifié ni supprimé en base : chaque changement d'exigence, de lien, de métrique ou de prose crée une nouvelle version avec auteur et horodatage. Une suppression est une version « retirée ». Chaque exigence a un historique consultable et un diff entre deux versions.

**Baselines nommées.** Une baseline fige ensemble :

- la version de chaque exigence et de chaque document, avec le changeset Tuleap correspondant ;
- la version de chaque plan de vérification ;
- les résultats de référence des quatre familles (session DV, campagne de simulation analogique, build FW, campagne de validation) ;
- l'état des discussions et des approbations.

Une baseline ne peut être créée que si toutes les exigences sont synchronisées avec Tuleap (aucune en attente ni en conflit) et, si la règle est active, qu'aucun fil bloquant n'est ouvert sur son périmètre. Elle est immuable. On peut comparer deux baselines : exigences ajoutées, modifiées, retirées, et statuts qui ont changé.

**Exports**, toujours générés depuis une baseline :

- **Matrice de traçabilité** (XLSX et CSV) : une ligne par exigence client, avec la chaîne aval, les métriques et le statut.
- **Documents** (DOCX et PDF) : chaque document rendu avec un gabarit client configurable (page de garde, en-têtes, pieds de page), généré côté serveur.
- **Rapport de preuve** (PDF) : synthèse de couverture, liste des exigences non prouvées avec la raison, identifiants de la baseline et des résultats de référence en tête.

## Vues de l'application

L'application s'organise autour d'un projet, avec douze vues (la douzième, Discussions, est décrite dans la section Discussions sur les exigences). Une barre latérale gauche y donne accès, un sélecteur de sous-système dans l'en-tête restreint les documents, la matrice et les anomalies, et une recherche globale (Ctrl+K) ouvre n'importe quelle exigence par ID ou par texte. Chaque exigence, document, session et baseline a une URL stable (par exemple `/projets/soc-demo/exigences/ERS-IO-012`) qu'on peut citer dans un mail ou un ticket. Les permissions sont celles de Tuleap ; seuls les administrateurs du projet voient l'administration.

### 1. Tableau de bord

Répond à « où en est-on ? » en un écran.

- Répartition des statuts des exigences client, par branche (numérique, analogique, FW) et par famille de plans.
- Évolution du nombre d'exigences client prouvées sur les 30 dernières régressions importées.
- Compteurs d'anomalies par catégorie, chacun cliquable vers la vue Anomalies.
- Derniers résultats importés par famille, état de la synchro Tuleap (en attente, conflits, heure de la dernière synchro), dernières baselines.
- Activité récente : imports, modifications, baselines créées.

### 2. Document

La vue de rédaction, celle du prototype.

```
┌ sommaire ─┬──────────── document ──────────────┬─ panneau ────┐
│ 1 Fonct.  │ [barre d'outils]                     │ ERS-003      │
│ 2 Robust. │ ● ERS-003  Toute erreur de bus… [2] │ Planifiée    │
│ 3 Interf. │                                      │ Traçabilité  │
│           │ ● ERS-006  Le logiciel doit…        │ Vérification │
│ filtres   │   dérive de ERS-003                  │ Historique   │
│           │                                      │ Synchro      │
│           │                                      │ Discussion   │
└───────────┴──────────────────────────────────────┴──────────────┘
```

- Sommaire repliable à gauche, avec par section le nombre d'exigences et la pastille du pire statut.
- Filtres d'affichage : par statut, par branche, exigences seules (prose masquée), anomalies seules.
- Modes lecture et édition ; passer en édition pose le verrou de section.
- Bandeau en haut si le document a des modifications en attente de synchro ou des conflits.

### 3. Panneau d'une exigence

Ouvert depuis n'importe quelle vue, à droite sur poste de travail, en tiroir sur téléphone. Cinq onglets, dont Discussion (décrit dans la section Discussions sur les exigences) :

- **Traçabilité** : statut et sa raison en une phrase, branche à traiter, liens « dérive de » et « satisfait » avec ajout et retrait, exigences dérivées et aval avec leur pastille, références entrantes.
- **Vérification** : pour un item de plan, méthode, métriques avec leur valeur dans les résultats affichés, objectif ; pour une autre exigence, les items de plan qui la prouvent, par famille, et ses plans requis.
- **Historique** : versions avec auteur, date et origine (saisie, import, synchro Tuleap), diff entre deux versions.
- **Synchro** : artefact Tuleap lié avec lien direct, état, dernier changeset, journal.

### 4. Explorateur de traçabilité

Vue graphique centrée sur une exigence : ancêtres à gauche, descendants à droite, jusqu'aux métriques des plans de vérification. Chaque nœud porte sa pastille ; un clic recentre sur lui. Sert à dérouler une chaîne en revue client. Export PNG et SVG.

### 5. Matrice de couverture

Le tableau dense pour l'analyse et l'export.

```
ID        Énoncé               SDS              DDS      vPlan           Statut
ERS-003   Toute erreur de bus  SDS-002 SDS-005  DDS-011  VP-003 VP-005   Planifiée
  ERS-006 Le logiciel doit…    SDS-005          —        VP-005          Prouvée
```

- Une ligne par exigence du niveau choisi (ERS par défaut), dérivées en retrait, une colonne par niveau aval.
- Filtres par statut, branche, section et texte ; tri par colonne.
- Choix de la régression ou de la baseline affichée ; mode comparaison qui surligne les statuts changés entre deux.
- Export XLSX et CSV de la vue filtrée.

### 6. Résultats de vérification

Les plans vus par leurs résultats : une ligne par item, ses métriques, leur résultat et l'objectif. Sélecteur de résultats et comparaison de deux jeux de résultats : métriques qui passent, régressent, apparaissent ou disparaissent. Lien vers la session vManager quand c'est possible.

### 7. Anomalies

Une file de travail, une section par catégorie avec compteur : sans lien amont, non tracées, références cassées, métriques absentes des résultats, « à revoir » après réimport, conflits et erreurs de synchro, plus les catégories propres aux familles de plans (ci-dessous) et aux discussions. Chaque ligne a une action directe (lier, ouvrir, résoudre) et peut être assignée à une personne.

### 8. Import

Un assistant en quatre étapes : fichier et modèle de document, correspondance (colonnes Excel ou règle Word), aperçu (nouvelles, modifiées, inchangées, absentes, erreurs), validation. Un historique liste les imports passés avec fichier source, empreinte et exigences touchées.

### 9. Synchronisation

État de la synchro Tuleap : file d'attente, erreurs, dernière synchro par tracker. Les conflits se résolvent côte à côte (version locale, version Tuleap, diff) avec trois choix : garder la mienne, prendre celle de Tuleap, fusionner à la main.

### 10. Baselines

Liste avec date, auteur, régression de référence et répartition des statuts. Création en deux temps : contrôles préalables (synchro complète, anomalies bloquantes), puis nom et commentaire. Comparaison de deux baselines et lancement des exports.

### 11. Administration

Niveaux et leur ordre, trackers Tuleap et types de liens par niveau, format d'ID par niveau et branche, modèles d'import, gabarits d'export, résultats de référence par défaut, rôles et règles de revue, plans requis par défaut, jeux de coins et règle post-layout.

**Quatre familles de plans dans toutes les vues.** Le tableau de bord montre les statuts par famille (DV, analogique, FW, validation). La matrice de couverture ajoute les colonnes ANS, FWS, plan analogique, plan de test FW et validation, avec un filtre par famille et par branche. La vue Résultats de vérification a un onglet par famille. L'onglet analogique présente une performance par ligne avec ses bornes, le pire coin, la marge et un indicateur pré ou post-layout. L'onglet validation liste les campagnes, leurs exécutions, les caractérisations, les résultats en attente de validation par une seconde personne et ceux « à rejouer ». Les anomalies ajoutent trois catégories : plan requis non couvert, résultat obtenu sur une version périmée, et performance prouvée seulement sur schéma quand le post-layout est exigé.

**Conventions communes.** Couleurs de statut identiques partout (prouvée en vert, planifiée en bleu, en échec en rouge, tracée en cercle gris, non tracée en ambre), toujours accompagnées du libellé pour ne pas dépendre de la couleur seule. Chaque vue vide dit quoi faire pour la remplir. Thème clair et sombre, interface en français, navigation complète au clavier. Sur téléphone, les vues 1, 3, 4, 7 et 12 sont optimisées pour la consultation ; l'édition se fait sur poste de travail.

## Aide en ligne et tutoriel

Avec plus de 200 utilisateurs de métiers différents (numérique, analogique, FW, validation, chefs de projet), l'outil doit s'apprendre seul, sans formation présentielle obligatoire.

**Aide contextuelle.**

- Un bouton « ? » dans chaque vue ouvre, dans un panneau latéral, la page d'aide de cette vue sans quitter le travail en cours.
- Info-bulles sur les termes du modèle : chaque statut, « dérive de » et « satisfait », plans requis, familles, contexte d'exécution, baseline. Chacune renvoie vers l'entrée du glossaire.
- Chaque raison de statut affichée dans le panneau (« pourquoi ce statut ? ») renvoie vers la règle de calcul correspondante.
- La touche `?` affiche la liste des raccourcis clavier.

**Documentation intégrée.**

- Pages en Markdown, en français, versionnées dans le dépôt avec le code (`docs/`) et servies par l'application, avec une recherche plein texte et une URL stable par page.
- Trois guides : utilisateur (par vue et par tâche), administration (configuration des trackers Tuleap, de vManager, des exports ADE, de la CI FW, des modèles d'import et des gabarits d'export), exploitation (déploiement, supervision, sauvegarde, mise à jour).
- Un glossaire et une FAQ.
- Les captures d'écran sont générées automatiquement par les tests Playwright sur le projet de démo, pour rester à jour à chaque version.
- Un journal des nouveautés s'affiche dans l'application après chaque mise à jour.
- Toute modification de comportement visible met à jour la page d'aide concernée dans le même commit.

**Tutoriel interactif.**

- Un projet de démo en bac à sable (le sous-système d'E/S du prototype : sept niveaux, quatre familles de plans, résultats fictifs), propre à chaque utilisateur et réinitialisable. Il n'est jamais synchronisé avec Tuleap.
- Une visite de premier lancement en cinq étapes au plus, qu'on peut passer et relancer depuis le menu d'aide.
- Des parcours guidés par rôle, de 10 à 15 minutes chacun :

| Parcours | Ce que l'utilisateur fait lui-même |
| --- | --- |
| Rédacteur | Créer une exigence, la lier en « satisfait » et en « dérive de », ajouter un chronogramme, ouvrir une discussion |
| Vérification DV | Préparer un vPlan depuis le DDS, ajouter des métriques, lire les résultats d'une régression |
| Analogique | Remplir un tableau de paramètres, lier une métrique `spec:` à une ligne, lire le pire coin et la marge |
| FW et validation | Créer un item de test FW, saisir une campagne de validation, faire valider un résultat |
| Responsable de projet | Lire la couverture, traiter une anomalie, créer une baseline, générer le rapport de preuve |

Chaque étape met en évidence l'élément à utiliser et ne passe à la suivante que lorsque l'action a réellement été faite, pas sur un simple « Suivant ». La progression est enregistrée par utilisateur et reprend là où elle s'est arrêtée. Le contenu des parcours est décrit en données (fichiers JSON ou YAML dans `docs/tutoriels/`), pour être modifié sans toucher au code.

**Contraintes.** Tout fonctionne on-premise, sans service tiers ni contenu chargé depuis Internet. L'aide et le tutoriel respectent les mêmes exigences d'accessibilité que le reste de l'interface : clavier, lecteur d'écran, thème sombre.

## Hors périmètre

Ne construis pas, sauf demande explicite :

- la coédition temps réel (Yjs ou équivalent) ;
- le suivi des modifications façon Word dans l'éditeur ;
- l'import de PDF, et la détection automatique d'exigences dans de la prose sans ID ;
- l'édition du vPlan dans vManager, ou une synchro continue du vPlan de vManager vers l'outil (seul un import ponctuel de migration est prévu) ;
- le pilotage des bancs de validation, l'exécution des tests FW ou le lancement des simulations analogiques : l'outil reçoit les résultats, il ne les produit pas ;
- la conformité à une norme de sûreté (ISO 26262, DO-254) ;
- toute réutilisation du code d'Artidoc (offre commerciale Tuleap Enterprise).

## Livraison par étapes

Livre dans cet ordre. Chaque étape se termine par une démo qui tourne, des tests verts, les pages d'aide de ses fonctions et une note courte de ce qui a été fait, de ce qui reste et des décisions prises. Attends la validation avant de passer à l'étape suivante.

| Étape | Contenu | Critère d'acceptation |
| --- | --- | --- |
| 0. Cadrage | Mesures de l'API Tuleap, test du nettoyage HTML, analyse d'un vPlan réel, d'exports ADE, d'un plan de test FW, d'un plan de validation et de fichiers Word et Excel client, réponses aux points À confirmer, choix de stack justifiés | Une note de deux pages au plus, validée |
| 1. Noyau | Modèle de données append-only, graphe, niveaux configurables (dont ANS, ANV, FWS, FWT, VAL), calcul incrémental des statuts avec plans requis, détection de cycles, isolation par projet, données de démo | Tests unitaires couvrant les cinq statuts, la dérivation, les plans requis et le refus des cycles ; statuts d'un projet de 5 000 exigences recalculés en moins de 1 s |
| 2. Éditeur | Tiptap, nœuds exigence, référence et diagramme (WaveDrom, Mermaid, images), panneau, vue de couverture, verrous et mises à jour en direct, discussions, revue et approbation, en local sans Tuleap | Un document de 200 exigences s'édite sans latence perceptible ; deux utilisateurs voient en direct le verrou de l'autre ; un fil bloquant ouvert empêche l'approbation, et une proposition acceptée crée une nouvelle version |
| 3. Import | Excel et CSV avec correspondance de colonnes, Word par ID, style ou tableau, aperçu, réimport d'une révision | Une spécification client réelle est importée sans perte ; un réimport signale les exigences modifiées et leur aval |
| 4. Tuleap | Miroir, synchro entrante mutualisée, écriture différée, conflits, permissions, SSO | Avec un faux Tuleap lent (2 s par appel), aucune action utilisateur ne dépasse 200 ms ; un conflit est détecté et résolu sans perte ; un utilisateur ne voit jamais un artefact interdit dans Tuleap |
| 5. Vérification DV | Création du vPlan (squelette, import ponctuel, autocomplétion des métriques), génération du vplanx, import des résultats depuis Jenkins, régression de référence | Un squelette couvre toutes les exigences feuilles d'un SDS réel ; un vPlan réel importé puis régénéré est accepté par vManager ; une régression importée change les statuts attendus |
| 6. Analogique, FW et validation | Plan de vérification analogique avec tableaux de paramètres et import des exports ADE (coins, Monte-Carlo, pré et post-layout), plans de test FW et de validation, import des résultats de la CI FW, campagnes de validation avec saisie, import de banc et double validation, contexte d'exécution, résultats à rejouer | Un export ADE réel met à jour les statuts analogiques avec pire coin et marge ; un build FW réel met à jour les statuts FW ; une campagne de validation saisie puis validée prouve une exigence ERS ; un changement de version marque les résultats concernés à rejouer |
| 7. Preuves | Baselines (résultats des quatre familles, discussions et approbations figés ensemble), comparaison, exports matrice, documents et rapport | Un rapport de preuve est régénéré à l'identique depuis une baseline un mois plus tard |
| 8. Charge, exploitation et tutoriel | Tests de charge, supervision, alertes, sauvegardes, procédure de mise à jour sans perte ; projet bac à sable, visite de premier lancement, parcours guidés par rôle, guides d'administration et d'exploitation | Avec 200 utilisateurs simulés dont 50 actifs, les cibles de temps de réponse sont tenues ; une restauration de sauvegarde est réussie ; trois nouveaux utilisateurs terminent seuls le parcours Rédacteur en moins de 15 minutes |

## Consignes de travail

- Commence par lire les ressources du dépôt (section Ressources fournies dans le dépôt), puis l'étape 0 : pose-moi les questions ci-dessous avant d'écrire du code applicatif. Une question à la fois si possible, avec ta recommandation.
- N'invente jamais un format d'API ou de fichier (Tuleap, vManager, ADE, CI FW, bancs) : vérifie sur la documentation de la version installée ou sur un exemple réel, et signale ce que tu n'as pas pu vérifier.
- Les statuts et la traçabilité sont des preuves contractuelles : en cas de doute, un statut plus pessimiste vaut mieux qu'un faux « prouvée ».
- Tiens à jour un `DECISIONS.md` : chaque décision d'architecture en trois lignes (contexte, choix, alternative écartée).
- Petits commits lisibles, un par changement logique.

Questions à me poser à l'étape 0 :

1. Version de Tuleap, édition (Community ou Enterprise) et mode d'authentification possible.
2. Liste des trackers par niveau (dont spécifications analogique et FW, plans analogique, FW et validation) et champs disponibles (ID lisible, branche numérique, analogique ou FW).
3. Noms des types de liens Tuleap à créer pour « dérive de » et « satisfait ».
4. Version de vManager, un vPlan réel de référence et la manière d'en extraire les résultats.
5. Flot analogique : version de Virtuoso et de Spectre, format des exports ADE Assembler ou Maestro, définition des jeux de coins, gestion des versions de cellviews, règle pré ou post-layout pour qu'un résultat compte comme preuve.
6. CI du firmware : outil, format des rapports de tests et de couverture de code, identification des builds.
7. Processus de validation et de caractérisation : bancs utilisés, format des résultats produits, nombre d'échantillons typique, usage éventuel de Tuleap Test Management, besoin d'une double validation des résultats.
8. Plans requis par défaut selon le type d'exigence (par exemple DV et validation pour les exigences client numériques, analogique et validation pour les performances analogiques).
9. Processus de revue : qui approuve quoi, combien d'approbateurs, règle de blocage des baselines ; échanges avec le client par fichiers ou par accès invité ; canaux de notification disponibles (e-mail, Teams, Slack).
10. Format d'ID souhaité et règles de numérotation par niveau et par branche.
11. Exemples réels de fichiers Word et Excel client à importer, et comment les exigences y sont repérées (ID, style, tableau).
12. Gabarit des documents client à reproduire à l'export.
13. Nombre de projets, d'utilisateurs actifs en même temps et d'exigences par projet attendus ; SSO disponible (LDAP ou OIDC) ; possibilité d'un compte de service Tuleap en lecture.
14. Hébergement cible, ressources serveur disponibles et contraintes réseau (accès à Tuleap, vManager, Jenkins, la CI FW, les serveurs de simulation analogique et les bancs depuis le serveur de l'outil).
