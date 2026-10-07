"""Catalog names change without breaking persistent cosmetic IDs."""
import unittest
from pathlib import PurePosixPath
from rating_unlocks import RATING_ART, THRESHOLDS, add_rating_catalogs, unlock_ratings

class CosmeticNameTests(unittest.TestCase):
 def test_all_rating_requirements_and_save_ids_are_preserved(self):
  catalogs=[{}, {}, {}];add_rating_catalogs(*catalogs)
  expected=set()
  for kind,catalog,prefix in zip(('backgrounds','felts','titles'),catalogs,('bg','f','t')):
   for category,thresholds in THRESHOLDS[kind].items():
    for threshold in thresholds:
     key=f'{prefix}_rating_{category}_{threshold}';expected.add(key)
     self.assertEqual(catalog[key]['rating_threshold'],threshold)
     self.assertEqual(catalog[key]['rating_category'],'overall' if category=='global' else category)
     self.assertEqual(PurePosixPath(catalog[key]['path']).parent,PurePosixPath('assets/ui/menu_ui')/kind)
     self.assertEqual(PurePosixPath(catalog[key]['path']).suffix,'.png')
  self.assertEqual(expected,set(RATING_ART));self.assertEqual(len(expected),33)
  unlocked=[set(),set(),set()];unlock_ratings(dict(strategy=3000,poker=3000,casino=3000,overall=3000),catalogs,unlocked)
  self.assertEqual(set.union(*unlocked),expected)
 def test_requested_spelling_and_filename_are_independent(self):
  backgrounds,felts,titles={},{},{};add_rating_catalogs(backgrounds,felts,titles)
  for catalog,key,name,filename in (
   (backgrounds,'bg_rating_strategy_2300','Consideration','bg_consideration.png'),
   (backgrounds,'bg_rating_strategy_1950','Zooming','bg_zoom.png'),
   (backgrounds,'bg_rating_poker_1750','Poker Shapes','bg_poker_shape.png'),
   (felts,'f_rating_casino_1450','Le Greene','f_le_green.png'),
   (felts,'f_rating_strategy_1600','Weak Purp','f_weak_purple.png'),
   (felts,'f_rating_casino_2600','Pink Weezer','f_pink_triangle.png'),
   (titles,'t_rating_global_3000','World Champ','title_world_champion.png'),
   (titles,'t_rating_poker_1300','Poke x2','title_poke_poke.png')):
   self.assertEqual(catalog[key]['name'],name);self.assertEqual(PurePosixPath(catalog[key]['path']).name,filename)
 def test_existing_catalog_entries_are_unchanged(self):
  backgrounds={'bg_default':{'name':'Default','path':'default.png'}};felts={};titles={}
  add_rating_catalogs(backgrounds,felts,titles)
  self.assertEqual(backgrounds['bg_default'],{'name':'Default','path':'default.png'})
