"""Each Game's full state as text, for `botingame play --show`. Seat 0 is X, seat 1 is O."""
import json
from collections.abc import Callable

MARK = {0: "X", 1: "O", None: ".", "draw": "#"}


def uttt(state: dict) -> str:
    rows = []
    for big_row in range(3):
        for small_row in range(3):
            rows.append(" | ".join(
                " ".join(MARK[state["cells"][board][small_row * 3 + c]] for c in range(3))
                for board in range(big_row * 3, big_row * 3 + 3)))
        if big_row < 2:
            rows.append("------+-------+------")
    won = " ".join(MARK[b] for b in state["boards"])
    forced = "any" if state["forced"] is None else state["forced"]
    return "\n".join(rows + [f"sub-boards: {won}   next sub-board: {forced}"])


def connect4(state: dict) -> str:
    rows = [" " + " ".join(MARK[cell] for cell in row) for row in state["board"]]
    return "\n".join(rows + [" " + " ".join(str(c) for c in range(len(state["board"][0])))])


def dots(state: dict) -> str:
    h, v, boxes = state["h"], state["v"], state["boxes"]
    rows = []
    for r in range(len(h)):
        rows.append("+" + "+".join("---" if line is not None else "   " for line in h[r]) + "+")
        if r < len(v):
            owners = [" " if owner is None else MARK[owner] for owner in boxes[r]] + [""]
            rows.append("".join(("|" if line is not None else " ") + (f" {owner} " if owner else "")
                                for line, owner in zip(v[r], owners)))
    a, b = state["scores"]
    return "\n".join(rows + [f"boxes: X {a}, O {b}"])


def battleship(state: dict) -> str:
    """Each seat's waters: its ships (S) and the shots at it (* hit, o miss)."""
    def waters(seat: int) -> list[str]:
        ships = {(ship["row"] + (i if ship["dir"] == "v" else 0), ship["col"] + (i if ship["dir"] == "h" else 0))
                 for ship in state["fleets"][seat] for i in range(ship["size"])}
        shots = state["boards"][seat]
        return [" ".join({"hit": "*", "miss": "o"}.get(shots[r][c]) or ("S" if (r, c) in ships else ".")
                         for c in range(len(shots))) for r in range(len(shots))]

    left, right = waters(0), waters(1)
    width = len(left[0])
    lines = [f"{'seat 0 (X)':<{width}}    seat 1 (O)"] + [f"{a}    {b}" for a, b in zip(left, right)]
    return "\n".join(lines + [f"phase: {state['phase']}"])


RENDERERS: dict[str, Callable[[dict], str]] = {"uttt": uttt, "connect4": connect4, "dots": dots,
                                               "battleship": battleship}


def board_text(game_id: str, state: dict) -> str:
    """The state as text; a Game without a renderer shows its state as JSON."""
    if game_id in RENDERERS:
        return RENDERERS[game_id](state)
    return json.dumps({k: v for k, v in state.items() if k != "seed"}, indent=2)
