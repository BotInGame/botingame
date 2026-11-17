"""Battleship rules, through the Game interface."""
import pytest

from botingame.games import GAMES, IllegalMove

game = GAMES["battleship"]


def test_seat_0_places_first_its_carrier_anywhere_it_lies_whole():
    s = game.initial_state(0)
    assert game.to_move(s) == {0}
    # The Carrier (5 long) first: 6 places across in each of 10 rows, 6 down in each of 10 columns.
    moves = game.legal_moves(s, 0)
    assert len(moves) == 120
    assert [0, 5, "h"] in moves and [5, 0, "v"] in moves
    assert [0, 6, "h"] not in moves and [6, 0, "v"] not in moves
    assert game.legal_moves(s, 1) == []


def test_seats_take_turns_placing_one_ship_per_move():
    s = game.initial_state(0)
    for i in range(10):
        seat = i % 2
        assert game.to_move(s) == {seat}
        with pytest.raises(IllegalMove):
            game.apply(s, 1 - seat, [FLEET_0, FLEET_1][1 - seat][i // 2])  # out of turn
        s = game.apply(s, seat, [FLEET_0, FLEET_1][seat][i // 2])
    assert game.view(s, None)["placed"] == [5, 5]


# A fleet per seat, as [row, col, "h"|"v"] in fleet order: Carrier 5, Battleship 4, Cruiser 3, Submarine 3, Destroyer 2.
# Seat 0's ships lie across rows 0, 2, 4, 6 and 8 from column 0; seat 1's lie down columns 9, 7, 5, 3 and 1 from row 0.
FLEET_0 = [[0, 0, "h"], [2, 0, "h"], [4, 0, "h"], [6, 0, "h"], [8, 0, "h"]]
FLEET_1 = [[0, 9, "v"], [0, 7, "v"], [0, 5, "v"], [0, 3, "v"], [0, 1, "v"]]


def placed(fleet_0=FLEET_0, fleet_1=FLEET_1):
    """Both fleets placed, ship by ship, seat 0 and seat 1 taking turns: five Cycles."""
    s = game.initial_state(0)
    for a, b in zip(fleet_0, fleet_1):
        s = game.apply(game.apply(s, 0, a), 1, b)
    return s


@pytest.mark.parametrize("move", [
    [0, 6, "h"],  # the Carrier would leave the board
    [6, 0, "v"],
    [-1, 0, "h"],
    [0, 0, "d"],  # neither across nor down
    [0, 0],  # a shot, while placing
    [0, 0, "h", 1],
    "0,0,h",
    [False, 0, "h"],  # a boolean is not a row
])
def test_a_ship_must_lie_whole_on_the_board(move):
    with pytest.raises(IllegalMove):
        game.apply(game.initial_state(0), 0, move)


def test_ships_of_a_fleet_may_touch_but_not_overlap_and_each_fleet_has_its_own_waters():
    s = game.apply(game.initial_state(0), 0, [0, 0, "h"])
    s = game.apply(s, 1, [0, 0, "h"])  # the same squares, in seat 1's own waters
    assert s["fleets"][1][0]["name"] == "Carrier"
    with pytest.raises(IllegalMove):
        game.apply(s, 0, [0, 4, "v"])  # crosses seat 0's Carrier's last square
    assert game.apply(s, 0, [1, 0, "h"])["placed"] == [2, 1]  # right alongside it


def test_while_placing_a_seat_sees_its_own_ships_and_only_how_many_the_other_has_placed():
    s = game.apply(game.apply(game.apply(game.initial_state(0), 0, FLEET_0[0]), 1, FLEET_1[0]), 0, FLEET_0[1])
    public = game.view(s, None)
    assert public["placed"] == [2, 1] and public["phase"] == "placement"
    assert "fleet" not in public and "fleets" not in public
    mine = game.view(s, 0)
    assert [(ship["name"], ship["row"], ship["col"], ship["dir"]) for ship in mine["fleet"]] == [
        ("Carrier", 0, 0, "h"), ("Battleship", 2, 0, "h")]
    assert game.view(s, 1)["fleet"] == [{"name": "Carrier", "size": 5, "row": 0, "col": 9, "dir": "v"}]


def test_once_both_fleets_are_placed_seat_0_shoots_first_at_any_square():
    s = placed()
    assert game.to_move(s) == {0}
    view = game.view(s, None)
    assert (view["phase"], view["next"], view["placed"]) == ("shooting", 0, [5, 5])
    assert len(game.legal_moves(s, 0)) == 100 and [9, 9] in game.legal_moves(s, 0)
    assert game.legal_moves(s, 1) == []
    for move in ([0, 0, "h"], [10, 0], [0, -1], [True, 0]):
        with pytest.raises(IllegalMove):
            game.apply(s, 0, move)


def shoot(state, *shots):
    """The seat to shoot fires each shot in turn."""
    for shot in shots:
        (seat,) = game.to_move(state)
        state = game.apply(state, seat, shot)
    return state


def test_a_shot_marks_a_hit_or_a_miss_for_everyone_and_the_turn_passes_either_way():
    s = shoot(placed(), [2, 9])  # seat 0 hits seat 1's Carrier (column 9, rows 0-4)
    view = game.view(s, None)
    assert view["boards"][1][2][9] == "hit" and game.to_move(s) == {1}
    s = shoot(s, [9, 9])  # seat 1 misses: row 9 of seat 0's waters is empty
    view = game.view(s, None)
    assert view["boards"][0][9][9] == "miss" and view["boards"][0][0][0] is None
    assert game.to_move(s) == {0} and view["turn"] == 12
    assert [2, 9] not in game.legal_moves(s, 0) and len(game.legal_moves(s, 0)) == 99
    with pytest.raises(IllegalMove):
        game.apply(s, 0, [2, 9])  # no square is shot twice


def test_a_ship_hit_on_every_square_is_sunk_and_shown_to_everyone():
    s = shoot(placed(), [0, 1], [9, 9], [1, 1])  # seat 1's Destroyer: column 1, rows 0-1
    assert game.view(s, None)["sunk"] == [[], [{"name": "Destroyer", "size": 2, "row": 0, "col": 1, "dir": "v"}]]
    assert game.outcome(s) is None


# Every square of seat 1's fleet, ship by ship, and squares of seat 0's waters with no ship (its odd rows).
SEAT_1_SQUARES = [[r, c] for c, size in zip((9, 7, 5, 3, 1), (5, 4, 3, 3, 2)) for r in range(size)]
SEAT_0_MISSES = [[r, c] for r in (1, 3, 5, 7, 9) for c in range(10)]


def test_sinking_the_whole_fleet_wins_at_once():
    assert len(SEAT_1_SQUARES) == 17
    shots = [shot for pair in zip(SEAT_1_SQUARES, SEAT_0_MISSES) for shot in pair][:-1]  # seat 0's 17th shot ends it
    s = shoot(placed(), *shots)
    assert game.outcome(s) == [1.0, 0.0] and game.to_move(s) == set()
    view = game.view(s, None)
    assert (view["phase"], view["next"]) == ("over", None)
    assert [ship["name"] for ship in view["sunk"][1]] == ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]
    assert view["sunk"][0] == []
