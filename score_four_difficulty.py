"""Offline puzzle pools from 4nums' empirical adjusted-median-time ranking."""
import json
from pathlib import Path
from functools import lru_cache
from itertools import combinations_with_replacement

DIFFICULTIES = {
    'easy': ('Easy', 'Fastest solved puzzles with numbers 1–10.', 30),
    'standard': ('Standard', 'All solvable puzzles using numbers 1–10.', 50),
    'difficult': ('Difficult', 'Slower half of ranked puzzles; J, Q and K included.', 70),
    'extreme': ('Extreme', 'The 300 slowest ranked puzzles; J, Q and K included.', 90),
}

@lru_cache(maxsize=1)
def ranked_puzzles():
    path = Path(__file__).resolve().parent / 'data' / 'score_four_difficulties.json'
    return json.loads(path.read_text(encoding='utf-8'))['puzzles']

@lru_cache(maxsize=4)
def puzzle_pool(difficulty):
    rows = ranked_puzzles()
    if difficulty == 'easy':
        return tuple(tuple(row['numbers']) for row in rows[:300] if max(row['numbers']) <= 10)
    if difficulty == 'standard':
        return tuple(tuple(row['numbers']) for row in rows if max(row['numbers']) <= 10)
    if difficulty == 'difficult':
        return tuple(tuple(row['numbers']) for row in rows[len(rows)//2:])
    if difficulty == 'extreme':
        return tuple(tuple(row['numbers']) for row in rows[-300:])
    raise ValueError('Unknown Score-Four difficulty: ' + str(difficulty))
