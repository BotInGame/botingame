"""Every registered Game honours the Game contract."""
import json
import random
from typing import get_args

import jsonschema
import pytest

from botingame.games import GAMES, Game
from botingame.games.base import SpectatingPolicy

GAME_IDS = sorted(GAMES)
MAX_MOVES = 10_000


def random_playout(game, seed, rng):
    """Play random legal moves to the end; return (states, move log)."""
    state = game.initial_state(seed)
    states, log = [state], []
    while (seats := game.to_move(state)) and len(log) < MAX_MOVES:
        seat = rng.choice(sorted(seats))
        move = rng.choice(game.legal_moves(state, seat))
        state = game.apply(state, seat, move)
        states.append(state)
        log.append((seat, move))
    return states, log


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_to_move_is_empty_exactly_when_outcome_is_set(game_id):
    game = GAMES[game_id]
    for seed in range(20):
        states, _ = random_playout(game, seed, random.Random(seed))
        for state in states:
            assert (not game.to_move(state)) == (game.outcome(state) is not None)


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_replay_from_seed_and_move_log_is_deterministic(game_id):
    game = GAMES[game_id]
    for seed in range(20):
        states, log = random_playout(game, seed, random.Random(seed))
        replayed = game.initial_state(seed)
        for seat, move in log:
            replayed = game.apply(replayed, seat, move)
        assert replayed == states[-1]
        assert game.initial_state(seed) == states[0]


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_random_playouts_terminate(game_id):
    game = GAMES[game_id]
    for seed in range(20):
        states, _ = random_playout(game, seed, random.Random(seed))
        assert len(states) <= MAX_MOVES
        assert game.outcome(states[-1]) is not None


def is_subset(small, big):
    """Every field in `small` is in `big` with the same content (dicts compared recursively)."""
    if isinstance(small, dict) and isinstance(big, dict):
        return all(k in big and is_subset(v, big[k]) for k, v in small.items())
    return small == big


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_public_view_is_within_every_seat_view_and_seed_never_leaks(game_id):
    game = GAMES[game_id]
    for i in range(20):
        rng = random.Random(i)
        seed = rng.getrandbits(63)
        states, _ = random_playout(game, seed, rng)
        for state in states:
            public = game.view(state, None)
            for seat in range(game.players):
                seat_view = game.view(state, seat)
                assert is_subset(public, seat_view)
                assert "seed" not in seat_view
                assert str(seed) not in json.dumps(seat_view)
            assert "seed" not in public
            assert str(seed) not in json.dumps(public)


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_views_and_legal_moves_match_the_schemas(game_id):
    game = GAMES[game_id]
    jsonschema.Draft202012Validator.check_schema(game.move_schema)
    jsonschema.Draft202012Validator.check_schema(game.view_schema)
    moves, views = jsonschema.Draft202012Validator(game.move_schema), jsonschema.Draft202012Validator(game.view_schema)
    legal: dict[str, object] = {}  # each distinct legal move once
    for seed in range(20):
        states, _ = random_playout(game, seed, random.Random(seed))
        for state in states:
            for seat in (None, *range(game.players)):
                views.validate(game.view(state, seat))
            for seat in game.to_move(state):
                for move in game.legal_moves(state, seat):
                    legal.setdefault(json.dumps(move), move)
    for move in legal.values():
        moves.validate(move)


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_declares_contract_metadata(game_id):
    game = GAMES[game_id]
    assert game.players == 2
    assert isinstance(game.version, str) and game.version
    assert game.spectating_policy in get_args(SpectatingPolicy)
    if game.spectating_policy == "delayed":
        assert isinstance(game.spectating_delay_turns, int) and game.spectating_delay_turns >= 1
    else:
        assert game.spectating_delay_turns is None
    assert 1 <= game.default_move_timeout_s <= 180


def hidden_move_leaks(game, seeds=range(20)) -> list:
    """Moves shown for more than the Public view says: from one state, two legal moves of a seat that leave the same
    Public view must get the same `public_move` and leave the same view for every other seat (an opponent learns no
    more of a move than a Spectator). Returns the leaks as (state, seat, move, what told them apart)."""
    leaks = []
    for seed in seeds:
        states, _ = random_playout(game, seed, random.Random(seed))
        for state in states:
            for seat in sorted(game.to_move(state)):
                shown: dict[str, tuple] = {}
                for move in game.legal_moves(state, seat):
                    after = game.apply(state, seat, move)
                    public = json.dumps(game.view(after, None), sort_keys=True)
                    others = json.dumps([game.view(after, t) for t in range(game.players) if t != seat], sort_keys=True)
                    first = shown.setdefault(public, (game.public_move(state, seat, move), others))
                    if first[0] != game.public_move(state, seat, move):
                        leaks.append((state, seat, move, "public_move"))
                    if first[1] != others:
                        leaks.append((state, seat, move, "view"))
    return leaks


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_a_move_never_shows_more_than_the_public_view_live_or_to_the_other_seats(game_id):
    assert hidden_move_leaks(GAMES[game_id]) == []


class Secret(Game):
    """Both seats pick a hidden digit at once; then the Match is over. A test double for the check above."""
    id, name, version = "secret", "Secret", "0.0.1"
    move_schema, view_schema = {"type": "integer"}, {"type": "object"}

    def initial_state(self, seed):
        return {"seed": seed, "digits": [None, None]}

    def to_move(self, state):
        return {i for i, d in enumerate(state["digits"]) if d is None}

    def legal_moves(self, state, seat):
        return list(range(10)) if seat in self.to_move(state) else []

    def apply(self, state, seat, move):
        digits = list(state["digits"])
        digits[seat] = move
        return {**state, "digits": digits}

    def outcome(self, state):
        return None if self.to_move(state) else [0.5, 0.5]

    def view(self, state, seat):
        return {"picked": [d is not None for d in state["digits"]],
                "mine": None if seat is None else state["digits"][seat]}


class HiddenSecret(Secret):
    def public_move(self, state, seat, move):
        return None


class PeekingSecret(HiddenSecret):
    """Each seat's view (not the Public view) shows both digits."""
    def view(self, state, seat):
        public = super().view(state, seat)
        return public if seat is None else {**public, "digits": state["digits"]}


def test_the_hidden_move_check_catches_a_game_that_shows_hidden_moves_live_or_to_the_other_seat():
    assert {leak[3] for leak in hidden_move_leaks(Secret(), range(2))} == {"public_move"}
    assert hidden_move_leaks(HiddenSecret(), range(2)) == []
    assert {leak[3] for leak in hidden_move_leaks(PeekingSecret(), range(2))} == {"view"}
    assert Secret().public_move({}, 0, 7) == 7  # by default a move is shown as played
