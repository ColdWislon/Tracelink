# Journal des décisions

Chaque entrée : contexte, décision, alternatives écartées. Avant de remettre un choix en cause,
lisez la raison ; si elle ne tient plus, ajoutez une nouvelle entrée plutôt que d'effacer l'ancienne.
Ces décisions ont été prises entre le 5 et le 8 octobre 2026 avec Bertrand Dosda.

## Produit

**D-01 — Outil autonome, Tuleap en arrière-plan.**
Tuleap reste la référence des exigences, mais il est lent. L'outil travaille sur un miroir local et
synchronise en arrière-plan ; aucune action utilisateur n'attend un appel Tuleap. Écritures différées,
avec le jeton de l'utilisateur, conflits montrés côte à côte, jamais d'écrasement silencieux.
Écarté : éditer directement dans Tuleap (trop lent, pas d'éditeur document) ; Artidoc (offre Tuleap
Enterprise : seuls titre et description éditables, pas de synchro continue, code non réutilisable).

**D-02 — Deux types de liens seulement : « dérive de » (même niveau) et « satisfait » (niveau supérieur).**
Suffisants pour toutes les chaînes discutées. Dans le prototype, le type se déduit du préfixe d'ID ;
l'application finale peut les stocker explicitement (ils deviennent deux types de liens Tuleap).

**D-03 — Cinq statuts calculés, règle de la pire branche.**
Une preuve contractuelle doit être pessimiste : une exigence n'est prouvée que si toutes ses branches
le sont. Ordre Non tracée < Tracée < En échec < Planifiée < Prouvée. « En échec » est sous « Planifiée »
car un échec est plus grave qu'une preuve incomplète. Statuts jamais stockés, toujours recalculés.

**D-04 — Plans requis par exigence.**
Sans eux, une exigence client couverte uniquement en simulation paraîtrait prouvée alors que le client
attend aussi une validation sur silicium. Une famille requise sans item en aval rend l'exigence non tracée.

**D-05 — Quatre familles de plans au même modèle (DV, analogique, FW, validation).**
Même structure d'item (énoncé, liens, méthode, métriques typées, objectif) ; seuls les types de
métriques et la source des résultats changent. Évite quatre outils différents.

**D-06 — Analogique : critères au pire coin, post-layout exigible.**
Une performance `spec:` n'est atteinte que si elle tient sur tous les coins. Un résultat sur schéma seul
reste « Planifiée » quand le projet exige le post-layout. Monte-Carlo jugé sur le Cpk (≥ 1,33 par défaut).

**D-07 — Un document = un niveau × un sous-système ; ID `NIVEAU-SOUS_SYSTÈME-NNN`.**
Constaté sur le prototype à 9 182 exigences : un document par niveau entier (jusqu'à 3 000 blocs) rend
l'éditeur inutilisable et les listes illisibles. Le format d'ID reste **À confirmer** avec l'équipe.

**D-08 — Diagrammes décrits en texte (WaveDrom, Mermaid) plutôt qu'en dessin libre.**
Dans un contenu contractuel, un diff lisible et une baseline exacte comptent plus que la liberté de dessin.
Les images restent possibles pour reprendre l'existant.

## Technique

**D-09 — Éditeur Tiptap v3.**
Licence MIT, schéma sur mesure (nœuds typés exigence, référence, diagramme), écosystème ProseMirror.
Écarté : CKEditor 5 (GPL ou licence commerciale, suivi des modifications payant) ; Lexical
(écosystème plus mince pour les tableaux et le collage depuis Word).

**D-10 — React + TypeScript, Vite pour le build.**
Recrutement, bibliothèques disponibles, et c'est la pile où les agents de code sont les plus fiables.
Vue a été envisagé ; pas de raison forte de le préférer. Vite est l'outil de build, pas un framework.

**D-11 — PostgreSQL append-only, fichiers adressés par empreinte, déploiement docker compose on-premise.**
L'historique est une preuve : rien n'est modifié ni supprimé. Pas de cloud tiers (données client).
Langage du backend (Node ou Python) : **non tranché**, à choisir selon l'équipe qui maintiendra.

**D-12 — Le prototype est jetable.**
Un seul fichier JS sans framework, état en localStorage : parfait pour valider l'ergonomie, inadapté
à 200 utilisateurs. SPEC.md demande de repartir de zéro et de reprendre seulement les règles et l'ergonomie.

**D-13 — Données de démo générées de façon déterministe.**
Graine fixe : tout le monde voit les mêmes exigences et statuts, les maquettes peuvent citer des IDs,
et seuls les documents modifiés sont sauvegardés (le reste est régénéré). Les exigences client racines
sont rédigées à la main pour que la démo soit crédible ; les niveaux inférieurs viennent de gabarits.
Conséquence : modifier l'ordre des tirages dans seed.js change les IDs (voir AGENTS.md, section 6).

## Design

**D-14 — Design system « Trace » : le document d'abord.**
Texte des exigences en IBM Plex Serif sur fond papier, interface en IBM Plex Sans, ID suspendu dans
une marge à gauche, filets plutôt qu'ombres. Polices servies localement (on-premise).
`tokens.json` est la source ; `tokens.css` est généré par `outils/generer_tokens_css.py`.

**D-15 — Couleurs de statut fixes, jamais seules.**
Prouvée vert, Planifiée bleu (couleur d'accent), En échec rouge, Tracée cercle gris vide, Non tracée ambre.
L'ambre a été foncé (#94600A au lieu de #B7790F) pour atteindre le contraste AA en texte.
Vert et rouge ont une clarté proche : un libellé ou une forme accompagne toujours la couleur.

**D-16 — Maquettes générées par script plutôt que dessinées.**
Elles reprennent les vraies données du prototype (statuts, IDs, compteurs) et se régénèrent quand
la démo change. Les éléments sans données (historique, discussions, synchro) sont inventés mais
cohérents ; la liste est en tête de `outils/generer_maquettes.py`.

**D-17 — Vues optimisées téléphone : consultation seulement.**
Tableau de bord, panneau d'exigence (en tiroir), explorateur, anomalies et discussions.
L'édition se fait sur poste de travail.

## Organisation

**D-18 — SPEC.md écrit comme un prompt d'agent, livraison en 9 étapes avec validation entre chaque.**
L'étape 0 (cadrage) pose 14 questions avant toute ligne de code applicatif. Les formats externes
(Tuleap, vManager, ADE, CI FW, bancs) ne doivent jamais être inventés : exemples réels obligatoires.
