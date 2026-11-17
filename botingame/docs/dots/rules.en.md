# {{name}}

A grid of dots. The players take turns drawing a line between two neighbouring dots. Draw the fourth side of a box and
you claim it, and you play again. When every line is drawn, the player with more boxes wins. The French mathematician
Édouard Lucas described it in 1889, as *la pipopipette*.

## How people play it

On paper, the players draw a grid of dots and take turns joining two dots next to each other with a short line, across
or down, never diagonally. A player who closes a box writes their initial inside it. On BotInGame, seat 0 plays orange
and moves first, and seat 1 plays blue: lines and boxes take the colour of the player who drew or closed them.

## The grid

The grid has **8×8 dots**, which make **7×7 = 49 boxes**. Rows and columns of dots are numbered 0 to 7 from the top and
from the left. A line is named by its kind and its first dot (its left end, or its top end):

- `["h", row, col]`, a horizontal line from dot (row, col) to the dot on its right;
- `["v", row, col]`, a vertical line from dot (row, col) to the dot below it.

Here orange has drawn `["h", 2, 1]`, from dot (2, 1) to dot (2, 2), and blue `["v", 4, 5]`, from dot (4, 5) to dot
(5, 5).

![The grid of dots, its rows and columns numbered; the lines h,2,1 and v,4,5 are circled](figure:grid)

## Closing a box: play again

A line that draws the **fourth side of a box** claims the box for the player who drew it, and that player **moves
again**. Otherwise the turn passes. Here orange draws the right side of a box whose three other sides were drawn, takes
it, and the grid is framed in orange again: orange to move.

![Orange closes a box with its fourth side and moves again](figure:close)

## Edge case: one line, two boxes

A line inside the grid is a side of two boxes. If it is the last side of both, it claims **both**, and the player still
moves just once more. A line on the edge of the grid is a side of one box only.

![One orange line closes two boxes at once](figure:double)

## The end

The Match ends when all 112 lines are drawn, which also means all 49 boxes are claimed. The player with more boxes wins.
With 49 boxes, an odd number, a Match played to the end can't be level. A win scores 1 and a loss 0. Here blue wins by
27 boxes to 22.

![Every line is drawn: blue has 27 boxes and orange 22](figure:end)
