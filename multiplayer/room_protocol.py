"""Public seat-relative room snapshots. Never serialize a deck, AI memory or hidden hand."""
import copy
from solitaireplus.games.poker.holdem import TexasHoldemGame
from solitaireplus.games.poker.core import describe_poker_score

# The room message format. The host stamps every message with it ('protocol'); a guest that
# sees no stamp or another number warns that the two games differ. Bump it whenever the room
# messages change meaning. (The relay's room version stays 2: changing it needs a relay redeploy.)
ROOM_PROTOCOL=3
PROTOCOL_NOTICE="The host's Solitaire+ is a different version. Update both games to play together."

PAIRS=(('player_stack','npc_stacks'),('player_hand_contribution','npc_hand_contributions'),('player_busted','npc_busted'),('player_bet_chunks','npc_bet_chunks'),('player_action_text','npc_action_texts'),('player_round_bet','npc_round_bets'),('player_folded','npc_folded'),('player_all_in','npc_all_in'),('player_has_acted','npc_has_acted'))
FIELDS=('hand_number','starting_stack','ante','small_blind','big_blind','pot','last_resolved_pot','current_bet','last_raise_size','betting_round_complete','current_stage','hand_complete','community_cards')

def seat_keys(mapping,index):
    """A {seat: chips} record seat-relative, with JSON-safe string keys (ClientGame turns them back)."""
    return {str(index[seat]):copy.deepcopy(value) for seat,value in mapping.items() if seat in index}

def int_keys(mapping):
    """seat_keys() back to {int seat: int chips}. Malformed host data is dropped, never raised on."""
    if not isinstance(mapping,dict):return {}
    result={}
    for seat,value in mapping.items():
        try:seat=int(seat)
        except (TypeError,ValueError):continue
        if isinstance(value,int) and not isinstance(value,bool):result[seat]=value
    return result

def clean_name(value):
    return ''.join(c for c in str(value) if c.isprintable())[:32].strip() or 'Player'

# A countdown further away than this (either way) is malformed and ignored.
COUNTDOWN_LIMIT_MS=3_600_000

def countdown_offset(message):
    """B70: milliseconds from the host's host_now to its countdown_at, or None when the message
    has no countdown or a malformed one (text, NaN, infinity, or absurdly far away)."""
    try:offset=int(message['countdown_at'])-int(message['host_now'])
    except (KeyError,TypeError,ValueError,OverflowError):return None
    return offset if -COUNTDOWN_LIMIT_MS<=offset<=COUNTDOWN_LIMIT_MS else None

def snapshot(game,viewer,revision,names):
    order=[viewer]+[i for i in range(len(names)) if i!=viewer];index={seat:i for i,seat in enumerate(order)}
    data={k:copy.deepcopy(getattr(game,k)) for k in FIELDS}
    for human,npc in PAIRS:
        values=[getattr(game,human),*getattr(game,npc)]
        data[human]=copy.deepcopy(values[viewer]);data[npc]=[copy.deepcopy(values[i]) for i in order[1:]]
    for key in ('current_actor','dealer_index','small_blind_index','big_blind_index','last_raiser'):
        data[key]=index.get(getattr(game,key),getattr(game,key))
    for key in ('winner_indexes','hand_seat_indexes','last_hand_busted_indexes'):
        data[key]=[index[i] for i in getattr(game,key) if i in index]
    hands=[game.player_hand,*game.npc_hands];folded=[game.player_folded,*game.npc_folded]
    reveal=game.current_stage=='showdown' or game.should_reveal_runout_hands()
    data['player_hand']=copy.deepcopy(hands[viewer])
    data['npc_hands']=[copy.deepcopy(hands[i]) if reveal and not folded[i] else [] for i in order[1:]]
    data['npcs']=[]
    for i in order[1:]:
        npc=game.npcs[i-1] if i>0 else {}
        public={key:copy.deepcopy(npc[key]) for key in ('id','portrait','avatar','portrait_style','age') if key in npc}
        public.update(id=npc.get('id',f'seat_{i}'),name=names[i])
        data['npcs'].append(public)
    data['showdown_hands']={}
    if game.current_stage=='showdown':
        for seat in order:
            if not folded[seat] and len(hands[seat])==2:
                evaluated=game.evaluate_best_hand(hands[seat]+game.community_cards)
                if evaluated:data['showdown_hands'][str(index[seat])]=describe_poker_score(evaluated[0],compact=True)
    data['last_pot_awards']=copy.deepcopy(game.last_pot_awards)
    for pot in data['last_pot_awards']:
        for key in ('winners','eligible','contributors'):
            if key in pot:pot[key]=[index[i] for i in pot[key] if i in index]
        # The shared engine's per-winner amounts (odd-chip order kept).
        if 'payouts' in pot:pot['payouts']=seat_keys(pot['payouts'],index)
    # Uncalled chips handed back (not a pot): the shared recap's 'Returned (uncalled):' lines.
    data['last_refunds']=seat_keys(getattr(game,'last_refunds',{}),index)
    data['result_text']=' | '.join(f"{names[i]} wins" for i in game.winner_indexes) if game.hand_complete else ''
    return {'type':'state','revision':revision,'data':data,'names':[names[i] for i in order]}

class ClientGame(TexasHoldemGame):
    quick_chat_enabled=False
    def __init__(self):super().__init__();self.names=[];self.revision=-1;self.ready_count=0;self.you_ready=False
    def apply(self,message):
        if message['data']['hand_number']!=self.hand_number:self.recap_open=False;self.recap_page=0
        self.revision=message['revision'];self.names=message['names']
        self.ready_count=message.get('ready_count',0);self.you_ready=message.get('you_ready',False)
        for key,value in message['data'].items():setattr(self,key,value)
        # Seat keys back to numbers for the shared recap and engine helpers (the message is not changed).
        if isinstance(self.last_pot_awards,list):
            self.last_pot_awards=[{**pot,'payouts':int_keys(pot['payouts'])} if isinstance(pot,dict) and 'payouts' in pot else pot for pot in self.last_pot_awards]
        self.last_refunds=int_keys(getattr(self,'last_refunds',{}))
    def get_table_player_name(self,index):return self.names[index] if 0<=index<len(self.names) else 'Player'
    def get_hand_history_lines(self):
        lines=[f'Hand {self.hand_number}: {self.current_stage.title()}',f'Blinds ${self.small_blind} / ${self.big_blind}']
        for name,action in zip(self.names,[self.player_action_text,*self.npc_action_texts]):
            if action:lines.append(f'{name}: {action}')
        return lines
