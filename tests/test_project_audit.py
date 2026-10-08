import base64
import tempfile
import unittest
from pathlib import Path
from tools.audit_project import scan, png_error

class ProjectAuditTests(unittest.TestCase):
    def test_exclusions_references_dynamic_and_duplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'assets').mkdir();(root/'data').mkdir();(root/'.venv').mkdir();(root/'saves').mkdir()
            (root/'main.py').write_text('import os\na="assets/" + "missing.png"\nb=os.path.join("assets", "present.wav")\nc=f"assets/cards/{rank}.png"\n')
            (root/'.venv'/'dependency.py').write_text('this is invalid python')
            (root/'saves'/'profile_1.json').write_text('{private save contents}')
            (root/'assets'/'present.wav').write_bytes(b'identical')
            (root/'assets'/'copy.wav').write_bytes(b'identical')
            (root/'data'/'catalog.json').write_text('{"art":"assets/not_here.png"}')
            report=scan(root)
            refs={x['path']:x['exists'] for x in report['references']}
            self.assertFalse(refs['assets/missing.png']);self.assertFalse(refs['assets/not_here.png'])
            self.assertTrue(refs['assets/present.wav']);self.assertTrue(report['dynamic_paths'])
            self.assertEqual(len(report['identical_files']),1)
            self.assertFalse(report['file_errors'])
            self.assertFalse(any('.venv' in x['path'] for x in report['inventory']))
            self.assertTrue(any(x['kind']=='save (contents omitted)' for x in report['inventory']))

    def test_png_bad_crc_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'bad.png'
            path.write_bytes(b'\x89PNG\r\n\x1a\n'+b'\x00\x00\x00\x0dIHDR'+b'\0'*13+b'\0'*4)
            self.assertIn('CRC error',png_error(path))

    def test_rating_table_resolved_without_importing_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'rating_unlocks.py').write_text('RATING_ART={"bg_rating_global_1500": ("bg_small_world.png", "Small World")}\nraise RuntimeError("must not execute")\n')
            refs=scan(root)['references']
            self.assertEqual(refs[0]['path'],'assets/ui/menu_ui/backgrounds/bg_small_world.png')
            self.assertFalse(refs[0]['exists'])
