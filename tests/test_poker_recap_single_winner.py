"""B43: a single-winner (everyone else folded) pot lists its eligible players in the recap."""
import unittest

from solitaireplus.games.poker.holdem import TexasHoldemGame
from solitaireplus.games.poker.recap import recap_lines


def card(rank, suit):
    return {'rank': rank, 'suit': suit}


def folded_out_game(winner_index):
    """Real engine: two opponents, everyone but winner_index folds at the river."""
    g = TexasHoldemGame()
    g.start_session([{'id': 'a', 'name': 'Alex'}, {'id': 'b', 'name': 'Blake'}], 1000, 10)
    g.start_hand()
    g.community_cards = [card('2', 'Clubs'), card('3', 'Diamonds'), card('4', 'Hearts'),
                         card('8', 'Spades'), card('9', 'Clubs')]
    g.player_hand_contribution = 50
    g.npc_hand_contributions = [50, 50]
    g.pot = 150
    g.player_stack = 950
    g.npc_stacks = [950, 950]
    g.player_busted = False
    g.npc_busted = [False, False]
    g.player_folded = winner_index != 0
    g.npc_folded = [winner_index != 1, winner_index != 2]
    g.current_stage = 'river'
    g.showdown()
    return g


class SingleWinnerRecapEligibleTests(unittest.TestCase):
    def test_human_wins_uncontested_pot_recap_lists_eligible(self):
        g = folded_out_game(0)
        self.assertEqual(len(g.last_pot_awards), 1)
        award = g.last_pot_awards[0]
        self.assertEqual(award['winners'], [0])
        self.assertEqual(award.get('eligible'), [0])
        lines = recap_lines(g)
        self.assertIn('    Eligible: You', lines)
        self.assertNotIn('    Eligible: ', lines)

    def test_npc_wins_uncontested_pot_recap_lists_eligible(self):
        g = folded_out_game(2)
        award = g.last_pot_awards[0]
        self.assertEqual(award['winners'], [2])
        self.assertEqual(award.get('eligible'), [2])
        lines = recap_lines(g)
        self.assertIn('    Eligible: Blake', lines)
        self.assertNotIn('    Eligible: ', lines)
        # Totals are unchanged by the recap data fix.
        self.assertEqual(g.player_stack + sum(g.npc_stacks), 3000)


if __name__ == '__main__':
    unittest.main()
