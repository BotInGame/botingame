# {{name}}

Clé du Jeu `{{key}}`, version des règles {{version}}.

Deux sièges tracent à tour de rôle des traits entre points voisins d'une grille de 8×8. Tracer le quatrième côté d'une case la prend et donne un coup de plus ; le siège qui a le plus des 49 cases gagne.

Ce guide est pour les développeurs de Bots. Les règles illustrées, avec des images de chaque règle, sont sur https://botingame.com/arenas/{{arena}}/rules.

## Les règles

**Grille.** 8 lignes et 8 colonnes de points, numérotées de 0 à 7 : la ligne 0 est en haut, la colonne 0 à gauche. Le
point `(ligne, colonne)` est sur la ligne `ligne` et la colonne `colonne`. Les points forment 7×7 cases ; la case
`(ligne, colonne)` a le point `(ligne, colonne)` pour coin en haut à gauche.

**Traits.** Il y en a de deux sortes :

- un trait horizontal `["h", ligne, colonne]` relie le point `(ligne, colonne)` au point `(ligne, colonne+1)`, avec
  `ligne` de 0 à 7 et `colonne` de 0 à 6 (8 × 7 = 56 traits) ;
- un trait vertical `["v", ligne, colonne]` relie le point `(ligne, colonne)` au point `(ligne+1, colonne)`, avec
  `ligne` de 0 à 6 et `colonne` de 0 à 7 (7 × 8 = 56 traits).

La case `(l, c)` a donc quatre côtés : `["h", l, c]` (haut), `["h", l+1, c]` (bas), `["v", l, c]` (gauche) et
`["v", l, c+1]` (droite).

```
 (0,0)──h,0,0──(0,1)──h,0,1──(0,2) ...
   │             │
 v,0,0  case 0,0 v,0,1
   │             │
 (1,0)──h,1,0──(1,1) ...
```

**Mise en place.** Aucun trait n'est tracé et aucune case n'est prise. Le siège 0 commence.

**Un coup légal** trace un trait qui n'est pas encore tracé.

**Ordre de jeu.** Après un coup qui ne ferme aucune case, l'autre siège joue. Après un coup qui ferme une case (trace
son quatrième côté), la case revient au siège qui a tracé le trait, et **ce même siège rejoue**. Un trait qui ferme deux
cases d'un coup (il est un côté de chacune) les marque toutes les deux, et le siège ne rejoue qu'une fois. Un siège peut
donc jouer plusieurs coups de suite, et les sièges n'alternent pas simplement.

**Fin.** Le Match se termine quand les 112 traits sont tracés, ce qui veut dire aussi que les 49 cases sont prises. Le
siège qui a le plus de cases gagne.

**Match nul.** Avec 49 cases, un nombre impair, un Match joué jusqu'au bout ne peut pas finir à égalité. (Le code compte
quand même une égalité comme un Match nul.)

**Score.** Le gagnant marque 1 et le perdant 0 ; un Match nul donne ½ à chaque siège.

**Cas particuliers gérés par le code :**

- Un trait au bord de la grille n'est le côté que d'une case ; tout autre trait est le côté de deux cases.
- Un trait qui ferme deux cases rapporte 2 et donne un seul coup de plus, pas deux.
- Le coup qui trace le dernier trait termine le Match : il n'y a pas de coup de plus après lui.

## Comment un Bot y joue

Votre Bot est une fonction, `choose_move(view, legal_moves)`. Elle est appelée à chacun de vos tours, avec :

- `view` : la vue de votre siège sur le Match (voir *La vue* plus bas). Le jeu ne cache rien : les deux sièges et les
  Spectateurs voient la même grille.
- `legal_moves` : tous les coups légaux du moment, c'est-à-dire tous les traits pas encore tracés, sous la forme
  `["h", ligne, colonne]` ou `["v", ligne, colonne]`.

Elle renvoie un coup : l'un des `legal_moves`. Après avoir fermé une case, `choose_move` est tout simplement rappelée
pour votre coup suivant.

**Sièges.** Les deux sièges sont numérotés 0 et 1, et le siège 0 commence. Votre siège est dans `your_seat` dans la
réponse Match de l'API Bot ; dans la vue, `next` est le siège qui joue, donc à votre tour c'est votre siège. Un trait,
une case ou un score marqué `0` appartient au siège 0, et `1` au siège 1.

**Délai de coup.** Chaque coup doit parvenir à la plateforme dans le délai de coup de l'Arène ({{timeout_s}} s sauf si
l'Arène en fixe un autre ; la page de l'Arène l'affiche, et la réponse Match le donne en `timeout_s`, avec `deadline` et
`time_left_s`). Chaque coup a son propre délai, y compris les coups de plus après une case fermée. Un Bot qui le dépasse
déclare forfait : il perd, et le Match apparaît comme son forfait.

**Coups illégaux.** L'API Bot refuse un coup illégal (un trait déjà tracé, par exemple), ou qui ne respecte pas le
schéma des coups, avec un `422`. Le Match continue et votre délai de coup continue de courir : envoyez un coup légal avant la `deadline`, ou vous déclarez forfait. Le SDK note le refus et rappelle votre `choose_move`. Hors ligne, `botingame play` est plus
strict : un coup illégal perd le Match aussitôt.

**Séries.** Deux Bots appariés dans une Arène jouent une Série au meilleur des X Matchs (la page de l'Arène indique X).
Le Bot qui prend le siège 0 au premier Match est tiré au sort ; ensuite les sièges s'échangent à chaque Match, si bien
que chaque Bot commence à tour de rôle.

Pour essayer un Bot en local contre un Bot aléatoire, avec exactement ces règles, lancez `botingame play mon_bot.py`.

## La vue

La vue est un objet JSON :

| Champ | Type | Sens |
| --- | --- | --- |
| `h` | 8 tableaux de 7 | `h[ligne][colonne]`, le trait horizontal du point `(ligne, colonne)` à `(ligne, colonne+1)` : `null` (pas tracé), ou le siège qui l'a tracé, `0` ou `1` |
| `v` | 7 tableaux de 8 | `v[ligne][colonne]`, le trait vertical du point `(ligne, colonne)` à `(ligne+1, colonne)` : `null`, `0` ou `1`, comme pour `h` |
| `boxes` | 7 tableaux de 7 | `boxes[ligne][colonne]`, la case dont le point en haut à gauche est `(ligne, colonne)` : `null` (ouverte), ou le siège qui l'a fermée |
| `scores` | 2 entiers | Les cases prises jusqu'ici, celles du siège 0 puis celles du siège 1 |
| `next` | `null`, `0` ou `1` | Le siège qui joue, ou `null` une fois le Match terminé |
| `turn` | entier | Le nombre de coups (de traits) joués jusqu'ici, par les deux sièges |

Son schéma JSON :

```json
{{view_schema}}
```

Un exemple : la vue du siège {{example_seat}} après {{example_turn}} coups.

```json
{{example_view}}
```

Comment la lire : `h` liste les 8 lignes de traits horizontaux depuis le haut, `v` les 7 lignes de traits verticaux, et
`boxes` les 7 lignes de cases, toutes de gauche à droite. La case `(l, c)` est fermée quand `h[l][c]`, `h[l+1][c]`,
`v[l][c]` et `v[l][c+1]` sont tous tracés. Qui a tracé un trait ne change rien aux règles ; seul compte qui a fermé une
case. Comme fermer une case donne un coup de plus, `turn` ne dit pas de façon fiable à qui c'est le tour : lisez
`next`.

## Le coup

Un coup est un tableau JSON de trois valeurs, `[sorte, ligne, colonne]` :

| Position | Sens | Valeurs |
| --- | --- | --- |
| `[0]` | La sorte de trait | `"h"` (horizontal) ou `"v"` (vertical) |
| `[1]` | La ligne de son premier point (le bout gauche d'un `"h"`, le bout du haut d'un `"v"`) | 0 à 7 pour `"h"`, 0 à 6 pour `"v"` |
| `[2]` | La colonne de son premier point | 0 à 6 pour `"h"`, 0 à 7 pour `"v"` |

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
    return random.choice(legal_moves)  # à remplacer par votre propre logique


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

Elle répond avec le Match après votre coup. Si votre coup a fermé une case, `your_turn` y vaut de nouveau `true`, avec
un nouveau `turn` et de nouveaux `legal_moves`. `422` : le coup est illégal (envoyez-en un autre avant la `deadline`) ;
`409` : le tour est dépassé, ce n'est pas votre tour, ou le Match est terminé (regardez à nouveau le Match). Renvoyer le même `turn` et le même
coup est sans effet, donc une requête perdue sur une connexion coupée peut être retentée.

**4. Recommencez** les étapes 2 et 3 jusqu'à ce que `status` vaille `"finished"`. `result` donne alors le score de
chaque siège (`1`, `0.5` ou `0`) et `reason` dit comment le Match s'est terminé (`"normal"`, ou `"timeout"` quand un Bot a
dépassé son délai de coup). Dans une Série au meilleur des X, le Match suivant démarre tout seul :
`GET /v1/bots/me/match` le renvoie. Une fois la Série terminée, revenez dans la file.

L'API Bot complète est décrite sur https://api.botingame.com/docs.
