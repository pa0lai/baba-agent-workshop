CHALLENGE_LEVELS = [
    {
        "level": "goto_win",
        "task": "env/goto_win",
        "seed": 0,
        "max_steps": 30,
        "description": "Basic navigation",
    },
    {
        "level": "goto_win-distr_obj_rule",
        "task": "env/goto_win-distr_obj_rule",
        "seed": 11,
        "max_steps": 40,
        "description": "Ignore distractions",
    },
    {
        "level": "two_room-goto_win",
        "task": "env/two_room-goto_win",
        "seed": 2,
        "max_steps": 55,
        "description": "Plan across rooms",
    },
    {
        "level": "two_room-goto_win-distr_win_rule",
        "task": "env/two_room-goto_win-distr_win_rule",
        "seed": 13,
        "max_steps": 65,
        "description": "Cross rooms with a false rule",
    },
    {
        "level": "make_win",
        "task": "env/make_win",
        "seed": 1,
        "max_steps": 45,
        "description": "Create a WIN rule",
    },
    {
        "level": "make_win-distr_rule",
        "task": "env/make_win-distr_rule",
        "seed": 12,
        "max_steps": 55,
        "description": "Create WIN with distractions",
    },
    {
        "level": "two_room-break_stop-goto_win",
        "task": "env/two_room-break_stop-goto_win",
        "seed": 14,
        "max_steps": 75,
        "description": "Break a STOP rule",
    },
    {
        "level": "two_room-break_stop-make_win",
        "task": "env/two_room-break_stop-make_win",
        "seed": 15,
        "max_steps": 90,
        "description": "Combined rule puzzle",
    },
    {
        "level": "two_room-make_you-make_win",
        "task": "env/two_room-make_you-make_win",
        "seed": 16,
        "max_steps": 120,
        "description": "Create YOU, then create WIN",
        "bonus": True,
    },
    {
        "level": "two_room-make_wall_win",
        "task": "env/two_room-make_wall_win",
        "seed": 17,
        "max_steps": 120,
        "description": "Turn a blocking wall into WIN",
        "bonus": True,
    },
]

LEVEL_BY_NAME = {item["level"]: item for item in CHALLENGE_LEVELS}
CORE_LEVELS = [item for item in CHALLENGE_LEVELS if not item.get("bonus")]
BONUS_LEVELS = [item for item in CHALLENGE_LEVELS if item.get("bonus")]

PUBLIC_SUITE = [
    LEVEL_BY_NAME["goto_win"],
    LEVEL_BY_NAME["make_win"],
    LEVEL_BY_NAME["two_room-goto_win"],
]

# Classroom-hidden, not security-hidden. The instructor can replace these
# immediately before the event or distribute a separate manifest.
FINAL_SUITE = [
    LEVEL_BY_NAME["goto_win-distr_obj_rule"],
    LEVEL_BY_NAME["make_win-distr_rule"],
    LEVEL_BY_NAME["two_room-goto_win-distr_win_rule"],
    LEVEL_BY_NAME["two_room-break_stop-goto_win"],
    LEVEL_BY_NAME["two_room-break_stop-make_win"],
    *BONUS_LEVELS,
]

ALL_SUITE = [*PUBLIC_SUITE, *FINAL_SUITE]

SUITES = {
    "public": PUBLIC_SUITE,
    "final": FINAL_SUITE,
    "all": ALL_SUITE,
}
