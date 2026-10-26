from arcade_support import (
    ARCADE_PRIZE_CATALOG,
    buy_token_package,
    award_ace_invaders_tickets,
    award_battle_bosses_tickets,
    award_king_pong_tickets,
    award_suit_snake_tickets,
    make_default_arcade_state,
    redeem_prize,
    register_ace_invaders_result,
    register_battle_bosses_result,
    register_king_pong_result,
    register_suit_snake_result,
    spend_tokens,
)


def test_buy_token_package_reduces_cash_and_adds_tokens():
    state = make_default_arcade_state()
    success, state, cash, message = buy_token_package(state, 25, "double_stack")
    assert success is True
    assert cash == 15
    assert state["tokens"] == 45
    assert state["stats"]["tokens_purchased"] == 45
    assert "45 arcade tokens" in message


def test_spend_tokens_prevents_overdraft():
    state = make_default_arcade_state()
    state["tokens"] = 1
    success, new_state = spend_tokens(state, 2)
    assert success is False
    assert new_state["tokens"] == 1


def test_king_pong_ticket_award_prefers_wins():
    win_tickets = award_king_pong_tickets(5, 2)
    loss_tickets = award_king_pong_tickets(3, 5)
    assert win_tickets > loss_tickets
    assert loss_tickets >= 20


def test_redeem_prize_consumes_tickets_and_adds_trophy():
    prize = ARCADE_PRIZE_CATALOG[0]
    state = make_default_arcade_state()
    state["tickets"] = prize["cost"]
    success, state, message, awarded = redeem_prize(state, prize["id"])
    assert success is True
    assert prize["id"] in state["trophies"]
    assert state["tickets"] == 0
    assert awarded["name"] == prize["name"]
    assert "Redeemed" in message


def test_register_king_pong_result_tracks_stats_and_tickets():
    state = make_default_arcade_state()
    updated = register_king_pong_result(state, True, 150)
    assert updated["tickets"] == 150
    assert updated["stats"]["king_pong_wins"] == 1
    assert updated["stats"]["tickets_won"] == 150


def test_arcade_games_are_not_rating_categories():
    from career_ratings import GAME_CATEGORIES

    for game_id in ("king_pong", "battle_bosses", "ace_invaders", "suit_snake"):
        assert game_id not in GAME_CATEGORIES


def test_arcade_asset_contract_matches_authored_files():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    pong_source = Path("king_pong.py").read_text(encoding="utf-8")

    assert '"assets/arcade/bg.png"' in main_source
    assert '"paddle_king_hearts.png"' in pong_source
    assert '"paddle_king_spades.png"' in pong_source
    assert '"chip_ball.png"' in pong_source
    assert 'f"score_{score}.png"' in pong_source
    assert 'award_game_xp("king_pong"' not in main_source


def test_king_pong_difficulty_and_ui_contract():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    pong_source = Path("king_pong.py").read_text(encoding="utf-8")

    assert 'STATE_KING_PONG_OPPONENT_SELECT' in main_source
    assert 'build_king_pong_opponent_choices' in main_source
    assert 'open_king_pong_opponent_select(refresh=True)' in main_source
    assert '"Quit"' in main_source
    assert '"logo.png"' in pong_source
    assert '"logo_old.png"' in pong_source
    assert '"low"' in pong_source
    assert '"medium"' in pong_source
    assert '"high"' in pong_source
    assert '"expert"' in pong_source
    assert '"ticket_multiplier": 0.75' in pong_source
    assert '"ticket_multiplier": 1.75' in pong_source
    assert 'Use WASD or Arrow Keys to move. Keep the Joker chip in play. First to 5 wins.' in pong_source
    assert '↑' not in pong_source
    assert '↓' not in pong_source
    assert 'pygame.K_a' in pong_source
    assert 'pygame.K_d' in pong_source
    assert 'pygame.K_LEFT' in pong_source
    assert 'pygame.K_RIGHT' in pong_source
    assert 'PLAYER_ZONE_FRACTION = 0.30' in pong_source
    assert 'OPPONENT_ZONE_FRACTION = 0.30' in pong_source
    assert 'image = self._fit_image(score_path, box.size)' in pong_source
    assert 'if score > 0 else None' not in pong_source


def test_king_pong_tokens_are_spent_only_when_match_starts():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    tile_branch = main_source.split('elif game_id == "king_pong":', 1)[1].split(
        'elif game_id == "token_exchange":',
        1,
    )[0]

    assert 'open_king_pong_opponent_select(refresh=True)' in tile_branch
    assert 'start_king_pong_session()' not in tile_branch

    start_block = main_source.split('def start_king_pong_session():', 1)[1].split(
        'def claim_king_pong_result():',
        1,
    )[0]
    assert 'spend_tokens(arcade_state, token_cost)' in start_block


def test_king_pong_reuses_five_o_point_sounds_and_pauses_between_points():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    pong_source = Path("king_pong.py").read_text(encoding="utf-8")

    assert '"assets/sounds/five_o_column_win.wav"' in main_source
    assert '"assets/sounds/five_o_column_loss.wav"' in main_source
    assert '"five_o_column_win"' in main_source
    assert '"five_o_column_loss"' in main_source
    assert 'point_event = king_pong_game.pop_point_event()' in main_source
    assert 'POINT_PAUSE_MS = 700' in pong_source
    assert 'def pop_point_event(self):' in pong_source
    assert 'self._serve_resume_at' in pong_source
    assert 'self._pending_serve_to_player' in pong_source


def test_battle_bosses_builds_four_three_npc_difficulty_squads():
    import random
    from battle_bosses import BATTLE_BOSSES_DIFFICULTIES, build_battle_bosses_choices

    npcs = []
    for tier in ("low", "mid", "strong", "elite"):
        for index in range(5):
            npcs.append({
                "id": f"{tier}_{index}",
                "name": f"{tier.title()} {index}",
                "skill_tier": tier,
            })

    choices = build_battle_bosses_choices(npcs, rng=random.Random(7))
    assert len(choices) == 4
    assert [choice["difficulty_id"] for choice in choices] == list(BATTLE_BOSSES_DIFFICULTIES)
    for choice in choices:
        assert len(choice["npcs"]) == 3
        assert len({npc["id"] for npc in choice["npcs"]}) == 3
        assert choice["config"]["ticket_multiplier"] > 0


def test_battle_bosses_opponent_select_and_playable_arena_are_wired():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    arcade_source = Path("arcade_support.py").read_text(encoding="utf-8")
    game_source = Path("battle_bosses_game.py").read_text(encoding="utf-8")

    assert 'STATE_BATTLE_BOSSES_OPPONENT_SELECT' in main_source
    assert 'STATE_BATTLE_BOSSES = "battle_bosses"' in main_source
    assert 'open_battle_bosses_opponent_select(refresh=True)' in main_source
    assert 'draw_battle_bosses_opponent_select()' in main_source
    assert '"Reroll Rivals"' in main_source
    assert 'start_battle_bosses_session()' in main_source
    assert 'spend_tokens(arcade_state, token_cost)' in main_source.split('def start_battle_bosses_session():', 1)[1].split('def claim_battle_bosses_result():', 1)[0]
    assert 'battle_bosses_game.update' in main_source
    assert '"joker_ball.png"' in game_source
    assert 'A/D or Left/Right moves your shield.' in game_source
    assert 'ARCADE_COMING_SOON_GAME_IDS = set()' in arcade_source


def test_battle_bosses_ticket_reward_scales_with_progress_and_win():
    partial = award_battle_bosses_tickets(1, False, 0)
    near_clear = award_battle_bosses_tickets(2, False, 0)
    win = award_battle_bosses_tickets(3, True, 3)
    assert partial < near_clear < win

    state = make_default_arcade_state()
    updated = register_battle_bosses_result(state, True, win, rivals_eliminated=3)
    assert updated["tickets"] == win
    assert updated["stats"]["battle_bosses_wins"] == 1
    assert updated["stats"]["battle_bosses_rivals_eliminated"] == 3


def test_arcade_night_action_buttons_use_authored_pngs_with_fallbacks():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    assert '"buy_tokens": "assets/arcade/ui/buy_tokens.png"' in main_source
    assert '"prize_counter": "assets/arcade/ui/prize_counter.png"' in main_source
    assert '"return": "assets/arcade/ui/return.png"' in main_source
    assert '"end": "assets/arcade/ui/end_night.png"' in main_source
    assert 'def draw_arcade_action_image_button' in main_source
    assert 'def get_cover_scaled_ui_asset' in main_source
    assert 'draw_arcade_action_image_button(' in main_source
    assert 'arcade_machine_prize_counter_rect' in main_source
    assert 'assets/arcade/ui/background.png' in main_source
    assert 'assets/arcade/ui/title.png' in main_source


def test_king_pong_ai_was_softened_after_2d_movement_feedback():
    import ast
    from pathlib import Path

    tree = ast.parse(Path("king_pong.py").read_text(encoding="utf-8"))
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "KING_PONG_DIFFICULTIES" for target in node.targets)
    )
    difficulties = ast.literal_eval(assignment.value)
    assert difficulties["low"]["npc_speed"] <= 225
    assert difficulties["medium"]["npc_speed"] <= 285
    assert difficulties["medium"]["tracking_error"] >= 100
    assert difficulties["high"]["tracking_error"] >= 65


def test_battle_bosses_ricochet_polish_uses_contact_point_and_optional_sfx():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    game_source = Path("battle_bosses_game.py").read_text(encoding="utf-8")

    assert 'def _closest_point_on_segment' in game_source
    assert 'safe_center = closest + normal * (contact_radius + 2.5)' in game_source
    assert 'COLLISION_STEP_PX = 5.0' in game_source
    assert 'tangent_impulse=tangent_impulse' in game_source
    assert 'os.path.join(ASSET_ROOT, "logo.png")' in game_source
    assert 'def pop_sound_events(self):' in game_source
    assert '"battle_bosses_ricochet"' in main_source
    assert '"battle_bosses_fort_hit"' in main_source
    assert '"battle_bosses_eliminate"' in main_source
    assert '"battle_bosses_win"' in main_source
    assert '"battle_bosses_loss"' in main_source
    assert 'for battle_sound_event in battle_bosses_game.pop_sound_events()' in main_source


def test_battle_bosses_compact_four_corner_spacing():
    from pathlib import Path

    game_source = Path("battle_bosses_game.py").read_text(encoding="utf-8")
    assert "ARENA_RECT = pygame.Rect(320, 170, 726, 450)" in game_source
    assert "SHIELD_RADIUS = 126" in game_source
    assert '"bottom_left": (-65.0, -5.0)' in game_source
    assert '"top_left": (5.0, 65.0)' in game_source
    assert '"top_right": (115.0, 175.0)' in game_source
    assert '"bottom_right": (185.0, 245.0)' in game_source
    assert "inset_x = 70" in game_source
    assert "inset_y = 70" in game_source


def test_battle_bosses_late_game_pace_corner_rotation_and_shield_wear():
    from pathlib import Path

    game_source = Path("battle_bosses_game.py").read_text(encoding="utf-8")
    assert "MIN_SHIELD_LENGTH = 46" in game_source
    assert "SHIELD_WEAR_PER_BLOCK = 3.0" in game_source
    assert 'fort["shield_blocks"] = int(fort.get("shield_blocks", 0)) + 1' in game_source
    assert "def _late_game_speed_floor(self):" in game_source
    assert "return max(base, 485.0)" in game_source
    assert "return max(base, 410.0)" in game_source
    assert "self._player_corner_rotation = (self._player_corner_rotation + 1) % len(self.CORNERS)" in game_source
    assert "player_corner = self.CORNERS[self._player_corner_rotation]" in game_source


def test_battle_bosses_anti_loop_watchdog_and_one_way_shields():
    from pathlib import Path
    game_source = Path("battle_bosses_game.py").read_text(encoding="utf-8")
    assert "LOOP_CONTACT_WINDOW_MS" in game_source
    assert "def _break_ricochet_loop_if_needed(self, now):" in game_source
    assert 'self._record_contact(now, "wall", bounced)' in game_source
    assert 'self._record_contact(now, "shield", fort["index"])' in game_source
    assert "front_side = (ball_center - shield_center).dot(radial)" in game_source
    assert "if front_side < -2.0:" in game_source
    assert "toward_center = pygame.Vector2(self.ARENA_RECT.center) - ball_center" in game_source


def test_ace_invaders_is_playable_unrated_and_removed_from_coming_soon():
    from pathlib import Path

    arcade_source = Path("arcade_support.py").read_text(encoding="utf-8")
    main_source = Path("main.py").read_text(encoding="utf-8")
    config_source = Path("ace_invaders.py").read_text(encoding="utf-8")
    game_source = Path("ace_invaders_game.py").read_text(encoding="utf-8")

    assert 'ARCADE_COMING_SOON_GAME_IDS = set()' in arcade_source
    assert '"ace_invaders"' not in arcade_source.split("ARCADE_COMING_SOON_GAME_IDS", 1)[1].split("ARCADE_TOKEN_PACKAGES", 1)[0]

    assert 'STATE_ACE_INVADERS_DIFFICULTY_SELECT' in main_source
    assert 'STATE_ACE_INVADERS = "ace_invaders"' in main_source
    assert 'open_ace_invaders_difficulty_select(reset_selection=True)' in main_source
    assert 'start_ace_invaders_session()' in main_source
    assert 'ace_invaders_game.update' in main_source
    assert 'draw_ace_invaders_screen()' in main_source

    assert '"casual"' in config_source
    assert '"standard"' in config_source
    assert '"difficult"' in config_source
    assert '"expert"' in config_source
    assert '"ticket_multiplier": 1.75' in config_source

    assert '"player_ship.png"' in game_source
    assert '"bullet.png"' in game_source
    assert 'f"ace_{suit}.png"' in game_source
    assert '"AS.png"' in game_source
    assert 'Use A/D or Left/Right to move. Space fires. Survive as long as you can.' in game_source
    assert 'ENDLESS SCORE ATTACK' in game_source
    assert 'SHIELD_CENTERS_X' in game_source
    assert 'self._reset_shields()' in game_source
    assert 'HIGH {self.high_score:,}' in game_source


def test_ace_invaders_ticket_rewards_scale_with_progress_and_win():
    early = award_ace_invaders_tickets(80, 1, False, 0)
    deep = award_ace_invaders_tickets(220, 3, False, 0)
    win = award_ace_invaders_tickets(350, 4, True, 2)

    assert early < deep < win

    state = make_default_arcade_state()
    updated = register_ace_invaders_result(
        state,
        True,
        win,
        score=350,
        enemies_destroyed=80,
        waves_cleared=4,
    )
    assert updated["tickets"] == win
    assert updated["stats"]["ace_invaders_wins"] == 1
    assert updated["stats"]["ace_invaders_enemies_destroyed"] == 80
    assert updated["stats"]["ace_invaders_waves_cleared"] == 4
    assert updated["stats"]["ace_invaders_high_score"] == 350


def test_ace_invaders_optional_audio_hooks_are_wired():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    game_source = Path("ace_invaders_game.py").read_text(encoding="utf-8")
    for sound_name in (
        "ace_invaders_shoot",
        "ace_invaders_enemy_shoot",
        "ace_invaders_enemy_hit",
        "ace_invaders_player_hit",
        "ace_invaders_shield_hit",
        "ace_invaders_wave_clear",
        "ace_invaders_loss",
    ):
        assert sound_name in main_source
        assert sound_name in game_source


def test_ace_invaders_endless_run_stats_track_runs_high_wave_and_high_score():
    state = make_default_arcade_state()
    payout = award_ace_invaders_tickets(725, 8)
    updated = register_ace_invaders_result(
        state,
        None,
        payout,
        score=725,
        enemies_destroyed=144,
        waves_cleared=8,
    )
    assert updated["stats"]["ace_invaders_runs"] == 1
    assert updated["stats"]["ace_invaders_wins"] == 0
    assert updated["stats"]["ace_invaders_losses"] == 0
    assert updated["stats"]["ace_invaders_high_wave"] == 9
    assert updated["stats"]["ace_invaders_high_score"] == 725
    assert updated["tickets"] == payout


def test_arcade_setup_controls_use_shared_authored_png_buttons():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    assert '"back": "assets/arcade/ui/back.png"' in main_source
    assert '"play_tokens": "assets/arcade/ui/play_tokens.png"' in main_source
    assert 'badge_text=f"{token_cost} TOKENS"' in main_source
    assert 'badge_text=f"{battle_cost} TOKENS"' in main_source
    assert 'badge_center = (rect.centerx, rect.top - 11)' in main_source
    assert 'badge_rect = badge.get_rect(midright=' not in main_source

    king_block = main_source.split("def draw_king_pong_opponent_select():", 1)[1].split(
        "def draw_battle_bosses_opponent_select():", 1
    )[0]
    assert '"back",\n        "Back"' in king_block
    assert '"buy_tokens",\n        "Buy Tokens"' in king_block
    assert '"play_tokens"' in king_block

    ace_block = main_source.split("def draw_ace_invaders_difficulty_select():", 1)[1].split(
        "def draw_ace_invaders_screen():", 1
    )[0]
    assert '"back",\n        "Back"' in ace_block
    assert '"buy_tokens",\n        "Buy Tokens"' in ace_block
    assert '"play_tokens"' in ace_block


def test_king_pong_difficulty_descriptions_are_wrapped_inside_cards():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    king_block = main_source.split("def draw_king_pong_opponent_select():", 1)[1].split(
        "def draw_battle_bosses_opponent_select():", 1
    )[0]
    assert "description_rect = pygame.Rect(" in king_block
    assert "rect.width - 32" in king_block
    assert "draw_wrapped_text_limited(" in king_block
    assert 'difficulty_descriptions.get(difficulty_id, "Arcade opponent")' in king_block


def test_ace_invaders_game_over_flashes_until_exit_and_select_spacing_is_adjusted():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    game_source = Path("ace_invaders_game.py").read_text(encoding="utf-8")

    ace_block = main_source.split("def draw_ace_invaders_difficulty_select():", 1)[1].split(
        "def draw_ace_invaders_screen():", 1
    )[0]
    assert "subtitle.get_rect(center=(BASE_WIDTH // 2, 157))" in ace_block
    assert "wallet.get_rect(center=(BASE_WIDTH // 2, 185))" in ace_block

    assert 'game_over_flash = self.finished and self._flash_message == "GAME OVER"' in game_source
    assert "game_over_flash and (now // 450) % 2 == 0" in game_source
    assert "flash_center_y = PLAYFIELD_RECT.centery if game_over_flash" in game_source


def test_user_arcade_wording_and_machine_mania_package_are_preserved():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    arcade_source = Path("arcade_support.py").read_text(encoding="utf-8")

    assert "Redeem tickets for trophies and exclusive arcade cosmetics." in main_source
    assert '"king_pong": ("Classic Pong.", "First to five wins.")' in main_source
    assert '"battle_bosses": ("Deflect a projectile", "and break the rival strongholds.")' in main_source
    assert '"ace_invaders": ("Defeat waves of incoming", "Ace suits before they reach you.")' in main_source
    assert '"id": "machine_mania_pass"' in arcade_source
    assert '"name": "Machine Mania Pass"' in arcade_source
    assert '"weekend_haul"' not in arcade_source


def test_suit_snake_sequence_and_mode_foundation():
    from suit_snake import (
        CARD_SEQUENCE,
        SUIT_SNAKE_MODES,
        SUIT_SNAKE_MOVEMENT_STYLES,
        sequence_card,
    )

    assert CARD_SEQUENCE[:8] == (
        ("2", "spades"),
        ("2", "diamonds"),
        ("2", "clubs"),
        ("2", "hearts"),
        ("3", "spades"),
        ("3", "diamonds"),
        ("3", "clubs"),
        ("3", "hearts"),
    )
    assert len(CARD_SEQUENCE) == 52
    assert sequence_card(52) == ("2", "spades", 2)
    assert list(SUIT_SNAKE_MODES) == [
        "classic_standard",
        "classic_big_grid",
        "lahey_wraparound",
        "lahey_wraparound_big_grid",
    ]
    assert SUIT_SNAKE_MODES["classic_standard"]["grid_columns"] == 24
    assert SUIT_SNAKE_MODES["classic_standard"]["grid_rows"] == 13
    assert SUIT_SNAKE_MODES["classic_big_grid"]["grid_columns"] == 30
    assert SUIT_SNAKE_MODES["classic_big_grid"]["grid_rows"] == 16
    assert SUIT_SNAKE_MODES["classic_standard"]["wraparound"] is False
    assert SUIT_SNAKE_MODES["lahey_wraparound"]["wraparound"] is True
    assert set(SUIT_SNAKE_MOVEMENT_STYLES) == {"step", "smooth"}


def test_suit_snake_is_playable_and_wired_into_arcade_night():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    arcade_source = Path("arcade_support.py").read_text(encoding="utf-8")
    debug_source = Path("debug_menu.py").read_text(encoding="utf-8")
    game_source = Path("suit_snake_game.py").read_text(encoding="utf-8")

    assert 'ARCADE_COMING_SOON_GAME_IDS = set()' in arcade_source
    assert 'STATE_SUIT_SNAKE_DIFFICULTY_SELECT' in main_source
    assert 'STATE_SUIT_SNAKE = "suit_snake"' in main_source
    assert 'open_suit_snake_difficulty_select(reset_selection=True)' in main_source
    assert 'start_suit_snake_session()' in main_source
    assert 'suit_snake_game.update' in main_source
    assert 'draw_suit_snake_screen()' in main_source
    assert 'ACTION_SUIT_SNAKE = "suit_snake"' in debug_source
    assert '(ACTION_SUIT_SNAKE, "Suit Snake")' in debug_source

    assert 'self.started = False' in game_source
    assert 'PRESS WASD OR ARROW KEY TO START' in game_source
    assert 'if not self.started:' in game_source
    assert 'if self.wraparound:' in game_source
    assert 'new_x %= self.grid_columns' in game_source
    assert 'new_y %= self.grid_rows' in game_source
    assert 'self.movement_style != "smooth"' in game_source
    assert '2S, 2D, 2C, 2H, then 3S...' in game_source
    assert 'new_head in body_to_check' in game_source
    assert 'self._place_target()' in game_source


def test_suit_snake_setup_screen_selects_mode_and_movement_separately():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    assert 'suit_snake_selected_mode_index' in main_source
    assert 'suit_snake_selected_movement_style = "step"' in main_source
    assert 'suit_snake_step_movement_rect' in main_source
    assert 'suit_snake_smooth_movement_rect' in main_source
    assert '"Choose a mode, then choose Step or Smooth Movement."' in main_source
    assert '"Choose a Suit Snake mode first."' in main_source
    assert 'movement_style=movement_style' in main_source


def test_suit_snake_ticket_and_save_stats_scale_with_progress():
    short = award_suit_snake_tickets(450, 4, 0)
    longer = award_suit_snake_tickets(1850, 16, 0)
    deck = award_suit_snake_tickets(6200, 52, 1)
    assert short < longer < deck

    state = make_default_arcade_state()
    updated = register_suit_snake_result(
        state,
        deck,
        score=6200,
        cards_collected=52,
        decks_completed=1,
        chain_length=53,
    )
    assert updated["tickets"] == deck
    assert updated["stats"]["suit_snake_runs"] == 1
    assert updated["stats"]["suit_snake_cards_collected"] == 52
    assert updated["stats"]["suit_snake_decks_completed"] == 1
    assert updated["stats"]["suit_snake_longest_chain"] == 53
    assert updated["stats"]["suit_snake_high_score"] == 6200


def test_suit_snake_uses_shared_custom_setup_buttons_and_optional_audio():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    block = main_source.split("def draw_suit_snake_difficulty_select():", 1)[1].split(
        "def draw_suit_snake_screen():", 1
    )[0]
    assert '"back",' in block and '"Back"' in block
    assert '"buy_tokens",' in block and '"Buy Tokens"' in block
    assert '"play_tokens"' in block
    assert 'get_machine_cost("suit_snake")' in block

    for sound_name in (
        "suit_snake_collect",
        "suit_snake_deck",
        "suit_snake_loss",
    ):
        assert sound_name in main_source
