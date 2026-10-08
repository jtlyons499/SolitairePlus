"""Alien Night story definition and calendar progression after Bigfoot Night."""
import json
from pathlib import Path
from career_activities import validate_story, new_story

STORY = validate_story(json.loads((Path(__file__).resolve().parent/'data/alien_story.json').read_text(encoding='utf-8')))

def new_alien_story():
    return new_story(data=STORY)

def refresh_adventure_schedule(schedule, bigfoot, alien, current_day=None):
    """Keep completed history and current outcome; replace only future adventure slots."""
    kind = 'bigfoot' if not bigfoot.get('finished') else 'alien' if not alien.get('finished') else None
    for day, entry in enumerate(schedule,1):
        if not isinstance(entry,dict):
            continue
        if entry.get('completed') or entry.get('event_id') not in ('career_encounter','bigfoot_night','alien_night'):
            continue
        state=entry.get('career_activity') or {}
        if day==current_day and state.get('claimed'):
            continue
        event_id = kind+'_night' if kind else 'press_interview_01'
        if entry.get('event_id') != event_id:
            entry.update(event_id=event_id,title={'bigfoot':'Bigfoot Night','alien':'Alien Night',None:'Press Interview'}[kind])
            entry.pop('career_activity',None)
