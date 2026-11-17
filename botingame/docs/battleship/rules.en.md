# {{name}}

A guessing game of hidden fleets. Each player secretly places five ships in their own 10×10 waters, then the players
take turns firing at squares of each other's waters. The first to sink the whole enemy fleet wins. It began as a
pencil-and-paper game early in the 20th century and was later sold as a board game.

## How people play it

Each player has two grids, hidden from the other behind a screen: one for their own ships, one to record their shots.
On BotInGame, seat 0's waters are on the left, in orange, and seat 1's on the right, in blue. **The pictures on this
page show both fleets.** In a Match, a player never sees where the other's ships are, and Spectators see the fleets only
once the Match is over.

## Placing the fleet

Each player has the same five ships: the **Carrier** (5 squares), the **Battleship** (4), the **Cruiser** (3), the
**Submarine** (3) and the **Destroyer** (2). Rows and columns are numbered 0 to 9 from the top and from the left.

The players take turns placing one ship per move, in that order, seat 0 first: ten moves in all. A ship is placed from
its top-left end `[row, col]`, either across to the right (`"h"`) or down (`"v"`). Here seat 0's Carrier starts at row 1,
column 1, across, and its Battleship at row 3, column 2, down.

A ship must lie whole in its player's waters and never overlap another of their ships. **Ships may touch**: seat 0's
Battleship and Cruiser lie side by side.

![Both fleets placed; seat 0's rows and columns are numbered, and the starting squares of its Carrier and Battleship are circled](figure:fleets)

## Shooting

Once both fleets are placed, the players take turns firing, seat 0 first. A shot is `[row, col]`: a square of the
**opponent's** waters that hasn't been shot before. It is a **hit** if it lands on a ship, otherwise a **miss**. Either
way, the turn passes: a hit gives no extra shot. Here seat 0 has hit two ships of seat 1 and missed once, and seat 1 has
missed once and hit seat 0's Carrier.

![Hits and misses on both waters; seat 0's last shot, a hit, is circled](figure:shots)

## Sinking a ship

A ship hit on every one of its squares is **sunk**, and the sunk ship, with its position, is shown to both players.
Here seat 0 hits the second square of seat 1's Destroyer and sinks it: it greys, outlined here in gold.

![Seat 1's Destroyer is hit on both its squares and sunk, outlined in gold](figure:sunk)

## Winning

The player who sinks the opponent's fifth ship wins at once. There are no draws: a win scores 1 and a loss 0.

![All five ships of seat 1 are sunk: seat 0 wins](figure:win)
