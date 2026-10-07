import json
import os
import tempfile
import unittest
from unittest.mock import patch
import profile as profiles

class SaveLockTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.folder_patch=patch.object(profiles,'SAVE_FOLDER',self.folder.name)
        self.folder_patch.start()
    def tearDown(self):
        self.folder_patch.stop();self.folder.cleanup()

    def test_temporary_lock_retries(self):
        original=os.replace
        calls=[]
        def replace(src,dst):
            calls.append(dst)
            if len(calls)<3:raise PermissionError('locked')
            return original(src,dst)
        with patch.object(profiles.os,'replace',side_effect=replace),patch.object(profiles.time,'sleep'):
            self.assertTrue(profiles.save_profile(profiles.make_default_profile()))
        self.assertEqual(len(calls),3)
        self.assertEqual(list(profiles.recovery_paths(1)),[])

    def test_persistent_lock_preserves_old_and_loads_recovery(self):
        data=profiles.make_default_profile();data['career']['cash']=10
        profiles.save_profile(data)
        path=os.path.abspath(profiles.get_profile_path(1));original=os.replace
        def replace(src,dst):
            if str(dst)==path:raise PermissionError('locked')
            return original(src,dst)
        data['career']['cash']=250
        with patch.object(profiles.os,'replace',side_effect=replace),patch.object(profiles.time,'sleep'):
            self.assertFalse(profiles.save_profile(data))
        with open(path) as f:self.assertEqual(json.load(f)['career']['cash'],10)
        self.assertEqual(profiles.load_profile()['career']['cash'],250)
        self.assertTrue(profiles.profile_exists(1))
        self.assertTrue(profiles.save_profile(data))
        self.assertFalse(profiles.recovery_paths(1))
        self.assertEqual(profiles.load_profile()['career']['cash'],250)

    def test_recovery_only_slot_can_load_and_delete(self):
        path=os.path.abspath(profiles.get_profile_path(2));original=os.replace
        def replace(src,dst):
            if str(dst)==path:raise PermissionError('locked')
            return original(src,dst)
        with patch.object(profiles.os,'replace',side_effect=replace),patch.object(profiles.time,'sleep'):
            self.assertFalse(profiles.save_profile(profiles.make_default_profile(),2))
        self.assertTrue(profiles.profile_exists(2));self.assertIsNotNone(profiles.load_profile(2))
        profiles.delete_profile(2)
        self.assertFalse(profiles.profile_exists(2))
