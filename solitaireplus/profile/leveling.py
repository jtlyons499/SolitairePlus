"""Player progression: XP and levels, round rewards, unlocks by level, achievement events and popups (moved out of legacy.py)."""
from solitaireplus.app.settings import LEVEL_UNLOCKS
from solitaireplus.app.settings import LEVEL_XP_THRESHOLDS
from solitaireplus.career.fans import fan_bonus_for_achievement
from solitaireplus.profile.achievements import iter_rewards as iter_achievement_rewards
from solitaireplus.profile.achievements import record_event as record_achievement_event
from solitaireplus.career.rating_events import record_result
from solitaireplus.app import state
from solitaireplus.app.lazy import lazy
legacy = lazy("solitaireplus.legacy")


# XP values intentionally stay modest because many of these games can be
# played repeatedly inside one Career event.  Solitaire keeps its score-based
# XP system; everything else now contributes to profile progression too.
GAME_XP_VALUES = {
    "crazy_eights": (45, 90),
    "bango": (30, 65),
    "score_four_solo": (55, 85),
    "score_four_competitive": (55, 105),
    "blackjack": (18, 38),
    "roulette": (15, 32),
    "horse_races": (20, 42),
    "faro": (55, 95),
    "five_o_poker": (60, 110),
    "blind_mans_bluff": (60, 110),
    "texas_holdem": (70, 125),
    "five_card_draw": (65, 115),
    "seven_card_stud": (70, 125),
    "head_to_head": (65, 135),
}


def award_game_xp(game_id, won=False, bonus=0):
    values = GAME_XP_VALUES.get(game_id, (25, 50))
    amount = values[1] if won else values[0]
    amount = max(1, int(amount) + int(bonus or 0))
    result = add_player_xp(amount)
    if result.get("level_up_screens"):
        state.level_up_queue.extend(result["level_up_screens"])
    return amount


def award_achievement_fans(difficulty="normal", achievement_name="Achievement"):
    return legacy.award_career_fans(
        fan_bonus_for_achievement(difficulty),
        f"Achievement: {achievement_name}"
    )


def process_achievement_event(event_name, **data):

    state.achievement_state, newly_unlocked = record_achievement_event(
        state.achievement_state,
        event_name,
        **data
    )

    for definition in newly_unlocked:
        if state.current_game_mode == "free":
            fan_reward = fan_bonus_for_achievement(
                definition.get("difficulty", "normal")
            )
            state.free_play_achievement_fans_earned += fan_reward
        else:
            fan_reward = award_achievement_fans(
                definition.get("difficulty", "normal"),
                definition.get("title", "Achievement"),
            )

        cosmetic_labels = []
        for reward in iter_achievement_rewards(definition):
            label = legacy.unlock_achievement_cosmetic(reward)
            if label:
                cosmetic_labels.append(label)

        legacy.queue_achievement_popup(
            definition,
            fan_reward,
            ", ".join(cosmetic_labels),
        )

    if newly_unlocked and state.current_game_mode != "free":
        legacy.auto_save_career()

    return newly_unlocked

def get_solitaire_rating_reward(current_rating):
    return 40

# ==================================================
# LEVEL / XP HELPERS
# ==================================================

def get_level_from_xp(xp):
    level = 1

    for candidate_level in sorted(
        LEVEL_XP_THRESHOLDS.keys()
    ):
        required_xp = (
            LEVEL_XP_THRESHOLDS[
                candidate_level
            ]
        )

        if xp >= required_xp:
            level = candidate_level
        else:
            break

    return level


def get_next_level_xp(level):
    next_level = level + 1

    if next_level in LEVEL_XP_THRESHOLDS:
        return LEVEL_XP_THRESHOLDS[
            next_level
        ]

    return None

def sync_unlocks_for_current_level():
    for level in sorted(
            LEVEL_UNLOCKS.keys()
    ):
        if level > state.player_level:
            break

        rewards = LEVEL_UNLOCKS.get(
            level,
            {}
        )

        for asset_id in rewards.get(
                "backgrounds",
                []
        ):
            state.unlocked_menu_backgrounds.add(
                asset_id
            )

        for asset_id in rewards.get(
                "felts",
                []
        ):
            state.unlocked_felts.add(
                asset_id
            )

        for asset_id in rewards.get(
                "titles",
                []
        ):
            state.unlocked_titles.add(
                asset_id
            )

def unlock_rewards_for_level(level):
    rewards = LEVEL_UNLOCKS.get(
        level,
        {}
    )

    newly_unlocked = []

    # ----------------------------
    # Backgrounds
    # ----------------------------

    for asset_id in rewards.get(
        "backgrounds",
        []
    ):
        if (
            asset_id
            not in state.unlocked_menu_backgrounds
        ):
            state.unlocked_menu_backgrounds.add(
                asset_id
            )

            newly_unlocked.append(
                (
                    "background",
                    asset_id
                )
            )

    # ----------------------------
    # Felts
    # ----------------------------

    for asset_id in rewards.get(
        "felts",
        []
    ):
        if asset_id not in state.unlocked_felts:
            state.unlocked_felts.add(
                asset_id
            )

            newly_unlocked.append(
                (
                    "felt",
                    asset_id
                )
            )

    # ----------------------------
    # Titles
    # ----------------------------

    for asset_id in rewards.get(
        "titles",
        []
    ):
        if asset_id not in state.unlocked_titles:
            state.unlocked_titles.add(
                asset_id
            )

            newly_unlocked.append(
                (
                    "title",
                    asset_id
                )
            )

    # ----------------------------
    # Games
    # ----------------------------

    for game_id in rewards.get(
            "games",
            []
    ):
        newly_unlocked.append(
            (
                "game",
                game_id
            )
        )

    return newly_unlocked

def add_player_xp(amount):

    old_level = state.player_level

    state.player_xp += max(
        0,
        amount
    )

    new_level = get_level_from_xp(
        state.player_xp
    )

    level_ups = []
    unlocked_items = []

    level_up_screens = []

    if new_level > old_level:
        for level in range(
            old_level + 1,
            new_level + 1
        ):
            level_ups.append(
                level
            )

            level_unlocks = (
                unlock_rewards_for_level(
                    level
                )
            )

            if legacy.game_namespace().get('cryptid_collection_state') is not None:
                from solitaireplus.games.cryptid.collection import award_level_packs
                packs=award_level_packs(state.cryptid_collection_state,level)
                if packs:level_unlocks.append(('cryptid_pack',str(packs)))
            unlocked_items.extend(
                level_unlocks
            )

            level_up_screens.append(
                {
                    "level": level,
                    "unlocks": level_unlocks,
                }
            )

    state.player_level = new_level

    next_threshold = get_next_level_xp(
        state.player_level
    )

    if next_threshold is None:
        state.player_xp_to_next = None

    else:
        state.player_xp_to_next = (
            next_threshold
        )

    return {
        "old_level": old_level,
        "new_level": new_level,
        "level_ups": level_ups,
        "unlocked_items": unlocked_items,
        "level_up_screens": level_up_screens,
        "xp_added": amount,
        "total_xp": state.player_xp,
    }

def apply_round_rewards(
        round_data
):


    # ==================================================
    # XP
    # ==================================================

    xp_earned = round_data.get(
        "xp_earned",
        0
    )

    progression_result = (
        add_player_xp(
            xp_earned
        )
    )

    print(
        "XP DEBUG:",
        "earned =",
        xp_earned,
        "| total XP =",
        progression_result[
            "total_xp"
        ],
        "| old level =",
        progression_result[
            "old_level"
        ],
        "| new level =",
        progression_result[
            "new_level"
        ],
        "| screens =",
        progression_result[
            "level_up_screens"
        ]
    )

    # ==================================================
    # Solitaire Points
    #
    # XP already includes the difficulty multiplier,
    # so SP inherits that benefit naturally.
    # ==================================================

    sp_earned = max(
        1,
        xp_earned // 2
    )

    state.player_solitaire_points += (
        sp_earned
    )

    round_data[
        "sp_earned"
    ] = sp_earned

    # Defaults for Free Play
    round_data[
        "cash_earned"
    ] = 0

    round_data[
        "rating_change"
    ] = 0

    # ==================================================
    # Career rewards
    # ==================================================

    if state.current_game_mode == "career":
        reward_multiplier = (
            round_data.get(
                "reward_multiplier",
                1.0
            )
        )

        base_cash = (
                100
                + round_data.get(
            "score",
            0
        ) // 100
        )

        cash_earned = max(
            1,
            int(
                round(
                    base_cash
                    * reward_multiplier
                )
            )
        )

        base_rating_change = (
            get_solitaire_rating_reward(
                state.career_ratings["solitaire"]
            )
        )

        rating_change = max(
            1,
            int(
                round(
                    base_rating_change
                    * reward_multiplier
                )
            )
        )

        state.career_cash += (
            cash_earned
        )

        rating_change = legacy.award_career_rating("solitaire", rating_change)
        record_result(state.career_rating_results, "solitaire", 1.0, rating_change)

        fans_earned = legacy.award_fans_for_rating_win(
            rating_change,
            "Solitaire win"
        )

        round_data[
            "cash_earned"
        ] = cash_earned

        round_data[
            "rating_change"
        ] = rating_change

        round_data[
            "fans_earned"
        ] = fans_earned

    return progression_result
