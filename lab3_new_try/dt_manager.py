class DTManager:
    """Менеджер доступа к наблюдаемым объектам для дерева решений."""

    def __init__(self):
        self.visible = {}
        self.team = ""
        self.side = ""
        self.player_number = 0
        self.x = None
        self.y = None

    def update(self, visible_objects, team="", side="", player_number=0, x=None, y=None):
        self.visible = visible_objects or {}
        self.team = team
        self.side = side
        self.player_number = player_number
        self.x = x
        self.y = y

    def getVisible(self, obj_key):
        return obj_key in self.visible

    def getDistance(self, obj_key):
        if obj_key in self.visible:
            return self.visible[obj_key].get("dist", 9999)
        return 9999

    def getDistChange(self, obj_key):
        if obj_key in self.visible:
            return self.visible[obj_key].get("dist_change", 0)
        return 0

    def getAngle(self, obj_key):
        if obj_key in self.visible:
            return self.visible[obj_key].get("dir", 0)
        return 0

    def getOurGoalFlag(self):
        """Флаг своих ворот (куда возвращаться): gl если side l, иначе gr."""
        return "gl" if self.side == "l" else "gr"

    def getAwayGoalFlag(self):
        """Флаг чужих ворот (куда бить): gr если мы слева (l), иначе gl."""
        return "gr" if self.side == "l" else "gl"

    def getPenaltyCenterFlag(self):
        """Центр своей штрафной: fplc если side l, иначе fprc."""
        return "fplc" if self.side == "l" else "fprc"

    def getAwayCornerTop(self):
        """Угловой флаг вперёд (в сторону чужих ворот): frt если side l, иначе flt."""
        return "frt" if self.side == "l" else "flt"

    def getAwayCornerBottom(self):
        return "frb" if self.side == "l" else "flb"

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

    def getTeammates(self):
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

    def getTeammateCount(self):
        return len(self.getTeammates())

    def getClosestTeammate(self):
        teammates = self.getTeammates()
        if not teammates:
            return None
        return min(teammates, key=lambda item: item[1].get("dist", 9999))
