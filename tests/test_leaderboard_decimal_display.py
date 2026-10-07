"""Run actual leaderboard formatting without launching assets."""
import ast
from pathlib import Path
import unittest

class LeaderboardDisplayTests(unittest.TestCase):
    def test_fractional_movements_render_as_signed_whole_points(self):
        tree=ast.parse((Path(__file__).resolve().parents[1]/'main.py').read_text(encoding='utf-8'))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='draw_career_leaderboards')
        loop=next(n for n in ast.walk(function) if isinstance(n,ast.For) and any(isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='rating_change' for t in s.targets) for s in n.body))
        assignment=next(n for n in loop.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='rating_change' for t in n.targets))
        formatting=next(n for n in loop.body if isinstance(n,ast.If) and ast.unparse(n.test)=='rating_change > 0')
        code=compile(ast.Module(body=[assignment,formatting],type_ignores=[]),'leaderboard formatting','exec')
        for value,expected in ((3.950000000000273,'+4'),(-7.949999999999818,'-8'),(1.75,'+2'),(2.0,'+2'),(-2.09,'-2'),(.449999999999818,''),(0,'')):
            with self.subTest(value=value):
                entry={'last_change':value};namespace={'entry':entry};exec(code,namespace)
                self.assertEqual(namespace['change_text'],expected)
                self.assertEqual(entry['last_change'],value)
