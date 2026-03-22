class TimedAutomaton:
    """
    Интерпретатор временного автомата.

    Формат автомата:
    {
        "state": {"location": "...", "command": None},
        "clocks": {"loc": 0.0, ...},
        "locations": {
            "name": {"action": callable(mgr, state, clocks)}
        },
        "transitions": [
            {
                "from": "loc_a",
                "to": "loc_b",
                "guard": callable(mgr, state, clocks) -> bool,
                "reset": ["loc", ...],
                "priority": 0
            }
        ]
    }
    """

    def __init__(self, automaton: dict, tick_seconds: float = 0.1):
        self.automaton = automaton
        self.tick_seconds = tick_seconds

    @property
    def state(self):
        return self.automaton["state"]

    @property
    def clocks(self):
        return self.automaton["clocks"]

    def reset(self):
        self.state["command"] = None
        initial_location = self.automaton.get("initial", self.state.get("location"))
        self.state["location"] = initial_location
        for clk in self.clocks:
            self.clocks[clk] = 0.0

    def step(self, mgr):
        self._tick()
        self._apply_transitions(mgr)
        self._run_location_action(mgr)
        return self.state.get("command")

    def _tick(self):
        for clk in self.clocks:
            self.clocks[clk] += self.tick_seconds

    def _apply_transitions(self, mgr):
        # Ограничение числа переходов за один такт защищает от циклов.
        max_hops = 8
        hops = 0
        while hops < max_hops:
            cur = self.state.get("location")
            candidates = [
                tr for tr in self.automaton.get("transitions", [])
                if tr.get("from") == cur
            ]
            candidates.sort(key=lambda tr: tr.get("priority", 0), reverse=True)
            chosen = None
            for tr in candidates:
                guard = tr.get("guard")
                if guard is None or guard(mgr, self.state, self.clocks):
                    chosen = tr
                    break
            if not chosen:
                return
            self.state["location"] = chosen["to"]
            for clk in chosen.get("reset", []):
                if clk in self.clocks:
                    self.clocks[clk] = 0.0
            hops += 1

    def _run_location_action(self, mgr):
        self.state["command"] = None
        loc = self.state.get("location")
        node = self.automaton["locations"].get(loc, {})
        action = node.get("action")
        if callable(action):
            action(mgr, self.state, self.clocks)

