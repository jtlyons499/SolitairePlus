"""Display names for jobs, homes and months (moved out of legacy.py)."""
from solitaireplus.app import paths
from solitaireplus.app import state


CAREER_MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


CAREER_RESIDENCE_NAMES = {
    "dingy_apartment":
        "Dingy Apartment",

    "hippie_commune":
        "Hippie Commune",

    "towers":
        "Tableau Towers",

    "summit":
        "Sorcerer's Summit",

    "heliyacht":
        "Heliyacht",

    "card_castle":
        "Card Castle",
}



CAREER_JOB_NAMES = {
    "custodian":
        "Custodian",

    "satellite_repair":
        "Satellite Repair",

    "videographer":
        "Videographer",

    "airline_pilot":
        "Airline Pilot",

    "spiritual_guru":
        "Spiritual Guru",

    "solitaire_pensioner":
        "Solitaire Pensioner",
}

CAREER_JOBS = {
    "custodian": {
        "name": "Custodian",
        "required_rating": 0,
        "pay": 75,
        "image":
            str(paths.asset("career/jobs/custodian.png")),
    },

    "satellite_repair": {
        "name": "Satellite Repair",
        "required_rating": 1200,
        "pay": 125,
        "image":
            str(paths.asset("career/jobs/satellite_repair.png")),
    },

    "videographer": {
        "name": "Videographer",
        "required_rating": 1500,
        "pay": 200,
        "image":
            str(paths.asset("career/jobs/videographer.png")),
    },

    "airline_pilot": {
        "name": "Airline Pilot",
        "required_rating": 1900,
        "pay": 300,
        "image":
            str(paths.asset("career/jobs/airline_pilot.png")),
    },

    "spiritual_guru": {
        "name": "Spiritual Guru",
        "required_rating": 2000,
        "pay": 450,
        "image":
            str(paths.asset("career/jobs/spiritual_guru.png")),
    },

    "solitaire_pensioner": {
        "name": "Solitaire Pensioner",
        "required_rating": 2500,
        "pay": 650,
        "image":
            str(paths.asset("career/jobs/solitaire_pensioner.png")),
    },
}

def get_career_residence_name():
    return (
        CAREER_RESIDENCE_NAMES.get(
            state.career_residence,
            state.career_residence
        )
    )


def get_career_job_name():
    return (
        CAREER_JOB_NAMES.get(
            state.career_job,
            state.career_job
        )
    )
