# {{name}}

Clé du Jeu `{{key}}`, version des règles {{version}}.

Chaque siège place cinq navires dans ses propres eaux cachées de 10×10, puis les sièges tirent à tour de rôle dans les eaux adverses. Le premier à couler toute la flotte ennemie gagne. Votre Bot ne voit jamais la flotte adverse.

Ce guide est pour les développeurs de Bots. Les règles illustrées, avec des images de chaque règle, sont sur https://botingame.com/arenas/{{arena}}/rules.

## Les règles

**Eaux.** Chaque siège a ses propres eaux de 10×10. Lignes et colonnes sont numérotées de 0 à 9 : la ligne 0 est en
haut, la colonne 0 à gauche. Une case est `(ligne, colonne)`.

**La flotte.** Chaque siège a les mêmes cinq navires, placés dans cet ordre :

| Navire | Taille (cases) |
| --- | --- |
| Carrier (porte-avions) | 5 |
| Battleship (cuirassé) | 4 |
| Cruiser (croiseur) | 3 |
| Submarine (sous-marin) | 3 |
| Destroyer (destroyer) | 2 |

**Mise en place.** Aucun navire n'est placé et aucun tir n'est tiré. Le Match a deux phases : le placement, puis les
tirs.

**Placement.** Les sièges jouent à tour de rôle, le siège 0 en premier, chacun plaçant un navire par coup, dans l'ordre
de la flotte : le Carrier du siège 0, le Carrier du siège 1, le Battleship du siège 0, et ainsi de suite, dix coups en
tout (cinq Cycles). Un coup de placement est `[ligne, colonne, sens]` :

- `"h"` place le navire à l'horizontale, à partir de `(ligne, colonne)` vers la droite : cases `(ligne, colonne)` à
  `(ligne, colonne + taille − 1)` ;
- `"v"` le place à la verticale, à partir de `(ligne, colonne)` vers le bas : cases `(ligne, colonne)` à
  `(ligne + taille − 1, colonne)`.

Un placement est légal si le navire tient en entier dans les eaux du siège et ne recouvre aucune case d'un navire de
la même flotte déjà placé. Les navires peuvent se toucher, côte à côte ou bout à bout.

**Tirs.** Une fois les deux flottes placées, les tirs commencent, le siège 0 en premier. Les sièges tirent à tour de
rôle, un tir chacun, touché ou non. Un tir est `[ligne, colonne]` : une case des eaux **adverses** qui n'a pas encore
été visée. Il touche s'il tombe sur un navire, sinon il tombe à l'eau. Un navire touché sur toutes ses cases est coulé,
et le navire coulé (son nom, sa taille et sa position) devient visible des deux sièges.

**Gagner.** Le siège qui coule le cinquième navire adverse gagne aussitôt. Il n'y a pas de Match nul sur le plateau.

**Score.** Le gagnant marque 1 et le perdant 0.

**Cas particuliers gérés par le code :**

- Pendant le placement, un coup à deux valeurs (un tir) est illégal, et pendant les tirs, un coup à trois valeurs (un
  placement) l'est aussi.
- Un navire qui dépasserait des eaux, ou chevaucherait l'un de vos navires, est illégal ; se toucher est permis.
- Une case déjà visée, touchée ou à l'eau, ne peut pas être visée de nouveau.
- Toucher ne donne pas de tir de plus : la main passe à l'autre siège dans tous les cas.

## Comment un Bot y joue

Votre Bot est une fonction, `choose_move(view, legal_moves)`. Elle est appelée à chacun de vos tours, avec :

- `view` : la vue de votre siège sur le Match (voir *La vue* plus bas). Elle contient votre propre flotte mais
  **jamais** celle de l'adversaire : des navires ennemis, vous ne voyez que ceux que vous avez coulés.
- `legal_moves` : tous les coups légaux du moment. Pendant le placement, toutes les positions `[ligne, colonne, sens]`
  légales pour votre prochain navire ; pendant les tirs, toutes les cases des eaux adverses pas encore visées, en
  `[ligne, colonne]`.

Elle renvoie un coup : l'un des `legal_moves`.

**Sièges.** Les deux sièges sont numérotés 0 et 1, et le siège 0 commence dans les deux phases. Votre siège est dans
`your_seat` dans la réponse Match de l'API Bot ; dans la vue, `next` est le siège qui joue, donc à votre tour c'est
votre siège. `boards[0]` et `sunk[0]` portent sur les eaux et la flotte du siège 0, `boards[1]` et `sunk[1]` sur
celles du siège 1.

**Ce que voient les autres.** Les Spectateurs qui regardent en direct ne voient jamais une flotte : les placements sont
cachés, seuls les tirs et les navires coulés sont montrés. Le Match entier, les deux flottes comprises, devient public
une fois terminé.

**Délai de coup.** Chaque coup, placements compris, doit parvenir à la plateforme dans le délai de coup de l'Arène
({{timeout_s}} s sauf si l'Arène en fixe un autre ; la page de l'Arène l'affiche, et la réponse Match le donne en
`timeout_s`, avec `deadline` et `time_left_s`). Un Bot qui le dépasse déclare forfait : il perd, et le Match apparaît
comme son forfait.

**Coups illégaux.** L'API Bot refuse un coup illégal, ou qui ne respecte pas le schéma des coups, avec un `422`. Le
Match continue et votre délai de coup continue de courir : envoyez un coup légal avant la `deadline`, ou vous déclarez forfait. Le SDK note le
refus et rappelle votre `choose_move`. Hors ligne, `botingame play` est plus strict : un coup illégal perd le Match
aussitôt.

**Séries.** Deux Bots appariés dans une Arène jouent une Série au meilleur des X Matchs (la page de l'Arène indique X).
Le Bot qui prend le siège 0 au premier Match est tiré au sort ; ensuite les sièges s'échangent à chaque Match, si bien
que chaque Bot commence à tour de rôle.

Pour essayer un Bot en local contre un Bot aléatoire, avec exactement ces règles, lancez `botingame play mon_bot.py`.

## La vue

La vue est un objet JSON :

| Champ | Type | Sens |
| --- | --- | --- |
| `phase` | chaîne | `"placement"`, `"shooting"` (les tirs) ou `"over"` (terminé) |
| `placed` | 2 entiers | Le nombre de navires placés par chaque siège (0 à 5), celui du siège 0 puis celui du siège 1 |
| `boards` | 2 grilles de 10×10 | `boards[siège][ligne][colonne]` : les eaux de ce siège telles que l'autre siège les a visées : `null` (pas visée), `"hit"` (touché) ou `"miss"` (à l'eau) |
| `sunk` | 2 tableaux de navires | `sunk[siège]` : les navires de ce siège coulés jusqu'ici, chacun avec sa position complète |
| `next` | `null`, `0` ou `1` | Le siège qui joue, ou `null` une fois le Match terminé |
| `turn` | entier | Le nombre de coups joués jusqu'ici, placements compris (les tirs commencent au coup 10) |
| `fleet` | tableau de navires | Vos propres navires placés jusqu'ici, dans l'ordre de placement |

Un navire, dans `fleet` et `sunk`, est un objet :

| Champ | Sens |
| --- | --- |
| `name` | `"Carrier"`, `"Battleship"`, `"Cruiser"`, `"Submarine"` ou `"Destroyer"` |
| `size` | Sa longueur en cases, de 2 à 5 |
| `row`, `col` | Son bout en haut à gauche (ligne, colonne) |
| `dir` | `"h"` (à l'horizontale, vers la droite) ou `"v"` (vers le bas) |

Son schéma JSON :

```json
{{view_schema}}
```

Un exemple : la vue du siège {{example_seat}} après {{example_turn}} coups.

```json
{{example_view}}
```

Comment la lire : vos tirs tombent dans les eaux **adverses**, donc au siège `me` vous tirez sur `boards[1 - me]`, et
`boards[me]` montre les tirs adverses sur vos eaux. Chaque grille liste ses lignes depuis le haut, de gauche à droite.
`sunk[1 - me]` liste les navires ennemis que vous avez coulés ; une case `"hit"` qu'aucun d'eux ne couvre appartient à
un navire encore à flot. `fleet` n'est qu'à vous : la vue de l'adversaire contient sa propre flotte à la place, et
celle de personne d'autre.

## Le coup

Un coup est un tableau JSON, de trois valeurs pendant le placement et de deux pendant les tirs :

| Phase | Coup | Valeurs |
| --- | --- | --- |
| `"placement"` | `[ligne, colonne, sens]` | `ligne`, `colonne` : 0 à 9, le bout du navire en haut à gauche ; `sens` : `"h"` (horizontal) ou `"v"` (vertical) |
| `"shooting"` | `[ligne, colonne]` | 0 à 9 : une case des eaux adverses |

Son schéma JSON :

```json
{{move_schema}}
```

Dans l'exemple ci-dessus, `legal_moves` vaut :

```json
{{example_legal_moves}}
```

et `{{example_move}}` est un coup légal.

## Depuis le code

Les exemples de code de ce guide sont sous [0BSD](https://opensource.org/license/0bsd) : copiez-les dans n'importe quel
Bot, sous n'importe quelle licence, sans mention requise.

### Avec le SDK Python

`botingame new` écrit un Bot de départ comme celui-ci. Mettez le jeton de votre Bot dans `BOTINGAME_TOKEN` (ou dans un
fichier `.env` à côté), puis lancez le fichier, ou `botingame run mon_bot.py` :

```python
import random

import botingame

GAME = "{{key}}"
GAME_VERSION = "{{version}}"  # la version des règles pour laquelle ce Bot a été écrit


def choose_move(view, legal_moves):
    me = view["next"]  # mon siège : 0 ou 1
    if view["phase"] == "placement":
        return random.choice(legal_moves)  # où va mon prochain navire
    return random.choice(legal_moves)  # où va mon prochain tir : à remplacer par votre propre logique


if __name__ == "__main__":
    botingame.run(choose_move, game=GAME, game_version=GAME_VERSION)
```

`botingame.run` entre dans la file de l'Arène du Jeu (`{{arena}}`), attend chacun de vos tours, appelle `choose_move`,
envoie son coup, et continue de jouer jusqu'à ce que vous l'arrêtiez (Ctrl+C).

### Avec l'API Bot directement

Chaque requête porte le jeton de votre Bot : `Authorization: Bearer big_...`. L'URL de base est
`https://api.botingame.com`. Chaque jeton a droit à 10 requêtes par seconde en moyenne, avec de courtes rafales jusqu'à 20.

**1. Entrez dans la file** de l'Arène jusqu'à être apparié. La requête attend jusqu'à `wait` secondes :

```
POST /v1/arenas/{{arena}}/queue?wait=25
```

Elle répond `{"status": "not_matched"}` au bout de `wait` secondes (revenez dans la file sous 10 s pour garder votre
place), ou, une fois apparié :

```json
{"status": "matched", "match_id": "3f9c2a7d1e4b"}
```

**2. Attendez votre tour.** Cette requête attend que ce soit votre tour ou que le Match se termine (au plus `wait`
secondes) :

```
GET /v1/matches/3f9c2a7d1e4b?wait=25
```

À votre tour, elle renvoie votre vue dans `state`, avec `your_turn`, `turn` et `legal_moves` :

```json
{{example_match}}
```

**3. Jouez** votre coup, avec le `turn` auquel vous répondez :

```
POST /v1/matches/3f9c2a7d1e4b/moves
```

```json
{{example_post}}
```

Elle répond avec le Match après votre coup. `422` : le coup est illégal (envoyez-en un autre avant la `deadline`) ;
`409` : le tour est dépassé, ce n'est pas votre tour, ou le Match est terminé (regardez à nouveau le Match). Renvoyer le même `turn` et le même
coup est sans effet, donc une requête perdue sur une connexion coupée peut être retentée.

**4. Recommencez** les étapes 2 et 3 jusqu'à ce que `status` vaille `"finished"`. `result` donne alors le score de
chaque siège (`1` ou `0`) et `reason` dit comment le Match s'est terminé (`"normal"`, ou `"timeout"` quand un Bot a dépassé
son délai de coup). Votre `state` ne contient toujours que votre propre flotte ; la rediffusion du Match sur le site
montre les deux. Dans une Série au meilleur des X, le Match suivant démarre tout seul : `GET /v1/bots/me/match` le
renvoie. Une fois la Série terminée, revenez dans la file.

L'API Bot complète est décrite sur https://api.botingame.com/docs.
