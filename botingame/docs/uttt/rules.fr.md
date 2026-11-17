# {{name}}

Le morpion sur neuf grilles à la fois. Gagnez des petites grilles pour prendre les cases de la grande ; trois alignées
gagnent le Match. La subtilité : la case que vous choisissez décide où votre adversaire devra jouer ensuite. C'est une
variante papier-crayon du morpion qui s'est fait connaître dans les années 2010.

## Comment on y joue

Deux joueurs, X et O, tracent une grande grille de morpion et une petite dans chacune de ses neuf cases. Ils tracent
leur symbole à tour de rôle dans une case d'une petite grille. Sur BotInGame, X est le siège 0, en orange, et O le
siège 1, en bleu.

## Le plateau

Neuf petites grilles rangées en 3×3 forment une grande grille. Les grilles sont numérotées de **0 à 8**, de gauche à
droite et de haut en bas, et les cases de chaque grille sont numérotées de la même façon : la grille du centre montre
ici les numéros de ses cases. Un coup désigne une grille et une case : `[grille, case]`.

![Le plateau : les petites grilles numérotées de 0 à 8, et les cases de la grille du centre numérotées de 0 à 8](figure:board)

## Le premier coup

X commence et peut jouer **n'importe où**. Ici, X joue la case en haut à droite (case 2) de la grille du centre
(grille 4) : le coup `[4, 2]`.

![X joue la case en haut à droite de la grille du centre](figure:first)

## Votre case envoie l'adversaire

La case que vous choisissez envoie votre adversaire dans la **grille correspondante**. X a joué la case en haut à
droite, donc O doit jouer dans la grille en haut à droite (grille 2). O joue ensuite la case en bas à gauche de cette
grille, ce qui envoie X dans la grille en bas à gauche (grille 6), désormais encadrée pour X.

![Flèches : la case en haut à droite de X envoie O dans la grille en haut à droite ; la case en bas à gauche de O envoie X dans la grille en bas à gauche](figure:sent)

## Gagner une petite grille

Trois symboles alignés (ligne, colonne ou diagonale) gagnent une petite grille : elle reçoit un grand symbole, et ses
cases vides ne peuvent **plus jamais être jouées**. Ici, X complète la colonne de gauche de la grille du bas au milieu
(grille 7).

![X complète une colonne de la grille du bas au milieu, qui affiche maintenant un grand X](figure:won)

## Cas particulier : envoyé vers une grille terminée, jouez où vous voulez

Si la grille où l'on vous envoie est déjà décidée (gagnée ou pleine), vous êtes libre : jouez dans **n'importe quelle
grille encore ouverte**. La vérification se fait après le coup. Ici, X gagne la grille du haut au milieu (grille 1) en
jouant sa case centrale, un coup qui enverrait O dans la grille 1 elle-même. La grille 1 est fermée, donc toutes les
grilles ouvertes sont encadrées pour O.

![X gagne la grille du haut au milieu avec sa case centrale ; toutes les autres grilles sont encadrées pour O](figure:free)

## Cas particulier : une grille pleine sans alignement est morte

Une petite grille dont les neuf cases se remplissent sans alignement est nulle : elle est **grisée**, ne compte pour
personne, et ne peut jamais faire partie d'un alignement gagnant sur la grande grille. Ici, X remplit la dernière case de
la grille du milieu à droite (grille 5).

![La grille du milieu à droite est pleine sans alignement, et grisée](figure:dead)

## Gagner le Match

Gagnez trois petites grilles alignées sur la grande grille, et vous gagnez le Match aussitôt. Quand toutes les petites
grilles sont décidées (gagnées ou mortes) sans qu'aucun joueur n'ait un tel alignement, le Match est nul. Une victoire
rapporte 1 et une défaite 0 ; un Match nul donne ½ à chaque joueur.

![X a gagné les trois grilles de la ligne du milieu, traversées d'un trait doré](figure:match)
