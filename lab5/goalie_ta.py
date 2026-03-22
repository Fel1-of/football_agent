def create_goalie_ta():
    true_func = lambda *args, **kwargs: True

    def update_timers(*names):
        def func(mgr, s):
            for key in names:
                s[key] = mgr.time_cycle
        return func

    def check_timer(timer_name, max_delta):
        def func(mgr, s):
            delta = mgr.time_cycle - s.get(timer_name, 0)
            return delta > max_delta
        return func

    def goalie_not_at_goal_but_sees_it(mgr, s):
        goal = mgr.own_goal_key()
        return mgr.getVisible(goal) and mgr.getDistance(goal) > 3

    def move_to_own_goal(mgr, s):
        goal = mgr.own_goal_key()
        angle = mgr.getAngle(goal)
        dist = mgr.getDistance(goal)

        if abs(angle) > 7:
            return ("turn", str(int(angle)))

        if dist > 6:
            return ("dash", "100")

        if dist > 3.5:
            return ("dash", "70")

        return None

    def move_to_ball(mgr, s):
        s["last_find_boal"] = mgr.time_cycle

        angle = mgr.getAngle("b")
        dist = mgr.getDistance("b")

        if abs(angle) > 7:
            return ("turn", str(int(angle)))

        if dist > 2:
            return ("dash", "100")

        return ("dash", "80")

    def kick_ball_from_goal(mgr, s):
        def normalize_angle(angle):
            while angle > 180:
                angle -= 360
            while angle < -180:
                angle += 360
            return angle

        enemy_goal = mgr.enemy_goal_key()
        own_goal = mgr.own_goal_key()

        if mgr.getVisible(enemy_goal):
            return ("kick", f"100 {int(mgr.getAngle(enemy_goal))}")

        if mgr.getVisible(own_goal):
            away_angle = normalize_angle(mgr.getAngle(own_goal) + 180)
            return ("kick", f"100 {int(away_angle)}")

        return ("kick", "100 0")

    ta = {
        "__start__": "serch_football_goal",
        "serch_football_goal": [
            (
                lambda mgr, s: mgr.getVisible(mgr.own_goal_key()),
                update_timers("last_find_boal"),
                "move_to_own_goal",
            ),
            (
                true_func,
                lambda mgr, s: ("turn", "90"),
                "serch_football_goal",
            ),
        ],
        "move_to_own_goal": [
            (
                check_timer("last_find_boal", 30),
                update_timers("last_find_boal"),
                "determine_distance_to_ball",
            ),
            (
                goalie_not_at_goal_but_sees_it,
                move_to_own_goal,
                "move_to_own_goal",
            ),
            (
                true_func,
                lambda mgr, s: ("turn", str(int(mgr.getAngle("b")))),
                "at_football_goal",
            ),
        ],
        "determine_distance_to_ball": [
            (
                lambda mgr, s: not mgr.getVisible("b"),
                lambda mgr, s: ("turn", "90"),
                "determine_distance_to_ball",
            ),
            (
                lambda mgr, s: mgr.getDistance("b") <= 10,
                update_timers("last_find_boal"),
                "move_to_ball_and_kick",
            ),
            (
                check_timer("last_find_boal", 4),
                update_timers("last_find_boal"),
                "serch_football_goal",
            ),
        ],
        "move_to_ball_and_kick": [
            (
                check_timer("last_find_boal", 5),
                update_timers("last_find_boal"),
                "serch_football_goal",
            ),
            (
                lambda mgr, s: not mgr.getVisible("b"),
                lambda mgr, s: ("turn", "90"),
                "move_to_ball_and_kick",
            ),
            (
                lambda mgr, s: mgr.getDistance("b") > 1,
                move_to_ball,
                "move_to_ball_and_kick",
            ),
            (
                lambda mgr, s: mgr.getDistance("b") <= 1,
                kick_ball_from_goal,
                "serch_football_goal",
            ),
        ],
        "at_football_goal": [
            (
                lambda mgr, s: not mgr.getVisible("b"),
                lambda mgr, s: ("turn", "90"),
                "at_football_goal",
            ),
            (
                lambda mgr, s: mgr.getDistance("b") > 15,
                lambda mgr, s: ("turn", str(int(mgr.getAngle("b")))),
                "at_football_goal",
            ),
            (
                true_func,
                update_timers("last_find_boal"),
                "move_to_ball_and_kick",
            ),
        ],
    }

    return ta

