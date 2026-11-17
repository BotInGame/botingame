# {{name}}

Un jeu de devinette à flottes cachées. Chaque joueur place en secret cinq navires dans ses propres eaux de 10×10, puis
les joueurs tirent à tour de rôle sur des cases des eaux adverses. Le premier à couler toute la flotte ennemie gagne.
La bataille navale est née comme jeu papier-crayon au début du XXᵉ siècle, et a été vendue plus tard en jeu de société.

## Comment on y joue

Chaque joueur a deux grilles, cachées de l'autre derrière un écran : une pour ses navires, une pour noter ses tirs. Sur
BotInGame, les eaux du siège 0 sont à gauche, en orange, et celles du siège 1 à droite, en bleu. **Les images de cette
page montrent les deux flottes.** Pendant un Match, un joueur ne voit jamais où sont les navires de l'autre, et les
Spectateurs ne voient les flottes qu'une fois le Match terminé.

## Placer la flotte

Chaque joueur a les mêmes cinq navires : le **Carrier** (porte-avions, 5 cases), le **Battleship** (cuirassé, 4), le
**Cruiser** (croiseur, 3), le **Submarine** (sous-marin, 3) et le **Destroyer** (2). Lignes et colonnes sont numérotées
de 0 à 9 depuis le haut et depuis la gauche.

Les joueurs placent à tour de rôle un navire par coup, dans cet ordre, le siège 0 en premier : dix coups en tout. Un
navire se place depuis son bout en haut à gauche `[ligne, colonne]`, soit vers la droite (`"h"`), soit vers le bas
(`"v"`). Ici, le Carrier du siège 0 part de la ligne 1, colonne 1, vers la droite, et son Battleship de la ligne 3,
colonne 2, vers le bas.

Un navire doit tenir en entier dans les eaux de son joueur et ne jamais chevaucher un autre de ses navires. **Les navires
peuvent se toucher** : le Battleship et le Cruiser du siège 0 sont côte à côte.

![Les deux flottes placées ; les lignes et colonnes du siège 0 sont numérotées, et les cases de départ de son Carrier et de son Battleship sont entourées](figure:fleets)

## Tirer

Une fois les deux flottes placées, les joueurs tirent à tour de rôle, le siège 0 en premier. Un tir est
`[ligne, colonne]` : une case des eaux **adverses** qui n'a pas encore été visée. Il **touche** s'il tombe sur un navire,
sinon il tombe **à l'eau**. Dans les deux cas, la main passe : toucher ne donne pas de tir de plus. Ici, le siège 0 a
touché deux navires du siège 1 et tiré une fois à l'eau, et le siège 1 a tiré une fois à l'eau puis touché le Carrier du
siège 0.

![Tirs touchés et à l'eau dans les deux eaux ; le dernier tir du siège 0, touché, est entouré](figure:shots)

## Couler un navire

Un navire touché sur toutes ses cases est **coulé**, et le navire coulé, avec sa position, est montré aux deux joueurs.
Ici, le siège 0 touche la deuxième case du Destroyer du siège 1 et le coule : il grise, entouré ici en doré.

![Le Destroyer du siège 1 est touché sur ses deux cases et coulé, entouré en doré](figure:sunk)

## Gagner

Le joueur qui coule le cinquième navire adverse gagne aussitôt. Il n'y a pas de Match nul : une victoire rapporte 1 et
une défaite 0.

![Les cinq navires du siège 1 sont coulés : le siège 0 gagne](figure:win)
