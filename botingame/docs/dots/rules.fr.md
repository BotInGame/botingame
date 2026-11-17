# {{name}}

Une grille de points. Les joueurs tracent à tour de rôle un trait entre deux points voisins. Tracez le quatrième côté
d'une case et elle est à vous, et vous rejouez. Quand tous les traits sont tracés, celui qui a le plus de cases gagne.
Le mathématicien français Édouard Lucas l'a décrit en 1889 sous le nom de *pipopipette*.

## Comment on y joue

Sur papier, les joueurs dessinent une grille de points et relient à tour de rôle deux points voisins par un petit
trait, à l'horizontale ou à la verticale, jamais en diagonale. Celui qui ferme une case y inscrit son initiale. Sur
BotInGame, le siège 0 joue en orange et commence, le siège 1 joue en bleu : traits et cases prennent la couleur du
joueur qui les a tracés ou fermées.

## La grille

La grille a **8×8 points**, qui forment **7×7 = 49 cases**. Les lignes et les colonnes de points sont numérotées de 0 à
7 depuis le haut et depuis la gauche. Un trait se désigne par sa sorte et son premier point (son bout gauche, ou son
bout du haut) :

- `["h", ligne, colonne]`, un trait horizontal du point (ligne, colonne) au point à sa droite ;
- `["v", ligne, colonne]`, un trait vertical du point (ligne, colonne) au point en dessous.

Ici, orange a tracé `["h", 2, 1]`, du point (2, 1) au point (2, 2), et bleu `["v", 4, 5]`, du point (4, 5) au point
(5, 5).

![La grille de points, lignes et colonnes numérotées ; les traits h,2,1 et v,4,5 sont entourés](figure:grid)

## Fermer une case : rejouer

Un trait qui trace le **quatrième côté d'une case** la donne au joueur qui l'a tracé, et ce joueur **rejoue**. Sinon,
la main passe. Ici, orange trace le côté droit d'une case dont les trois autres côtés étaient tracés, la prend, et la
grille est de nouveau encadrée en orange : c'est encore à orange de jouer.

![Orange ferme une case avec son quatrième côté et rejoue](figure:close)

## Cas particulier : un trait, deux cases

Un trait à l'intérieur de la grille est un côté de deux cases. S'il est le dernier côté des deux, il les prend **toutes
les deux**, et le joueur ne rejoue toujours qu'une fois. Un trait au bord de la grille n'est le côté que d'une case.

![Un seul trait orange ferme deux cases à la fois](figure:double)

## La fin

Le Match se termine quand les 112 traits sont tracés, ce qui veut dire aussi que les 49 cases sont prises. Le joueur qui
a le plus de cases gagne. Avec 49 cases, un nombre impair, un Match joué jusqu'au bout ne peut pas finir à égalité. Une
victoire rapporte 1 et une défaite 0. Ici, bleu gagne par 27 cases à 22.

![Tous les traits sont tracés : bleu a 27 cases et orange 22](figure:end)
