import ast
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pygame
from cosmetic_assets import CosmeticCatalog, SingleDriftCache
import five_o_poker_ui as five

class CustomizationFinishTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  pygame.init();pygame.display.set_mode((1366,768))
 @classmethod
 def tearDownClass(cls):pygame.quit()
 def test_missing_and_invalid_pngs_use_default_but_cannot_be_equipped(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);default=p/'default.png';bad=p/'bad.png';missing=p/'missing.png'
   image=pygame.Surface((8,8));image.fill((30,40,50));pygame.image.save(image,default);bad.write_bytes(b'broken PNG')
   catalog=CosmeticCatalog({'default':{'path':str(default)},'missing':{'path':str(missing)},'bad':{'path':str(bad)}},'default')
   self.assertFalse(catalog.available('missing'));self.assertFalse(catalog.available('bad'))
   self.assertIs(catalog.surfaces['missing'],catalog.surfaces['default'])
   self.assertIs(catalog.surfaces['bad'],catalog.surfaces['default'])
   image.fill((80,90,100));pygame.image.save(image,missing);pygame.image.save(image,bad)
   catalog.refresh(force=True)
   self.assertTrue(catalog.available('missing'));self.assertTrue(catalog.available('bad'))
   self.assertEqual(catalog.surfaces['missing'].get_at((0,0))[:3],(80,90,100))
 def test_surface_dictionary_identity_survives_later_art_installation(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);default=p/'default.png';later=p/'later.png';pygame.image.save(pygame.Surface((8,8)),default)
   catalog=CosmeticCatalog({'default':{'path':str(default)},'later':{'path':str(later)}},'default');bound=catalog.surfaces
   pygame.image.save(pygame.Surface((12,12)),later);catalog.refresh(force=True)
   self.assertIs(bound,catalog.surfaces);self.assertEqual(bound['later'].get_size(),(12,12))
 def test_animation_cache_holds_one_background_and_rebuilds_only_when_needed(self):
  cache=SingleDriftCache();source=pygame.Surface((8,8))
  with patch('cosmetic_assets.pygame.transform.smoothscale',wraps=pygame.transform.smoothscale) as scale:
   first=cache.get('a',source,(16,16));self.assertIs(first,cache.get('a',source,(16,16)))
   second=cache.get('b',source,(16,16));self.assertIs(second,cache.surface);self.assertIsNot(first,second)
   self.assertEqual(scale.call_count,2)
 def test_drawing_and_clicks_share_sorted_catalog_order(self):
  tree=ast.parse(Path('main.py').read_text())
  function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='draw_customize_menu')
  assignment=next(n for n in ast.walk(function) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='asset_ids' for t in n.targets))
  self.assertEqual(ast.unparse(assignment.value),'get_customize_asset_ids()')
  equip=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='equip_customize_item')
  env=dict(refresh_cosmetic_assets=lambda:None,cosmetic_art_available=lambda asset:False,selected_felt='f_default')
  exec(compile(ast.Module(body=[equip],type_ignores=[]),'equip integration','exec'),env)
  env['equip_customize_item']('missing');self.assertEqual(env['selected_felt'],'f_default')
 def test_five_o_controls_clear_all_columns_and_right_edge_is_aligned(self):
  for column in five.FIVE_O_PLAYER_COLUMN_RECTS:
   last=pygame.Rect(column.centerx-five.CARD_SIZE[0]//2,column.y+8+4*five.STACK_OFFSET,*five.CARD_SIZE)
   self.assertGreater(five.ACTION_Y,last.bottom+20)
   self.assertFalse(any(last.colliderect(rect) for rect in five.BET_PRESET_RECTS))
  self.assertEqual(five.FIVE_O_ACTION_RECTS[five.ACTION_BET].right,five.FIVE_O_PLAYER_COLUMN_RECTS[-1].right)
  self.assertLessEqual(five.FIVE_O_NEXT_RECT.bottom,768)
