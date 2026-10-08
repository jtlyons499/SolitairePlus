"""Data-driven adventure engine. Bigfoot is the default story definition."""
import copy
import json
from pathlib import Path

def validate_story(data):
    scenes = data['scenes']
    if data['start'] not in scenes:
        raise ValueError('Story start scene does not exist')
    option_ids = set()
    for scene_id, scene in scenes.items():
        if scene['location'] not in data['locations'] or not scene['options']:
            raise ValueError(f'Invalid story scene: {scene_id}')
        for option in scene['options']:
            if option['id'] in option_ids:
                raise ValueError(f"Duplicate choice ID: {option['id']}")
            option_ids.add(option['id'])
            if option['next'] != 'finished' and option['next'] not in scenes:
                raise ValueError(f"Missing destination: {option['next']}")
            effects = option['effects']
            for key in ('cash', 'fans'):
                if not isinstance(effects[key], int):
                    raise ValueError(f'Non-integer {key}: {scene_id}')
            for item in effects['items'] + option['requires'].get('items', []):
                if item not in data['items']:
                    raise ValueError(f'Unknown item: {item}')
            for cosmetic in effects['cosmetics']:
                if cosmetic not in data['cosmetics']:
                    raise ValueError(f'Unknown cosmetic: {cosmetic}')
    reachable = set()

    def visit(scene_id):
        if scene_id == 'finished' or scene_id in reachable:
            return
        reachable.add(scene_id)
        for option in scenes[scene_id]['options']:
            visit(option['next'])
    visit(data['start'])
    if reachable != set(scenes):
        raise ValueError('Story contains unreachable scenes')
    return data
STORY = validate_story(json.loads((Path(__file__).resolve().parent / 'data' / 'bigfoot_story.json').read_text(encoding='utf-8')))

def new_story(*, data=None):
    data = STORY if data is None else data
    return {'schema': 2, 'visits': 0, 'scene': data['start'], 'location': data['scenes'][data['start']]['location'], 'items': [], 'flags': {}, 'cosmetics': [], 'history': [], 'visited_locations': [data['scenes'][data['start']]['location']], 'last_result': '', 'finished': False}

def normalize_story(value, *, data=None):
    data = STORY if data is None else data
    result = new_story(data=data)
    if not isinstance(value, dict):
        return result
    try:
        result['visits'] = max(0, int(value.get('visits', 0)))
    except (TypeError, ValueError):
        pass
    if value.get('schema') != 2:
        if value.get('shoes'):
            result['items'] = ['sasquatch_sandals']
        return result
    result['scene'] = value.get('scene') if value.get('scene') in data['scenes'] or value.get('scene') == 'finished' else data['start']
    result['finished'] = result['scene'] == 'finished'
    for key, catalog in (('items', data['items']), ('cosmetics', data['cosmetics']), ('visited_locations', data['locations'])):
        values = value.get(key, [])
        if isinstance(values, list):
            result[key] = list(dict.fromkeys((x for x in values if isinstance(x, str) and x in catalog)))
    flags = value.get('flags', {})
    result['flags'] = copy.deepcopy(flags) if isinstance(flags, dict) else {}
    result['location'] = data.get('finish_location', 'Bigfoot’s Ladder') if result['finished'] else data['scenes'][result['scene']]['location']
    if result['location'] not in result['visited_locations']:
        result['visited_locations'].append(result['location'])
    result['last_result'] = str(value.get('last_result', ''))
    result['history'] = copy.deepcopy(value.get('history', [])) if isinstance(value.get('history'), list) else []
    return result

def start_night(story, *, data=None):
    data = STORY if data is None else data
    if story['finished']:
        return {'kind': data.get('kind', 'bigfoot'), 'version': 2, 'night': story['visits'], 'scene': 'finished', 'intro': 'Your ' + data.get('name', 'Bigfoot Night') + ' adventure is complete.', 'options': [], 'claimed': True, 'stage': 'complete', 'result_text': story['last_result'], 'cash_change': 0, 'fan_change': 0}
    scene = data['scenes'][story['scene']]
    return {'kind': data.get('kind', 'bigfoot'), 'version': 2, 'night': story['visits'] + 1, 'scene': story['scene'], 'intro': scene['intro'], 'options': copy.deepcopy(scene['options']), 'claimed': False, 'stage': 'intro'}

def requirement_reason(story, option, cash, *, data=None):
    data = STORY if data is None else data
    requirements = option['requires']
    missing = [data['items'][item] for item in requirements.get('items', []) if item not in story['items']]
    if missing:
        return 'Requires: ' + ', '.join(missing)
    if requirements.get('attitude') and story['flags'].get('attitude') not in requirements['attitude']:
        return 'Requires: Bigfoot’s trust' if requirements['attitude'] == ['trusted'] else 'Requires: Bigfoot’s distrust or clout-chaser impression'
    if cash + option['effects']['cash'] < 0:
        return f"Requires: ${-option['effects']['cash']:,}"
    return ''

def choose_option(story, night, index, cash, *, data=None):
    data = STORY if data is None else data
    if night.get('claimed') or story['finished'] or night.get('scene') != story['scene']:
        return None
    if not isinstance(index, int) or not 0 <= index < len(night['options']):
        return None
    option_id = night['options'][index]['id']
    choice = next((o for o in data['scenes'][story['scene']]['options'] if o['id'] == option_id), None)
    if choice is None or any((h.get('choice') == option_id for h in story['history'] if isinstance(h, dict))):
        return None
    if requirement_reason(story, choice, cash, data=data):
        return None
    effects = choice['effects']
    story['items'] = list(dict.fromkeys(story['items'] + effects['items']))
    story['cosmetics'] = list(dict.fromkeys(story['cosmetics'] + effects['cosmetics']))
    story['flags'].update(effects['flags'])
    story['visits'] += 1
    story['history'].append({'night': night['night'], 'scene': story['scene'], 'choice': option_id})
    story['scene'] = choice['next']
    story['finished'] = choice['next'] == 'finished'
    if not story['finished']:
        story['location'] = data['scenes'][choice['next']]['location']
    if story['location'] not in story['visited_locations']:
        story['visited_locations'].append(story['location'])
    story['last_result'] = choice['result']
    night.update(claimed=True, stage='result', result_text=choice['result'], cash_change=effects['cash'], fan_change=effects['fans'], earned_items=effects['items'], earned_cosmetics=effects['cosmetics'])
    return copy.deepcopy(effects)

def add_story_catalogs(backgrounds, felts, titles, *, data=None):
    data = STORY if data is None else data
    catalogs = {'backgrounds': backgrounds, 'felts': felts, 'titles': titles}
    for key, data in data['cosmetics'].items():
        catalogs[data['kind']][key] = copy.deepcopy(data)

def reconcile_story_cosmetics(story, backgrounds, felts, titles, *, data=None):
    data = STORY if data is None else data
    sets = {'backgrounds': backgrounds, 'felts': felts, 'titles': titles}
    for key in story['cosmetics']:
        sets[data['cosmetics'][key]['kind']].add(key)
