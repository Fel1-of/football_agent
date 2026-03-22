class TA:
    def __init__(self, ta_dict):
        self.ta = ta_dict
        self.current = ta_dict["__start__"]
        self.state = {}

    def reset(self):
        self.current = self.ta["__start__"]
        self.state = {}

    def step(self, mgr):
        node = self.ta.get(self.current)
        if node is None:
            raise ValueError(f"Node {self.current} not found")

        for cond, action, nxt in node:
            if cond(mgr, self.state):
                result = action(mgr, self.state)
                self.current = nxt
                return result

