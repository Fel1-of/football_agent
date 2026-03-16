class DecisionTree:
    """
    Дерево решений состоит из узлов трёх типов:
    - exec: выполняет действие и переходит к следующему узлу
    - condition: выбирает одну из двух ветвей
    - command: возвращает итоговую команду
    """

    def __init__(self, tree):
        self.tree = tree

    @property
    def state(self):
        return self.tree["state"]

    def execute(self, mgr):
        return self._run(mgr, "root")

    def _run(self, mgr, node_name):
        node = self.tree[node_name]
        if "exec" in node:
            node["exec"](mgr, self.state)
            return self._run(mgr, node["next"])
        if "condition" in node:
            if node["condition"](mgr, self.state):
                return self._run(mgr, node["trueCond"])
            return self._run(mgr, node["falseCond"])
        if "command" in node:
            return node["command"](mgr, self.state)
        raise ValueError(f"Узел {node_name} не содержит exec/condition/command")
