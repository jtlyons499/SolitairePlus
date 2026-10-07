"""Rating cosmetics and readable unlock requirements."""
THRESHOLDS = {'backgrounds': {'strategy': [1400, 1950, 2300], 'poker': [1300, 1750, 2500], 'casino': [1350, 1950, 2600], 'global': [1500, 2500]}, 'felts': {'strategy': [1150, 1600, 1800], 'poker': [1100, 1400, 2000], 'casino': [1450, 1600, 2600], 'global': [1300, 2000]}, 'titles': {'strategy': [1500, 1900, 2800], 'poker': [1300, 1600, 2400], 'casino': [1200, 1500, 2300], 'global': [1750, 3000]}}
# Keys remain stable so existing save selections and earned unlocks survive.
# Only the art filename and player-facing display name change.
RATING_ART = {'bg_rating_casino_1350': ('bg_snowlight.png', 'Snowlight'),
 'bg_rating_casino_1950': ('bg_roulette.png', 'Roulette'),
 'bg_rating_casino_2600': ('bg_myce.png', 'Myce'),
 'bg_rating_global_1500': ('bg_small_world.png', 'Small World'),
 'bg_rating_global_2500': ('bg_spinning.png', 'Spinning'),
 'bg_rating_poker_1300': ('bg_chips.png', 'Chips'),
 'bg_rating_poker_1750': ('bg_poker_shape.png', 'Poker Shapes'),
 'bg_rating_poker_2500': ('bg_poker_king.png', 'Poker King'),
 'bg_rating_strategy_1400': ('bg_stripes.png', 'Stripes'),
 'bg_rating_strategy_1950': ('bg_zoom.png', 'Zooming'),
 'bg_rating_strategy_2300': ('bg_consideration.png', 'Consideration'),
 'f_rating_casino_1450': ('f_le_green.png', 'Le Greene'),
 'f_rating_casino_1600': ('f_deep_dark.png', 'Deep Dark'),
 'f_rating_casino_2600': ('f_pink_triangle.png', 'Pink Weezer'),
 'f_rating_global_1300': ('f_globe.png', 'Globe'),
 'f_rating_global_2000': ('f_purple_haze.png', 'Purple Haze'),
 'f_rating_poker_1100': ('f_maze_1.png', 'Maze 1'),
 'f_rating_poker_1400': ('f_maze_2.png', 'Maze 2'),
 'f_rating_poker_2000': ('f_maze_3.png', 'Maze 3'),
 'f_rating_strategy_1150': ('f_pinkle.png', 'Pinkle'),
 'f_rating_strategy_1600': ('f_weak_purple.png', 'Weak Purp'),
 'f_rating_strategy_1800': ('f_green_rect.png', 'Green Rect'),
 't_rating_casino_1200': ('title_cha_ching.png', 'Cha-Ching'),
 't_rating_casino_1500': ('title_casi.png', 'Casi'),
 't_rating_casino_2300': ('title_casino_king.png', 'Casino King'),
 't_rating_global_1750': ('title_soli_soli.png', 'Soli Soli'),
 't_rating_global_3000': ('title_world_champion.png', 'World Champ'),
 't_rating_poker_1300': ('title_poke_poke.png', 'Poke x2'),
 't_rating_poker_1600': ('title_soli_chalked.png', 'Chalked'),
 't_rating_poker_2400': ('title_poker_1.png', 'Poker One'),
 't_rating_strategy_1500': ('title_strat_soli_1.png', 'Strat Soli 1'),
 't_rating_strategy_1900': ('title_strat_soli_2.png', 'Strat Soli 2'),
 't_rating_strategy_2800': ('title_strat_lord.png', 'Strat Lord')}

def add_rating_catalogs(backgrounds, felts, titles):
    for kind, catalog, prefix in (("backgrounds", backgrounds, "bg"), ("felts", felts, "f"), ("titles", titles, "t")):
        for category, thresholds in THRESHOLDS[kind].items():
            for index, threshold in enumerate(thresholds):
                key = f"{prefix}_rating_{category}_{threshold}"
                filename, name = RATING_ART[key]
                catalog[key] = {"name": name,
                                "path": f"assets/ui/menu_ui/{kind}/{filename}",
                                "rating_category": "overall" if category == "global" else category,
                                "rating_threshold": threshold, "order": 1000 + threshold}

def unlock_ratings(ratings, catalogs, unlocked_sets):
    for catalog, unlocked in zip(catalogs, unlocked_sets):
        for key, data in catalog.items():
            if data.get("rating_threshold") and float(ratings.get(data["rating_category"], 1000)) >= data["rating_threshold"]:
                unlocked.add(key)

def lock_reason(asset_id, data, kind, level_unlocks, achievements):
    threshold = data.get("rating_threshold")
    if threshold:
        labels = {"overall": "Global Rating", "strategy": "Strategy Rating", "poker": "Poker Rating", "casino": "Casino Rating"}
        return f"Reach {threshold:,} in {labels[data['rating_category']]}"
    for achievement in achievements:
        from achievements import iter_rewards
        expected = {"backgrounds": "background", "felts": "felt", "titles": "title"}.get(kind, kind)
        if any(reward.get("type") == expected and reward.get("id") == asset_id for reward in iter_rewards(achievement)):
            return "Get Achievement: " + achievement["title"]
    for level, rewards in sorted(level_unlocks.items()):
        if asset_id in rewards.get(kind, []):
            return f"Reach Level {level}"
    return data.get("unlock_description", "Unlock through achievements or play")


def rating_lock_progress(data, ratings):
    """Whole-point progress below a rating-gated cosmetic's requirement."""
    category = data.get('rating_category')
    if not data.get('rating_threshold') or category is None:
        return ''
    return f"Current: {round(float(ratings.get(category, 1000))):,} / {data['rating_threshold']:,}"
