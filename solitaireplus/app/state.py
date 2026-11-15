"""Shared runtime state: the variables that used to be globals of main.py.

Read and write them as ``state.name``. Values below are the starting values; the names
listed at the end get their first value during start-up (solitaireplus.legacy and the
modules it imports), in the same order as in the old main.py.
"""

profile_select_notice = ""
_reward_cosmetic_order = 2000
horse_race_music_sound = None
horse_race_music_channel = None
horse_race_previous_music_volume = None
help_current_page = (
    "solitaire_basics"
)
help_nav_scroll = 0
help_nav_max_scroll = 0
help_content_scroll = 0
help_content_max_scroll = 0
fullscreen_enabled = False
scaled_surface_cache = None
confirm_return_to_menu = False
game_pause_menu_open = False
profile_switch_snapshot = None
current_profile_slot = 1
guest_mode = False
profile_creation_mode = False
pending_profile_slot = None
profile_delete_slot = None
confirm_delete_profile = False
player_solitaire_points = 0
texas_holdem_hand_win_sound_at = 0
music_slider_dragging = False
sfx_slider_dragging = False
blackjack_dealer_npc = None
texas_holdem_starting_stack = 0
texas_holdem_session_net = 0
texas_holdem_buy_in_active = False
texas_holdem_next_npc_action_at = 0
texas_holdem_round_advance_at = 0
texas_holdem_next_hand_at = 0
texas_holdem_last_processed_showdown_hand = 0
texas_holdem_session_end_at = 0
texas_holdem_table_sweep_rewarded = False
five_card_draw_starting_stack = 0
five_card_draw_session_net = 0
five_card_draw_buy_in_active = False
five_card_draw_next_npc_action_at = 0
five_card_draw_round_advance_at = 0
five_card_draw_next_hand_at = 0
five_card_draw_session_end_at = 0
five_card_draw_hand_win_sound_at = 0
five_card_draw_last_processed_showdown_hand = 0
five_card_draw_table_sweep_rewarded = False
seven_card_stud_starting_stack = 0
seven_card_stud_session_net = 0
seven_card_stud_buy_in_active = False
seven_card_stud_next_npc_action_at = 0
seven_card_stud_round_advance_at = 0
seven_card_stud_next_hand_at = 0
seven_card_stud_session_end_at = 0
seven_card_stud_hand_win_sound_at = 0
seven_card_stud_last_processed_showdown_hand = 0
seven_card_stud_table_sweep_rewarded = False
arcade_night_tokens_spent = 0
arcade_night_tickets_won = 0
arcade_pending_launch_game_id = None
arcade_selected_prize_index = 0
arcade_prize_page = 0
king_pong_opponent_choices = []
king_pong_selected_opponent_index = None
battle_bosses_opponent_choices = []
battle_bosses_selected_choice_index = None
ace_invaders_selected_difficulty_index = None
suit_snake_selected_mode_index = None
suit_snake_selected_movement_style = "step"
arcade_status_message = ""
arcade_status_message_expires = 0
arcade_placeholder_music_enabled = False
roulette_session_net = 0
roulette_chip_value = 10
horse_races_session_net = 0
horse_races_last_rewarded_races = 0
faro_session_net = 0
faro_chip_value = 10
five_o_poker_starting_stack = 0
five_o_poker_session_net = 0
five_o_poker_buy_in_active = False
blind_mans_bluff_starting_stack = 0
blind_mans_bluff_session_net = 0
blind_mans_bluff_buy_in_active = False
blackjack_session_net = 0
blackjack_session_rating_change = 0
blackjack_selected_bet_percentage = None
blackjack_bet_dropdown_open = False
score_four_opponent_choices = []
score_four_opponent_npc = None
debug_previous_state = None
debug_poker_select_game_id = None
debug_poker_selected_ids = []
career_event_entry = None
career_event_has_activity = False
career_event_summary_title = ""
career_event_summary_lines = []
career_event_result_log = []
career_event_news_posted = False
career_news_page = 0
career_rating = 1000
career_rating_results = {}
career_cash = 500
career_fans = 0
career_last_fan_change = 0
career_last_fan_reason = ""
career_fan_rewarded_jobs = set()
career_fan_news_milestones = set()
career_fan_trend = []
career_rating_news_flags = set()
achievements_scroll_y = 0
achievement_popup_queue = []
achievement_popup_current = None
achievement_popup_started = 0
achievement_popup_fans = 0
achievement_popup_cosmetic = ""
blackjack_round_doubled = False
blackjack_round_all_in = False
blackjack_round_start_bet = 0
free_play_achievement_fans_earned = 0
career_interview_recent_ids = []
career_interview_questions = []
career_interview_index = 0
career_interview_media_heat = 0
career_interview_fan_change = 0
career_interview_feedback = ""
career_autograph_fan_change = 0
career_autograph_last_change = 0
head_to_head_opponents = []
head_to_head_selected_index = None
head_to_head_previous_deal_mode = None
head_to_head_previous_difficulty = None
head_to_head_previous_stock_draw_count = None
career_year = 2026
career_month = 1
career_day_of_month = 1
career_weekday_index = 0
career_day = 1
career_leaderboard_state = {}
career_npc_world = {}
career_leaderboard_star_id = None
career_residence = (
    "dingy_apartment"
)
career_owned_residences = [
    "dingy_apartment"
]
career_job = (
    "custodian"
)
selected_leaderboard_entry = None
career_rounds_won = 0
career_challenges_won = 0
career_total_moves = 0
career_leaderboard_page = 0
career_leaderboard_rating_key = "overall"
career_completed_days = []
career_current_schedule = []
career_news_items = []
pending_career_activity_index = None
pending_career_activity_type = None
pending_career_challenge_id = None
current_game_mode = None
selected_cursor = "cursor"
profile_country_text = ""
profile_age_text = ""
profile_hometown_text = ""
profile_bio_text = ""
profile_gender = "non-binary"
profile_favorite_suit = ""
gender_dropdown_open = False
favorite_suit_dropdown_open = False
profile_name_active = False
profile_country_active = False
profile_age_active = False
profile_hometown_active = False
profile_bio_active = False
profile_message = ""
selected_avatar_base = "base_01"
selected_avatar_eyes = "eyes_01"
selected_avatar_hair = "hair_01"
selected_avatar_glasses = "glasses_01"
selected_avatar_top = "top_01"
software_cursor_fallback = False
software_cursor_force_accessible = False
courrier_font_path = None
free_play_snapshot = None
career_leaderboard_bio_rects = []
update_message = ""
customize_page = 0
round_recap_data = None
last_progression_result = None
level_up_queue = []
current_level_up_data = None
menu_mouse_pos = (
    0,
    0
)

# Set during start-up:

#   WINDOWED_HEIGHT, WINDOWED_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH, _entry, _inserted,
#   achievement_state, additional_bet, age_value, arcade_state, asset_id, career_alien_story,
#   career_back_rect, career_bigfoot_story, career_calendar_action_rect, career_calendar_skip_rect,
#   career_jobs_rect, career_leaderboards_rect, career_news_rect, career_play_rect,
#   career_poker_learning, career_ratings, career_real_estate_rect, case_collection_state,
#   column_index, courrier_title_font, cryptid_collection_state, current_index, current_state,
#   cursor_files, cursor_image, customize_category, customize_return_state,
#   dead_mans_hand_return_state, direction, display_name, free_game_id, game_mouse_pos, horse_index,
#   index, loaded, modern_splash_background, modern_splash_logo, options_return_state,
#   package_index, play_background_image, player_chat_action, player_level, player_name, player_xp,
#   player_xp_to_next, post_round_return_state, preview_source, preview_surface, profile_name_text,
#   profile_return_state, profile_select_return_state, profile_switch_rect, rect, relative_x,
#   running, screen, selected_felt, selected_menu_background, selected_title, success,
#   system_cursor_metrics, unlocked_felts, unlocked_menu_backgrounds, unlocked_titles, volume, wager
