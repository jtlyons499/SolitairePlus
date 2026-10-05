"""Artist-layer, saved-identity and production portrait integration tests."""
import ast
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

import npc_manager
from career_npc_world import add_prospect, ensure_career_world
from npc_avatars import (AVATAR_PARTS, avatar_age_band, ensure_prospect_avatar,
                         get_avatar_choices, valid_part_id)
from npc_portraits import NpcAvatarRenderer

ROOT = Path(__file__).resolve().parents[1]


def character(**choices):
    avatar = {"version": 1, "seed": 123}
    avatar.update({key: f"{prefix}_01" for key, (_, prefix) in AVATAR_PARTS.items()})
    avatar.update(background=None, glasses=None)
    avatar.update(choices)
    return {"id": "test_artist", "age": 8, "is_prospect": True, "avatar": avatar}


def png(root, part, color, variant=1, band=None, rect=None):
    folder, prefix = AVATAR_PARTS[part]
    path = Path(root) / ("ages" if band else "")
    if band:
        path /= band
    path = path / folder / f"{prefix}_{variant:02d}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image = pygame.Surface((512, 512), pygame.SRCALPHA)
    if rect is None:
        image.fill(color)
    else:
        pygame.draw.rect(image, color, rect)
    pygame.image.save(image, path)
    return path


def core_art(root):
    png(root, "base", (210, 160, 110, 255), rect=(100, 80, 312, 330))
    png(root, "shirt", (15, 90, 180, 255), rect=(60, 350, 392, 162))
    png(root, "nose", (130, 55, 40, 255), rect=(245, 240, 22, 30))
    png(root, "eyes", (25, 35, 45, 255), rect=(155, 200, 202, 20))
    png(root, "smile", (180, 35, 75, 255), rect=(210, 295, 92, 18))


def register_player(renderer):
    base = pygame.Surface((300, 360), pygame.SRCALPHA)
    base.fill((90, 170, 220, 255))
    eyes = pygame.Surface((300, 360), pygame.SRCALPHA)
    pygame.draw.rect(eyes, (0, 0, 0, 255), (80, 90, 140, 20))
    empty = pygame.Surface((300, 360), pygame.SRCALPHA)
    shirt = pygame.Surface((300, 360), pygame.SRCALPHA)
    pygame.draw.rect(shirt, (30, 180, 90, 255), (0, 260, 300, 100))
    renderer.register_player_art({"base_01": base}, {"eyes_01": eyes},
                                 {"hair_01": empty}, {}, {"top_01": shirt})
    return base


class SavedAvatarTests(unittest.TestCase):
    def test_all_prospects_have_complete_choices_and_use_all_ten_core_variants(self):
        for part in ("base", "smile", "nose", "eyes", "shirt", "hair", "eyebrows"):
            values = set()
            for npc in npc_manager.PROSPECT_POOL:
                self.assertTrue(valid_part_id(part, npc["avatar"][part]))
                values.add(npc["avatar"][part])
                self.assertNotIn("portrait_style", npc)
            self.assertEqual(len(values), 10, part)

    def test_missing_or_invalid_fields_migrate_once_without_losing_valid_choices(self):
        npc = {"id": "old_prospect", "portrait_style": {"seed": 64, "glasses": True},
               "avatar": {"base": "base_10", "eyes": "../../outside",
                          "hair": None, "smile": "smile_11"}}
        choices = ensure_prospect_avatar(npc)
        self.assertEqual(choices["seed"], 64)
        self.assertEqual(choices["base"], "base_10")
        self.assertIsNone(choices["hair"])
        self.assertTrue(valid_part_id("eyes", choices["eyes"]))
        self.assertTrue(valid_part_id("smile", choices["smile"]))
        self.assertIsNotNone(choices["glasses"])
        self.assertNotIn("portrait_style", npc)
        saved = json.loads(json.dumps(npc))
        ensure_prospect_avatar(saved)
        self.assertEqual(saved, npc)

    def test_loaded_development_batch_gets_avatar_without_changing_career(self):
        states = {}
        world = ensure_career_world({}, states, npc_manager.BASE_NPCS, 2026, 1, seed=42)
        story = add_prospect(world, states, npc_manager.PROSPECT_POOL, 2026, 1, True)
        state = states[story["npc_id"]]
        state["prospect_record"].pop("avatar")
        state["prospect_record"]["portrait_style"] = {"seed": 128, "glasses": True}
        original = copy.deepcopy(state)
        before_world = copy.deepcopy(world)
        ensure_career_world(world, states, npc_manager.BASE_NPCS, 2026, 1)
        self.assertEqual(world, before_world)
        for key in original:
            if key != "prospect_record":
                self.assertEqual(state[key], original[key], key)
        self.assertEqual(state["prospect_record"]["avatar"]["seed"], 128)
        self.assertEqual(state["prospect_record"]["personality_traits"],
                         original["prospect_record"]["personality_traits"])
        npc_manager.sync_npc_runtime_state(states)
        self.addCleanup(npc_manager.sync_npc_runtime_state, {})
        live = next(n for n in npc_manager.NPCS if n["id"] == story["npc_id"])
        self.assertEqual(live["avatar"], state["prospect_record"]["avatar"])

    def test_pure_read_does_not_reroll_age_or_size_and_never_mutates_record(self):
        npc = {"id": "new", "age": 5}
        original = copy.deepcopy(npc)
        first = get_avatar_choices(npc)
        self.assertEqual(npc, original)
        npc["age"] = 80
        self.assertEqual(get_avatar_choices(npc), first)
        self.assertEqual([avatar_age_band(age) for age in (5, 12, 13, 19, 20, 49, 50)],
                         ["child", "child", "teen", "teen", "adult", "adult", "veteran"])


class ArtistRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.renderer = NpcAvatarRenderer(self.folder.name)

    def test_layers_align_and_remain_transparent_without_recolouring(self):
        core_art(self.folder.name)
        npc = character()
        image = self.renderer.render(npc, 512)
        self.assertEqual(image.get_at((0, 0)).a, 0)
        for position, color in (((120, 100), (210, 160, 110)),
                                ((256, 250), (130, 55, 40)),
                                ((200, 210), (25, 35, 45)),
                                ((256, 300), (180, 35, 75)),
                                ((256, 450), (15, 90, 180))):
            self.assertEqual(tuple(image.get_at(position))[:3], color)
        self.assertEqual(self.renderer.render(npc, 72).get_size(), (72, 72))

    def test_optional_glasses_are_last_and_none_omits_them(self):
        core_art(self.folder.name)
        png(self.folder.name, "glasses", (200, 210, 20, 255), rect=(150, 195, 210, 30))
        with_glasses = self.renderer.render(character(glasses="glasses_01"), 512)
        without_glasses = self.renderer.render(character(), 512)
        self.assertEqual(tuple(with_glasses.get_at((200, 210)))[:3], (200, 210, 20))
        self.assertEqual(tuple(without_glasses.get_at((200, 210)))[:3], (25, 35, 45))

    def test_existing_player_art_is_used_whole_and_keeps_its_proportions(self):
        base = register_player(self.renderer)
        original = pygame.image.tobytes(base, "RGBA")
        image = self.renderer.render(character(base="base_10", eyes="eyes_10", shirt="shirt_10"), 360)
        self.assertEqual(image.get_at((0, 0)).a, 0)
        self.assertEqual(tuple(image.get_at((180, 180)))[:3], (90, 170, 220))
        self.assertEqual(tuple(image.get_at((180, 300)))[:3], (30, 180, 90))
        self.assertEqual(pygame.image.tobytes(base, "RGBA"), original)

    def test_incomplete_new_pack_does_not_mix_incompatible_player_coordinates(self):
        register_player(self.renderer)
        png(self.folder.name, "base", (255, 0, 0, 255))
        image = self.renderer.render(character(), 360)
        self.assertEqual(tuple(image.get_at((180, 180)))[:3], (90, 170, 220))

    def test_partial_pack_uses_available_variants_without_rewriting_saved_choices(self):
        core_art(self.folder.name)
        npc = character(base="base_10", smile="smile_10", eyes="eyes_10")
        original = copy.deepcopy(npc)
        image = self.renderer.render(npc, 512)
        self.assertEqual(tuple(image.get_at((120, 100)))[:3], (210, 160, 110))
        self.assertEqual(npc, original)
        png(self.folder.name, "base", (50, 130, 80, 255), variant=10)
        self.renderer.refresh(force=True)
        image = self.renderer.render(npc, 512)
        self.assertEqual(tuple(image.get_at((120, 100)))[:3], (50, 130, 80))
        self.assertEqual(npc, original)

    def test_age_specific_art_overrides_only_same_part_and_number(self):
        core_art(self.folder.name)
        png(self.folder.name, "base", (80, 45, 200, 255), band="adult")
        npc = character()
        original = copy.deepcopy(npc["avatar"])
        child = self.renderer.render(npc, 512)
        npc["age"] = 30
        adult = self.renderer.render(npc, 512)
        self.assertEqual(tuple(child.get_at((120, 100)))[:3], (210, 160, 110))
        self.assertEqual(tuple(adult.get_at((120, 100)))[:3], (80, 45, 200))
        self.assertEqual(tuple(adult.get_at((256, 300)))[:3], (180, 35, 75))
        self.assertEqual(npc["avatar"], original)

    def test_edited_art_refreshes_cached_image_without_changing_identity(self):
        core_art(self.folder.name)
        npc = character()
        old = self.renderer.render(npc, 512)
        self.assertIs(self.renderer.render(npc, 512), old)
        path = png(self.folder.name, "base", (20, 190, 30, 255))
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000000))
        self.renderer.refresh(force=True)
        new = self.renderer.render(npc, 512)
        self.assertIsNot(old, new)
        self.assertEqual(tuple(new.get_at((120, 100)))[:3], (20, 190, 30))

    def test_corrupt_age_png_uses_common_art_and_corrupt_core_uses_player_art(self):
        core_art(self.folder.name)
        bad = png(self.folder.name, "base", (0, 0, 0, 255), band="child")
        bad.write_bytes(b"broken PNG")
        image = self.renderer.render(character(), 512)
        self.assertEqual(tuple(image.get_at((120, 100)))[:3], (210, 160, 110))
        register_player(self.renderer)
        smile = Path(self.folder.name) / "smiles" / "smile_01.png"
        smile.write_bytes(b"broken PNG")
        self.renderer.refresh(force=True)
        image = self.renderer.render(character(), 360)
        self.assertEqual(tuple(image.get_at((180, 180)))[:3], (90, 170, 220))

    def test_main_portrait_override_has_priority_then_falls_back_to_artist_layers(self):
        tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == "get_npc_portrait_surface")
        calls = []
        expected = pygame.Surface((72, 72))
        env = {"pygame": pygame, "npc_icon_cache": {},
               "draw_layered_portrait": lambda npc, size: calls.append(npc["id"]) or expected}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "main portrait integration", "exec"), env)
        path = png(self.folder.name, "base", (25, 175, 75, 255))
        npc = dict(character(), portrait=str(path))
        image = env["get_npc_portrait_surface"](npc, 72)
        # SDL's smooth downsampling rounds channels by a few values.
        self.assertTrue(all(abs(actual - source) <= 3 for actual, source in
                            zip(tuple(image.get_at((30, 30)))[:3], (25, 175, 75))))
        self.assertEqual(calls, [])
        npc["portrait"] = str(Path(self.folder.name) / "not_installed.png")
        self.assertIs(env["get_npc_portrait_surface"](npc, 72), expected)
        self.assertEqual(calls, [npc["id"]])


if __name__ == "__main__":
    unittest.main()
