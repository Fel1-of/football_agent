class TAManager:
    def __init__(self):
        self.visible = {}
        self.team = ""
        self.side = ""
        self.player_number = 0
        self.time_cycle = 0

    def update(
        self,
        visible_objects: dict,
        team: str = "",
        side: str = "",
        player_number: int = 0,
        time_cycle: int = 0,
    ):
        self.visible = visible_objects or {}
        self.team = team
        self.side = side
        self.player_number = player_number
        self.time_cycle = time_cycle

    def getVisible(self, obj_key: str) -> bool:
        return obj_key in self.visible

    def getDistance(self, obj_key: str) -> float:
        if obj_key in self.visible:
            return self.visible[obj_key].get("dist", 9999)
        return 9999

    def getAngle(self, obj_key: str) -> float:
        if obj_key in self.visible:
            return self.visible[obj_key].get("dir", 0)
        return 0

    def own_goal_key(self) -> str:
        return "gl" if self.side == "l" else "gr"

    def enemy_goal_key(self) -> str:
        return "gr" if self.side == "l" else "gl"

