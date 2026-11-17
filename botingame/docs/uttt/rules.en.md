# {{name}}

Tic-tac-toe on nine boards at once. Win small boards to claim squares of the big one; three in a line wins the Match.
The twist: the cell you pick decides where your opponent must play next. It is a pen-and-paper variant of tic-tac-toe
that became widely known in the 2010s.

## How people play it

Two players, X and O, draw a large tic-tac-toe grid and a small one inside each of its nine squares. They take turns
drawing their mark in a cell of a small board. On BotInGame, X is seat 0, drawn in orange, and O is seat 1, in blue.

## The board

Nine small boards sit in a 3×3 grid and form one big board. The boards are numbered **0 to 8**, left to right and top
to bottom, and the cells inside each board are numbered the same way: the centre board shows its cell numbers here.
A move names a board and a cell: `[board, cell]`.

![The board: the small boards numbered 0 to 8, and the cells of the centre board numbered 0 to 8](figure:board)

## The first move

X moves first and may play **anywhere**. Here X plays the top-right cell (cell 2) of the centre board (board 4): the
move `[4, 2]`.

![X plays the top-right cell of the centre board](figure:first)

## Your cell sends your opponent

The cell you choose sends your opponent to the **matching board**. X played the top-right cell, so O must play in the
top-right board (board 2). O then plays the bottom-left cell of that board, which sends X to the bottom-left board
(board 6), now outlined for X.

![Arrows: X's top-right cell sends O to the top-right board; O's bottom-left cell sends X to the bottom-left board](figure:sent)

## Winning a small board

Three marks in a line (a row, a column or a diagonal) win a small board: it gets a big mark, and its empty cells can
**never be played** again. Here X completes the left column of the bottom-middle board (board 7).

![X completes a column in the bottom-middle board, which now shows a big X](figure:won)

## Edge case: sent to a finished board, play anywhere

If the board you are sent to is already decided (won or full), you are free: play in **any board still open**. This is
checked after the move. Here X wins the top-middle board (board 1) by playing its centre cell, a move that would send O
to board 1 itself. Board 1 is closed, so every open board is outlined for O.

![X wins the top-middle board with its centre cell; every other board is outlined for O](figure:free)

## Edge case: a full board with no line is dead

A small board whose nine cells fill up with no line is a draw: it is **greyed out**, counts for neither player, and can
never be part of a winning line on the big board. Here X fills the last cell of the middle-right board (board 5).

![The middle-right board is full with no line, and greyed out](figure:dead)

## Winning the Match

Win three small boards in a line on the big board, and you win the Match at once. When every small board is decided
(won or dead) and nobody has such a line, the Match is a draw. A win scores 1 and a loss 0; a draw gives each player ½.

![X has won the three boards of the middle row, with a gold line through them](figure:match)
