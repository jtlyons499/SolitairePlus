import random


# ==================================================
# CHAT FREQUENCY
# ==================================================

ACTION_CHAT_CHANCE = {
    "check": 0.12,
    "call": 0.20,
    "bet": 0.32,
    "raise": 0.52,
    "fold": 0.18,
    "all_in": 0.72,
}

PLAYER_REACTION_CHANCE = {
    "check": 0.06,
    "call": 0.10,
    "bet": 0.22,
    "raise": 0.35,
    "all_in": 0.52,
}


# ==================================================
# NPC ACTION CHAT
# ==================================================

NPC_ACTION_CHAT = {

    "timid": {

        "check": [
            "I'm fine with that.",
            "No need to get carried away.",
            "Let's keep this reasonable.",
            "I'll see another card.",
        ],

        "call": [
            "Okay... I'll stay in.",
            "That's enough for me.",
            "I'll take a look.",
            "Fine. I'm in.",
        ],

        "bet": [
            "I'll put a little something out there.",
            "Nothing crazy.",
            "Let's see what happens.",
            "Just testing the water.",
        ],

        "raise": [
            "I actually like this one.",
            "I'll go a little higher.",
            "Don't read too much into this.",
            "I think I can afford it.",
        ],

        "fold": [
            "Nope. I'm out.",
            "Too rich for me.",
            "You can have this one.",
            "I'm not chasing that.",
        ],

        "all_in": [
            "Well... I guess this is it.",
            "I really hope I'm right.",
            "Everything I've got.",
            "Regret.",
        ],
    },


    "opportunist": {

        "check": [
            "Nothing to see here.",
            "Go ahead.",
            "I'll wait.",
            "Your move.",
        ],

        "call": [
            "I'll pay to see it.",
            "Interesting.",
            "I'm still here.",
            "Let's keep going.",
        ],

        "bet": [
            "Time to make this interesting.",
            "Let's put some pressure on.",
            "I've seen enough.",
            "Now we're playing.",
        ],

        "raise": [
            "I think you missed something.",
            "Let's make it expensive.",
            "That's not enough.",
            "I'll raise.",
        ],

        "fold": [
            "Not worth it.",
            "I'll wait for a better spot.",
            "You got this one.",
            "Bad price. I'm out.",
        ],

        "all_in": [
            "This is the spot.",
            "All of it.",
            "Let's settle it.",
            "I don't need another decision.",
        ],
    },


    "aggressive": {

        "check": [
            "Don't get comfortable.",
            "Fine. Check.",
            "I'll give you one free card.",
            "For now.",
        ],

        "call": [
            "That's all?",
            "Easy call.",
            "I'm not going anywhere.",
            "Keep betting.",
        ],

        "bet": [
            "Let's go.",
            "Pay up.",
            "Make a decision.",
            "Here's something to think about.",
        ],

        "raise": [
            "Not enough.",
            "Let's really play.",
            "Raise.",
            "You wanted action.",
            "Now what?",
        ],

        "fold": [
            "Fine.",
            "Enjoy it.",
            "I'll get it back.",
            "Not this time.",
        ],

        "all_in": [
            "All in.",
            "Let's go!",
            "Everything.",
            "Who's got some cajones?",
        ],
    },


    "escalator": {

        "check": [
            "I'll let you decide.",
            "Go ahead...I dare you.",
            "Your turn to make it expensive!",
            "My favorite bird is a Checkadee!",
        ],

        "call": [
            "Turt for tart.",
            "I'll match it.",
            "You started this.",
            "Fine by me.",
        ],

        "bet": [
            "Let's start something.",
            "Your turn.",
            "Let's see how serious you are.",
            "A little pressure.",
        ],

        "raise": [
            "You wanted to bet?",
            "Let's raise the stakes.",
            "I'll see that and add some.",
            "You opened the door.",
            "Careful what you start.",
        ],

        "fold": [
            "Not following you there.",
            "That's enough.",
            "QQ.",
            "I'll pass.",
        ],

        "all_in": [
            "You wanted bigger. Here you go.",
            "Let's take this all the way.",
            "No half measures.",
            "Your move now.",
        ],
    },


    "unpredictable": {

        "check": [
            "Hmm.",
            "Check.",
            "Maybe.",
            "Nothing happening here.",
            "*raises spork*",
        ],

        "call": [
            "Sure, why not?",
            "Let's find out.",
            "I have a feeling.",
            "And away we go.",
        ],

        "bet": [
            "Let's do something weird.",
            "This feels right.",
            "I have a plan. Probably.",
            "Money goes here.",
        ],

        "raise": [
            "Time to suffer!",
            "Let's make this worse.",
            "I changed my mind.",
            "More.",
            "Well, that escalated quickly xD",
        ],

        "fold": [
            "Actually, never mind.",
            "I suddenly hate these cards.",
            "Abort.",
            "I've lost interest.",
        ],

        "all_in": [
            "YOLO.",
            "ALL of it.",
            "I have made a decision.",
            "Future me can deal with this.",
        ],
    },


    "balanced": {

        "check": [
            "Check check.",
            "I'll check.",
            "Let's see another.",
            "Checkbacca."
        ],

        "call": [
            "Call.",
            "I'll stay in.",
            "I'm good with that.",
        ],

        "bet": [
            "I'll bet.",
            "Let's put something out there.",
            "I'll lead.",
        ],

        "raise": [
            "Raise (da roof).",
            "I'll bump it up.",
            "Let's go higher.",
        ],

        "fold": [
            "Fold.",
            "I'm out.",
            "Not this one.",
        ],

        "all_in": [
            "All in.",
            "Everything I've got.",
            "Let's see it.",
        ],
    },
}


# ==================================================
# REACTIONS TO PLAYER
# ==================================================

PLAYER_REACTION_CHAT = {

    "timid": {

        "bet": [
            "That's a lot.",
            "You're making this difficult.",
            "Do we really need to do this?",
        ],

        "raise": [
            "Again?",
            "That's getting expensive.",
            "I don't love that.",
        ],

        "all_in": [
            "Psychopath.",
            "Seriously?",
            "Annoying...",
        ],
    },


    "opportunist": {

        "bet": [
            "Interesting.",
            "Now we're getting somewhere.",
            "That's useful information.",
        ],

        "raise": [
            "Feeling confident?",
            "I was hoping you'd do that.",
            "Okay. Interesting.",
        ],

        "all_in": [
            "That's a decision.",
            "Let's see if you mean it.",
            "Now this is interesting.",
        ],
    },


    "aggressive": {

        "bet": [
            "That's it?",
            "Come on.",
            "Keep going.",
        ],

        "raise": [
            "Finally.",
            "Tilted???",
            "You sure about that?",
        ],

        "all_in": [
            "Let's go!",
            "That's more like it.",
            "Hurt me more.",
        ],
    },


    "escalator": {

        "bet": [
            "Oh, we're betting now?",
            "You sure you want to start this?",
            "Interesting choice.",
        ],

        "raise": [
            "Keep pushing.",
            "Careful.",
            "You know I'm coming with you.",
        ],

        "all_in": [
            "Fight me like Gandalf and the Balrog.",
            "Fine, fiend.",
            "You started it.",
        ],
    },


    "unpredictable": {

        "bet": [
            "Bold.",
            "I like numbers.",
            "Interesting development.",
        ],

        "raise": [
            "Exciting.",
            "Ooooh.",
            "Things are happening.",
        ],

        "all_in": [
            "Tasty decision...",
            "Excellent chaos.",
            "Now we're talking.",
        ],
    },


    "balanced": {

        "bet": [
            "Okay.",
            "Hmmm.",
        ],

        "raise": [
            "That's a raise.",
            "All right.",
        ],

        "all_in": [
            "All in, nerds.",
            "Big move.",
        ],
    },
}


# ==================================================
# HELPERS
# ==================================================

def get_personality(
        holdem_game,
        npc_index
):

    if not (
            0
            <= npc_index
            < len(holdem_game.npcs)
    ):
        return "balanced"

    personality = str(
        holdem_game.npcs[
            npc_index
        ].get(
            "game_personality",
            "balanced"
        )
    ).strip().lower()

    if personality not in NPC_ACTION_CHAT:

        return "balanced"

    return personality


def get_npc_name(
        holdem_game,
        npc_index
):

    if not (
            0
            <= npc_index
            < len(holdem_game.npcs)
    ):
        return "Opponent"

    return (
        holdem_game.npcs[
            npc_index
        ].get(
            "name",
            "Opponent"
        )
    )


def get_action_type(
        holdem_game,
        npc_index
):

    if not (
            0
            <= npc_index
            < len(holdem_game.npc_action_texts)
    ):
        return None

    action_text = (
        holdem_game.npc_action_texts[
            npc_index
        ].strip().lower()
    )

    # All-in takes priority over the visible
    # Bet / Call / Raise wording.
    if (
            npc_index
            < len(holdem_game.npc_all_in)
            and holdem_game.npc_all_in[
                npc_index
            ]
    ):

        if action_text.startswith(
                (
                    "called",
                    "bet",
                    "raised",
                )
        ):
            return "all_in"

    if action_text.startswith("checked"):
        return "check"

    if action_text.startswith("called"):
        return "call"

    if action_text.startswith("bet"):
        return "bet"

    if action_text.startswith("raised"):
        return "raise"

    if action_text.startswith("folded"):
        return "fold"

    return None


# ==================================================
# CHAT AFTER AN NPC ACTION
# ==================================================

def generate_npc_action_chat(
        holdem_game,
        npc_index
):

    action_type = (
        get_action_type(
            holdem_game,
            npc_index
        )
    )

    if action_type is None:
        return None

    chance = (
        ACTION_CHAT_CHANCE.get(
            action_type,
            0.15
        )
    )

    personality = (
        get_personality(
            holdem_game,
            npc_index
        )
    )

    # Unpredictable characters talk a little more.
    if personality == "unpredictable":
        chance += 0.08

    if random.random() > chance:
        return None

    phrases = (
        NPC_ACTION_CHAT[
            personality
        ].get(
            action_type,
            []
        )
    )

    if not phrases:
        return None

    return (
        get_npc_name(
            holdem_game,
            npc_index
        ),
        random.choice(
            phrases
        )
    )


# ==================================================
# REACTION TO A PLAYER ACTION
# ==================================================

def generate_player_action_reaction(
        holdem_game,
        action_type
):

    if (
            holdem_game.player_all_in
            and action_type in (
                "bet",
                "raise",
                "call",
            )
    ):
        action_type = "all_in"

    chance = (
        PLAYER_REACTION_CHANCE.get(
            action_type,
            0.0
        )
    )

    if random.random() > chance:
        return None

    possible_npcs = []

    for npc_index in range(
            len(holdem_game.npcs)
    ):

        if (
                holdem_game.npc_busted[
                    npc_index
                ]
                or holdem_game.npc_folded[
                    npc_index
                ]
        ):
            continue

        possible_npcs.append(
            npc_index
        )

    if not possible_npcs:
        return None

    npc_index = random.choice(
        possible_npcs
    )

    personality = (
        get_personality(
            holdem_game,
            npc_index
        )
    )

    phrases = (
        PLAYER_REACTION_CHAT[
            personality
        ].get(
            action_type,
            []
        )
    )

    if not phrases:
        return None

    return (
        get_npc_name(
            holdem_game,
            npc_index
        ),
        random.choice(
            phrases
        )
    )

# ==================================================
# SHOWDOWN / KNOCKOUT CHAT
# ==================================================

SHOWDOWN_CHAT = {

    "timid": {

        "win": [
            "Oh. I actually won that.",
            "That went better than expected.",
            "I'll take it.",
        ],

        "loss": [
            "Yeah, I had a bad feeling.",
            "I should have gotten out earlier.",
            "Suspicious loss...",
        ],

        "split": [
            "I'll take half.",
            "Could have been worse.",
            "Fair enough.",
        ],

        "bust": [
            "And that's me done.",
            "I knew this was getting expensive.",
            "Well... good game.",
        ],
    },


    "opportunist": {

        "win": [
            "ezpz sorry 4 the L",
            "Patience pays.",
            "Exactly what I wanted.",
        ],

        "loss": [
            "Wrong spot.",
            "I thought I had you.",
            "That didn't work.",
        ],

        "split": [
            "Fine. We'll divide it.",
            "A draw will do.",
            "Nobody gets all of it.",
        ],

        "bust": [
            "Picked the wrong moment.",
            "That's the end of my run.",
            "I got robbed.",
        ],
    },


    "aggressive": {

        "win": [
            "It pays to be assertive.",
            "Keep the chips coming.",
            "Beautiful.",
        ],

        "loss": [
            "Lucky.",
            "I'll get it back.",
            "That one got away.",
        ],

        "split": [
            "I wanted the whole thing.",
            "Half isn't enough.",
            "Fine. Split it.",
        ],

        "bust": [
            "That's poker.",
            "I went down fighting.",
            "Fine. I'm done.",
            "GGWP",
            "See u l8r"
        ],
    },


    "escalator": {

        "win": [
            "Get destroyed lol.",
            "That's what happens.",
            "Worth the escalation.",
        ],

        "loss": [
            "Okay, you got me.",
            "Maybe I pushed that one too far.",
            "That got expensive.",
        ],

        "split": [
            "All that for half?",
            "Fine. Take your share.",
            "King Solomon, split it up pls.",
        ],

        "bust": [
            "Rip gg.",
            "That's the last raise from me.",
            "You finally got me.",
        ],
    },


    "unpredictable": {

        "win": [
            "Well, that just happened! (laugh track)",
            "free <3",
            "Nobody saw it coming 8)",
        ],

        "loss": [
            "ugh rip.",
            "Interesting.",
            "i done imploded.",
        ],

        "split": [
            "Shared custody of the pot.",
            "Everybody wins. Sort of.",
            "How diplomatic.",
        ],

        "bust": [
            "I regret nothing.",
            "And now I vanish.",
            "That concludes the experiment.",
        ],
    },


    "balanced": {

        "win": [
            "Coolio.",
            "I'll take it.",
        ],

        "loss": [
            "Nice hand.",
            "You got me there.",
        ],

        "split": [
            "Boring.",
            "Fair enough.",
        ],

        "bust": [
            "Good game.",
            "That's it for me.",
        ],
    },
}


def get_showdown_phrase(
        holdem_game,
        npc_index,
        reaction_type
):

    personality = (
        get_personality(
            holdem_game,
            npc_index
        )
    )

    phrases = (
        SHOWDOWN_CHAT.get(
            personality,
            SHOWDOWN_CHAT[
                "balanced"
            ]
        ).get(
            reaction_type,
            []
        )
    )

    if not phrases:
        return None

    return random.choice(
        phrases
    )


def generate_showdown_chat(
        holdem_game
):

    messages = []

    newly_busted = set(
        holdem_game.last_hand_busted_indexes
    )

    # ==================================================
    # BUSTED NPCS ALWAYS GET A FINAL LINE
    # ==================================================

    busted_npc_indexes = []

    for player_index in newly_busted:

        if player_index <= 0:
            continue

        npc_index = (
            player_index - 1
        )

        if not (
                0
                <= npc_index
                < len(holdem_game.npcs)
        ):
            continue

        phrase = (
            get_showdown_phrase(
                holdem_game,
                npc_index,
                "bust"
            )
        )

        if phrase:

            messages.append(
                (
                    get_npc_name(
                        holdem_game,
                        npc_index
                    ),
                    phrase
                )
            )

            busted_npc_indexes.append(
                npc_index
            )

    # ==================================================
    # NORMAL SHOWDOWN REACTION
    #
    # Only one extra NPC talks so the table doesn't
    # become a wall of dialogue every hand.
    # ==================================================

    if holdem_game.table_is_over():

        return messages

    winner_indexes = list(
        holdem_game.winner_indexes
    )

    # ------------------------------------------
    # Player won at least part of the pot
    # ------------------------------------------

    if 0 in winner_indexes:

        # True split pot
        if len(winner_indexes) > 1:

            npc_winners = [
                player_index - 1
                for player_index
                in winner_indexes
                if player_index > 0
            ]

            if npc_winners:

                npc_index = random.choice(
                    npc_winners
                )

                phrase = (
                    get_showdown_phrase(
                        holdem_game,
                        npc_index,
                        "split"
                    )
                )

                if phrase:

                    messages.append(
                        (
                            get_npc_name(
                                holdem_game,
                                npc_index
                            ),
                            phrase
                        )
                    )

        # Player won without an NPC co-winner.
        else:

            possible_losers = []

            for npc_index in range(
                    len(holdem_game.npcs)
            ):

                if npc_index in busted_npc_indexes:
                    continue

                if holdem_game.npc_busted[
                        npc_index
                ]:
                    continue

                possible_losers.append(
                    npc_index
                )

            if (
                    possible_losers
                    and random.random() < 0.60
            ):

                npc_index = random.choice(
                    possible_losers
                )

                phrase = (
                    get_showdown_phrase(
                        holdem_game,
                        npc_index,
                        "loss"
                    )
                )

                if phrase:

                    messages.append(
                        (
                            get_npc_name(
                                holdem_game,
                                npc_index
                            ),
                            phrase
                        )
                    )

    # ------------------------------------------
    # NPC won
    # ------------------------------------------

    else:

        npc_winners = [
            player_index - 1
            for player_index
            in winner_indexes
            if player_index > 0
        ]

        npc_winners = [
            npc_index
            for npc_index
            in npc_winners
            if (
                0
                <= npc_index
                < len(holdem_game.npcs)
                and not holdem_game.npc_busted[
                    npc_index
                ]
            )
        ]

        if npc_winners:

            npc_index = random.choice(
                npc_winners
            )

            reaction_type = (
                "split"
                if len(winner_indexes) > 1
                else "win"
            )

            phrase = (
                get_showdown_phrase(
                    holdem_game,
                    npc_index,
                    reaction_type
                )
            )

            if phrase:

                messages.append(
                    (
                        get_npc_name(
                            holdem_game,
                            npc_index
                        ),
                        phrase
                    )
                )

    return messages