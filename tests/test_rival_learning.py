"""Rival memories survive saves, track identities, and never transfer unwitnessed facts."""
import ast
import copy
import json
import tempfile
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch
from poker_learning import new_learning, normalize_learning
from poker_strategy import PokerTableReads
from texas_holdem import TexasHoldemGame
from five_card_draw import FiveCardDrawGame
from seven_card_stud import SevenCardStudGame
from npc_personality import npc_identity
import profile as profiles


def npc(identity):
    return {'id': identity, 'name': identity, 'skill_tier': 'elite'}


def witness(game, count=20):
    for n in range(count):
        game.log_hand_event('bet', 'You bet', actor_index=0, amount=50)
        game.log_hand_event('fold', 'Other folds', actor_index=2)


class LearningTests(unittest.TestCase):
    def test_all_three_formats_restore_reads_for_same_identity_after_seat_change(self):
        for cls in (TexasHoldemGame, FiveCardDrawGame, SevenCardStudGame):
            store=new_learning();game=cls();game.learning_store=store
            game.start_session([npc('rival'),npc('other')],1000,10)
            witness(game)
            context=game.build_npc_ai_context(0,strength=.5)
            before=next(r for r in context['opponent_reads'] if r['seat']==0)
            self.assertEqual(before['decisions'],20)
            # JSON round trip simulates a saved profile; the observer moved seats.
            game.learning_store=json.loads(json.dumps(store))
            game.start_session([npc('other'),npc('rival')],1000,10)
            context=game.build_npc_ai_context(1,strength=.5)
            after=next(r for r in context['opponent_reads'] if r['seat']==0)
            self.assertEqual(after['decisions'],20)
            self.assertEqual(after['aggression'],before['aggression'])
            self.assertEqual(after['hand_actions'],[])
            self.assertIsNone(after['draw_count'])

    def test_new_rival_does_not_inherit_another_observers_learning(self):
        store=new_learning();game=TexasHoldemGame();game.learning_store=store
        game.start_session([npc('old'),npc('other')],1000,10);witness(game)
        game.start_session([npc('new'),npc('old')],1000,10)
        for seat,expected in ((0,0),(1,20)):
            context=game.build_npc_ai_context(seat,strength=.5)
            self.assertEqual(next(r for r in context['opponent_reads'] if r['seat']==0)['decisions'],expected)
        witness(game,1)
        self.assertEqual(next(r for r in game.build_npc_ai_context(0,strength=.5)['opponent_reads'] if r['seat']==0)['decisions'],1)

    def test_games_profiles_and_free_tables_are_isolated(self):
        store=new_learning();g=TexasHoldemGame();g.learning_store=store
        g.start_session([npc('rival'),npc('other')],1000,10);witness(g)
        before=copy.deepcopy(store)
        g.learning_store=None;g.start_session([npc('rival'),npc('other')],1000,10);witness(g)
        self.assertEqual(store,before)
        for cls in (FiveCardDrawGame,SevenCardStudGame):
            other=cls();other.learning_store=store;other.start_session([npc('rival'),npc('other')],1000,10)
            read=next(r for r in other.build_npc_ai_context(0,strength=.5)['opponent_reads'] if r['seat']==0)
            self.assertEqual(read['decisions'],0)
        g.learning_store=new_learning();g.start_session([npc('rival'),npc('other')],1000,10)
        self.assertEqual(next(r for r in g.build_npc_ai_context(0,strength=.5)['opponent_reads'] if r['seat']==0)['decisions'],0)

    def test_only_revealed_bluffs_persist_and_histories_are_bounded(self):
        store=new_learning();reads=PokerTableReads();reads.bind_learning(store,'texas_holdem',{0:'player',1:'rival'})
        for hand in range(120):
            reads.observe('bet',0,hand_number=hand,stage='river',amount=10,pot=30)
            reads.observe('player_hand',0,hand_number=hand,stage='river',hand_name='High Card')
        self.assertEqual(reads.snapshot(0,observer='rival')['reveal_confidence'],0)
        reads.observe('showdown_hand',0,hand_number=119,stage='river',hand_name='High Card')
        restored=PokerTableReads();restored.bind_learning(normalize_learning(store),'texas_holdem',{0:'player',1:'rival'})
        result=restored.snapshot(0,observer='rival')
        self.assertEqual(result['decisions'],96)
        self.assertGreater(result['reveal_confidence'],0)
        self.assertEqual(result['hand_actions'],[])

    def test_saved_slots_migrate_and_preserve_separate_memories(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(profiles,'SAVE_FOLDER',directory):
            for slot in (1,2):
                data=profiles.make_default_profile();reads=PokerTableReads()
                reads.bind_learning(data['poker_learning'],'texas_holdem',{0:'player',1:'rival'})
                for n in range(slot):reads.observe('check',0,hand_number=n,stage='flop')
                profiles.save_profile(data,slot)
            for slot in (1,2):
                loaded=profiles.load_profile(slot)
                self.assertEqual(len(loaded['poker_learning']['games']['texas_holdem']['rival']['player']['history']),slot)
            old=profiles.make_default_profile();old.pop('poker_learning')
            Path(directory,'profile_3.json').write_text(json.dumps(old))
            self.assertEqual(profiles.load_profile(3)['poker_learning'],new_learning())

    def test_busted_rival_stops_collecting_observations(self):
        store=new_learning();game=TexasHoldemGame();game.learning_store=store
        game.start_session([npc('departed'),npc('remaining')],1000,10)
        witness(game,1)
        game.npc_busted[0]=True
        witness(game,3)
        records=store['games']['texas_holdem']
        self.assertEqual(len(records['departed']['player']['history']),1)
        self.assertEqual(len(records['remaining']['player']['history']),4)

    def test_actual_main_profile_and_session_bindings(self):
        tree=ast.parse(Path('main.py').read_text())
        functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        for key,cls in (('texas_holdem',TexasHoldemGame),('five_card_draw',FiveCardDrawGame),('seven_card_stud',SevenCardStudGame)):
            function=functions['start_'+key+'_session']
            binding=next(n for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='learning_store' for t in n.targets))
            program=compile(ast.Module(body=[binding],type_ignores=[]),'production learning binding','exec')
            bank=new_learning();game=cls()
            env={key+'_game':game,'current_game_mode':'career','career_poker_learning':bank}
            exec(program,env);self.assertIs(game.learning_store,bank)
            env['current_game_mode']='free';exec(program,env);self.assertIsNone(game.learning_store)
        # Execute the production profile field handling. Loading an old second
        # profile must discard the first profile's learned observations.
        bank=new_learning();reads=PokerTableReads();reads.bind_learning(bank,'texas_holdem',{0:'player',1:'rival'})
        reads.observe('bet',0,hand_number=1,stage='river',amount=50,pot=100)
        function=functions['build_profile_save_data']
        save_nodes=[n for n in function.body if isinstance(n,ast.ImportFrom) and n.module=='poker_learning']
        save_nodes += [n for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.slice,ast.Constant) and t.slice.value=='poker_learning' for t in n.targets)]
        env={'profile_data':{},'career_poker_learning':bank}
        exec(compile(ast.Module(body=save_nodes,type_ignores=[]),'actual profile save field','exec'),env)
        self.assertEqual(env['profile_data']['poker_learning'],bank)
        self.assertIsNot(env['profile_data']['poker_learning'],bank)
        apply_nodes=[n for n in functions['apply_profile_save_data'].body
                     if (isinstance(n,ast.Global) and 'career_poker_learning' in n.names)
                     or (isinstance(n,ast.ImportFrom) and n.module=='poker_learning')
                     or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='career_poker_learning' for t in n.targets))]
        self.assertEqual(len(apply_nodes),3)
        env['data']={'poker_learning':bank}
        program=compile(ast.Module(body=apply_nodes,type_ignores=[]),'actual profile load field','exec')
        exec(program,env);self.assertEqual(env['career_poker_learning'],bank)
        env['data']={};exec(program,env);self.assertEqual(env['career_poker_learning'],new_learning())

    def test_malformed_memory_is_sanitized(self):
        source={'games':{'texas_holdem':{'rival':{'player':{'history':[[[],{},False,[]],['bet','river',True,float('nan')],['call','river',True,.3]],'reveals':[1,False]}}}}}
        cleaned=normalize_learning(source)
        record=cleaned['games']['texas_holdem']['rival']['player']
        self.assertEqual(record['history'],[['call','river',True,.3]])
        self.assertEqual(record['reveals'],[False])
