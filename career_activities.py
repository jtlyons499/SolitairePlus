"""Persistent, manually authored Bigfoot Night story rules."""
import copy

NIGHT_ONE = 'As a bigfoot enthusiast, you are excited to have finally joined a group of like-minded individuals and start your journey toward finding bigfoot and unlocking its powers.'

def new_story():
    return {'visits': 0, 'location': 'Camp', 'shoes': False, 'clues': 0, 'last_result': '', 'history': []}

def normalize_story(value):
    result = new_story()
    if not isinstance(value, dict):
        return result
    for key in ('visits', 'clues'):
        try: result[key] = max(0, int(value.get(key, 0)))
        except (TypeError, ValueError): pass
    result['location'] = value.get('location') if value.get('location') in ('Camp', 'Forest', 'Clearing') else 'Camp'
    result['shoes'] = value.get('shoes') is True
    result['last_result'] = str(value.get('last_result', ''))
    result['history'] = [x for x in value.get('history', []) if isinstance(x, dict)][-30:] if isinstance(value.get('history'), list) else []
    return result

def option(name, cash, fans, result, **changes):
    return dict(name=name, cash=cash, fans=fans, result=result, changes=changes)

def chapter(story):
    location = story['location']
    if location == 'Camp':
        intro = NIGHT_ONE if story['visits'] == 0 else 'You meet your fellow Bigfoot investigators at camp again. Mead, stories and an unexplored trail await.'
        options = [
            option('Drink mead and gamble with your fellow Bigfoot investigators', 50, 50,
                   'You have a great night with everyone, and win big at darts. The journey can wait a little.'),
            option('Get advice on the best Bigfoot tracking gear and then go shopping', -50, 0,
                   'You acquired advanced Sasquatch Shoes and will be better prepared for your first outing.', shoes=True),
            option('Head out on the trail with your group', 0, 100,
                   "A few hours into the night, your group runs out of beer and begins to head home. However, as you're walking back, you all hear a twig snap. To be continued...", location='Forest'),
        ]
        if story['shoes']:
            options[1] = option('Take the prepared trail in your Sasquatch Shoes', 0, 150,
                                'Your Sasquatch Shoes make the muddy trail easy going. Near the forest, you find an enormous footprint before the others notice it.', location='Forest', clue=1)
    elif location == 'Forest':
        intro = 'The twig snap is still on everyone\'s mind. Tonight your group returns to the forest. A heavy trail leads toward a clearing; another path winds back to camp.'
        options = [
            option('Follow the heavy tracks together', 0, 40, 'You follow deep impressions through the trees and reach a quiet clearing. Something very large has passed through here.', location='Clearing', clue=1),
            option('Keep watch and document the forest', 25, 30, 'You record a distant call and send your notes to the investigators. The group chips in for your careful work.', clue=1),
            option('Return to camp and share the story', 0, 50, 'The group gathers around the fire to compare what everyone heard. You decide to prepare another outing.', location='Camp'),
        ]
        if story['shoes']:
            options.insert(0, option('Use your Sasquatch Shoes to examine the muddy tracks', 25, 75,
                                    'Your shoes carry you safely through the mud. You photograph a clear footprint and lead the group to the clearing.', location='Clearing', clue=2))
    else:
        intro = 'You return to the clearing with your notes. Broken branches form a strange arch, and a low call rolls through the trees. Your group must decide how to investigate.'
        options = [
            option('Observe quietly and record the call', 25, 50, 'You capture the call without disturbing the clearing. Back at camp, the group adds your recording to its growing evidence collection.', location='Camp', clue=2),
            option('Inspect the branches with the group', 0, 60, 'You find coarse hair caught in the branches. Nobody can identify it, but you carefully bag the sample before returning to the forest.', location='Forest', clue=2),
            option('Leave a respectful offering and head home', -25, 80, 'You leave a small offering and return to camp. A shape watches from the treeline, then disappears. The investigators will remember this night.', location='Camp', clue=1),
        ]
    return {'intro': intro, 'options': options}

def start_night(story):
    data = chapter(story)
    return {'kind': 'bigfoot', 'night': story['visits']+1, 'intro': data['intro'],
            'options': data['options'], 'stage': 'intro', 'claimed': False}

def choose_option(story, night, index, cash):
    if night.get('claimed') or not isinstance(index, int) or not 0 <= index < len(night['options']):
        return None
    choice = night['options'][index]
    if cash + choice['cash'] < 0:
        return None
    changes = choice['changes']
    story['location'] = changes.get('location', story['location'])
    story['shoes'] = changes.get('shoes', story['shoes'])
    story['clues'] += changes.get('clue', 0)
    story['visits'] += 1
    story['last_result'] = choice['result']
    story['history'].append({'night': night['night'], 'choice': choice['name'], 'location': story['location']})
    story['history'] = story['history'][-30:]
    night.update(claimed=True, stage='result', result_text=choice['result'], cash_change=choice['cash'], fan_change=choice['fans'])
    return copy.deepcopy(choice)
