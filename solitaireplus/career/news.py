import random


CASUAL_GAME_NAMES = {
    "score_four": "Score-Four",
    "crazy_eights": "Crazy Eights",
    "bango": "Bango",
}

POKER_GAME_NAMES = {
    "texas_holdem": "Texas Hold'em",
    "five_card_draw": "Five-Card Draw",
    "seven_card_stud": "Seven-Card Stud",
}


def build_casual_cards_story(player_name, result_log):
    result_log = list(result_log or [])
    wins = [entry for entry in result_log if entry.get("won")]
    chosen = wins[-1] if wins else (result_log[-1] if result_log else None)

    if chosen is None:
        return (
            f"{player_name.upper()} SPOTTED AT CASUAL CARDS",
            f"{player_name} spent part of the week rotating through the casual card tables. Witnesses described the atmosphere as unusually competitive for something labeled casual.",
            "cards",
        )

    game_id = chosen.get("game_id")
    won = bool(chosen.get("won"))

    if game_id == "crazy_eights":
        if won:
            return random.choice((
                (
                    f"{player_name.upper()} EMPTIES HAND IN CRAZY EIGHTS WIN",
                    f"{player_name} closed out a Crazy Eights table after navigating a late run of wild-card suit changes.",
                    "cards",
                ),
                (
                    f"EIGHT IS ENOUGH FOR {player_name.upper()}",
                    f"A timely wild eight helped {player_name} finish first in a crowded Casual Cards match.",
                    "cards",
                ),
            ))
        return (
            f"CRAZY EIGHTS TABLE OUTLASTS {player_name.upper()}",
            f"{player_name} left the Crazy Eights table without the win after a stubborn draw pile refused to cooperate.",
            "cards",
        )

    if game_id == "bango":
        if won:
            return (
                f"{player_name.upper()} SHOUTS BANGO FIRST",
                f"Five exact calls fell into place for {player_name}, who covered the final card before the rest of the table.",
                "cards",
            )
        return (
            f"BANGO CALL GOES TO ANOTHER TABLE",
            f"{player_name} came up short in Bango as another player covered all five cards first.",
            "cards",
        )

    game_name = CASUAL_GAME_NAMES.get(game_id, "Casual Cards")
    return (
        f"{player_name.upper()} TAKES ON {game_name.upper()}",
        f"{player_name} logged another appearance in {game_name} during Casual Cards week.",
        "cards",
    )


def build_poker_story(player_name, session_nets):
    sessions = [
        (game_id, int(net))
        for game_id, net in (session_nets or {}).items()
        if int(net or 0) != 0
    ]

    if not sessions:
        return (
            f"{player_name.upper()} SITS IN FOR POKER NIGHT",
            f"{player_name} logged time at the Poker Night tables without a major swing in either direction.",
            "poker",
        )

    game_id, net = max(sessions, key=lambda item: abs(item[1]))
    game_name = POKER_GAME_NAMES.get(game_id, "Poker")

    if net > 0:
        return (
            f"{player_name.upper()} LEAVES {game_name.upper()} UP ${net:,}",
            f"The biggest swing of the night came in {game_name}, where {player_name} finished the session ${net:,} ahead.",
            "poker",
        )

    return (
        f"{game_name.upper()} COSTS {player_name.upper()} ${abs(net):,}",
        f"{player_name} absorbed a ${abs(net):,} loss in {game_name} during the latest Poker Night appearance.",
        "poker",
    )


def build_casino_story(
        player_name,
        blackjack_net=0,
        roulette_net=0,
        horse_races_net=0
):
    blackjack_net = int(blackjack_net or 0)
    roulette_net = int(roulette_net or 0)
    horse_races_net = int(horse_races_net or 0)
    results = {
        "Blackjack": blackjack_net,
        "Roulette": roulette_net,
        "Horse Races": horse_races_net,
    }
    combined = sum(results.values())

    if combined > 0:
        detail, detail_net = max(
            results.items(),
            key=lambda item: item[1],
        )
        return (
            f"{player_name.upper()} FINISHES CASINO NIGHT UP ${combined:,}",
            f"A profitable {detail} session helped {player_name} leave Casino Night ${combined:,} ahead overall.",
            "casino",
        )

    if combined < 0:
        worst_game, worst_net = min(
            results.items(),
            key=lambda item: item[1],
        )
        return (
            f"CASINO NIGHT TAKES ${abs(combined):,} FROM {player_name.upper()}",
            f"The largest setback came at {worst_game}, and {player_name} finished Casino Night ${abs(combined):,} in the red overall.",
            "casino",
        )

    return (
        f"{player_name.upper()} ESCAPES CASINO NIGHT EVEN",
        f"After Blackjack, Roulette, and the races were settled, {player_name} left Casino Night almost exactly where the evening began.",
        "casino",
    )


def build_monthly_flavor_story(npc_names=None):
    npc_names = [name for name in (npc_names or []) if name]
    npc = random.choice(npc_names) if npc_names else "an unnamed competitor"

    stories = (
        (
            "CARD ROOM GRANDFATHER CLOCK RUNS BACKWARD",
            "Card players recently noticed the room's grandfather clock was running backwards mere days after the room was used for a seance.",
            "strange",
        ),
        (
            "MYSTERY FIFTH SUIT DESCRIBED IN ANCIENT TOME",
            "A local solitaire historian at Arlen Community College came across an ancient book that described the mysterious Swords suit.",
            "strange",
        ),
        (
            "ROULETTE WHEEL SPINS FOREVER!",
            "Casino staff were bemused and even afraid last night as a roulette wheel spun for over an hour. Ghost of Roulette Past suspected.",
            "strange",
        ),
        (
            "LOCAL CASINO DEALER KEEPS DRAWING JOKERS",
            "Journalists around the world agree his misfortune is a good source of clicks.",
            "strange",
        ),
        (
            "SOLITAIRE TABLE SHAPED FLYING OBJECT SPOTTED",
            "Two dozen residents of Las Clubes insist they saw a flying and glowing solitaire card table.",
            "oddity",
        ),
        (
            "LOCAL GRANDMOTHER ARRESTED FOR CARD COUNTING",
            "Merriam Winkle was taken into custody after card counting and reeking of Vicks Nose Drops, ew.",
            "oddity",
        ),
        (
            f"{npc.upper()} REPORTEDLY PRACTICES CRAZY EIGHTS WITH EIGHT DECKS",
            f"Sources say {npc} insists the method improves skill, despite current scientific theories. Joe Rogan has organized a GoFundMe.",
            "players",
        ),
        (
            f"{npc.upper()} BUYS 300 NEW DECKS OF CARDS",
            f"{npc} insists that new decks improves performance, likening the move to buying a new CSGO skin.",
            "players",
        ),
        (
            "TOURNAMENT VENDING MACHINE ENTERS POWER RANKINGS BY MISTAKE",
            "A data-entry error briefly placed a snack machine at #43. Administrators removed it, despite Deep Blue's protests.",
            "oddity",
        ),
        (
            "MAN IN GREEN SUIT? OR GREEN MAN FROM SPACE?!",
            "Security footage caught a green humanoid figure at the casino. When staff asked for ID, he gleegl'd loudly and ran out.",
            "strange",
        ),
    )

    return random.choice(stories)


def build_niche_story(player_name, result_log):
    """Build a news item for Niche Game Night results."""
    result_log = list(result_log or [])
    niche_entries = [
        entry for entry in result_log
        if entry.get("game_id") in {
            "faro",
            "five_o_poker",
            "blind_mans_bluff",
        }
    ]

    if not niche_entries:
        return (
            f"{player_name.upper()} VISITS NICHE GAME NIGHT",
            f"{player_name} spent the evening among some of the card world's less familiar tables.",
            "cards",
        )

    # Prefer a winning result for the headline; otherwise use the most recent
    # niche table the player actually completed.
    winning_entries = [entry for entry in niche_entries if entry.get("won")]
    entry = winning_entries[-1] if winning_entries else niche_entries[-1]
    game_id = entry.get("game_id")
    net = int(entry.get("net", 0) or 0)

    if game_id == "five_o_poker":
        five_o_wins = int(entry.get("five_o_wins", 0) or 0)
        if five_o_wins > 0:
            return (
                f"{player_name.upper()} SCORES A FIVE-O SWEEP",
                f"{player_name} won all five corresponding poker hands in the same deal, the signature Five-O result, during Niche Game Night.",
                "cards",
            )
        if net > 0:
            return (
                f"{player_name.upper()} WINS FIVE-O POKER SESSION",
                f"Five simultaneous poker hands paid off for {player_name}, who left the heads-up Five-O table ${net:,} ahead.",
                "cards",
            )
        if net < 0:
            return (
                f"FIVE-O POKER COSTS {player_name.upper()} ${abs(net):,}",
                f"The five-column poker board turned against {player_name}, who finished the Five-O session ${abs(net):,} down.",
                "cards",
            )
        return (
            f"{player_name.upper()} SPLITS FIVE-O POKER SESSION",
            f"After building five poker hands at once, {player_name} left the Five-O table exactly even.",
            "cards",
        )

    if game_id == "blind_mans_bluff":
        if net > 0:
            return (
                f"{player_name.upper()} PROFITS WITHOUT SEEING OWN CARD",
                f"{player_name} finished Blind Man's Bluff ${net:,} ahead while making every betting decision from the cards on everyone else's forehead.",
                "cards",
            )
        if net < 0:
            return (
                f"BLIND MAN'S BLUFF TAKES ${abs(net):,} FROM {player_name.upper()}",
                f"Reading the table proved difficult for {player_name}, who left the forehead-poker game ${abs(net):,} down.",
                "cards",
            )
        return (
            f"{player_name.upper()} BREAKS EVEN IN BLIND MAN'S BLUFF",
            f"A full session of betting on an unseen card ended with {player_name} exactly even.",
            "cards",
        )

    # Faro
    if net > 0:
        return (
            f"{player_name.upper()} BEATS THE FARO BANK FOR ${net:,}",
            f"A profitable Faro shoe left {player_name} ${net:,} ahead by the time the case card appeared.",
            "cards",
        )

    if net < 0:
        return (
            f"FARO BANK TAKES ${abs(net):,} FROM {player_name.upper()}",
            f"Banker cards and a stubborn shoe left {player_name} down ${abs(net):,} at Niche Game Night.",
            "cards",
        )

    return (
        f"{player_name.upper()} BREAKS EVEN AT FARO",
        f"After a full stretch of banker and player cards, {player_name} left the Faro table exactly even.",
        "cards",
    )


def build_arcade_story(player_name, result_log):
    """Build a Career news item for Arcade Night."""
    result_log = list(result_log or [])
    arcade_entries = [
        entry for entry in result_log
        if entry.get("game_id") in {"king_pong", "battle_bosses", "ace_invaders", "suit_snake", "prize_counter"}
    ]

    if not arcade_entries:
        return (
            f"{player_name.upper()} VISITS ARCADE NIGHT",
            f"{player_name} spent the evening feeding tokens into the local arcade machines.",
            "arcade",
        )

    suit_entries = [entry for entry in arcade_entries if entry.get("game_id") == "suit_snake"]
    if suit_entries:
        entry = suit_entries[-1]
        tickets = int(entry.get("tickets", 0) or 0)
        score = int(entry.get("score", 0) or 0)
        cards = int(entry.get("cards_collected", 0) or 0)
        decks = int(entry.get("decks_completed", 0) or 0)
        if decks > 0:
            return (
                f"{player_name.upper()} RUNS THE DECK IN SUIT SNAKE",
                f"{player_name} completed {decks} full deck{'s' if decks != 1 else ''}, scored {score:,} points, and cashed out {tickets:,} arcade tickets.",
                "arcade",
            )
        return (
            f"{player_name.upper()} BUILDS A {cards}-CARD SUIT SNAKE",
            f"A Suit Snake run reached {cards} collected cards and {score:,} points, earning {player_name} {tickets:,} arcade tickets.",
            "arcade",
        )

    ace_entries = [entry for entry in arcade_entries if entry.get("game_id") == "ace_invaders"]
    if ace_entries:
        entry = ace_entries[-1]
        tickets = int(entry.get("tickets", 0) or 0)
        score = int(entry.get("score", 0) or 0)
        high_score = int(entry.get("high_score", score) or score)
        waves = int(entry.get("waves_cleared", 0) or 0)
        reached_wave = max(1, waves + 1)
        if score >= high_score and score > 0:
            return (
                f"{player_name.upper()} POSTS ACE INVADERS HIGH SCORE",
                f"An endless Ace Invaders run carried {player_name} to wave {reached_wave} and {score:,} points, good for {tickets:,} arcade tickets.",
                "arcade",
            )
        return (
            f"ACE INVADERS END {player_name.upper()}'S RUN",
            f"{player_name} reached wave {reached_wave} and scored {score:,} points before the Aces broke through, earning {tickets:,} tickets.",
            "arcade",
        )

    battle_entries = [entry for entry in arcade_entries if entry.get("game_id") == "battle_bosses"]
    if battle_entries:
        entry = battle_entries[-1]
        tickets = int(entry.get("tickets", 0) or 0)
        rivals = int(entry.get("rivals_eliminated", 0) or 0)
        if entry.get("won"):
            return (
                f"{player_name.upper()} CLEARS THE BATTLE BOSSES ARENA",
                f"{player_name} knocked out all three rival forts in Battle Bosses and collected {tickets:,} arcade tickets.",
                "arcade",
            )
        return (
            f"BATTLE BOSSES HOLD OFF {player_name.upper()}",
            f"{player_name} eliminated {rivals} rival fort{'s' if rivals != 1 else ''} before falling in Battle Bosses, earning {tickets:,} tickets.",
            "arcade",
        )

    king_pong_entries = [entry for entry in arcade_entries if entry.get("game_id") == "king_pong"]
    if king_pong_entries:
        entry = king_pong_entries[-1]
        tickets = int(entry.get("tickets", 0) or 0)
        player_score = int(entry.get("player_score", 0) or 0)
        opponent_score = int(entry.get("opponent_score", 0) or 0)
        if entry.get("won"):
            return (
                f"{player_name.upper()} RULES THE KING PONG CABINET",
                f"{player_name} beat an arcade rival {player_score}-{opponent_score} in King Pong and walked away with {tickets:,} tickets.",
                "arcade",
            )
        return (
            f"KING PONG STALLS {player_name.upper()} AT THE ARCADE",
            f"{player_name} dropped a King Pong match {player_score}-{opponent_score}, but still claimed {tickets:,} tickets at Arcade Night.",
            "arcade",
        )

    return (
        f"{player_name.upper()} CASHES IN TICKETS AT THE PRIZE COUNTER",
        f"Arcade Night ended with {player_name} cashing tickets in at the prize counter after a long run on the machines.",
        "arcade",
    )



def build_head_to_head_story(player_name, opponent_name, won, elapsed_text=None):
    """Build a Career news item for the timed Klondike head-to-head event."""
    player_name = str(player_name or "Player")
    opponent_name = str(opponent_name or "an opponent")
    elapsed_suffix = f" in {elapsed_text}" if elapsed_text else ""

    if won:
        return (
            f"{player_name.upper()} WINS HEAD-TO-HEAD SOLITAIRE RACE",
            f"{player_name} beat {opponent_name} to the final foundation card{elapsed_suffix} in a direct Klondike race.",
            "competition",
        )

    return (
        f"{opponent_name.upper()} EDGES {player_name.upper()} IN KLONDIKE RACE",
        f"{opponent_name} reached 52 foundation cards before {player_name}{elapsed_suffix} in the latest Head-to-Head event.",
        "competition",
    )
