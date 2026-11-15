"""Real pot resolution, odd chips, modal controls and production timer gating.

B86 review: F5 (Hold'em's collapsed showdown banner shows the recap's 'You received', refunds
included), F6 (Blind Man's Bluff plays the win sound only for a won or tied hand) and F7 (the
recap lists returned uncalled chips under their own heading; on screen every indented line keeps
its indent and a heading never ends a page).
"""
from tests.support import locate
import ast
import random
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock
import pygame
from solitaireplus.games.poker.holdem import TexasHoldemGame
from solitaireplus.games.poker.recap import (recap_lines, recap_display_lines, recap_pages, draw_recap,
                                             get_recap_action, handle_recap_action, CLOSE, NEXT, ROWS)
from solitaireplus.profile.achievements import make_default_achievement_state, record_event
from solitaireplus.games.poker.blind_mans_bluff import BlindMansBluffGame
from solitaireplus.games.poker.bluff_presentation import effects_for, draw_bluff_effects, update_bluff_presentation


def card(rank,suit):return {'rank':rank,'suit':suit}


def showdown_game(split=False):
    g=TexasHoldemGame();g.start_session([{'id':'a','name':'Alex'},{'id':'b','name':'Blake'}],1000,10);g.start_hand()
    g.community_cards=[card('2','Clubs'),card('3','Diamonds'),card('4','Hearts'),card('8','Spades'),card('9','Clubs')]
    if split:
        g.player_hand=[card('A','Spades'),card('K','Diamonds')]
        g.npc_hands=[[card('A','Hearts'),card('K','Clubs')],[card('Q','Hearts'),card('J','Spades')]]
        g.player_hand_contribution=5;g.npc_hand_contributions=[5,5];g.pot=15
    else:
        g.player_hand=[card('A','Spades'),card('A','Diamonds')]
        g.npc_hands=[[card('K','Hearts'),card('K','Clubs')],[card('Q','Hearts'),card('Q','Spades')]]
        g.player_hand_contribution=100;g.npc_hand_contributions=[200,200];g.pot=500
    g.player_stack=1000-g.player_hand_contribution
    g.npc_stacks=[1000-x for x in g.npc_hand_contributions]
    g.player_folded=False;g.npc_folded=[False,False];g.player_busted=False;g.npc_busted=[False,False]
    g.current_stage='river';g.showdown()
    return g


class RecapTests(unittest.TestCase):
    def test_actual_main_and_side_pots_show_winning_hands_and_net(self):
        g=showdown_game();lines=recap_lines(g)
        self.assertFalse(g.recap_open)
        self.assertEqual([x['amount'] for x in g.last_pot_awards],[300,200])
        self.assertTrue(any('Main pot: $300' in x and 'Aces' in x for x in lines))
        self.assertTrue(any('Side pot 1: $200' in x and 'Kings' in x for x in lines))
        self.assertIn('You received: $300',lines)
        self.assertIn('Your net for this hand: +$200',lines)
        self.assertEqual(g.player_stack+sum(g.npc_stacks),3000)

    def test_split_odd_chip_is_assigned_to_exact_winner(self):
        # B38: the odd chip goes to the first tied winner left of the dealer. You deal hand 1
        # (seat 0), so Alex (seat 1) takes it and the dealer comes last.
        g=showdown_game(True);lines=recap_lines(g)
        self.assertFalse(g.recap_open)
        self.assertEqual(g.dealer_index,0)
        self.assertIn('    Alex receives $8 (odd chip included)',lines)
        self.assertIn('    You receive $7',lines)
        self.assertIn('You received: $7',lines)
        self.assertIn('Your net for this hand: +$2',lines)

    @staticmethod
    def uncalled_game():
        # You bet 300 and only Alex's 100 was called: the 200 nobody matched comes back.
        g=TexasHoldemGame();g.start_session([{'id':'a','name':'Alex'},{'id':'b','name':'Blake'}],1000,10);g.start_hand()
        g.community_cards=[card('2','Clubs'),card('3','Diamonds'),card('4','Hearts'),card('8','Spades'),card('9','Clubs')]
        g.player_hand=[card('K','Spades'),card('K','Diamonds')]
        g.npc_hands=[[card('A','Hearts'),card('A','Clubs')],[card('Q','Hearts'),card('J','Spades')]]
        g.player_hand_contribution=300;g.npc_hand_contributions=[100,20];g.pot=420
        g.player_stack=700;g.npc_stacks=[900,980]
        g.player_folded=False;g.npc_folded=[False,True];g.player_busted=False;g.npc_busted=[False,False]
        g.current_stage='river';g.showdown()
        return g

    def test_uncalled_chips_are_listed_and_counted_in_your_net(self):
        g=self.uncalled_game();lines=recap_lines(g)
        self.assertEqual(g.winner_indexes,[1])
        self.assertEqual(g.last_refunds,{0:200})
        self.assertEqual([x['amount'] for x in g.last_pot_awards],[220])
        self.assertIn('    Alex receives $220',lines)
        self.assertIn('    Uncalled $200 returned to you',lines)
        self.assertIn('You received: $200',lines)
        self.assertIn('Your hand contribution: $300',lines)
        self.assertIn('Your net for this hand: −$100',lines)
        self.assertEqual(g.player_stack,900)
        self.assertEqual(g.player_stack+sum(g.npc_stacks),3000)

    def test_returned_chips_have_their_own_heading(self):
        # F7: the refund lines used to follow the last pot's Eligible line at the same indent.
        lines=recap_lines(self.uncalled_game())
        self.assertTrue(lines[0].startswith('Main pot: $220'))
        self.assertEqual(lines[1:5],['    Alex receives $220','    Eligible: You, Alex',
                                     'Returned (uncalled):','    Uncalled $200 returned to you'])
        # No heading when nothing came back.
        self.assertNotIn('Returned (uncalled):',recap_lines(showdown_game()))

    def test_the_screen_rows_keep_the_indent_under_each_heading(self):
        # F7 review: the rows drawn on the Payout details screen dropped every indent.
        pygame.font.init()
        rows=recap_display_lines(self.uncalled_game())
        self.assertEqual(rows[1:5],['    Alex receives $220','    Eligible: You, Alex',
                                    'Returned (uncalled):','    Uncalled $200 returned to you'])
        # A wrapped indented line keeps its indent on every row and still fits 800 px.
        g=self.uncalled_game();g.get_table_player_name=lambda seat:'You' if seat==0 else 'Alex '*30
        rows=recap_display_lines(g);font=pygame.font.Font(None,32)
        eligible=[row for row in rows if 'Alex Alex' in row]
        self.assertGreater(len(eligible),2)
        self.assertTrue(all(row.startswith('    ') for row in eligible),eligible)
        self.assertTrue(all(font.size(row)[0]<=800 for row in rows))

    def test_a_heading_never_ends_a_recap_page(self):
        # F7 review: two split pots and a refund put 'Returned (uncalled):' last on page 1
        # and its line first on page 2, at every Hold'em-family table.
        from tests.support.poker_variants import ADAPTERS_BY_KEY
        pygame.font.init()
        for key in ('texas_holdem','five_card_draw','seven_card_stud'):
            with self.subTest(key):
                adapter=ADAPTERS_BY_KEY[key];g=adapter.new_game(random.Random(1))
                adapter.force_showdown(g,[100,80,30,0,0],[True,True,True,False,False],[14,14,9,2,2],0)
                pages=recap_pages(g)
                self.assertEqual(len(pages),2)
                self.assertTrue(all(len(page)<=ROWS for page in pages))
                self.assertEqual(pages[0][-1],'    Eligible: You, '+g.get_table_player_name(1))
                self.assertEqual(pages[1][:2],['Returned (uncalled):','    Uncalled $20 returned to you'])
                self.assertEqual([row for page in pages for row in page],recap_display_lines(g))
                # Next and Previous walk these pages.
                g.recap_open,g.recap_page=True,0
                for _ in range(3):handle_recap_action(g,'recap_next')
                self.assertEqual(g.recap_page,1)

    def test_collapsed_showdown_banner_agrees_with_the_recap(self):
        # F5: the banner's 'You received' summed only pot shares, so a refund-only hand showed $0.
        from solitaireplus.games.poker import holdem_ui
        g=self.uncalled_game();rendered=[]

        class WideFont:
            # Every word is wider than the banner, so the result needs more than three rows
            # and the banner collapses to its summary.
            def size(self,text):return (1000,32)
            def render(self,text,*args):rendered.append(text);return pygame.Surface((10,10))

        with mock.patch.object(holdem_ui.ui_text,'get_font',lambda *a,**k:WideFont()):
            holdem_ui.draw_holdem_showdown_banner(pygame.Surface((1366,768)),g)
        self.assertIn('You received: $200',recap_lines(g))
        self.assertEqual(rendered[0],'You received $200 • 1 pot(s) resolved')

    def test_bluff_win_sound_only_for_a_won_hand(self):
        # F6: a payout that is only the human's own uncalled chips is not a win, as at the
        # Hold'em tables: it sounds like any other payout.
        from tests.support.poker_variants import ADAPTERS_BY_KEY
        adapter=ADAPTERS_BY_KEY['blind_mans_bluff']
        for ranks,expected in (([2,14,9,9],False),([14,2,9,9],True)):
            with self.subTest(human_wins=expected):
                game=adapter.new_game(random.Random(4))
                adapter.force_showdown(game,[300,100,0,0],[True,True,False,False],ranks,3)
                sounds=[];update_bluff_presentation(game,sounds.append,100)
                self.assertEqual('poker_hand_win' in sounds,expected,sounds)
                self.assertIn('poker_chips_1' if not expected else 'poker_hand_win',sounds)

    def test_modal_blocks_underlying_actions_and_paginates(self):
        g=showdown_game();g.last_pot_awards *= 2
        handle_recap_action(g,"recap_open")
        self.assertEqual(get_recap_action((900,730),g),'recap_block')
        self.assertEqual(get_recap_action(NEXT.center,g),'recap_next')
        handle_recap_action(g,'recap_next');self.assertEqual(g.recap_page,1)
        handle_recap_action(g,'recap_close');self.assertFalse(g.recap_open)
        self.assertEqual(get_recap_action((900,730),g),None)
        handle_recap_action(g,'recap_open');self.assertEqual(g.recap_page,0)

    def test_production_timers_pause_and_restart_after_review(self):
        branches=[]
        for node in locate.walk():
            if not isinstance(node,ast.If):continue
            condition=ast.unparse(node.test)
            if condition=='getattr(texas_holdem_game, \'recap_open\', False)' and any(isinstance(x,ast.Assign) for x in node.body):
                branches.append(node)
            elif 'state.texas_holdem_next_hand_at == 0' in condition and 'is_holdem_auto_deal_enabled()' in condition:
                branches.append(node)
        self.assertEqual(len(branches),2)
        branches.sort(key=lambda n:n.lineno)
        program=compile(ast.Module(body=branches,type_ignores=[]),'real recap timer gates','exec')
        g=showdown_game();env=dict(texas_holdem_game=g,texas_holdem_next_hand_at=500,texas_holdem_session_end_at=800,
                                 now=10000,is_holdem_auto_deal_enabled=lambda:True,get_holdem_next_hand_delay=lambda:15000)
        locate.namespace(env,branches)
        exec(program,env)
        self.assertEqual((env['texas_holdem_next_hand_at'],env['texas_holdem_session_end_at']),(500,800))
        handle_recap_action(g,'recap_open')
        exec(program,env)
        self.assertEqual((env['texas_holdem_next_hand_at'],env['texas_holdem_session_end_at']),(0,0))
        g.recap_open=False;exec(program,env)
        self.assertEqual(env['texas_holdem_next_hand_at'],25000)

    def test_table_clear_unlocks_once_and_old_stats_survive(self):
        state=make_default_achievement_state();state['stats']['holdem_hand_wins']=8
        state,unlocked=record_event(state,'poker_table_clear',game='texas_holdem')
        self.assertIn('table_clear',[x['id'] for x in unlocked])
        state,again=record_event(state,'poker_table_clear',game='five_card_draw')
        self.assertNotIn('table_clear',[x['id'] for x in again])
        self.assertEqual(state['stats']['holdem_hand_wins'],8)

    def test_actual_main_table_clear_hook_does_not_repeat_each_frame(self):
        function=locate.function_node('process_texas_holdem_showdown')
        g=TexasHoldemGame();g.start_session([{'name':'Rival'}],1000,10)
        g.hand_number=1;g.hand_complete=True;g.current_stage='showdown';g.npc_busted=[True];g.player_busted=False;g.winner_indexes=[]
        events=[]
        no_op=lambda *a,**k:None
        env=dict(texas_holdem_game=g,texas_holdem_last_processed_showdown_hand=0,texas_holdem_table_sweep_rewarded=False,
                 texas_holdem_next_hand_at=100,texas_holdem_session_end_at=0,current_game_mode='career',career_event_has_activity=False,
                 TEXAS_HOLDEM_TABLE_SWEEP_RATING_BONUS=100,TEXAS_HOLDEM_SESSION_END_DELAY=15000,
                 audio=SimpleNamespace(play_sound=no_op),pygame=SimpleNamespace(time=SimpleNamespace(get_ticks=lambda:50)),
                 record_poker_showdown=no_op,generate_showdown_chat=lambda game:[],post_texas_holdem_chat=no_op,
                 award_fans_for_rating_win=lambda *a:0,process_achievement_event=lambda name,**data:events.append(name))
        locate.namespace(env,[function])
        exec(compile(ast.Module(body=[function],type_ignores=[]),'actual table clear hook','exec'),env)
        env['process_texas_holdem_showdown']();env['process_texas_holdem_showdown']()
        self.assertEqual(events,['poker_table_clear'])

    def test_recap_render_and_chip_events_do_not_change_rules_or_repeat_sfx(self):
        pygame.init()
        try:
            pygame.display.set_mode((1366,768));surface=pygame.Surface((1366,768))
            g=showdown_game();draw_recap(surface,None,g)
            pygame.image.save(surface,'/workspace/scratch/8857fb6c22d0/holdem_recap_preview.png')
            bluff=BlindMansBluffGame();bluff.start_session([{'name':'Rival'}],1000)
            state=(bluff.player_stack,list(bluff.npc_stacks),bluff.pot,list(bluff.cards))
            sounds=[];update_bluff_presentation(bluff,sounds.append,100)
            fx=effects_for(bluff);self.assertTrue(fx.motions)
            first=list(sounds);update_bluff_presentation(bluff,sounds.append,200)
            self.assertEqual(sounds,first)
            draw_bluff_effects(surface,bluff,400)
            self.assertEqual((bluff.player_stack,list(bluff.npc_stacks),bluff.pot,list(bluff.cards)),state)
            update_bluff_presentation(bluff,sounds.append,1200);self.assertEqual(fx.motions,[])
        finally:pygame.quit()


class RecapPageBreakTests(unittest.TestCase):
    """B86 polish P8: a page that ends inside a pot (or the 'Returned (uncalled):' block)
    starts the next page with that heading again, marked '(continued)'."""

    TABLES = ('texas_holdem', 'five_card_draw', 'seven_card_stud')

    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def game(self, key, contributions, live, ranks):
        from tests.support.poker_variants import ADAPTERS_BY_KEY
        adapter = ADAPTERS_BY_KEY[key]
        return adapter.force_showdown(adapter.new_game(random.Random(f'recap-break-{key}')),
                                      contributions, live, ranks, 0)

    def check_pages(self, pages, lines):
        """Every recap row appears once, in order; the only extra rows are a heading marked
        '(continued)' at the top of a page whose first row belongs under that heading."""
        from solitaireplus.games.poker import recap
        from solitaireplus.ui import text as ui_text
        font = ui_text.get_font(None, 32)
        expected, heading_of, heading = [], [], None
        for index, line in enumerate(lines):
            indented = line.startswith(' ')
            if not indented:
                heading = line if index + 1 < len(lines) and lines[index + 1].startswith(' ') else None
            for row in recap._wrap_recap_line(font, line):
                expected.append(row)
                heading_of.append(heading if indented else None)
        position = 0
        for number, page in enumerate(pages):
            self.assertTrue(0 < len(page) <= ROWS, [len(page) for page in pages])
            rows = list(page)
            if number and heading_of[position] is not None:
                continued = recap._wrap_recap_line(font, recap._continued(heading_of[position]))
                self.assertEqual(rows[:len(continued)], continued)
                rows = rows[len(continued):]
            self.assertEqual(rows, expected[position:position + len(rows)])
            position += len(rows)
        self.assertEqual(position, len(expected))

    def test_a_pot_split_by_a_page_break_repeats_its_heading(self):
        # A five-way tie for the main pot (7 rows) and a two-way side pot: the side pot's
        # heading and first winner end page 1, its second winner starts page 2.
        for key in self.TABLES:
            with self.subTest(key):
                g = self.game(key, [10, 10, 10, 20, 20], [True] * 5, [14] * 5)
                lines = recap_lines(g)
                side = lines[7]
                self.assertTrue(side.startswith('Side pot 1: $20 — '), side)
                pages = recap_pages(g)
                self.assertEqual(pages[0][-2], side)
                self.assertEqual(pages[1][:2], [side + ' (continued)', lines[9]])
                self.check_pages(pages, lines)
                self.assertEqual([row for page in pages for row in page], recap_display_lines(g))

    def test_the_returned_block_split_by_a_page_break_repeats_its_heading(self):
        # Two folded seats over the live ones each get 20 back; the block straddles the break.
        for key in self.TABLES:
            with self.subTest(key):
                g = self.game(key, [10, 10, 20, 40, 40], [True, True, True, False, False], [14, 14, 9, 2, 2])
                lines = recap_lines(g)
                self.assertEqual(lines[7], 'Returned (uncalled):')
                pages = recap_pages(g)
                self.assertEqual(pages[0][-2:], lines[7:9])
                self.assertEqual(pages[1][:2], ['Returned (uncalled) (continued):', lines[9]])
                self.check_pages(pages, lines)

    def test_a_break_between_blocks_repeats_nothing(self):
        # The F7 case: 'Returned (uncalled):' starts page 2 itself, so nothing is repeated.
        from tests.support.poker_variants import ADAPTERS_BY_KEY
        for key in self.TABLES:
            with self.subTest(key):
                adapter = ADAPTERS_BY_KEY[key]
                g = adapter.force_showdown(adapter.new_game(random.Random(1)), [100, 80, 30, 0, 0],
                                           [True, True, True, False, False], [14, 14, 9, 2, 2], 0)
                pages = recap_pages(g)
                self.assertFalse([row for page in pages for row in page if 'continued' in row])
                self.check_pages(pages, recap_lines(g))

    def test_random_recaps_never_start_a_page_inside_a_block(self):
        # Reviewer property (b86_rr/ui_text/recap_property.py), with synthetic recap lines.
        from solitaireplus.games.poker import recap
        words = 'alpha beta gamma delta epsilon zeta theta iota kappa lambda omicron'.split()
        rng = random.Random(7)

        def text(count):
            return ' '.join(rng.choice(words) for _ in range(count))

        for trial in range(1500):
            lines = []
            for _ in range(rng.randint(1, 8)):
                lines.append('Pot: ' + text(rng.choice([2, 4, 12, 25])))
                lines.extend('    ' + text(rng.choice([2, 4, 14, 30])) for _ in range(rng.randint(1, 4)))
            lines.extend('Summary ' + text(rng.choice([2, 20])) for _ in range(rng.randint(0, 3)))
            with mock.patch.object(recap, 'recap_lines', lambda game: list(lines)):
                pages = recap.recap_pages(None)
            with self.subTest(trial=trial):
                self.check_pages(pages, lines)
