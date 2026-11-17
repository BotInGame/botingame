# SPDX-License-Identifier: GPL-3.0-or-later. The starter Bot file this module writes (TEMPLATE) is 0BSD: see NOTICE.
"""`botingame new`: the starter Bot file, and the Bot's token kept in a `.env` file that git ignores."""
from pathlib import Path

from ..games import GAMES
from ..sdk import TOKEN_VAR

# What each Game's `view` holds, as comments in the starter Bot. Seats are 0 and 1; `null` in JSON is None here.
VIEWS = {
    "uttt": """\
    #   `cells`: 9 sub-boards x 9 cells, row-major; each cell is None, 0 or 1 (the seat that played it).
    #   `boards`: per sub-board, None (still open), 0 or 1 (won by that seat) or "draw" (full, no line).
    #   `forced`: the sub-board you must play in, or None to play in any open one.
    #   `turn`: moves played so far. `winner`: None until a seat wins.
    # A move is [board, cell], both 0-8.""",
    "connect4": """\
    #   `board`: 6 rows x 7 columns, row 0 at the top; each cell is None, 0 or 1 (the seat whose disc it is).
    #   `turn`: moves played so far. `winner`: None until a seat wins.
    # A move is a column, 0-6.""",
    "dots": """\
    #   `h`: 8 rows x 7 horizontal lines; `h[r][c]` joins dot (r, c) to dot (r, c+1).
    #   `v`: 7 rows x 8 vertical lines; `v[r][c]` joins dot (r, c) to dot (r+1, c).
    #     Each line is None (not drawn yet), 0 or 1 (the seat that drew it).
    #   `boxes`: 7 x 7, each None or the seat that closed it. `scores`: boxes per seat.
    #   `next`: the seat to move (closing a box moves again). `turn`: moves played so far.
    # A move is ["h", row, col] or ["v", row, col].""",
    "battleship": """\
    #   `phase`: "placement" (one ship per move, Carrier first), "shooting" or "over".
    #   `fleet`: your own ships so far, each {"name", "size", "row", "col", "dir"}.
    #   `placed`: how many ships each seat has placed.
    #   `boards`: each seat's 10 x 10 waters as shot at: None, "hit" or "miss". Shoot at boards[1 - your seat].
    #   `sunk`: each seat's sunk ships. `next`: the seat to move. `turn`: moves played so far.
    # A move is [row, col, "h" or "v"] to place a ship, then [row, col] to shoot.""",
}

TEMPLATE = '''\
# SPDX-License-Identifier: 0BSD
"""A BotInGame Bot for {name}.

Try it offline:          botingame play {path}
Play it on the platform: botingame run {path}   (reads BOTINGAME_TOKEN from .env)
The rules:               botingame game {key}
"""
import random

GAME = "{key}"
GAME_VERSION = "{version}"  # the {name} rules this Bot was written for: botingame warns when they change


def choose_move(view, legal_moves):
    # Return one of `legal_moves`. `view` is what your seat sees of the Match:
{view}
    # This Bot plays a random legal move: make it smarter.
    return random.choice(legal_moves)
'''


def starter_bot(key: str, path: str, version: str) -> str:
    return TEMPLATE.format(name=GAMES[key].name, key=key, path=path, view=VIEWS[key], version=version)


def save_token(env: Path, token: str) -> None:
    """Set BOTINGAME_TOKEN in the `.env` file, keeping every other line."""
    lines = env.read_text().splitlines() if env.exists() else []
    line = f"{TOKEN_VAR}={token}"
    if any(old.startswith(f"{TOKEN_VAR}=") for old in lines):
        lines = [line if old.startswith(f"{TOKEN_VAR}=") else old for old in lines]
    else:
        lines.append(line)
    env.write_text("".join(f"{old}\n" for old in lines))


def ignore_env(gitignore: Path) -> None:
    """List `.env` in the `.gitignore` file (created if missing), once."""
    text = gitignore.read_text() if gitignore.exists() else ""
    if ".env" in (line.strip() for line in text.splitlines()):
        return
    gitignore.write_text(text + ("" if text.endswith("\n") or not text else "\n") + ".env\n")


def token_from_env_file(env: Path) -> str | None:
    """BOTINGAME_TOKEN as a `.env` file sets it, if it does."""
    if not env.exists():
        return None
    for line in env.read_text().splitlines():
        key, sep, value = line.strip().removeprefix("export ").partition("=")
        if sep and key.strip() == TOKEN_VAR:
            return value.strip().strip("'\"") or None
    return None
