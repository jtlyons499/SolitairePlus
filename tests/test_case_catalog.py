"""Editable catalogs reject broken odds/pools and drive rewards and shop pages."""
import copy,json,random,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pygame
import case_opening as core
from case_opening_ui import CaseOpeningScreen

class CatalogTests(unittest.TestCase):
 def load(self,data):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'catalog.json';p.write_text(json.dumps(data));return core.load_catalog(p)
 def data(self):return {'cases':copy.deepcopy(core.CASES),'items':copy.deepcopy(core.ITEMS)}
 def test_new_case_and_custom_pool(self):
  data=self.data();data['cases']['duck_box']={'name':'Duck Box','minimum':10,'fraction':0,'weights':{'junk':100},'pool':['cold_pizza']}
  cases,items=self.load(data)
  with patch.dict(core.CASES,cases,clear=True):
   for _ in range(20):self.assertEqual(core.choose_item('duck_box',random.Random())['id'],'cold_pizza')
 def test_bad_odds_and_pools(self):
  for edit in ('odds','unknown','empty'):
   d=self.data()
   if edit=='odds':d['cases']['street']['weights']['junk']=54
   elif edit=='unknown':d['cases']['street']['pool']=['missing']
   else:d['cases']['street']['pool']=['cold_pizza']
   with self.assertRaises(ValueError):self.load(d)
 def test_custom_fixed_reward(self):
  item=dict(core.ITEMS['cash_pouch'],cash_amount=1234)
  with patch('case_opening.choose_item',return_value=item):
   receipt,wallet=core.purchase(core.new_case_state(),'street',5000)
  self.assertEqual(receipt['amount'],1234);self.assertEqual(wallet,5000-receipt['cost']+1234)
 def test_fourth_case_on_second_shop_page(self):
  pygame.init();pygame.display.set_mode((1366,768))
  cases=copy.deepcopy(core.CASES);cases['extra']=dict(cases['street'],name='Extra')
  with patch.dict(core.CASES,cases,clear=True):
   screen=CaseOpeningScreen();screen.enter(core.new_case_state(),5000,lambda key:None)
   out=pygame.Surface((1366,768));screen.draw(out)
   self.assertEqual(len([a for _,a in screen.buttons if a.startswith('open:')]),3)
   screen.page=1;screen.draw(out)
   self.assertEqual([a for _,a in screen.buttons if a.startswith('open:')],['open:extra'])
  pygame.quit()
