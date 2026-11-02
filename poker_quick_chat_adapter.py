"""Compatibility adapter that lets the Hold'em quick-chat logic serve other poker games."""
from __future__ import annotations

from poker_ai import get_poker_skill_factor


class PokerQuickChatAdapter:
    def __init__(self, game, game_id):
        object.__setattr__(self, "game", game)
        object.__setattr__(self, "game_id", str(game_id))

    @property
    def npcs(self):
        value = getattr(self.game, "npcs", None)
        if value:
            return list(value)
        npc = getattr(self.game, "npc", None)
        return [npc] if isinstance(npc, dict) else []

    @property
    def npc_busted(self):
        value = getattr(self.game, "npc_busted", None)
        if isinstance(value, (list, tuple)):
            return list(value)
        stacks = getattr(self.game, "npc_stacks", None)
        if isinstance(stacks, (list, tuple)):
            return [int(stack or 0) <= 0 for stack in stacks[:len(self.npcs)]]
        if len(self.npcs) == 1:
            return [getattr(self.game, "npc_stack", 1) <= 0]
        return [False] * len(self.npcs)

    @property
    def npc_folded(self):
        value = getattr(self.game, "npc_folded", None)
        if isinstance(value, (list, tuple)):
            return list(value)
        folded = getattr(self.game, "folded", None)
        if isinstance(folded, (list, tuple)) and len(folded) >= len(self.npcs) + 1:
            return [bool(flag) for flag in folded[1:1+len(self.npcs)]]
        if len(self.npcs) == 1:
            return [bool(value)]
        return [False] * len(self.npcs)

    @property
    def hand_complete(self):
        return bool(getattr(self.game, "hand_complete", False))

    @property
    def hand_number(self):
        return int(getattr(self.game, "hand_number", 0) or 0)

    @property
    def current_stage(self):
        stage = getattr(self.game, "current_stage", None)
        if stage:
            return str(stage)
        return str(getattr(self.game, "phase", "idle") or "idle")

    @property
    def winner_indexes(self):
        winners = getattr(self.game, "winner_indexes", None)
        if winners is None:
            winners = getattr(self.game, "last_winner_indexes", None)
        if winners is not None:
            try:
                return list(winners)
            except TypeError:
                pass
        if not self.hand_complete:
            return []
        player = int(getattr(self.game, "player_column_wins", 0) or 0)
        npc = int(getattr(self.game, "npc_column_wins", 0) or 0)
        if player > npc:
            return [0]
        if npc > player:
            return [1]
        return [0, 1]

    @property
    def quick_chat_state(self):
        return getattr(self.game, "quick_chat_state", None)

    @quick_chat_state.setter
    def quick_chat_state(self, value):
        setattr(self.game, "quick_chat_state", value)

    def sync(self):
        """Create lightweight event ticks for poker variants without hand history."""
        if callable(getattr(self.game, "get_hand_history_events", None)):
            return
        signature = (
            self.hand_number,
            self.current_stage,
            getattr(self.game, "current_actor", None),
            getattr(self.game, "bet_state", None),
            int(getattr(self.game, "current_bet", 0) or 0),
            int(getattr(self.game, "pot", 0) or 0),
            int(getattr(self.game, "player_stack", 0) or 0),
            int(getattr(self.game, "npc_stack", 0) or 0),
            tuple(int(v or 0) for v in (getattr(self.game, "npc_stacks", ()) or ())),
            tuple(int(v or 0) for v in (getattr(self.game, "round_bets", ()) or ())),
            getattr(self.game, "placement_round", None),
        )
        previous = getattr(self.game, "_quick_chat_event_signature", None)
        if signature != previous:
            setattr(self.game, "_quick_chat_event_signature", signature)
            setattr(self.game, "_quick_chat_event_counter", int(getattr(self.game, "_quick_chat_event_counter", 0)) + 1)

    def get_hand_history_events(self):
        getter = getattr(self.game, "get_hand_history_events", None)
        if callable(getter):
            return getter()
        self.sync()
        return range(max(0, int(getattr(self.game, "_quick_chat_event_counter", 0))))

    def get_table_player_name(self, player_index):
        getter = getattr(self.game, "get_table_player_name", None)
        if callable(getter):
            return getter(player_index)
        if player_index == 0:
            return "You"
        npc_index = player_index - 1
        if 0 <= npc_index < len(self.npcs):
            return str(self.npcs[npc_index].get("name", "Opponent"))
        return "Opponent"

    def get_npc_skill_factor(self, npc_index):
        getter = getattr(self.game, "get_npc_skill_factor", None)
        if callable(getter):
            return getter(npc_index)
        if 0 <= npc_index < len(self.npcs):
            return get_poker_skill_factor(self.npcs[npc_index], self.game_id)
        return 0.55


def adapt_quick_chat_game(game, game_id):
    return PokerQuickChatAdapter(game, game_id)
