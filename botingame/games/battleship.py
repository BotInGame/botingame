"""Battleship on a 10x10 board: the seats take turns placing a fleet of five ships, one ship per move, then take turns
shooting. Each seat's fleet is hidden from the other seat and from Spectators until the Match ends."""
from .base import Game, IllegalMove

SIZE = 10
FLEET = (("Carrier", 5), ("Battleship", 4), ("Cruiser", 3), ("Submarine", 3), ("Destroyer", 2))


def _cells(row: int, col: int, direction: str, size: int) -> list[tuple[int, int]]:
    """The cells of a ship whose top-left end is (row, col), lying across ("h") or down ("v")."""
    return [(row, col + i) if direction == "h" else (row + i, col) for i in range(size)]


_INDEX = {"type": "integer", "minimum": 0, "maximum": SIZE - 1}
_SHIP_SCHEMA = {
    "type": "object",
    "required": ["name", "size", "row", "col", "dir"],
    "additionalProperties": False,
    "properties": {
        "name": {"enum": [name for name, _ in FLEET]}, "size": {"type": "integer", "minimum": 2, "maximum": 5},
        "row": _INDEX, "col": _INDEX, "dir": {"enum": ["h", "v"]},
    },
}
_BOARD_SCHEMA = {"type": "array", "minItems": SIZE, "maxItems": SIZE, "items": {
    "type": "array", "minItems": SIZE, "maxItems": SIZE, "items": {"enum": [None, "hit", "miss"]}}}


def _by_seat(item: dict) -> dict:
    """The schema of a list holding one `item` per seat."""
    return {"type": "array", "minItems": 2, "maxItems": 2, "items": item}


def _empty_board() -> list[list]:
    return [[None] * SIZE for _ in range(SIZE)]


def _ship(index: int, row: int, col: int, direction: str) -> dict:
    name, size = FLEET[index]
    return {"name": name, "size": size, "row": row, "col": col, "dir": direction}


def _cells_of(ship: dict) -> list[tuple[int, int]]:
    return _cells(ship["row"], ship["col"], ship["dir"], ship["size"])


class Battleship(Game):
    id, name, version = "battleship", "Battleship", "1.0.0"
    spectating_policy = "post-match"
    rules = (
        f"Each seat has its own {SIZE}x{SIZE} waters (row 0 at the top, column 0 on the left) "
        "and a fleet of five ships: "
        + ", ".join(f"{name} ({size})" for name, size in FLEET) + ". "
        "Placement: the seats take turns, seat 0 first, each placing one ship per move in that order. "
        'Move = [row, col, "h"] for a ship across from (row, col) to the right, or [row, col, "v"] for one down from '
        "(row, col). A ship lies whole in its seat's waters and never overlaps another of the same fleet (touching is "
        "fine). "
        "Shooting starts once both fleets are placed: seat 0 first, then each seat in turn, hit or miss. "
        "Move = [row, col], a square of the opponent's waters not shot before. A ship hit on every square is sunk, "
        "and the sunk ship is shown to both seats. The seat that sinks the whole opposing fleet wins. "
        'The view: `phase` ("placement", "shooting" or "over"), `placed` (ships placed by seat), `boards` (each '
        'seat\'s waters as shot at: null, "hit" or "miss"), `sunk` (each seat\'s sunk ships), `next` (the seat to '
        "move), `turn`, and `fleet`: your own ships. The opponent's fleet is never in your view."
    )
    move_schema = {
        "oneOf": [
            {"type": "array", "minItems": 3, "maxItems": 3, "prefixItems": [_INDEX, _INDEX, {"enum": ["h", "v"]}]},
            {"type": "array", "minItems": 2, "maxItems": 2, "prefixItems": [_INDEX, _INDEX]},
        ],
    }
    view_schema = {
        "type": "object",
        "required": ["phase", "placed", "boards", "sunk", "next", "turn"],
        "additionalProperties": False,
        "properties": {
            "phase": {"enum": ["placement", "shooting", "over"]},
            "placed": _by_seat({"type": "integer", "minimum": 0, "maximum": len(FLEET)}),
            "boards": _by_seat(_BOARD_SCHEMA),
            "sunk": _by_seat({"type": "array", "maxItems": len(FLEET), "items": _SHIP_SCHEMA}),
            "next": {"enum": [None, 0, 1]},
            "turn": {"type": "integer", "minimum": 0},
            "fleet": {"type": "array", "maxItems": len(FLEET), "items": _SHIP_SCHEMA},
        },
    }

    def initial_state(self, seed):
        return {"seed": seed, "fleets": [[], []], "phase": "placement", "placed": [0, 0],
                "boards": [_empty_board(), _empty_board()], "sunk": [[], []], "next": 0, "turn": 0}

    def to_move(self, state):
        return set() if state["next"] is None else {state["next"]}

    def legal_moves(self, state, seat):
        if seat not in self.to_move(state):
            return []
        if state["phase"] == "shooting":
            target = state["boards"][1 - seat]
            return [[r, c] for r in range(SIZE) for c in range(SIZE) if target[r][c] is None]
        return [[r, c, d] for d in ("h", "v") for r in range(SIZE) for c in range(SIZE)
                if self._fits(state, seat, r, c, d)]

    @staticmethod
    def _fits(state, seat, row, col, direction) -> bool:
        """The seat's next ship may lie at (row, col) that way: whole in its waters, over none of its other ships."""
        fleet = state["fleets"][seat]
        taken = {cell for ship in fleet for cell in _cells_of(ship)}
        return all(0 <= r < SIZE and 0 <= c < SIZE and (r, c) not in taken
                   for r, c in _cells(row, col, direction, FLEET[len(fleet)][1]))

    def _legal(self, state, seat, move) -> bool:
        """`move` is one of `legal_moves(state, seat)`, checked without listing them all."""
        shooting = state["phase"] == "shooting"
        if (seat not in self.to_move(state) or not isinstance(move, list) or len(move) != (2 if shooting else 3)
                or any(type(x) is not int or not 0 <= x < SIZE for x in move[:2])):
            return False
        if shooting:  # a square of the opponent's waters not shot before
            return state["boards"][1 - seat][move[0]][move[1]] is None
        return move[2] in ("h", "v") and self._fits(state, seat, *move)

    def apply(self, state, seat, move):
        if not self._legal(state, seat, move):
            raise IllegalMove(f"illegal move {move!r}")
        if state["phase"] == "shooting":
            return self._shoot(state, seat, *move)
        fleets = [list(f) for f in state["fleets"]]
        fleets[seat].append(_ship(len(fleets[seat]), *move))
        placed = [len(f) for f in fleets]
        done = placed == [len(FLEET)] * 2
        # Seat 1 places last, so seat 0 shoots first: the seats keep taking turns.
        return {**state, "fleets": fleets, "placed": placed, "turn": state["turn"] + 1,
                "phase": "shooting" if done else "placement", "next": 1 - seat}

    def _shoot(self, state, seat, row, col):
        target = 1 - seat
        ship = next((ship for ship in state["fleets"][target] if (row, col) in _cells_of(ship)), None)
        board = [r[:] for r in state["boards"][target]]
        board[row][col] = "miss" if ship is None else "hit"
        boards, sunk = list(state["boards"]), [list(s) for s in state["sunk"]]
        boards[target] = board
        if ship is not None and all(board[r][c] == "hit" for r, c in _cells_of(ship)):
            sunk[target].append(ship)
        over = len(sunk[target]) == len(FLEET)
        return {**state, "boards": boards, "sunk": sunk, "turn": state["turn"] + 1,
                "phase": "over" if over else "shooting", "next": None if over else target}

    def view(self, state, seat):
        """The Public view is everything but the seed and the fleets; a seat also sees its own fleet."""
        public = {k: v for k, v in state.items() if k not in ("seed", "fleets")}
        return public if seat is None else {**public, "fleet": state["fleets"][seat]}

    def public_move(self, state, seat, move):
        """A placed ship stays hidden live (the move shows as null); a shot is public."""
        return None if state["phase"] == "placement" else move

    def outcome(self, state):
        if state["phase"] != "over":
            return None
        return [0.0, 1.0] if len(state["sunk"][0]) == len(FLEET) else [1.0, 0.0]
