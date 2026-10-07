"""Save and resume a calendar night's public results and session totals."""
import copy
FIELDS=('career_event_has_activity','career_event_result_log','career_event_news_posted',
        'texas_holdem_session_net','five_card_draw_session_net','seven_card_stud_session_net',
        'blackjack_session_net','blackjack_session_rating_change','roulette_session_net',
        'horse_races_session_net','horse_races_last_rewarded_races','faro_session_net',
        'five_o_poker_session_net','blind_mans_bluff_session_net',
        'career_event_start_strategy','career_event_start_poker','career_event_start_casino',
        'career_event_start_global','career_event_start_fans','career_event_start_cash','career_event_start_xp','career_event_money_totals')

def store_event_progress(entry,namespace):
    if not isinstance(entry,dict) or entry.get('debug') or namespace.get('current_game_mode')!='career':return
    entry['night_progress']={key:copy.deepcopy(namespace.get(key,{} if key=='career_event_money_totals' else [] if key=='career_event_result_log' else False if key in ('career_event_has_activity','career_event_news_posted') else 0)) for key in FIELDS}

def restore_event_progress(entry,namespace):
    progress=entry.get('night_progress') if isinstance(entry,dict) else None
    if not isinstance(progress,dict):
        for category in ('strategy','poker','casino'):
            namespace['career_event_start_'+category] = float(namespace.get('career_ratings',{}).get(category,1000))
        namespace['career_event_start_global'] = float(namespace.get('career_rating',1000))
        namespace['career_event_start_fans'] = namespace.get('career_fans',0)
        namespace['career_event_money_totals'] = {}
        namespace['career_event_start_cash'] = namespace.get('career_cash',0)
        namespace['career_event_start_xp'] = namespace.get('player_xp',0)
        return False
    for key in FIELDS:
        default = namespace.get('career_ratings',{}).get(key.removeprefix('career_event_start_'),1000) if key.startswith('career_event_start_') else None
        if key == 'career_event_start_global': default = namespace.get('career_rating',1000)
        if key == 'career_event_start_fans': default = namespace.get('career_fans',0)
        if key == 'career_event_start_cash': default = namespace.get('career_cash',0)
        if key == 'career_event_start_xp': default = namespace.get('player_xp',0)
        value=progress.get(key, default)
        if key=='career_event_money_totals':
            if isinstance(value, dict):
                namespace[key] = {game: int(net) for game, net in value.items() if isinstance(net, (int, float)) and not isinstance(net, bool)}
            else:
                # Older in-progress saves only contain the last session totals.
                namespace[key] = {game: int(progress.get(game+'_session_net', 0)) if isinstance(progress.get(game+'_session_net', 0), (int, float)) else 0 for game in
                                  ('texas_holdem','five_card_draw','seven_card_stud','blackjack','roulette','horse_races','faro','five_o_poker','blind_mans_bluff')}
        elif key=='career_event_result_log':
            namespace[key]=copy.deepcopy(value) if isinstance(value,list) else []
        elif key in ('career_event_has_activity','career_event_news_posted'):namespace[key]=value is True
        else:namespace[key]=value if isinstance(value,(int,float)) and not isinstance(value,bool) else 0
    return True

