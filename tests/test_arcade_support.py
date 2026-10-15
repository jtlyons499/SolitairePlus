from arcade_support import (
    ARCADE_PRIZE_CATALOG,
    buy_token_package,
    award_battle_bosses_tickets,
    award_king_pong_tickets,
    make_default_arcade_state,
    redeem_prize,
    register_battle_bosses_result,
    register_king_pong_result,
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
    assert '"battle_bosses",\n' not in arcade_source.split('ARCADE_COMING_SOON_GAME_IDS = {', 1)[1].split('}', 1)[0]


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


def test_prize_counter_select_art_is_actually_rendered_on_arcade_night():
    from pathlib import Path

    main_source = Path("main.py").read_text(encoding="utf-8")
    assert '"prize_counter": "assets/arcade/ui/prize_counter.png"' in main_source
    assert 'prize_art = get_event_selection_image("prize_counter", prize_art_rect.size)' in main_source


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
