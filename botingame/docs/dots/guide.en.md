# {{name}}

Game key `{{key}}`, rules version {{version}}.

Two seats take turns drawing lines between neighbouring dots of an 8×8 grid. Drawing the fourth side of a box claims it and gives another move; the seat with more of the 49 boxes wins.

This guide is for Bot developers. The rules, illustrated with a picture of each one, are at https://botingame.com/arenas/{{arena}}/rules.

## The rules

**Grid.** 8 rows and 8 columns of dots, both numbered 0 to 7: row 0 is the top, column 0 the left. Dot `(row, col)` is
in row `row` and column `col`. The dots make 7×7 boxes; box `(row, col)` has dot `(row, col)` as its top-left corner.

**Lines.** There are two kinds:

- a horizontal line `["h", row, col]` joins dot `(row, col)` to dot `(row, col+1)`, with `row` 0 to 7 and `col` 0 to 6
  (8 × 7 = 56 lines);
- a vertical line `["v", row, col]` joins dot `(row, col)` to dot `(row+1, col)`, with `row` 0 to 6 and `col` 0 to 7
  (7 × 8 = 56 lines).

So box `(r, c)` has four sides: `["h", r, c]` (top), `["h", r+1, c]` (bottom), `["v", r, c]` (left) and
`["v", r, c+1]` (right).

```
 (0,0)──h,0,0──(0,1)──h,0,1──(0,2) ...
   │             │
 v,0,0  box 0,0  v,0,1
   │             │
 (1,0)──h,1,0──(1,1) ...
```

**Setup.** No line is drawn and no box is claimed. Seat 0 moves first.

**A legal move** draws one line that is not drawn yet.

**Turn order.** After a move that closes no box, the other seat moves. After a move that closes a box (draws its fourth
side), the box goes to the seat that drew the line, and **the same seat moves again**. A line that closes two boxes at
once (it is a side of both) scores both, and the seat still moves just once more. So a seat may play several moves in
a row, and the seats do not simply alternate.

**End.** The Match ends when all 112 lines are drawn, which also means all 49 boxes are claimed. The seat with more
boxes wins.

**Draw.** With 49 boxes, an odd number, a Match played to the end can't be level. (The code still scores a level count
as a draw.)

**Scoring.** The winner scores 1 and the loser 0; a draw gives each seat ½.

**Edge cases the code handles:**

- A line on the edge of the grid is a side of one box only; any other line is a side of two boxes.
- A line that closes two boxes scores 2 and gives one extra move, not two.
- The move that draws the last line ends the Match: there is no extra move after it.

## How a Bot plays it

Your Bot is one function, `choose_move(view, legal_moves)`. It is called on each of your turns, with:

- `view`: your seat's view of the Match (see *The view* below). Dots and Boxes hides nothing: both seats and
  Spectators see the same grid.
- `legal_moves`: every legal move right now: every line not drawn yet, as `["h", row, col]` or `["v", row, col]`.

It returns one move: one of `legal_moves`. After you close a box, `choose_move` is simply called again for your next
move.

**Seats.** The two seats are numbered 0 and 1, and seat 0 moves first. Your seat is in `your_seat` in the Bot API's
Match response; in the view, `next` is the seat to move, so on your turn it is your seat. A line, a box or a score
marked `0` belongs to seat 0, and `1` to seat 1.

**Move timeout.** Each move must reach the platform within the Arena's move timeout ({{timeout_s}} s unless the Arena
sets another; the Arena page shows it, and the Match response gives it as `timeout_s`, with the `deadline` and
`time_left_s`). Every move has its own timeout, extra moves after a box included. A Bot that misses it forfeits the
Match: it loses, and the Match shows as its forfeit.

**Illegal moves.** The Bot API refuses an illegal move (a line already drawn, say), or one that doesn't match the move
schema, with `422`. The Match goes on and your move timeout keeps running: send a legal move before the deadline or forfeit the Match. The SDK logs the refusal and asks your `choose_move` again. Offline, `botingame play` is stricter: an illegal
move loses the Match at once.

**Series.** Two Bots paired in an Arena play a best-of-X Series (the Arena page shows X). Who takes seat 0 in the first
Match is random; after that, the seats swap every Match, so each Bot moves first in turn.

To try a Bot locally against a random one, with these exact rules, run `botingame play my_bot.py`.

## The view

The view is a JSON object:

| Field | Type | Meaning |
| --- | --- | --- |
| `h` | 8 arrays of 7 | `h[row][col]`, the horizontal line from dot `(row, col)` to `(row, col+1)`: `null` (not drawn), or the seat that drew it, `0` or `1` |
| `v` | 7 arrays of 8 | `v[row][col]`, the vertical line from dot `(row, col)` to `(row+1, col)`: `null`, `0` or `1`, as for `h` |
| `boxes` | 7 arrays of 7 | `boxes[row][col]`, the box whose top-left dot is `(row, col)`: `null` (open), or the seat that closed it |
| `scores` | 2 integers | Boxes claimed so far, seat 0's then seat 1's |
| `next` | `null`, `0` or `1` | The seat to move, or `null` once the Match is over |
| `turn` | integer | How many moves (lines) have been played so far, by both seats |

Its JSON Schema:

```json
{{view_schema}}
```

An example: seat {{example_seat}}'s view after {{example_turn}} moves.

```json
{{example_view}}
```

How to read it: `h` lists the 8 rows of horizontal lines from the top, `v` the 7 rows of vertical lines, and `boxes`
the 7 rows of boxes, all left to right. Box `(r, c)` is closed when `h[r][c]`, `h[r+1][c]`, `v[r][c]` and `v[r][c+1]`
are all drawn. Who drew a line doesn't affect the rules; only who closed a box counts. Because closing a box gives an
extra move, `turn` is not a reliable guide to whose move it is: read `next`.

## The move

A move is a JSON array of three values, `[kind, row, col]`:

| Position | Meaning | Values |
| --- | --- | --- |
| `[0]` | The kind of line | `"h"` (horizontal) or `"v"` (vertical) |
| `[1]` | The row of its first dot (the left end of an `"h"`, the top end of a `"v"`) | 0 to 7 for `"h"`, 0 to 6 for `"v"` |
| `[2]` | The column of its first dot | 0 to 6 for `"h"`, 0 to 7 for `"v"` |

Its JSON Schema:

```json
{{move_schema}}
```

In the example above, `legal_moves` is:

```json
{{example_legal_moves}}
```

and `{{example_move}}` is one legal move.

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
    me = view["next"]  # my seat: 0 or 1
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

It answers with the Match after your move. If your move closed a box, `your_turn` is `true` again in that answer, with a
new `turn` and `legal_moves`. `422` means the move is illegal (send another before the deadline); `409` means the turn is stale, it is not your turn, or the Match has finished (look at the Match again). Sending the same `turn` and move again is harmless, so a
request lost to a dropped connection can be retried.

**4. Repeat** steps 2 and 3 until `status` is `"finished"`. Then `result` gives each seat's score (`1`, `0.5` or `0`) and
`reason` says how it ended (`"normal"`, or `"timeout"` when a Bot missed its move timeout). In a best-of-X Series the
next Match starts by itself: `GET /v1/bots/me/match` returns it. Once the Series is over, queue again.

The full Bot API is described at https://api.botingame.com/docs.
