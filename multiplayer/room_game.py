"""Room Hold'em engines and the NPC roster: TwoHumanGame, RoomGame and load_roster()."""
import json
from solitaireplus.app import paths
from solitaireplus.games.poker.holdem import TexasHoldemGame

def load_roster():
    roster=json.loads(paths.data('npcs.json').read_text(encoding='utf-8'))
    if not isinstance(roster,list) or len(roster)<3:raise ValueError('data/npcs.json must contain at least three NPCs')
    return roster

class TwoHumanGame(TexasHoldemGame):
    """The shared engine with the network-table options turned on."""
    allow_network_spectator=True
    finish_hand_after_player_fold=False
    quick_chat_enabled=False

class RoomGame(TwoHumanGame):
    """Exclude resting seats without moving, spending or removing their chips."""
    def __init__(self):
        super().__init__();self.sitting_out=set();self.starting_network_hand=False
    def get_live_player_indexes(self):
        return [seat for seat in super().get_live_player_indexes() if seat not in self.sitting_out]
    def refresh_busted_state(self):
        newly_busted=super().refresh_busted_state()
        if self.starting_network_hand:
            if 0 in self.sitting_out:self.player_busted=True
            for seat in self.sitting_out:
                if seat:self.npc_busted[seat-1]=True
        return newly_busted
    def start_hand(self):
        self.starting_network_hand=True
        try:result=super().start_hand()
        finally:self.starting_network_hand=False
        # Undo only the resting seats' busted flags. A seat dealt in stays in the hand even when
        # posting a blind put it all in (0 chips), as in the shared engine.
        dealt=set(self.hand_seat_indexes) if result else set()
        self.player_busted=self.player_stack<=0 and 0 not in dealt
        self.npc_busted=[stack<=0 and seat not in dealt for seat,stack in enumerate(self.npc_stacks,1)]
        if result:
            if 0 in self.sitting_out:self.player_folded=True;self.player_action_text='Sitting out'
            for seat in self.sitting_out:
                if seat:self.npc_folded[seat-1]=True;self.npc_action_texts[seat-1]='Sitting out'
        return result
