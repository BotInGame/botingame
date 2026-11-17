# botingame

[![CI](https://github.com/BotInGame/botingame/actions/workflows/ci.yml/badge.svg)](https://github.com/BotInGame/botingame/actions/workflows/ci.yml)

Write a Bot for [BotInGame](https://botingame.com), try it offline against the exact Game rules the platform runs,
then let it play ranked Matches.

This repository holds the `botingame` package: the Games' rules, the Bot SDK, the `botingame` CLI and each Game's
guide. It is free software under the GNU GPL v3 or later, with an attribution term (see [License](#license)).

## Install

The package is not on PyPI yet. Install the CLI straight from this repository, with
[uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/):

```sh
uv tool install git+https://github.com/BotInGame/botingame
# or
pipx install git+https://github.com/BotInGame/botingame
```

Add `@<tag>` to the URL for a given release, for example `git+https://github.com/BotInGame/botingame@v0.1.0.dev4`.
Python 3.14 or newer is needed: uv fetches it if you don't have it, pipx needs it installed.

Or clone it and work from the checkout:

```sh
git clone https://github.com/BotInGame/botingame
cd botingame
uv sync
uv run botingame --version
```

## Your first Match

```sh
botingame new                # pick a Game, a file name, and paste your Bot's token (from your Dashboard)
botingame play uttt_bot.py   # offline, against a random Bot
botingame run uttt_bot.py    # online: queue, play, repeat (Ctrl+C to stop)
```

`botingame new` writes a starter Bot; `botingame play` needs no account and no network. To play ranked Matches, sign
in on [botingame.com](https://botingame.com), create a Bot on your Dashboard and copy its token.

A Bot is one function. It gets its seat's view of the Match and its legal moves, and returns one of them:

```python
GAME = "uttt"
GAME_VERSION = "1.0.0"  # the rules it was written for

def choose_move(view, legal_moves):
    return legal_moves[0]
```

## Commands

| Command | What it does |
| --- | --- |
| `botingame games` | The platform's Games: key, name, players and version. In a terminal it is an inline menu: open a Game to read its guide (keys below). `--plain`, or piped output, prints the table |
| `botingame game <key>` | The Game's technical guide: its exact rules, how a Bot plays it, the `view` and the move (JSON Schemas and examples) and code to start from. Long guides open in a pager; `--no-pager` prints them straight, and piped output is plain Markdown |
| `botingame new` | Write a starter Bot, linked to the platform's version of its Game, and keep its token in `.env` as `BOTINGAME_TOKEN` (git-ignored). Pick the Game from the same menu; `--game`, `--path`, `--token` skip the questions, and without a terminal all three are needed |
| `botingame play bot.py` | Offline Matches. `--game` (default: the file's `GAME`), `--vs random` or `--vs other_bot.py`, `--matches N` (alternating seats), `--seed`, `--show` (the board after every move), `--step` (one move per Enter, and a pause between Matches; `q` then Enter or Ctrl+C stops and still prints the tally; implies `--show`, needs a terminal) |
| `botingame run bot.py` | Play ranked Series on the platform. Token from `--token`, else `BOTINGAME_TOKEN`, else `.env` in the current folder. `--series N` (default 1; 0: until Ctrl+C), always finishing the Series it is in, `--arena`. Shows each Match's link (`--web-url`), the opponent with its Elo and creator, your Elo and seat, the Series score, and your Elo change at the end of each Series |
| `botingame health` | Check that the web app and the Bot API are up (exits 1 if either is down). `--web-url`, `--url` |
| `botingame --version` | The package version, then the copyright and licence notices |

### The Game menu

`botingame games` in a terminal, and `botingame new` when it asks for the Game:

A list under the prompt, with the keys that work next to its question:

| Key | What it does |
| --- | --- |
| ↑ ↓ (or `j` `k`) | Move the selection |
| Enter or → | `games`: open the Game's guide, in a pager when it is longer than the screen (`q` there comes back to the list, on the same Game). `new`: pick the Game |
| `q`, Esc or Ctrl+C | Quit |

`games`, `game` and `run` read the platform's Bot API (`--url` or `BOTINGAME_URL` to point elsewhere);
`games --offline` and `game --offline` show the rules installed with the package instead. Each Game's guide also
ships with the package, in English and French, in the `botingame.docs` subpackage: one folder per Game holds its guide
(`botingame/docs/<key>/guide.en.md`, `guide.fr.md`) and its illustrated rules page (`rules.en.md`, `rules.fr.md`),
which botingame.com shows at `/arenas/<arena>/rules`. `play` works offline.
Each online command opens with a one-line health check of the web app (`--web-url` or `BOTINGAME_WEB_URL`) and the
Bot API.

## Game versions

Each Game's rules have a version. Three should match: the platform's, the one installed with this package (what
`play` runs), and the one a Bot was written for (its `GAME_VERSION`, set by `botingame new`). When they drift,
`games`, `game`, `new`, `play` and `run` print a warning: update the package (`uv tool upgrade botingame`,
`pipx upgrade botingame`, or `git pull` then `uv sync` in a checkout), check the new rules with
`botingame game <key>`, update the Bot, then its `GAME_VERSION`.

## The SDK

`botingame run` uses the SDK, which you can also call from your own code:

```python
import botingame

botingame.run(choose_move, token="big_...")  # or set BOTINGAME_TOKEN; plays one Series (series=0: until stopped)
```

It finds your Bot's Game from its token, resumes an active Match (after a crash, or the next Match of a Series),
otherwise queues into the Game's ranked Arena, long-polls for its turn and posts each move with its turn number. It
counts whole Series and always plays the one it is in to the end, every Match of a best-of-X. Pass
`on_event=lambda kind, view: ...` to follow the Matches: `"queueing"`, `"matched"` and `"finished"`, with the Match
view (players' Elo and creators, the Series score, and each Bot's Elo before and after once the Series is over).
Dropped connections and server errors are retried (a repeated move is idempotent), and a `429` waits out its
`Retry-After`. Each move takes at least 0.5 s (`min_move_s`), which keeps a Bot under the rate limit of 10 requests
a second.

Not in Python? Every language can use the `/v1` Bot API over HTTP: see the OpenAPI spec at https://api.botingame.com/docs.

## Examples

[`examples/`](examples/) holds reference Bots that talk to the Bot API directly, without this package.
[`examples/python/random_bot.py`](examples/python/random_bot.py) plays random legal moves with the Python standard
library only:

```sh
BOTINGAME_TOKEN=big_... python3 examples/python/random_bot.py --arena connect4-elo --games 1
```

## Development

```sh
uv sync
uv run ruff check .
uv run pytest
```

Bug reports and ideas: [GitHub Issues](https://github.com/BotInGame/botingame/issues). To contribute code, see
[CONTRIBUTING.md](CONTRIBUTING.md): contributions come in under the same licence they go out under, signed off (DCO).

## License

Copyright (C) 2026 BotInGame. [GNU GPL v3 or later](LICENSE), with one additional term under its section 7(b): keep
the attribution in [NOTICE](NOTICE) ("Based on botingame by BotInGame") in any copy of this package and in any work
based on it.

In practice:

- **Using it is free.** Run the CLI, write and run Bots, privately or on your own server, with no obligation.
- **Sharing a fork, or a program that imports `botingame`,** means releasing it under the GPL v3 (or later) with its
  source, and keeping the attribution.
- **Starter code is free to copy.** The reference Bots in `examples/`, the code samples in the Game guides and the
  Bot file `botingame new` writes are under [0BSD](examples/LICENSE): copy them into your Bot, with any licence, no credit needed. A Bot that talks to
  the Bot API over HTTP without importing `botingame` is yours to license as you like.
