"""Rating rewards for the training games (shared by several game screens; moved out of legacy.py)."""


TRAINING_RATING_REWARDS = {

    "card_bingo": {
        "loss": 20,
        "win": 35,
    },

    "trash": {
        "loss": 20,
        "win": 35,
    },

    "score_four": {
        "complete": 60,
    },

    "crazy_eights": {
        "loss": 45,
        "win": 60,
    },

    "cassino": {
        "loss": 60,
        "win": 80,
    },

    "piquet": {
        "loss": 90,
        "win": 100,
    },

    "blackjack": {
        0: 10,
        1: 25,
        2: 35,
        3: 45,
    },
    "faro": {
        "bad_session": 25,
        "break_even": 40,
        "profit": 55,
        "strong_profit": 70,
    },
    "five_o_poker": {
        "loss": 25,
        "break_even": 40,
        "profit": 70,
        "five_o": 95,
    },
    "blind_mans_bluff": {
        "loss": 20,
        "break_even": 35,
        "profit": 60,
    },
}
