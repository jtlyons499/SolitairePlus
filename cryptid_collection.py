"""Owned cards, legal decks and durable pack receipts; independent of Pygame."""
from collections import Counter
from functools import lru_cache
import copy
import random
import secrets
from cryptid_creatures import CryptidCatalog

SCHEMA_VERSION=1
PACK_SIZE=5
LEVEL_PACKS=2


@lru_cache(maxsize=1)
def catalog():return CryptidCatalog()


def _number(value,default=0,maximum=999999):
    try:return max(0,min(maximum,int(value)))
    except (ValueError,TypeError,OverflowError):return default


def starter_inventory(cards):
    owned=Counter()
    for deck in cards.decks.values():
        for cid,count in Counter(deck['cards']).items():owned[cid]=max(owned[cid],count)
    return dict(owned)


def deck_errors(deck,owned=None,cards=None):
    cards=cards or catalog()
    errors=[]
    if not isinstance(deck,list):return ['Deck must be a list of cards.']
    if len(deck)!=30:errors.append(f'{len(deck)}/30 cards: add or remove cards to reach 30.')
    counts=Counter(cid for cid in deck if isinstance(cid,str))
    if len(list(counts.elements()))!=len(deck) or any(cid not in cards.cards for cid in counts):
        errors.append('Deck contains an unknown card.');return errors
    creatures=sum(n for cid,n in counts.items() if cards.cards[cid]['kind']=='creature')
    if creatures!=8:errors.append(f'{creatures}/8 creatures: use exactly eight creature cards.')
    if any(n>2 for n in counts.values()):errors.append('A deck allows at most two copies of each card.')
    if owned is not None and any(n>owned.get(cid,0) for cid,n in counts.items()):
        errors.append('This deck uses more copies than you own.')
    return errors


def new_collection(level=1,cards=None):
    cards=cards or catalog()
    return dict(schema_version=SCHEMA_VERSION,owned=starter_inventory(cards),
                decks=[dict(name=d['name'],cards=list(d['cards'])) for d in cards.decks.values()],
                active_deck=0,packs={'creature':2},rewarded_through_level=max(1,_number(level,1)),
                pack_seed=secrets.randbits(63),packs_opened=0,pending_reveal=None,
                matches=0,wins=0,draws=0,battle_serial=0,last_rewarded_battle=0)


def normalize_collection(value=None,level=1,cards=None):
    cards=cards or catalog()
    if not isinstance(value,dict) or not isinstance(value.get('owned'),dict):
        return new_collection(level,cards)
    result=new_collection(level,cards)
    for cid,count in value['owned'].items():
        if cid in cards.cards:result['owned'][cid]=max(result['owned'].get(cid,0),_number(count))
    result['packs']={'creature':_number(value.get('packs',{}).get('creature',0)) if isinstance(value.get('packs'),dict) else 0}
    result['rewarded_through_level']=max(_number(level,1),_number(value.get('rewarded_through_level'),1))
    for name in ('packs_opened','matches','wins','draws','battle_serial','last_rewarded_battle'):
        result[name]=_number(value.get(name,0))
    result['pack_seed']=_number(value.get('pack_seed'),result['pack_seed'],2**63-1)
    decks=value.get('decks',[])
    for i in range(3):
        if isinstance(decks,list) and i<len(decks) and isinstance(decks[i],dict):
            d=decks[i]
            if not deck_errors(d.get('cards'),result['owned'],cards):
                result['decks'][i]={'name':str(d.get('name') or f'Deck {i+1}')[:32],'cards':list(d['cards'])}
    result['active_deck']=_number(value.get('active_deck'),0,2)
    receipt=value.get('pending_reveal')
    if isinstance(receipt,dict) and isinstance(receipt.get('cards'),list) and len(receipt['cards'])==PACK_SIZE:
        entries=receipt['cards']
        if all(isinstance(e,dict) and e.get('id') in cards.cards for e in entries):
            result['pending_reveal']={'number':_number(receipt.get('number'),result['packs_opened']),
                'cards':[{'id':e['id'],'new':bool(e.get('new')),'copies_after':_number(e.get('copies_after'),1)} for e in entries]}
    return result


def award_level_packs(state,level):
    level=max(1,_number(level,1))
    through=state['rewarded_through_level']
    if level<=through:return 0
    amount=(level-through)*LEVEL_PACKS
    state['packs']['creature']+=amount
    state['rewarded_through_level']=level
    return amount


def open_pack(state,cards=None):
    cards=cards or catalog()
    if state.get('pending_reveal'):return state['pending_reveal']
    if state['packs']['creature']<1:raise ValueError('No creature packs available.')
    rng=random.Random(f"{state['pack_seed']}:{state['packs_opened']+1}")
    common=[cid for cid,c in cards.cards.items() if c['kind']=='creature' and c['rarity']=='Common']
    uncommon=[cid for cid,c in cards.cards.items() if c['kind']=='creature' and c['rarity']!='Common']
    support=[cid for cid,c in cards.cards.items() if c['kind']!='creature']
    premium=[cid for cid,c in cards.cards.items() if c['rarity']!='Common']
    chosen=[rng.choice(uncommon if uncommon and rng.random()<.18 else common) for _ in range(3)]
    chosen.append(rng.choice(support))
    chosen.append(rng.choice(premium or uncommon or common))
    entries=[]
    for cid in chosen:
        before=state['owned'].get(cid,0)
        state['owned'][cid]=before+1
        entries.append({'id':cid,'new':before==0,'copies_after':before+1})
    state['packs']['creature']-=1
    state['packs_opened']+=1
    state['pending_reveal']={'number':state['packs_opened'],'cards':entries}
    return state['pending_reveal']


def save_deck(state,index,deck,name,cards=None):
    errors=deck_errors(deck,state['owned'],cards)
    if errors:raise ValueError(' '.join(errors))
    if index not in (0,1,2):raise ValueError('Choose one of the three deck slots.')
    state['decks'][index]={'name':str(name or f'Deck {index+1}')[:32],'cards':list(deck)}
    state['active_deck']=index


def reward_battle(state,serial,winner):
    if serial<=state['last_rewarded_battle'] or serial>state['battle_serial']:return None
    if winner not in (0,1,2):return None
    state['last_rewarded_battle']=serial
    state['matches']+=1
    state['wins']+=int(winner==0)
    state['draws']+=int(winner==2)
    if winner==0:state['packs']['creature']+=1
    return {'xp':120 if winner==0 else 70 if winner==2 else 55,'packs':int(winner==0)}


def transaction(state,operation,persist):
    """Rollback the live collection if saving fails; do not reveal uncommitted cards."""
    before=copy.deepcopy(state)
    try:
        result=operation()
        if persist:persist()
        return result
    except Exception:
        state.clear();state.update(before)
        raise
