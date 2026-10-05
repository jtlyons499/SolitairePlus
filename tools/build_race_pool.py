"""Offline pool builder. Run from the project root; never runs during play."""
import heapq
import json
from pathlib import Path
import random
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from solitaire_race_deals import apply_move, fits, initial_state, opening_is_varied, rank, red, verify_deal


def safe(card, foundations):
    value, suit = rank(card), card // 13
    other = [index for index in range(4) if red(index * 13) != red(card)]
    same = next(index for index in range(4) if index != suit and red(index * 13) == red(card))
    return value <= 2 or (min(foundations[index] for index in other) >= value - 1
                         and foundations[same] >= value - 2)


def successors(state):
    columns, reserve, foundations = state
    moves = []
    for index, (hidden, column) in enumerate(columns):
        if column and rank(column[-1]) == foundations[column[-1] // 13] + 1:
            move = ("tf", index, 0, 1)
            if safe(column[-1], foundations):
                return [move]
            moves.append(move)
    for card in reserve:
        if rank(card) == foundations[card // 13] + 1:
            move = ("rf", card, 0, 1)
            if safe(card, foundations):
                return [move]
            moves.append(move)
    for source, (hidden, column) in enumerate(columns):
        for start in range(hidden, len(column)):
            run = column[start:]
            for destination, (_, target) in enumerate(columns):
                if source == destination or not fits(run[0], target):
                    continue
                if not target and start == 0:
                    continue  # Moving a whole King column to another empty slot gains nothing.
                moves.append(("tt", source, destination, len(run)))
    for card in reserve:
        empty_seen = False
        for destination, (_, target) in enumerate(columns):
            if fits(card, target):
                if not target and empty_seen:
                    continue
                empty_seen |= not target
                moves.append(("rt", card, destination, 1))
    return moves


def score(state):
    columns, reserve, foundations = state
    hidden = sum(count for count, _ in columns)
    return 10 * sum(foundations) + 35 * (21 - hidden) + 2 * (24 - len(reserve))


def solve(deck, budget=6000):
    start = initial_state(deck)
    queue = [(-score(start), 0, start, None)]
    seen, parents = set(), {}
    serial = 0
    while queue and len(parents) < budget:
        _, node, state, parent = heapq.heappop(queue)
        canonical = (tuple(sorted(state[0])), state[1], state[2])
        if canonical in seen:
            continue
        seen.add(canonical)
        parents[node] = parent
        if sum(state[2]) == 52:
            solution = []
            while parents[node] is not None:
                node, move = parents[node]
                solution.append(move)
            solution.reverse()
            return solution
        for move in successors(state):
            next_state = apply_move(state, move)
            serial += 1
            heapq.heappush(queue, (-score(next_state), serial, next_state, (node, move)))
    return None


def main():
    rng = random.Random(20261005)
    deals, attempts = [], 0
    started = time.monotonic()
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 160
    while len(deals) < count:
        deck = list(range(52))
        rng.shuffle(deck)
        attempts += 1
        if not opening_is_varied(deck):
            continue
        solution = solve(deck)
        if not solution or len(solution) < 68:
            continue
        verify_deal(deck, solution)
        deals.append({"deck": deck, "solution": solution})
        if len(deals) % 10 == 0:
            print(f"{len(deals)} proven deals / {attempts} shuffles, {time.monotonic() - started:.1f}s", flush=True)
    target = Path(__file__).resolve().parents[1] / "data" / "solitaire_race_deals.json"
    target.write_text(json.dumps({"version": 1, "draw_count": 1, "deals": deals}, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
