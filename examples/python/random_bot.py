# SPDX-License-Identifier: 0BSD  (free to copy as the start of your own Bot: see examples/LICENSE)
"""Reference bot: plays random legal moves. Stdlib only, so it doubles as API docs.

Usage: BOTINGAME_TOKEN=big_... python3 examples/python/random_bot.py --name alice --arena connect4-elo --games 5

Get the token by creating the Bot on your Dashboard at https://botingame.com. The Arena must be one of the Bot's
Game, for example uttt-elo for a uttt Bot. The Bot API is --base if given, else BOTINGAME_URL, else
https://api.botingame.com.

Keeping under the rate limit is the Bot's job: this one takes at least THINK_S per move, so it never rushes a Match.
"""
import argparse
import itertools
import json
import os
import random
import time
import urllib.request

THINK_S = 0.5  # the least time a move takes


def call(base, method, path, token=None, body=None):
    req = urllib.request.Request(base + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def log(name, msg):
    print(f"[{name}] {msg}", flush=True)


def play_one(base, token, arena, name):
    log(name, f"queueing in {arena} on {base}")
    # Queueing is a long-poll: we stay queued only while it is open, so re-poll until paired.
    while (q := call(base, "POST", f"/v1/arenas/{arena}/queue?wait=25", token))["status"] != "matched":
        log(name, "still waiting for an opponent")
    match_id = q["match_id"]
    log(name, f"matched: {match_id}")
    while True:
        m = call(base, "GET", f"/v1/matches/{match_id}?wait=25", token)  # returns on my turn or the end
        if m["status"] == "finished":
            return m
        if m["your_turn"]:
            time.sleep(THINK_S)
            move = random.choice(m["legal_moves"])
            log(name, f"turn {m['turn']}: playing {move}")
            call(base, "POST", f"/v1/matches/{match_id}/moves", token, {"turn": m["turn"], "move": move})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("BOTINGAME_URL", "https://api.botingame.com"))
    ap.add_argument("--name", default="bot", help="label for the log lines")
    ap.add_argument("--arena", default="connect4-elo")
    ap.add_argument("--games", type=int, default=5, help="0 = play forever (Ctrl+C to stop)")
    a = ap.parse_args()
    token = os.environ["BOTINGAME_TOKEN"]
    for i in itertools.count() if a.games == 0 else range(a.games):
        m = play_one(a.base, token, a.arena, a.name)
        score = m["result"][m["your_seat"]]
        log(a.name, f"game {i + 1}: {'win' if score == 1 else 'draw' if score == 0.5 else 'loss'} ({m['reason']})")


if __name__ == "__main__":
    main()
