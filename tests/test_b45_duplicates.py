"""B45: names that were defined or assigned twice by the old main.py start-up code.

The three Hold'em sound helpers were defined twice, ``STATE_CAREER_NEWS`` was assigned twice and a
handful of shared start-up values (``blackjack_dealer_npc``, ``play_background_image``,
``profile_switch_rect`` and the Career hub button rects) were assigned twice. Only one copy of
each is kept, and it is the one that was in effect (the value the game actually ran with).

These checks read the source with ``ast`` (main.py and solitaireplus/**, as tests/support/locate
does), so they do not depend on which module a name lives in today.
"""
import ast
import types
import unittest

from tests.support import locate

SOUND_FUNCTIONS = (
    "play_texas_holdem_npc_action_sound",
    "play_texas_holdem_new_hand_sound",
    "play_texas_holdem_street_sound",
)

# The definitions Python used: the later copy in the file (comments are not part of the AST).
KEPT_SOUND_SOURCE = '''
def play_texas_holdem_npc_action_sound(npc_index):
    if not (0 <= npc_index < len(texas_holdem_game.npc_action_texts)):
        return
    action_text = texas_holdem_game.npc_action_texts[npc_index].strip().lower()
    if action_text.startswith("checked"):
        sounds.audio.play_sound("poker_check")
        return
    if action_text.startswith(("called", "bet", "raised")):
        play_texas_holdem_chip_sound()


def play_texas_holdem_new_hand_sound():
    sounds.audio.play_sound("card_draw")


def play_texas_holdem_street_sound():
    sounds.audio.play_sound("card_draw")
'''

# The Rect each name held once start-up finished (the later assignment in the old main.py).
KEPT_RECTS = {
    "profile_switch_rect": (630, 650, 240, 48),
    "career_jobs_rect": (740, 703, 390, 26),
    "career_real_estate_rect": (335, 703, 390, 26),
    "career_leaderboards_rect": (1175, 285, 180, 45),
    "career_news_rect": (1175, 645, 180, 45),
    "career_back_rect": (1175, 710, 180, 45),
}


def _module_level(nodes):
    """Statements and expressions that run at import time (not inside def/class/lambda bodies)."""
    for node in nodes:
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield from _module_level(ast.iter_child_nodes(node))


def _bound_name(target):
    """``x`` for ``x = ...`` and ``state.x = ...``; None for anything else."""
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "state":
        return target.attr
    return None


def module_level_bindings(name):
    """[(file, statement)] for every import-time def/assignment of ``name`` (or ``state.name``)."""
    found = []
    for path, tree in locate.trees():
        for node in _module_level(tree.body):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == name:
                    found.append((path, node))
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(_bound_name(t) == name for t in targets):
                    found.append((path, node))
    return found


def _where(bindings):
    return [f"{path.relative_to(locate.ROOT)}:{node.lineno}" for path, node in bindings]


class DuplicateDefinitionTests(unittest.TestCase):
    def single_binding(self, name):
        bindings = module_level_bindings(name)
        self.assertEqual(len(bindings), 1, f"{name} is bound at import time in {_where(bindings)}")
        return bindings[0]

    # -- Hold'em sound helpers -----------------------------------------------------------------

    def test_each_holdem_sound_helper_is_defined_once(self):
        for name in SOUND_FUNCTIONS:
            with self.subTest(name=name):
                self.single_binding(name)

    def test_kept_holdem_sound_helpers_are_the_definitions_python_used(self):
        expected = {node.name: ast.dump(node) for node in ast.parse(KEPT_SOUND_SOURCE).body}
        for name in SOUND_FUNCTIONS:
            with self.subTest(name=name):
                path, _ = self.single_binding(name)
                self.assertEqual(ast.dump(locate.function_node(name, path=path)), expected[name])

    def test_npc_action_sound_still_plays_the_right_sound(self):
        played = []
        game = types.SimpleNamespace(npc_action_texts=[" Checked ", "Called $50", "Bet $20", "Raised to $90", "Folded"])
        env = {
            "texas_holdem_game": game,
            "sounds": types.SimpleNamespace(audio=types.SimpleNamespace(play_sound=played.append)),
            "play_texas_holdem_chip_sound": lambda: played.append("chips"),
        }
        path = locate.file_of("play_texas_holdem_npc_action_sound")
        locate.exec_functions(list(SOUND_FUNCTIONS), env, path=path)
        for index, expected in enumerate((["poker_check"], ["chips"], ["chips"], ["chips"], [])):
            with self.subTest(text=game.npc_action_texts[index]):
                del played[:]
                env["play_texas_holdem_npc_action_sound"](index)
                self.assertEqual(played, expected)
        del played[:]
        env["play_texas_holdem_npc_action_sound"](len(game.npc_action_texts))
        env["play_texas_holdem_npc_action_sound"](-1)
        self.assertEqual(played, [])
        env["play_texas_holdem_new_hand_sound"]()
        env["play_texas_holdem_street_sound"]()
        self.assertEqual(played, ["card_draw", "card_draw"])

    # -- STATE_CAREER_NEWS ---------------------------------------------------------------------

    def test_state_career_news_is_assigned_once(self):
        path, node = self.single_binding("STATE_CAREER_NEWS")
        self.assertEqual(path.name, "state_names.py")
        self.assertEqual(ast.literal_eval(node.value), "career_news")

    # -- shared start-up values ----------------------------------------------------------------

    def test_blackjack_dealer_npc_starts_as_none_once(self):
        path, node = self.single_binding("blackjack_dealer_npc")
        self.assertEqual(path.name, "state.py")
        self.assertIsNone(ast.literal_eval(node.value))

    def test_play_background_image_is_assigned_once(self):
        self.single_binding("play_background_image")

    def test_play_background_image_is_still_the_scaled_menu_background(self):
        # Run the import-time assignment(s) with stand-ins and check what start-up leaves behind.
        bindings = module_level_bindings("play_background_image")
        self.assertTrue(bindings)

        class Loaded:
            def __init__(self, file):
                self.file = file

            def convert_alpha(self):
                return ("converted", self.file)

        env = {
            "pygame": types.SimpleNamespace(
                image=types.SimpleNamespace(load=Loaded),
                transform=types.SimpleNamespace(smoothscale=lambda surface, size: ("scaled", surface, size)),
            ),
            "paths": types.SimpleNamespace(asset=lambda relative: f"<assets>/{relative}"),
            "BASE_WIDTH": 1366,
            "BASE_HEIGHT": 768,
        }
        locate.exec_nodes([node for _, node in bindings], env)
        self.assertEqual(
            env["play_background_image"],
            ("scaled", ("converted", "<assets>/ui/menu_ui/play_background.png"), (1366, 768)),
        )

    def test_rects_are_assigned_once_with_the_value_in_effect(self):
        for name, expected in KEPT_RECTS.items():
            with self.subTest(name=name):
                path, node = self.single_binding(name)
                self.assertEqual(path.name, "legacy.py")
                value = node.value
                self.assertIsInstance(value, ast.Call)
                self.assertEqual(ast.unparse(value.func), "pygame.Rect")
                self.assertEqual(tuple(ast.literal_eval(arg) for arg in value.args), expected)


if __name__ == "__main__":
    unittest.main()
