# {{name}}

Deux joueurs lâchent à tour de rôle des pions dans une grille verticale de sept colonnes et six lignes. Un pion tombe
dans la case libre la plus basse de sa colonne. Le premier à aligner quatre de ses pions gagne. Le Puissance 4 a été
commercialisé pour la première fois par Milton Bradley en 1974 et reste depuis un classique des jeux de société.

## Comment on y joue

Autour d'une table, on joue avec un cadre en plastique dressé à la verticale et deux couleurs de jetons, une par
joueur. Sur BotInGame, le siège 0 joue en orange et commence, le siège 1 joue en bleu.

## Le plateau

Sept colonnes, numérotées de **0 à 6** de gauche à droite, et six lignes, numérotées de **0 à 5 depuis le haut** : la
ligne 0 est en haut, la ligne 5 en bas, là où les pions se posent d'abord. Un coup, c'est simplement un numéro de
colonne.

![Le plateau vide, ses colonnes numérotées de 0 à 6 au-dessus et ses lignes de 0 à 5 depuis le haut](figure:board)

## Lâcher un pion

Vous choisissez une colonne, et votre pion tombe dans la **case vide la plus basse** de cette colonne. Ici, bleu joue la
colonne 3, où deux pions sont déjà posés : le nouveau se pose par-dessus, en ligne 2.

![Un pion bleu lâché dans la colonne 3 se pose sur les deux pions déjà présents](figure:drop)

## Cas particulier : une colonne pleine est fermée

Une fois qu'une colonne contient six pions, plus personne ne peut y jouer jusqu'à la fin du Match. Ici, la colonne 0
est pleine : les seuls coups possibles sont les colonnes 1 à 6.

![La colonne 0 est pleine jusqu'en haut : on ne peut plus la jouer](figure:full)

## Quatre alignés gagnent

Un joueur gagne dès que son coup **aligne quatre (ou plus) de ses pions** : à l'horizontale, à la verticale, ou sur
l'une des deux diagonales. Le Match s'arrête là. Ici, orange gagne sur une diagonale, du coin en bas à gauche jusqu'à la
ligne 2.

![Orange gagne avec quatre pions en diagonale, soulignés en doré](figure:win)

## Cas particulier : un plateau plein est un Match nul

Si les 42 cases se remplissent sans alignement de quatre, le Match est nul. Un coup qui aligne quatre pions et remplit
le plateau est une victoire, pas un Match nul. Une victoire rapporte 1 et une défaite 0 ; un Match nul donne ½ à chaque
joueur.

![Le plateau est plein et personne n'a aligné quatre pions : Match nul](figure:draw)
