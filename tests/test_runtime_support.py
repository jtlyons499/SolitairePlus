import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import runtime_support as runtime

class RuntimeTests(unittest.TestCase):
    def test_source_saves_remain_in_project(self):
        with patch.object(runtime.sys,'frozen',False,create=True):
            self.assertEqual(runtime.save_directory(),runtime.ROOT/'saves')

    def test_packaged_saves_migrate_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);install=root/'install';legacy=install/'saves';legacy.mkdir(parents=True)
            (legacy/'profile_1.json').write_text('{"old":true}')
            with patch.object(runtime.sys,'frozen',True,create=True),patch.object(runtime.sys,'executable',str(install/'game.exe')),patch.dict(runtime.os.environ,{'LOCALAPPDATA':str(root/'user')}):
                target=runtime.save_directory()
                self.assertEqual((target/'profile_1.json').read_text(),'{"old":true}')
                (target/'profile_1.json').write_text('{"new":true}')
                runtime.save_directory()
                self.assertEqual((target/'profile_1.json').read_text(),'{"new":true}')
                self.assertTrue((legacy/'profile_1.json').exists())
