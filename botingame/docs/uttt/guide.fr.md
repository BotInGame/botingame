# {{name}}

Clé du Jeu `{{key}}`, version des règles {{version}}.

Le morpion sur neuf grilles à la fois : on gagne des petites grilles, et trois grilles gagnées alignées gagnent le Match. La case de chaque coup décide dans quelle grille l'adversaire joue ensuite.

Ce guide est pour les développeurs de Bots. Les règles illustrées, avec des images de chaque règle, sont sur https://botingame.com/arenas/{{arena}}/rules.

## Les règles

**Plateau.** Neuf sous-grilles numérotées de 0 à 8 ligne par ligne : 0, 1, 2 en haut, 3, 4, 5 au milieu, 6, 7, 8 en
bas. Chaque sous-grille a neuf cases numérotées de la même façon (la case 0 est sa case en haut à gauche, la case 8 sa
case en bas à droite).

```
 grille 0 | grille 1 | grille 2          case 0 | case 1 | case 2
----------+----------+----------        --------+--------+--------
 grille 3 | grille 4 | grille 5          case 3 | case 4 | case 5
----------+----------+----------        --------+--------+--------
 grille 6 | grille 7 | grille 8          case 6 | case 7 | case 8
```

**Mise en place.** Toutes les cases sont vides. Le siège 0 joue X et commence ; le siège 1 joue O.

**Ordre de jeu.** Les sièges alternent, un coup chacun, le siège 0 en premier.

**Un coup légal** est `[grille, case]` : une case vide d'une sous-grille encore indécise (ni gagnée ni pleine), et :

- si une sous-grille est **imposée**, le coup doit être dans cette sous-grille ;
- si aucune n'est imposée (au premier coup du Match, et après un envoi vers une sous-grille décidée), le coup peut être
  dans n'importe quelle sous-grille indécise.

**Où va le coup suivant.** Après un coup dans la case `c`, l'autre siège doit jouer dans la sous-grille `c`. Si la
sous-grille `c` est décidée à ce moment-là (gagnée ou pleine), rien n'est imposé : l'autre siège peut jouer dans
n'importe quelle sous-grille indécise. La vérification se fait *après* le coup : un coup qui gagne ou remplit la
sous-grille `c` elle-même libère donc aussi le coup suivant.

**Décider une sous-grille.** Une sous-grille est gagnée par le siège qui y aligne trois de ses symboles (ligne, colonne
ou diagonale). Une sous-grille dont les neuf cases sont pleines sans alignement est nulle : elle est morte et ne compte
pour aucun siège. Une sous-grille gagnée est fermée pour de bon : ses cases vides ne peuvent plus être jouées.

**Gagner le Match.** Un siège gagne le Match dès qu'il a gagné trois sous-grilles alignées sur la grande grille (ligne,
colonne ou diagonale de sous-grilles). Une sous-grille nulle ne compte jamais dans un alignement.

**Match nul.** Quand toutes les sous-grilles sont décidées (gagnées ou nulles) sans que personne n'ait trois
sous-grilles gagnées alignées, le Match est nul.

**Score.** Le gagnant marque 1 et le perdant 0 ; un Match nul donne ½ à chaque siège.

**Cas particuliers gérés par le code :**

- Être envoyé vers une sous-grille gagnée qui a encore des cases vides : rien n'est imposé, et ces cases restent
  fermées.
- Un coup qui gagne ou remplit la sous-grille même où il envoie l'adversaire : rien n'est imposé.
- Une sous-grille remplie sans alignement : elle devient `"draw"` dans `boards`, ne compte pour personne, et n'est plus
  jamais imposée.
- Un siège a toujours au moins un coup légal tant que le Match dure : une sous-grille imposée est indécise, donc elle
  a une case vide.

## Comment un Bot y joue

Votre Bot est une fonction, `choose_move(view, legal_moves)`. Elle est appelée à chacun de vos tours, avec :

- `view` : la vue de votre siège sur le Match (voir *La vue* plus bas). Le morpion ultime ne cache rien : les deux
  sièges et les Spectateurs voient le même plateau.
- `legal_moves` : tous les coups légaux du moment, en liste de paires `[grille, case]`.

Elle renvoie un coup : l'un des `legal_moves`.

**Sièges.** Les deux sièges sont numérotés 0 et 1, et le siège 0 commence. Votre siège est dans `your_seat` dans la
réponse Match de l'API Bot ; à partir de la vue seule, c'est `view["turn"] % 2`, puisque les sièges alternent. Dans la
vue, une case qui contient `0` porte le symbole du siège 0 (X), et `1` celui du siège 1 (O).

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
| `cells` | 9 tableaux de 9 | `cells[grille][case]` : `null` (vide), `0` (X du siège 0) ou `1` (O du siège 1) |
| `boards` | tableau de 9 | L'état de chaque sous-grille : `null` (indécise), `0` ou `1` (gagnée par ce siège), ou `"draw"` (pleine sans alignement) |
| `forced` | entier ou `null` | La sous-grille où le siège qui joue doit jouer, ou `null` s'il peut jouer dans n'importe quelle sous-grille indécise |
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

Comment la lire : `cells` liste les sous-grilles dans l'ordre, donc la première ligne est la sous-grille 0 (en haut à
gauche), et dans chaque ligne les cases se lisent de gauche à droite, de haut en bas. `boards` indique quelles
sous-grilles sont gagnées (par `0` ou `1`) ou nulles, dans le même ordre. `forced` nomme la sous-grille où ce coup doit
être joué, si bien que tous les coups légaux commencent par ce numéro, sauf s'il vaut `null`. Comme les sièges alternent
et que le siège 0 a commencé, le siège qui joue est `turn % 2`.

## Le coup

Un coup est un tableau JSON de deux entiers, `[grille, case]` :

| Position | Sens | Valeurs |
| --- | --- | --- |
| `[0]` | La sous-grille | 0 à 8, ligne par ligne (0 en haut à gauche, 8 en bas à droite) |
| `[1]` | La case dans cette sous-grille | 0 à 8, ligne par ligne |

Son schéma JSON :

```json
{{move_schema}}
```

Dans l'exemple ci-dessus, `legal_moves` vaut :

```json
{{example_legal_moves}}
```

et `{{example_move}}` est un coup légal : la case qu'il désigne choisit aussi où l'adversaire jouera ensuite.

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
    me = view["turn"] % 2  # mon siège : 0 (X) ou 1 (O)
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
