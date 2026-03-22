TEAM_ROLES = [
    "goalie",
    "defender_top",
    "defender_center",
    "defender_bottom",
    "defender_sweeper",
    "midfielder_top",
    "midfielder_center",
    "midfielder_bottom",
    "forward_top",
    "forward_center",
    "forward_bottom",
]


ROLE_CONFIG = {
    "l": {
        "goalie": {"home_flag": "gl", "start_pos": (-50, 0)},
        "defender_top": {"home_flag": "fplt", "start_pos": (-42, -20)},
        "defender_center": {"home_flag": "fplc", "start_pos": (-38, 0)},
        "defender_bottom": {"home_flag": "fplb", "start_pos": (-42, 20)},
        "defender_sweeper": {"home_flag": "fplc", "start_pos": (-46, 0)},
        "midfielder_top": {"home_flag": "fct", "attack_flag": "fprt", "start_pos": (-24, -16)},
        "midfielder_center": {"home_flag": "fc", "attack_flag": "fprc", "start_pos": (-26, 0)},
        "midfielder_bottom": {"home_flag": "fcb", "attack_flag": "fprb", "start_pos": (-24, 16)},
        "forward_top": {"home_flag": "fct", "attack_flag": "fprt", "start_pos": (-8, -24)},
        "forward_center": {"home_flag": "fc", "attack_flag": "fprc", "start_pos": (-10, 0)},
        "forward_bottom": {"home_flag": "fcb", "attack_flag": "fprb", "start_pos": (-8, 24)},
    },
    "r": {
        "goalie": {"home_flag": "gr", "start_pos": (-50, 0)},
        "defender_top": {"home_flag": "fprt", "start_pos": (-42, 20)},
        "defender_center": {"home_flag": "fprc", "start_pos": (-38, 0)},
        "defender_bottom": {"home_flag": "fprb", "start_pos": (-42, -20)},
        "defender_sweeper": {"home_flag": "fprc", "start_pos": (-46, 0)},
        "midfielder_top": {"home_flag": "fct", "attack_flag": "fplt", "start_pos": (-24, 16)},
        "midfielder_center": {"home_flag": "fc", "attack_flag": "fplc", "start_pos": (-26, 0)},
        "midfielder_bottom": {"home_flag": "fcb", "attack_flag": "fplb", "start_pos": (-24, -16)},
        "forward_top": {"home_flag": "fct", "attack_flag": "fplt", "start_pos": (-8, 24)},
        "forward_center": {"home_flag": "fc", "attack_flag": "fplc", "start_pos": (-10, 0)},
        "forward_bottom": {"home_flag": "fcb", "attack_flag": "fplb", "start_pos": (-8, -24)},
    },
}


def get_role_config(side, role_key):
    return ROLE_CONFIG[side][role_key]


def role_family(role_key):
    if role_key == "goalie":
        return "goalie"
    if role_key.startswith("defender"):
        return "defender"
    return "forward"
