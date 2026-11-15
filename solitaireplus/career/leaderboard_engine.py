"""The career leaderboard and NPC roster kept in step with the calendar (moved out of legacy.py)."""
from solitaireplus.npc.manager import BASE_NPCS
from solitaireplus.npc.manager import NPCS
from solitaireplus.npc.manager import PROSPECT_POOL
from solitaireplus.career.ratings import RATING_DISPLAY_NAMES
from solitaireplus.career.ratings import RATING_KEYS
from solitaireplus.career.npc_world import advance_career_world
from solitaireplus.career.ratings import boost_npc_overall
from solitaireplus.career.npc_development import development_stage
from solitaireplus.career.npc_world import ensure_career_world
from solitaireplus.career.ratings import ensure_npc_career_state
from solitaireplus.career.ratings import make_npc_rating_bundle
import random
from solitaireplus.app import state
from solitaireplus.npc.manager import sync_npc_runtime_state
from solitaireplus.app.lazy import lazy
news_screen = lazy("solitaireplus.career.news_screen")
career_saving = lazy("solitaireplus.career.career_saving")
legacy = lazy("solitaireplus.legacy")


def load_career_leaderboard_players():
    # One in-place roster feeds rankings, normal game selectors and F10.
    return NPCS

def update_career_leaderboard_ratings():
    if state.current_game_mode == "free" or not state.career_leaderboard_state:
        return False
    previous_month = state.career_npc_world.get("last_simulated_month")
    before_rankings = get_npc_leaderboard_snapshot()
    state.career_npc_world, stories = advance_career_world(
        state.career_npc_world, state.career_leaderboard_state, BASE_NPCS, PROSPECT_POOL,
        state.career_year, state.career_month,
    )
    sync_career_npc_runtime_state()
    if state.career_npc_world["last_simulated_month"] == previous_month:
        return False
    for story in stories:
        news_screen.add_career_news(story["headline"], story["body"], story["category"],
                        year=story["year"], month=story["month"])
    add_monthly_leaderboard_news(before_rankings, get_npc_leaderboard_snapshot())
    return True


CAREER_LEADERBOARD_PLAYERS = (
    load_career_leaderboard_players()
)

def get_npc_leaderboard_snapshot():

    rankings = []

    for npc in CAREER_LEADERBOARD_PLAYERS:

        npc_id = npc.get(
            "id"
        )

        if (
            npc_id is None
            or npc_id
            not in state.career_leaderboard_state
        ):
            continue

        rankings.append(
            {
                "id":
                    npc_id,

                "name":
                    npc.get(
                        "name",
                        "Unknown Player"
                    ),

                "rating":
                    state.career_leaderboard_state[
                        npc_id
                    ].get(
                        "rating",
                        1000
                    ),
            }
        )

    rankings.sort(
        key=lambda item:
            item[
                "rating"
            ],
        reverse=True
    )

    return rankings

def add_monthly_leaderboard_news(
        before,
        after
):

    if not before or not after:
        return

    before_rank = {
        entry[
            "id"
        ]:
            index + 1

        for index, entry
        in enumerate(
            before
        )
    }

    after_rank = {
        entry[
            "id"
        ]:
            index + 1

        for index, entry
        in enumerate(
            after
        )
    }

    # ==================================================
    # World #1
    # ==================================================

    old_number_one = (
        before[
            0
        ]
    )

    new_number_one = (
        after[
            0
        ]
    )

    if (
        old_number_one[
            "id"
        ]
        !=
        new_number_one[
            "id"
        ]
    ):

        news_screen.add_career_news(
            (
                f"{new_number_one['name'].upper()} "
                f"SEIZES WORLD #1"
            ),
            (
                f"{new_number_one['name']} has overtaken "
                f"{old_number_one['name']} for the top spot "
                f"in the international Global rankings."
            ),
            "leaderboard"
        )

    else:

        news_screen.add_career_news(
            (
                f"{new_number_one['name'].upper()} "
                f"RETAINS WORLD #1"
            ),
            (
                f"{new_number_one['name']} remains atop "
                f"the international rankings with a rating "
                f"of {new_number_one['rating']:,}."
            ),
            "leaderboard"
        )

    # ==================================================
    # Biggest climber
    # ==================================================

    biggest_riser = None
    biggest_rise = 0

    for entry in after:

        npc_id = entry[
            "id"
        ]

        if (
            npc_id
            not in before_rank
        ):
            continue

        movement = (
            before_rank[
                npc_id
            ]
            - after_rank[
                npc_id
            ]
        )

        if movement > biggest_rise:

            biggest_rise = (
                movement
            )

            biggest_riser = (
                entry
            )

    if (
        biggest_riser is not None
        and biggest_rise >= 2
    ):

        news_screen.add_career_news(
            (
                f"{biggest_riser['name'].upper()} "
                f"SURGES UP RANKINGS"
            ),
            (
                f"{biggest_riser['name']} climbed "
                f"{biggest_rise} places this month "
                f"and now sits at world "
                f"#{after_rank[biggest_riser['id']]}."
            ),
            "leaderboard"
        )

    # ==================================================
    # Biggest fall
    # ==================================================

    biggest_faller = None
    biggest_fall = 0

    for entry in after:

        npc_id = entry[
            "id"
        ]

        if (
            npc_id
            not in before_rank
        ):
            continue

        movement = (
            after_rank[
                npc_id
            ]
            - before_rank[
                npc_id
            ]
        )

        if movement > biggest_fall:

            biggest_fall = (
                movement
            )

            biggest_faller = (
                entry
            )

    if (
        biggest_faller is not None
        and biggest_fall >= 2
    ):

        news_screen.add_career_news(
            (
                f"ROUGH MONTH FOR "
                f"{biggest_faller['name'].upper()}"
            ),
            (
                f"{biggest_faller['name']} fell "
                f"{biggest_fall} places in the international "
                f"rankings and now sits at world "
                f"#{after_rank[biggest_faller['id']]}."
            ),
            "leaderboard"
        )

def sync_career_npc_runtime_state():
    """Migrate at the current date and restore this profile's complete roster."""
    if state.career_leaderboard_state:
        state.career_npc_world = ensure_career_world(
            state.career_npc_world, state.career_leaderboard_state, BASE_NPCS,
            state.career_year, state.career_month,
        )
    sync_npc_runtime_state(state.career_leaderboard_state, month=state.career_month)



def ensure_career_leaderboard():

    if not state.career_leaderboard_state:
        initialize_career_leaderboard()

        career_saving.auto_save_career()
    else:
        sync_career_npc_runtime_state()

def initialize_career_leaderboard():

    state.career_leaderboard_state = {}
    state.career_npc_world = {}
    sync_npc_runtime_state({})

    if not CAREER_LEADERBOARD_PLAYERS:
        return

    # ==================================================
    # Pick this career's superstar
    # ==================================================

    elite_candidates = [
        npc
        for npc in CAREER_LEADERBOARD_PLAYERS
        if npc.get(
            "skill_tier"
        ) == "elite"
    ]

    if elite_candidates:
        star = random.choice(
            elite_candidates
        )

    else:
        star = random.choice(
            CAREER_LEADERBOARD_PLAYERS
        )

    state.career_leaderboard_star_id = (
        star.get(
            "id"
        )
    )

    # ==================================================
    # Rating ranges
    # ==================================================

    rating_ranges = {
        "elite":
            (
                2150,
                2800
            ),

        "strong":
            (
                1650,
                2200
            ),

        "mid":
            (
                1150,
                1750
            ),

        "low":
            (
                750,
                1300
            ),
    }

    # ==================================================
    # Generate everybody
    # ==================================================

    for npc in CAREER_LEADERBOARD_PLAYERS:

        npc_id = npc.get(
            "id"
        )

        if npc_id is None:
            continue

        tier = npc.get(
            "skill_tier",
            "mid"
        )

        minimum, maximum = (
            rating_ranges.get(
                tier,
                rating_ranges[
                    "mid"
                ]
            )
        )

        rating = random.randint(
            minimum,
            maximum
        )

        npc_state = {
            "rating": rating,
            "last_change": 0,
            "ratings": make_npc_rating_bundle(
                rating,
                tier
            ),
        }

        state.career_leaderboard_state[
            npc_id
        ] = ensure_npc_career_state(
            npc_state,
            npc
        )

    # ==================================================
    # Give one player a Magnus-style lead
    # ==================================================

    if (
        state.career_leaderboard_star_id
        in state.career_leaderboard_state
    ):

        other_ratings = [
            data.get(
                "rating",
                1000
            )
            for npc_id, data
            in state.career_leaderboard_state.items()
            if npc_id
            != state.career_leaderboard_star_id
        ]

        if other_ratings:

            second_best = max(
                other_ratings
            )

            star_rating = (
                second_best
                + random.randint(
                    175,
                    325
                )
            )

            star_state = state.career_leaderboard_state[
                state.career_leaderboard_star_id
            ]

            boost_npc_overall(star_state, star_rating)

    sync_career_npc_runtime_state()

def get_career_leaderboard(
        rating_key="overall"
):

    ensure_career_leaderboard()

    if rating_key not in RATING_KEYS:
        rating_key = "overall"

    leaderboard = []

    for npc in CAREER_LEADERBOARD_PLAYERS:

        npc_id = npc.get(
            "id"
        )

        npc_state = (
            state.career_leaderboard_state.get(
                npc_id,
                {}
            )
        )

        npc_state = ensure_npc_career_state(
            npc_state,
            npc
        )

        state.career_leaderboard_state[
            npc_id
        ] = npc_state

        ratings = npc_state.get(
            "ratings",
            {}
        )

        selected_rating = ratings.get(
            rating_key,
            npc_state.get(
                "rating",
                1000
            )
        )

        monthly_change = npc_state.get("last_changes", {}).get(rating_key, 0)

        leaderboard.append(
            {
                "id": npc_id,
                "name": npc.get(
                    "name",
                    "Unknown Player"
                ),
                "rating": selected_rating,
                "rating_key": rating_key,
                "rating_label": RATING_DISPLAY_NAMES.get(
                    rating_key,
                    "Global"
                ),
                "ratings": dict(ratings),
                "last_change": monthly_change,
                "bio": npc.get(
                    "bio",
                    "Professional card player."
                ),
                "country": npc.get(
                    "country",
                    "Unknown"
                ),
                "age": npc_state.get(
                    "age",
                    npc.get(
                        "age",
                        "Unknown"
                    )
                ),
                "birthday_month": npc_state.get(
                    "birthday_month"
                ),
                "hometown": npc.get(
                    "hometown",
                    "Unknown"
                ),
                "favorite_suit": npc.get(
                    "favorite_suit",
                    "Unknown"
                ),
                "game_personality": npc.get(
                    "game_personality",
                    "balanced"
                ),
                "career_stage": development_stage(npc_state, state.career_month),
                "is_prospect": bool(npc_state.get("prospect_record")),
                "is_prodigy": bool(npc_state.get("development", {}).get("prodigy")),
                "joined_month": npc_state.get("joined_month"),
                "fans": npc_state.get("fans", 0),
                "public_appeal": npc_state.get("public_appeal", "steady"),
                "npc": npc,
                "is_star": (
                    rating_key == "overall"
                    and npc_id
                    == state.career_leaderboard_star_id
                ),
                "is_player": False,
            }
        )

    player_rating = state.career_ratings.get(
        rating_key,
        state.career_rating
    )

    leaderboard.append(
        {
            "id": "player",
            "name": state.player_name,
            "rating": player_rating,
            "rating_key": rating_key,
            "rating_label": RATING_DISPLAY_NAMES.get(
                rating_key,
                "Global"
            ),
            "ratings": dict(state.career_ratings),
            "last_change": 0,
            "bio": state.profile_bio_text.strip() or "Current Career Mode player.",
            "country": state.profile_country_text.strip().upper()[:3],
            "age": state.profile_age_text.strip() or "Unknown",
            "birthday_month": None,
            "hometown": state.profile_hometown_text.strip() or "Unknown",
            "favorite_suit": state.profile_favorite_suit or "Unknown",
            "game_personality": "player",
            "fans": state.career_fans,
            "public_appeal": "player",
            "npc": None,
            "is_star": False,
            "is_player": True,
        }
    )

    leaderboard.sort(
        key=lambda item: item[
            "rating"
        ],
        reverse=True
    )

    for index, entry in enumerate(leaderboard):
        entry["is_star"] = rating_key == "overall" and index == 0
    return leaderboard


def get_player_leaderboard_rank(
        rating_key="overall"
):

    leaderboard = (
        get_career_leaderboard(
            rating_key=rating_key
        )
    )

    for index, entry in enumerate(
        leaderboard
    ):

        if entry.get(
            "is_player"
        ):
            return index + 1

    return None
