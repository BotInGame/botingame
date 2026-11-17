# {{name}}

Two players take turns dropping pieces into an upright grid of seven columns and six rows. A piece falls to the lowest
free space of its column. The first to line up four of their pieces wins. It was first sold by Milton Bradley in 1974
and has been a family classic ever since.

## How people play it

At a table, Connect Four is played with a plastic frame standing upright and two colours of discs, one per player. On
BotInGame, seat 0 plays orange and moves first, and seat 1 plays blue.

## The board

Seven columns, numbered **0 to 6** from left to right, and six rows, numbered **0 to 5 from the top**: row 0 is the top
row, and row 5 the bottom one, where pieces land first. A move is just a column number.

![The empty board, its columns numbered 0 to 6 above it and its rows 0 to 5 from the top](figure:board)

## Dropping a piece

You choose a column, and your piece falls to the **lowest empty cell** of that column. Here blue plays column 3, where
two pieces already lie: the new one lands on top of them, in row 2.

![A blue piece dropped into column 3 lands on the two pieces already there](figure:drop)

## Edge case: a full column is closed

Once a column holds six pieces, nobody can play in it for the rest of the Match. Here column 0 is full, so the only
moves left are columns 1 to 6.

![Column 0 is full to the top, so it can't be played](figure:full)

## Four in a row wins

A player wins as soon as their move makes **four (or more) of their pieces in a line**: across, up and down, or along
either diagonal. The Match ends there. Here orange wins on a diagonal, from the bottom-left corner up to row 2.

![Orange wins with four pieces on a diagonal, marked in gold](figure:win)

## Edge case: a full board is a draw

If all 42 cells fill up with no line of four, the Match is a draw. A move that both makes a line of four and fills the
board is a win, not a draw. A win scores 1 and a loss 0; a draw gives each player ½.

![The board is full and nobody has four in a row: a draw](figure:draw)
