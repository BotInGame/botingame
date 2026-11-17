# {{name}}

Game key `{{key}}`, rules version {{version}}.

Two seats take turns dropping pieces into a 7×6 upright grid; a piece falls to the lowest free cell of its column. Four in a row wins.

This guide is for Bot developers. The rules, illustrated with a picture of each one, are at https://botingame.com/arenas/{{arena}}/rules.

## The rules

**Board.** Seven columns, numbered 0 to 6 from left to right, and six rows, numbered 0 to 5 **from the top**: row 0 is
the top row, row 5 the bottom row, where pieces land first.

**Setup.** The board is empty. Seat 0 moves first.

**Turn order.** The seats alternate, one move each, seat 0 first.

**A legal move** is a column, 0 to 6, that is not full (its top cell, in row 0, is empty). The piece lands in the lowest
empty row of that column.

**Winning.** A seat wins as soon as its move makes four (or more) of its pieces in a line: across a row, down a column,
or along either diagonal. The Match ends there.

**Draw.** When the board is full (all 42 cells, so every column's top cell) with no line of four, the Match is a draw.

**Scoring.** The winner scores 1 and the loser 0; a draw gives each seat ½.

**Edge cases the code handles:**

- A full column is never among the legal moves; playing it is an illegal move.
- A move that both makes a line of four and fills the board is a win, not a draw.
- A line longer than four (five or more in a row) wins too.

## How a Bot plays it

Your Bot is one function, `choose_move(view, legal_moves)`. It is called on each of your turns, with:

- `view`: your seat's view of the Match (see *The view* below). Connect Four hides nothing: both seats and Spectators
  see the same board.
- `legal_moves`: every legal move right now: the columns that are not full, as integers.

It returns one move: one of `legal_moves`.

**Seats.** The two seats are numbered 0 and 1, and seat 0 moves first. Your seat is in `your_seat` in the Bot API's
Match response; from the view alone it is `view["turn"] % 2`, since the seats alternate. On the board, `0` is a piece
of seat 0 and `1` a piece of seat 1.

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
| `board` | 6 arrays of 7 | `board[row][column]`, row 0 at the top: `null` (empty), `0` (seat 0's piece) or `1` (seat 1's piece) |
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

How to read it: each line of `board` is a row, and the first line is the **top** row, so the pieces pile up from the
last line. A column is `board[0][c]`, `board[1][c]` … `board[5][c]`; it is full when `board[0][c]` is not `null`. Since
seats alternate and seat 0 moved first, the seat to move is `turn % 2`.

## The move

A move is a JSON integer: the column to drop a piece into.

| Value | Meaning |
| --- | --- |
| `0` to `6` | The column, 0 on the left; it must not be full |

Its JSON Schema:

```json
{{move_schema}}
```

In the example above, `legal_moves` is `{{example_legal_moves}}`, and `{{example_move}}` is one legal move.

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
    me = view["turn"] % 2  # my seat: 0 or 1
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
`reason` says how it ended (`"normal"`, or `"timeout"` when a Bot missed its move timeout). In a best-of-X Series the
next Match starts by itself: `GET /v1/bots/me/match` returns it. Once the Series is over, queue again.

The full Bot API is described at https://api.botingame.com/docs.
