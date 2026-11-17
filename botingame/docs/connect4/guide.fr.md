# {{name}}

Clé du Jeu `{{key}}`, version des règles {{version}}.

Deux sièges lâchent à tour de rôle des pions dans une grille verticale de 7×6 ; un pion tombe dans la case libre la plus basse de sa colonne. Quatre alignés gagnent.

Ce guide est pour les développeurs de Bots. Les règles illustrées, avec des images de chaque règle, sont sur https://botingame.com/arenas/{{arena}}/rules.

## Les règles

**Plateau.** Sept colonnes, numérotées de 0 à 6 de gauche à droite, et six lignes, numérotées de 0 à 5 **depuis le
haut** : la ligne 0 est en haut, la ligne 5 en bas, là où les pions se posent d'abord.

**Mise en place.** Le plateau est vide. Le siège 0 commence.

**Ordre de jeu.** Les sièges alternent, un coup chacun, le siège 0 en premier.

**Un coup légal** est une colonne, de 0 à 6, qui n'est pas pleine (sa case du haut, en ligne 0, est vide). Le pion se
pose dans la ligne vide la plus basse de cette colonne.

**Gagner.** Un siège gagne dès que son coup aligne quatre (ou plus) de ses pions : sur une ligne, dans une colonne ou
sur l'une des deux diagonales. Le Match s'arrête là.

**Match nul.** Quand le plateau est plein (les 42 cases, donc la case du haut de chaque colonne) sans alignement de
quatre, le Match est nul.

**Score.** Le gagnant marque 1 et le perdant 0 ; un Match nul donne ½ à chaque siège.

**Cas particuliers gérés par le code :**

- Une colonne pleine ne fait jamais partie des coups légaux ; la jouer est un coup illégal.
- Un coup qui aligne quatre pions et remplit le plateau est une victoire, pas un Match nul.
- Un alignement de plus de quatre (cinq ou plus) gagne aussi.

## Comment un Bot y joue

Votre Bot est une fonction, `choose_move(view, legal_moves)`. Elle est appelée à chacun de vos tours, avec :

- `view` : la vue de votre siège sur le Match (voir *La vue* plus bas). Le Puissance 4 ne cache rien : les deux sièges
  et les Spectateurs voient le même plateau.
- `legal_moves` : tous les coups légaux du moment, c'est-à-dire les colonnes qui ne sont pas pleines, en entiers.

Elle renvoie un coup : l'un des `legal_moves`.

**Sièges.** Les deux sièges sont numérotés 0 et 1, et le siège 0 commence. Votre siège est dans `your_seat` dans la
réponse Match de l'API Bot ; à partir de la vue seule, c'est `view["turn"] % 2`, puisque les sièges alternent. Sur le
plateau, `0` est un pion du siège 0 et `1` un pion du siège 1.

**Délai de coup.** Chaque coup doit parvenir à la plateforme dans le délai de coup de l'Arène ({{timeout_s}} s sauf si
l'Arène en fixe un autre ; la page de l'Arène l'affiche, et la réponse Match le donne en `timeout_s`, avec `deadline` et
`time_left_s`). Un Bot qui le dépasse déclare forfait : il perd, et le Match apparaît comme son forfait.

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
| `board` | 6 tableaux de 7 | `board[ligne][colonne]`, ligne 0 en haut : `null` (vide), `0` (pion du siège 0) ou `1` (pion du siège 1) |
| `turn` | entier | Le nombre de coups joués jusqu'ici (0 avant le premier coup) |
| `winner` | `null`, `0` ou `1` | Le siège qui a gagné le Match, ou `null` tant qu'il n'est pas décidé, ou s'il est nul |

Son schéma JSON :

```json
{{view_schema}}
```

Un exemple : la vue du siège {{example_seat}} après {{example_turn}} coups.

```json
{{example_view}}
```

Comment la lire : chaque ligne de `board` est une ligne du plateau, et la première est la ligne du **haut** : les pions
s'empilent donc depuis la dernière. Une colonne, c'est `board[0][c]`, `board[1][c]` … `board[5][c]` ; elle est pleine
quand `board[0][c]` n'est pas `null`. Comme les sièges alternent et que le siège 0 a commencé, le siège qui joue est
`turn % 2`.

## Le coup

Un coup est un entier JSON : la colonne où lâcher un pion.

| Valeur | Sens |
| --- | --- |
| `0` à `6` | La colonne, 0 à gauche ; elle ne doit pas être pleine |

Son schéma JSON :

```json
{{move_schema}}
```

Dans l'exemple ci-dessus, `legal_moves` vaut `{{example_legal_moves}}`, et `{{example_move}}` est un coup légal.

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
    me = view["turn"] % 2  # mon siège : 0 ou 1
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

Elle répond avec le Match après votre coup. `422` : le coup est illégal (envoyez-en un autre avant la `deadline`) ;
`409` : le tour est dépassé, ce n'est pas votre tour, ou le Match est terminé (regardez à nouveau le Match). Renvoyer le même `turn` et le même
coup est sans effet, donc une requête perdue sur une connexion coupée peut être retentée.

**4. Recommencez** les étapes 2 et 3 jusqu'à ce que `status` vaille `"finished"`. `result` donne alors le score de
chaque siège (`1`, `0.5` ou `0`) et `reason` dit comment le Match s'est terminé (`"normal"`, ou `"timeout"` quand un Bot a
dépassé son délai de coup). Dans une Série au meilleur des X, le Match suivant démarre tout seul :
`GET /v1/bots/me/match` le renvoie. Une fois la Série terminée, revenez dans la file.

L'API Bot complète est décrite sur https://api.botingame.com/docs.
