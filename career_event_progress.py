"""Save and resume a calendar night's public results and session totals."""
import copy
FIELDS=('career_event_has_activity','career_event_result_log','career_event_news_posted',
        'texas_holdem_session_net','five_card_draw_session_net','seven_card_stud_session_net',
        'blackjack_session_net','blackjack_session_rating_change','roulette_session_net',
        'horse_races_session_net','horse_races_last_rewarded_races','faro_session_net',
        'five_o_poker_session_net','blind_mans_bluff_session_net')

def store_event_progress(entry,namespace):
    if not isinstance(entry,dict) or entry.get('debug') or namespace.get('current_game_mode')!='career':return
    entry['night_progress']={key:copy.deepcopy(namespace.get(key,[] if key=='career_event_result_log' else False if key in ('career_event_has_activity','career_event_news_posted') else 0)) for key in FIELDS}

def restore_event_progress(entry,namespace):
    progress=entry.get('night_progress') if isinstance(entry,dict) else None
    if not isinstance(progress,dict):return False
    for key in FIELDS:
        value=progress.get(key)
        if key=='career_event_result_log':
            namespace[key]=copy.deepcopy(value) if isinstance(value,list) else []
        elif key in ('career_event_has_activity','career_event_news_posted'):namespace[key]=value is True
        else:namespace[key]=value if isinstance(value,(int,float)) and not isinstance(value,bool) else 0
    return True
