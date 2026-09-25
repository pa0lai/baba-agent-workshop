PUBLIC_SUITE = [
    {"task": "env/goto_win", "seed": 0, "max_steps": 30},
    {"task": "env/make_win", "seed": 1, "max_steps": 45},
    {"task": "env/two_room-goto_win", "seed": 2, "max_steps": 55},
]

# Classroom-hidden, not security-hidden. The instructor can replace these
# immediately before the event or distribute a separate manifest.
FINAL_SUITE = [
    {"task": "env/goto_win-distr_obj_rule", "seed": 11, "max_steps": 40},
    {"task": "env/make_win-distr_rule", "seed": 12, "max_steps": 55},
    {"task": "env/two_room-goto_win-distr_win_rule", "seed": 13, "max_steps": 65},
    {"task": "env/two_room-break_stop-goto_win", "seed": 14, "max_steps": 75},
    {"task": "env/two_room-break_stop-make_win", "seed": 15, "max_steps": 90},
]

