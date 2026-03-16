class DecisionTree:
    """
    Дерево решений: exec-узел, condition-узел, command-узел.
    """
    def __init__(self, tree: dict):
        self.tree = tree

    @property
    def state(self):
        return self.tree["state"]

    def execute(self, mgr):
        return self._run(mgr, "root")

    def _run(self, mgr, node_name: str):
        node = self.tree[node_name]
        if "exec" in node:
            node["exec"](mgr, self.state)
            return self._run(mgr, node["next"])
        if "condition" in node:
            cond = node["condition"](mgr, self.state)
            return self._run(mgr, node["trueCond"] if cond else node["falseCond"])
        if "command" in node:
            return node["command"](mgr, self.state)
        raise ValueError(f"Узел {node_name} не содержит exec/condition/command")
