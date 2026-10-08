Trace est un outil de traçabilité des exigences pour des équipes de conception et de vérification de circuits. L'interface sert un seul but : montrer, pour chaque exigence, par quoi elle est raffinée, par quoi elle est vérifiée et avec quel résultat. Tout ce qui ne sert pas cette lecture est retiré.

## Principes

- **Le document d'abord.** Les exigences se lisent comme une spécification : texte en `prose` (serif) sur `paper`, l'interface autour en `sans`. Ne mettez jamais l'énoncé d'une exigence dans une carte ou un tableau quand il peut rester dans le flux du document.
- **L'identifiant suspendu.** Chaque exigence porte son ID dans une marge de `space-margin` à gauche du texte, en `req-id` couleur `accent`, précédé de sa pastille de statut, avec ses liens amont en dessous en `caption` couleur `ink-muted`. Sur téléphone, la marge passe au-dessus du texte, sur une ligne.
- **Filets, pas d'ombres.** Séparez par des filets `rule` de 1px. Pas d'ombres portées, sauf le tiroir du panneau sur téléphone. Pas de dégradés.
- **Le statut se lit sans la couleur.** Une pastille ou un badge de statut est toujours accompagné de son libellé, dans le panneau, la matrice et les exports.

## Couleurs et statuts

Les cinq statuts ont une couleur fixe, identique dans toutes les vues :

| Statut | Token | Pastille |
| --- | --- | --- |
| Prouvée | `ok` | disque plein |
| Planifiée | `accent` | disque plein |
| En échec | `danger` | disque plein |
| Tracée | `ink-muted` | cercle vide (contour 1,5px) |
| Non tracée | `gap` | disque plein |

- Badge de statut : texte `label` dans la couleur du statut, sur un fond de cette couleur à 13 % d'opacité, rayon `radius-sm`.
- Pastilles de famille (DV, ANA, FW, VAL) : 10px de texte en capitales, fond plein de la couleur du statut le plus faible de la famille, texte `on-accent` ; famille sans item : contour `rule` ; famille requise sans item : contour pointillé `gap`.
- Exigence active : marge gauche du texte en `accent` (2px) et fond `req`. Exigence inactive : marge `rule`.
- Un seul bouton principal par vue, en aplat `accent` avec texte `on-accent`. Les autres actions sont des boutons texte `ink` sur fond transparent, `req` au survol.
- `ok` et `danger` ont une clarté proche : ne les distinguez jamais par la seule couleur.

## Typographie

IBM Plex Sans pour l'interface, IBM Plex Serif pour le texte des documents, chargées depuis Google Fonts. Chiffres tabulaires (`font-variant-numeric: tabular-nums`) pour les ID, les compteurs et les résultats. `title` pour le titre d'un document ou d'une vue, `heading` pour une section, `body-ui` pour le texte d'interface, `label` pour les boutons et les en-têtes de colonnes, `caption` pour les métadonnées.

## Rédaction

Interface en français, phrases courtes, majuscule au premier mot seulement. Les libellés de statut s'écrivent exactement : Prouvée, Planifiée, En échec, Tracée, Non tracée. Les liens amont s'écrivent « dérive de » (même niveau) et « satisfait » (niveau supérieur). Une raison de statut tient en une phrase et nomme ce qui manque (« Plan requis sans aucun item : Validation »).

## Iconographie

Pas de logo ni de jeu d'icônes pour l'instant : le nom s'écrit en `sans` 600, et les actions utilisent des libellés texte plutôt que des pictogrammes.
