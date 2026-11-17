# {{name}}

Game key `{{key}}`, rules version {{version}}.

Tic-tac-toe on nine boards at once: win small boards, and three won boards in a line win the Match. Each move's cell decides which board the opponent plays in next.

This guide is for Bot developers. The rules, illustrated with a picture of each one, are at https://botingame.com/arenas/{{arena}}/rules.

## The rules

**Board.** Nine sub-boards numbered 0 to 8 in row-major order: 0, 1, 2 across the top, 3, 4, 5 across the middle,
6, 7, 8 across the bottom. Each sub-board has nine cells numbered the same way (cell 0 is its top-left cell, cell 8 its
bottom-right cell).

```
 board 0 | board 1 | board 2          cell 0 | cell 1 | cell 2
---------+---------+---------        --------+--------+--------
 board 3 | board 4 | board 5          cell 3 | cell 4 | cell 5
---------+---------+---------        --------+--------+--------
 board 6 | board 7 | board 8          cell 6 | cell 7 | cell 8
```

**Setup.** Every cell is empty. Seat 0 plays X and moves first; seat 1 plays O.

**Turn order.** The seats alternate, one move each, seat 0 first.

**A legal move** is `[board, cell]`: an empty cell of a sub-board that is still undecided (neither won nor full), and:

- if a sub-board is **forced**, the move must be in that sub-board;
- if no sub-board is forced (the first move of the Match, and after being sent to a decided sub-board), the move may
  be in any undecided sub-board.

**Where the next move goes.** After a move in cell `c`, the other seat is forced to play in sub-board `c`. If
sub-board `c` is decided by then (won, or full), nothing is forced: the other seat may play in any undecided
sub-board. This is checked *after* the move, so a move that wins or fills sub-board `c` itself also frees the
next move.

**Deciding a sub-board.** A sub-board is won by the seat that gets three of its marks in a line in it (a row, a column
or a diagonal). A sub-board whose nine cells are full with no such line is a draw: it is dead and counts for neither
seat. A won sub-board is closed for good: its empty cells can never be played.

**Winning the Match.** A seat wins the Match as soon as it has won three sub-boards in a line on the big board (a row,
a column or a diagonal of sub-boards). Drawn sub-boards never count toward a line.

**Draw.** When every sub-board is decided (won or drawn) and no seat has three won sub-boards in a line, the Match is a
draw.

**Scoring.** The winner scores 1 and the loser 0; a draw gives each seat ½.

**Edge cases the code handles:**

- Being sent to a won sub-board that still has empty cells: nothing is forced, and those cells stay closed.
- A move that wins or fills the very sub-board it sends the opponent to: nothing is forced.
- A sub-board filled without a line: it becomes `"draw"` in `boards`, counts for nobody, and nothing is ever forced
  there again.
- A seat always has at least one legal move until the Match ends: a forced sub-board is undecided, so it has an empty
  cell.

## How a Bot plays it

Your Bot is one function, `choose_move(view, legal_moves)`. It is called on each of your turns, with:

- `view`: your seat's view of the Match (see *The view* below). Ultimate Tic-tac-toe hides nothing: both seats and
  Spectators see the same board.
- `legal_moves`: every legal move right now, as a list of `[board, cell]` pairs.

It returns one move: one of `legal_moves`.

**Seats.** The two seats are numbered 0 and 1, and seat 0 moves first. Your seat is in `your_seat` in the Bot API's
Match response; from the view alone it is `view["turn"] % 2`, since the seats alternate. In the view, a cell holding
`0` is seat 0's mark (X) and `1` is seat 1's (O).

**Move timeout.** Each move must reach the platform within the Arena's move timeout ({{timeout_s}} s unless the Arena
sets another; the Arena page shows it, and the Match response gives it as `timeout_s`, with the `deadline` and
`time_left_s`). A Bot that misses it forfeits the Match: it loses, and the Match shows as its forfeit.

**Illegal moves.** The Bot API refuses an illegal move, or one that doesn't match the move schema, with `422`. The
Match goes on and your move timeout keeps running: send a legal move before the deadline or forfeit the Match. The SDK logs the
refusal and asks your `choose_move` again. Offline, `botingame play` is stricter: an illegal move loses the Match at
once.

**Series.** Two Bots paired in an Arena play a best-of-X Series (the Arena page shows X). Who takes seat 0 in the first
Match is random; after that, the seats swap every Match, so each Bot moves first in turn.

To try a Bot locally against a random one, with these exact rules, run `botingame play my_bot.py`.

## The view

The view is a JSON object:

| Field | Type | Meaning |
| --- | --- | --- |
| `cells` | 9 arrays of 9 | `cells[board][cell]`: `null` (empty), `0` (seat 0's X) or `1` (seat 1's O) |
| `boards` | array of 9 | Each sub-board's state: `null` (undecided), `0` or `1` (won by that seat), or `"draw"` (full with no line) |
| `forced` | integer or `null` | The sub-board the seat to move must play in, or `null` when it may play in any undecided sub-board |
| `turn` | integer | How many moves have been played so far (0 before the first move) |
| `winner` | `null`, `0` or `1` | The seat that won the Match, or `null` while it is undecided or drawn |

Its JSON Schema:

```json
{{view_schema}}
```

An example: seat {{example_seat}}'s view after {{example_turn}} moves.

```json
{{example_view}}
```

How to read it: `cells` lists the sub-boards in order, so the first row is sub-board 0 (top left), and within each row
the cells read left to right, top to bottom. `boards` shows which sub-boards are won (by `0` or `1`) or drawn, in the
same order. `forced` names the sub-board this move must be in, so every legal move starts with that number, unless it
is `null`. Since seats alternate and seat 0 moved first, the seat to move is `turn % 2`.

## The move

A move is a JSON array of two integers, `[board, cell]`:

| Position | Meaning | Values |
| --- | --- | --- |
| `[0]` | The sub-board | 0 to 8, row-major (0 top left, 8 bottom right) |
| `[1]` | The cell in that sub-board | 0 to 8, row-major |

Its JSON Schema:

```json
{{move_schema}}
```

In the example above, `legal_moves` is:

```json
{{example_legal_moves}}
```

and `{{example_move}}` is one legal move: the cell it names also chooses where the opponent plays next.

## Using it from code

The code samples in this guide are under [0BSD](https://opensource.org/license/0bsd): copy them into any Bot, under any
licence, no credit needed.

### With the Python SDK

`botingame new` writes a starter Bot like this one. Put your Bot's token in `BOTINGAME_TOKEN` (or a `.env` file next
to it), then run the file, or `botingame run my_bot.py`:

```python
import random

import botingame

GAME = "{{key}}"
GAME_VERSION = "{{version}}"  # the rules version this Bot was written for


def choose_move(view, legal_moves):
    me = view["turn"] % 2  # my seat: 0 (X) or 1 (O)
    return random.choice(legal_moves)  # replace with your own logic


if __name__ == "__main__":
    botingame.run(choose_move, game=GAME, game_version=GAME_VERSION)
```

`botingame.run` queues into the Game's Arena (`{{arena}}`), waits for each of your turns, calls `choose_move` and posts
its move, and plays on until you stop it (Ctrl+C).

### With the raw Bot API

Every request carries your Bot's token: `Authorization: Bearer big_...`. The base URL is `https://api.botingame.com`.
Each token may make 10 requests a second on average, with short bursts of up to 20.

**1. Queue** into the Arena until you are paired. The request holds for up to `wait` seconds:

```
POST /v1/arenas/{{arena}}/queue?wait=25
```

It answers `{"status": "not_matched"}` after `wait` seconds (queue again within 10 s to keep your place), or, once
paired:

```json
{"status": "matched", "match_id": "3f9c2a7d1e4b"}
```

**2. Wait for your turn.** This request holds until it is your turn or the Match ends (at most `wait` seconds):

```
GET /v1/matches/3f9c2a7d1e4b?wait=25
```

On your turn it returns your view as `state`, with `your_turn`, `turn` and `legal_moves`:

```json
{{example_match}}
```

**3. Play** your move, with the `turn` you are answering:

```
POST /v1/matches/3f9c2a7d1e4b/moves
```

```json
{{example_post}}
```

It answers with the Match after your move. `422` means the move is illegal (send another before the deadline); `409`
means the turn is stale, it is not your turn, or the Match has finished (look at the Match again). Sending the same `turn` and move again is
harmless, so a request lost to a dropped connection can be retried.

**4. Repeat** steps 2 and 3 until `status` is `"finished"`. Then `result` gives each seat's score (`1`, `0.5` or `0`) and
`reason` says how it ended (`"normal"`, or `"timeout"` when a Bot missed its move timeout). In a best-of-X Series the next Match starts by
itself: `GET /v1/bots/me/match` returns it. Once the Series is over, queue again.

The full Bot API is described at https://api.botingame.com/docs.
