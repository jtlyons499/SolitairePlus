# Make the case simulator your own

Extract this batch over the previous Case Opening batch. It contains changed/new files only. Back up saves first. Keep the existing felt PNGs from the prior batch.

## The file you edit
`data/case_opening.json` controls cases, items, artwork and rewards. Open it in PyCharm. JSON requires double quotes, commas between entries, and no trailing commas or comments. Restart the game after editing it. Invalid catalogs stop startup with an error identifying the offending case/item rather than silently changing your odds.

Keep internal IDs stable once players own items. Rename the `name` freely. Removing an item ID removes its saved inventory entry on the next normalization. Existing IDs and collections are preserved by this batch.

## Case example
Add a new entry inside the `cases` object, with a comma between it and the previous entry:

```json
"duck_box": {
  "name": "Duck Discovery",
  "image": "cases/duck_box.png",
  "minimum": 50,
  "fraction": 0.02,
  "rating_points": 12,
  "weights": {"junk": 70, "trophy": 30},
  "pool": ["rubber_duck", "golden_shuffler"]
}
```

This costs the greater of $50 or 2% of current cash, rounded to the nearest dollar. The pool contains only the specified items. Each positive-weight category must have an eligible item in that pool. Category weights must total 100; categories may be omitted or given zero weight. Within a category, eligible items have equal chances. Earned trophies do not roll from cases.

Add the matching item below before running this example. There is no fixed case-count limit: the shop shows three cases per page in JSON order. Names are fitted to the case cards and buttons.

## Item example
Add inside the `items` object:

```json
"rubber_duck": {
  "name": "Suspicious Rubber Duck",
  "kind": "junk",
  "image": "items/rubber_duck.png"
}
```

Then include `rubber_duck` in whichever case pools should contain it. Adding an item does not automatically add it to the explicit pools shipped with this batch. If a case omits `pool`, all non-earned items are eligible.

Supported kinds: `junk`, `trophy`, `cash`, `fans`, `rating`, `cosmetic`. All pulls retain duplicate counts in the collection.

## Reward settings
Add these fields to the item object as appropriate:

| Kind | Fields | Behavior |
|---|---|---|
| junk / trophy | No amount fields | Collectible only |
| cash | `cash_multiplier`: 2.5 | Gross cash reward equals 2.5 times the price paid |
| cash | `cash_amount`: 750 | Fixed gross reward; overrides multiplier |
| fans | `fan_multiplier`: 2, `fan_minimum`: 5 | Reward is square root of paid price times multiplier, with minimum |
| fans | `fan_amount`: 25 | Fixed fan reward; overrides scaling |
| rating | `game`: "blackjack" | Selects the game rating; uses case `rating_points` |
| rating | `rating_points`: 15 | Item-specific points override the case amount |
| cosmetic | `felt_path`: "assets/case_opening/cosmetics/duck_felt.png" | Unlocks a felt in Customize |

Amounts round to whole numbers. Rating game IDs: `solitaire`, `texas_holdem`, `five_card_draw`, `seven_card_stud`, `blackjack`, `roulette`, `score_four`. Overall is derived from these ratings. Rating/fan caps still apply. Cash rewards are gross: the case cost is deducted first.

New cosmetics register automatically, with internal felt ID `f_case_<item_id>`. Supply the felt image before launching; it is loaded with the game's other felts. Other optional artwork can be missing and will use the existing drawn graphics. This batch supports felt cosmetics, not new avatar/shirt reward types.

## Your artwork
The JSON `image` paths are relative to `assets/case_opening/`, so `items/rubber_duck.png` means `assets/case_opening/items/rubber_duck.png`. You may rename image files independently of item IDs by editing `image`.

| Artwork | Recommended dimensions |
|---|---|
| Case picture | 600x420 transparent PNG |
| Item picture | 320x320 transparent PNG |
| `assets/case_opening/background.png` | 1920x1080 |
| `assets/case_opening/trophy_room/walls/<residence_id>.png` | 1920x1080 |
| `assets/case_opening/trophy_room/cabinet.png` | 1600x640 transparent PNG |
| Cosmetic `felt_path` | 1366x768 |

Draw the object only. The UI adds the name, category color, and quantity. Artwork reloads upon re-entering the room; catalog changes require restarting. Existing exact item paths remain listed in CASE_OPENING_GUIDE.md from the first batch.

## Earned trophies and limits
The existing `hundred_wins` and `table_champion` IDs remain linked to 100 Solitaire wins and the Table Clear achievement. Their names/artwork can change. `earned: true` excludes an item from random pulls; it does not create a new achievement trigger. New earned conditions, rare NPC pulls, and ranking trophies still require a future code batch.

Free Play uses temporary loot and money. Career purchases save before the reel, with rollback if saving fails. Cryptid remains unchanged and parked for its pacing/information/arena-effects pass.
