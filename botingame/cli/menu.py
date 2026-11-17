"""The Game menu: an inline arrow-key list under the prompt (questionary), as `botingame new` picks a Game from it and
`botingame games` browses it (Enter opens the Game's guide in a pager; quitting the pager comes back to the list)."""
from collections.abc import Callable

import questionary
from prompt_toolkit.keys import Keys

STYLE = questionary.Style([("key", "fg:ansicyan bold"), ("name", "bold"), ("dim", "fg:ansibrightblack"),
                           ("instruction", "fg:ansibrightblack"), ("pointer", "fg:ansicyan bold"),
                           ("highlighted", "fg:ansicyan bold")])


def choice(g: dict) -> questionary.Choice:
    """One Game in the list: its key, name, players and version."""
    return questionary.Choice(title=[("class:key", f"{g['id']:<11}"), ("class:name", g["name"]),
                                     ("class:dim", f"  {g['players']} players · {g['version']}")], value=g["id"])


def pick_game(rows: list[dict], default: str | None = None, action: str = "pick", **terminal) -> str | None:
    """The key of the Game picked from `rows` (↑/↓ or j/k move, Enter or → picks), or None on q, Esc or Ctrl+C.
    `terminal` replaces the real terminal's input and output (tests)."""
    question = questionary.select("Which Game?", choices=[choice(g) for g in rows], default=default, style=STYLE,
                                  pointer="❯", instruction=f"↑↓ move · enter {action} · q quit", **terminal)
    bindings = question.application.key_bindings
    enter = next(b.handler for b in bindings.bindings if b.keys == (Keys.ControlM,))
    bindings.add(Keys.Right, eager=True)(enter)
    for key in ("q", Keys.Escape):
        bindings.add(key, eager=True)(lambda event: event.app.exit(result=None))
    return question.ask()


def browse(rows: list[dict], show_page: Callable[[str], None], pick=pick_game) -> None:
    """`botingame games`: pick a Game, show its page, then come back to the list on the same Game, until q."""
    selected = None
    while (key := pick(rows, default=selected, action="open")) is not None:
        show_page(key)
        selected = key
