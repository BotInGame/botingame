# {{name}}

Game key `{{key}}`, rules version {{version}}.

Each seat places five ships in its own hidden 10×10 waters, then the seats take turns shooting at each other's waters. The first to sink the whole enemy fleet wins. Your Bot never sees the opponent's fleet.

This guide is for Bot developers. The rules, illustrated with a picture of each one, are at https://botingame.com/arenas/{{arena}}/rules.

## The rules

**Waters.** Each seat has its own 10×10 waters. Rows and columns are numbered 0 to 9: row 0 is the top, column 0 the
left. A square is `(row, col)`.

**The fleet.** Each seat has the same five ships, placed in this order:

| Ship | Size (squares) |
| --- | --- |
| Carrier | 5 |
| Battleship | 4 |
| Cruiser | 3 |
| Submarine | 3 |
| Destroyer | 2 |

**Setup.** No ship is placed and no shot fired. The Match has two phases: placement, then shooting.

**Placement.** The seats take turns, seat 0 first, each placing one ship per move, in the fleet's order: seat 0's
Carrier, seat 1's Carrier, seat 0's Battleship, and so on, ten moves in all (five Cycles). A placement move is
`[row, col, dir]`:

- `"h"` places the ship across, from `(row, col)` to the right: squares `(row, col)` to `(row, col + size − 1)`;
- `"v"` places it down, from `(row, col)` downwards: squares `(row, col)` to `(row + size − 1, col)`.

A placement is legal if the whole ship lies inside the seat's waters and covers no square of a ship of the same fleet
already placed. Ships may touch, side by side or end to end.

**Shooting.** Once both fleets are placed, the shooting starts, seat 0 first. The seats take turns, one shot each,
whether it hits or misses. A shot is `[row, col]`: a square of the **opponent's** waters that hasn't been shot before.
It is a hit if it lands on a ship, otherwise a miss. A ship hit on every one of its squares is sunk, and the sunk ship
(its name, size and position) becomes visible to both seats.

**Winning.** The seat that sinks the opponent's fifth ship wins at once. There are no draws on the board.

**Scoring.** The winner scores 1 and the loser 0.

**Edge cases the code handles:**

- During placement, a two-value move (a shot) is illegal, and during shooting so is a three-value move (a placement).
- A ship that would stick out of the waters, or overlap one of your ships, is illegal; touching is fine.
- A square already shot, hit or miss, can't be shot again.
- A hit gives no extra shot: the turn passes to the other seat either way.

## How a Bot plays it

Your Bot is one function, `choose_move(view, legal_moves)`. It is called on each of your turns, with:

- `view`: your seat's view of the Match (see *The view* below). It holds your own fleet but **never** the opponent's:
  of the enemy ships, you only see the ones you have sunk.
- `legal_moves`: every legal move right now. During placement, every legal `[row, col, dir]` for your next ship; during
  shooting, every square of the opponent's waters not shot yet, as `[row, col]`.

It returns one move: one of `legal_moves`.

**Seats.** The two seats are numbered 0 and 1, and seat 0 moves first in both phases. Your seat is in `your_seat` in
the Bot API's Match response; in the view, `next` is the seat to move, so on your turn it is your seat. `boards[0]` and
`sunk[0]` are about seat 0's waters and fleet, and `boards[1]` and `sunk[1]` about seat 1's.

**What others see.** Spectators watching live never see a fleet: placements are hidden, and only shots and sunk ships
are shown. The whole Match, both fleets included, becomes public once it ends.

**Move timeout.** Each move, placements included, must reach the platform within the Arena's move timeout
({{timeout_s}} s unless the Arena sets another; the Arena page shows it, and the Match response gives it as
`timeout_s`, with the `deadline` and `time_left_s`). A Bot that misses it forfeits the Match: it loses, and the Match
shows as its forfeit.

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
| `phase` | string | `"placement"`, `"shooting"` or `"over"` |
| `placed` | 2 integers | How many ships each seat has placed (0 to 5), seat 0's then seat 1's |
| `boards` | 2 grids of 10×10 | `boards[seat][row][col]`: that seat's waters as the other seat has shot them: `null` (not shot), `"hit"` or `"miss"` |
| `sunk` | 2 arrays of ships | `sunk[seat]`: that seat's ships sunk so far, each with its full position |
| `next` | `null`, `0` or `1` | The seat to move, or `null` once the Match is over |
| `turn` | integer | How many moves have been played so far, placements included (the shooting starts at turn 10) |
| `fleet` | array of ships | Your own ships placed so far, in placement order |

A ship, in `fleet` and `sunk`, is an object:

| Field | Meaning |
| --- | --- |
| `name` | `"Carrier"`, `"Battleship"`, `"Cruiser"`, `"Submarine"` or `"Destroyer"` |
| `size` | Its length in squares, 2 to 5 |
| `row`, `col` | Its top-left end |
| `dir` | `"h"` (across, to the right) or `"v"` (down) |

Its JSON Schema:

```json
{{view_schema}}
```

An example: seat {{example_seat}}'s view after {{example_turn}} moves.

```json
{{example_view}}
```

How to read it: your shots land on the **opponent's** board, so as seat `me` you shoot at `boards[1 - me]`, and
`boards[me]` shows the opponent's shots at your waters. Each board lists its rows from the top, left to right. `sunk[1 -
me]` lists the enemy ships you have sunk; a `"hit"` square not covered by any of them belongs to a ship still afloat.
`fleet` is yours alone: the opponent's view holds its own fleet instead, and nobody else's.

## The move

A move is a JSON array, of three values during placement and two during shooting:

| Phase | Move | Values |
| --- | --- | --- |
| `"placement"` | `[row, col, dir]` | `row`, `col`: 0 to 9, the ship's top-left end; `dir`: `"h"` (across) or `"v"` (down) |
| `"shooting"` | `[row, col]` | 0 to 9: a square of the opponent's waters |

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
    if view["phase"] == "placement":
        return random.choice(legal_moves)  # where my next ship goes
    return random.choice(legal_moves)  # where my next shot goes: replace with your own logic


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

**4. Repeat** steps 2 and 3 until `status` is `"finished"`. Then `result` gives each seat's score (`1` or `0`) and `reason`
says how it ended (`"normal"`, or `"timeout"` when a Bot missed its move timeout). Your `state` still holds only your
own fleet; the Match's replay on the website shows both. In a best-of-X Series the next Match starts by itself: `GET /v1/bots/me/match`
returns it. Once the Series is over, queue again.

The full Bot API is described at https://api.botingame.com/docs.
