"""Case odds, scaled prices and persistent collections; no UI or random rerolls."""
import copy
import math
import random
from career_ratings import CATEGORY_KEYS, GAME_RATING_KEYS

COLORS={'junk':(104,192,231),'trophy':(244,194,70),'cash':(88,205,129),'rating':(225,89,97),'fans':(194,203,216),'cosmetic':(80,112,225)}
# Artwork paths are relative to assets/case_opening; felt paths to the game folder.
import json
from pathlib import Path

CONFIG_PATH=Path(__file__).resolve().parent/'data'/'case_opening.json'


def load_catalog(path=CONFIG_PATH):
 data=json.loads(Path(path).read_text(encoding='utf-8'))
 cases=data['cases'];items=data['items']
 if not isinstance(cases,dict) or not cases or not isinstance(items,dict):raise ValueError('Cases and items must be nonempty objects.')
 def number(value,label):
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:raise ValueError(label+' must be a nonnegative number.')
 for key,item in items.items():
  if not isinstance(item,dict) or item.get('kind') not in COLORS or not isinstance(item.get('name'),str):raise ValueError('Invalid item: '+key)
  item['id']=key
  if item['kind']=='rating' and item.get('game') not in (*GAME_RATING_KEYS,*CATEGORY_KEYS):raise ValueError('Invalid rating target: '+key)
  for field in ('cash_multiplier','cash_amount','cash_fraction','cash_minimum','fan_multiplier','fan_fraction','fan_minimum','fan_amount','rating_points','weight'):
   if field in item:number(item[field],key+' '+field)
  if item['kind']=='cosmetic':
   if item.get('cosmetic_type') not in ('background','felt','title','cursor'):
    raise ValueError('Invalid cosmetic type: '+key)
   if not isinstance(item.get('asset_id'),str) or not item.get('asset_id'):
    raise ValueError('Cosmetic needs asset_id: '+key)
   if not isinstance(item.get('asset_path'),str) or not item.get('asset_path'):
    raise ValueError('Cosmetic needs asset_path: '+key)
 for key,case in cases.items():
  if not isinstance(case,dict) or not isinstance(case.get('name'),str):raise ValueError('Invalid case: '+key)
  for field in ('minimum','fraction','rating_points'):number(case.get(field,0),key+' '+field)
  weights=case.get('weights',{})
  if not isinstance(weights,dict) or not weights or any(k not in COLORS for k in weights):raise ValueError('Invalid categories: '+key)
  for value in weights.values():number(value,key+' weight')
  if abs(sum(weights.values())-100)>.0001:raise ValueError('Category odds must total 100: '+key)
  pool=case.get('pool',list(items))
  if not isinstance(pool,list) or not pool or any(not isinstance(i,str) or i not in items for i in pool) or len(set(pool))!=len(pool):raise ValueError('Invalid item pool: '+key)
  for kind,weight in weights.items():
   if weight>0 and not any(items[i]['kind']==kind and not items[i].get('earned') for i in pool):raise ValueError('No eligible '+kind+' item in '+key)
 return cases,items

CASES,ITEMS=load_catalog()


def new_case_state():return {'version':1,'opened':0,'spent':0,'inventory':{},'history':[]}


def normalize_case_state(value):
 result=new_case_state()
 if not isinstance(value,dict):return result
 for key in ('opened','spent'):
  n=value.get(key,0);result[key]=max(0,min(10**15,n)) if isinstance(n,int) else 0
 inventory=value.get('inventory',{})
 if isinstance(inventory,dict):result['inventory']={key:min(10**9,n) for key,n in inventory.items() if key in ITEMS and isinstance(n,int) and n>0}
 history=value.get('history',[])
 if isinstance(history,list):
  for receipt in history[-30:]:
   if isinstance(receipt,dict) and isinstance(receipt.get('item_id'),str) and receipt.get('item_id') in ITEMS and isinstance(receipt.get('case'),str) and receipt.get('case') in CASES and isinstance(receipt.get('number'),int):
    result['history'].append(copy.deepcopy(receipt))
 return result


def case_price(case_id,cash):
 case=CASES[case_id];return max(case['minimum'],int(max(0,cash)*case['fraction']+.5))


def choose_item(case_id,rng):
 case=CASES[case_id];kinds=list(case['weights'])
 kind=rng.choices(kinds,weights=[case['weights'][k] for k in kinds],k=1)[0]
 pool=[ITEMS[key] for key in case.get('pool',list(ITEMS)) if ITEMS[key]['kind']==kind and not ITEMS[key].get('earned')]
 return rng.choices(pool,weights=[max(0,float(item.get('weight',1))) for item in pool],k=1)[0]


def purchase(state,case_id,cash,rng=None,fans=0):
 """Commit one purchase and reward receipt. Caller saves atomically before reveal."""
 if case_id not in CASES:raise ValueError('Unknown case.')
 cost=case_price(case_id,cash)
 if cash<cost:raise ValueError('Not enough cash for this case.')
 rng=rng or random.SystemRandom();item=choose_item(case_id,rng)
 amount=0
 if item['kind']=='cash':
  if 'cash_amount' in item:amount=round(item['cash_amount'])
  elif 'cash_fraction' in item:amount=max(round(item.get('cash_minimum',0)),round(max(0,cash)*item['cash_fraction']))
  else:amount=round(cost*item.get('cash_multiplier',1))
 elif item['kind']=='rating':amount=round(item.get('rating_points',CASES[case_id].get('rating_points',8)))
 elif item['kind']=='fans':
  if 'fan_amount' in item:amount=round(item['fan_amount'])
  elif 'fan_fraction' in item:amount=max(round(item.get('fan_minimum',5)),round(max(0,fans)*item['fan_fraction']))
  else:amount=round(max(item.get('fan_minimum',5),round(math.sqrt(cost)*item.get('fan_multiplier',1))))
 result={'number':state['opened']+1,'case':case_id,'cost':cost,'item_id':item['id'],'kind':item['kind'],'amount':amount}
 if 'game' in item:result['game']=item['game']
 state['opened']+=1;state['spent']+=cost
 state['inventory'][item['id']]=state['inventory'].get(item['id'],0)+1
 state['history'].append(result);del state['history'][:-30]
 return result,cash-cost+(amount if item['kind']=='cash' else 0)


def award_earned_trophies(state,achievements):
 stats=achievements.get('stats',{}) if isinstance(achievements,dict) else {}
 unlocked=achievements.get('unlocked',[]) if isinstance(achievements,dict) else []
 for identity,earned in [('hundred_wins',stats.get('solitaire_wins',0)>=100),('table_champion','table_clear' in unlocked)]:
  if earned:state['inventory'].setdefault(identity,1)
