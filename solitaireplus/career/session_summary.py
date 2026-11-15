"""Shared, player-facing session requirements and night totals."""

def poker_session_status(game, rated=True):
    completed = len(getattr(game, 'rating_seen_hands', ()))
    if not rated:
        return 'Practice table • No Career rating changes'
    if completed:
        return f'Session counts • {completed} hands • Rating on cash-out'
    return 'Complete 1 hand • XP and rating on cash-out'


def night_game_net(results, game_id, fallback=0):
    values = [entry['net'] for entry in results if isinstance(entry, dict)
              and entry.get('game_id') == game_id and isinstance(entry.get('net'), (int, float))]
    return int(sum(values)) if values else int(fallback)


def track_night_cash(namespace, game_id, net):
    if namespace.get('current_game_mode') != 'career':
        return
    totals = namespace.setdefault('career_event_money_totals', {})
    totals[game_id] = int(totals.get(game_id, 0)) + int(net)


def night_cash_total(namespace, game_id, fallback=0):
    return int(namespace.get('career_event_money_totals', {}).get(game_id, fallback))
