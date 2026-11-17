"""Connect Four rules, through the Game interface."""
import pytest

from botingame.games import GAMES, IllegalMove

game = GAMES["connect4"]


def play(columns, seed=0):
    state = game.initial_state(seed)
    for col in columns:
        (seat,) = game.to_move(state)
        state = game.apply(state, seat, col)
    return state


def test_vertical_four_wins():
    assert game.outcome(play([0, 1, 0, 1, 0, 1, 0])) == [1.0, 0.0]


def test_horizontal_four_wins():
    assert game.outcome(play([0, 0, 1, 1, 2, 2, 3])) == [1.0, 0.0]


def test_diagonal_four_wins_for_second_seat():
    # seat 1 builds the rising diagonal (5,1) (4,2) (3,3) (2,4)
    s = play([0, 1, 2, 2, 3, 3, 4, 3, 4, 4, 0, 4])
    assert game.outcome(s) == [0.0, 1.0]


def test_falling_diagonal_wins():
    # seat 0 builds (2,0) (3,1) (4,2) (5,3)
    s = play([3, 2, 2, 1, 1, 0, 1, 0, 0, 6, 0])
    assert game.outcome(s) == [1.0, 0.0]


def test_full_board_without_four_is_a_draw():
    # columns filled in pairs with a shifted order: no line of four for anyone
    order = [0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0,
             2, 3, 2, 3, 2, 3, 3, 2, 3, 2, 3, 2,
             4, 5, 4, 5, 4, 5, 5, 4, 5, 4, 5, 4,
             6, 6, 6, 6, 6, 6]
    s = play(order)
    assert game.outcome(s) == [0.5, 0.5]
    assert game.to_move(s) == set()


def test_full_column_is_illegal():
    s = play([0] * 6)
    assert 0 not in game.legal_moves(s, 0)
    with pytest.raises(IllegalMove):
        game.apply(s, 0, 0)


def test_seat_not_to_move_has_no_legal_moves_and_cannot_move():
    s = game.initial_state(0)
    assert game.legal_moves(s, 1) == []
    with pytest.raises(IllegalMove):
        game.apply(s, 1, 3)
