from pathlib import Path


def test_ambient_playlist_auto_discovers_drop_in_tracks():
    main_source = Path("main.py").read_text(encoding="utf-8")

    assert 'discover_music_files(' in main_source
    assert '"assets/music",' in main_source
    assert '"ambient_",' in main_source
    assert '"assets/music/ambient_05' not in main_source


def test_arcade_cabinets_have_optional_individual_music_hooks():
    main_source = Path("main.py").read_text(encoding="utf-8")
    audio_source = Path("audio.py").read_text(encoding="utf-8")

    for game_id in (
        "king_pong",
        "battle_bosses",
        "ace_invaders",
        "suit_snake",
    ):
        assert f'"{game_id}"' in main_source

    assert '"assets/music/arcade"' in main_source
    assert 'sync_machine_music(' in main_source
    assert 'sync_machine_music' in audio_source
    assert 'loops=-1' in audio_source
    assert 'self.arcade_gain' in audio_source


def test_machine_music_respects_global_off_and_restores_playlist():
    audio_source = Path("audio.py").read_text(encoding="utf-8")

    assert 'self.music_mode == "off"' in audio_source
    assert 'self.machine_music_resume_mode' in audio_source
    assert '("playlist", resume_mode)' in audio_source
    assert 'self.set_music_mode(' in audio_source


def test_placeholder_machine_music_defaults_off_and_requires_opt_in():
    main_source = Path("main.py").read_text(encoding="utf-8")

    assert "arcade_placeholder_music_enabled = False" in main_source
    assert 'Placeholder Music: {\'On\' if arcade_placeholder_music_enabled else \'Off\'}' in main_source
    assert "if arcade_placeholder_music_enabled" in main_source
    assert "arcade_placeholder_music_toggle_rect" in main_source


def test_bad_music_files_are_skipped_instead_of_crashing_playlist():
    audio_source = Path("audio.py").read_text(encoding="utf-8")

    assert "self._failed_music_tracks = set()" in audio_source
    assert "except (pygame.error, OSError) as exc:" in audio_source
    assert "Skipping unsupported/unreadable music track" in audio_source
    assert "while self.music_queue:" in audio_source
    assert "track not in self._failed_music_tracks" in audio_source


def test_arcade_custom_reroll_and_quit_assets_are_wired():
    main_source = Path("main.py").read_text(encoding="utf-8")

    assert '"reroll_rivals": "assets/arcade/ui/reroll_rivals.png"' in main_source
    assert '"quit": "assets/arcade/ui/quit.png"' in main_source
    assert '"reroll_rivals",\n        "Reroll Rivals"' in main_source
    assert main_source.count('\n        "quit",\n        "Quit",') >= 4
    assert "suit_snake_quit_rect = pygame.Rect(1155, 660, 190, 50)" in main_source
