class DTManager:
    """Интерфейс для рутинных задач дерева решений."""
    def __init__(self):
        self.visible = {}
        self.team = ""
        self.side = ""
        self.player_number = 0
        self.x = None
        self.y = None
        self.last_heard_msg = None

    def update(
        self,
        visible_objects: dict,
        team: str = "",
        side: str = "",
        player_number: int = 0,
        x=None,
        y=None,
        last_heard_msg=None,
    ):
        self.visible = visible_objects
        self.team = team
        self.side = side
        self.player_number = player_number
        self.x = x
        self.y = y
        self.last_heard_msg = last_heard_msg

    def getGoalFlag(self) -> str:
        return "gr" if self.side == "l" else "gl"

    def getCenterFlag(self) -> str:
        return "fplc" if self.side == "l" else "fprc"

    def getCornerFlag(self) -> str:
        return "fplb" if self.side == "l" else "fprb"

    def getGoalCornerFlag(self) -> str:
        return "fgrb" if self.side == "l" else "fglt"

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

    def _player_team_from_name(self, name: list):
        """Имя команды из name игрока: (p TeamName unum) или (p unum TeamName)."""
        if not name or len(name) < 2:
            return None
        for i in (1, 2):
            if i < len(name):
                v = name[i]
                if isinstance(v, str):
                    return v.strip('"').strip()
        return None

    def getTeammates(self) -> list:
        teammates = []
        my_team_norm = (self.team or "").strip().lower()
        for key, obj in self.visible.items():
            name = obj.get("name", [])
            if not isinstance(name, list) or len(name) < 2:
                continue
            first = name[0]
            if isinstance(first, str) and first.lower() != "p":
                continue
            seen_team = self._player_team_from_name(name)
            if seen_team and seen_team.lower() == my_team_norm:
                teammates.append((key, obj))
        return teammates

    def getTeammateCount(self) -> int:
        return len(self.getTeammates())

    def getClosestTeammate(self):
        teammates = self.getTeammates()
        if not teammates:
            return None
        return min(teammates, key=lambda t: t[1].get("dist", 9999))
