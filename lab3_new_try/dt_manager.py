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

    def getTeammates(self):
        teammates = []
        for key, obj in self.visible.items():
            name = obj.get("name", [])
            if not isinstance(name, list) or len(name) < 2:
                continue
            if name[0] == "p" and str(name[1]).strip('"') == self.team:
                teammates.append((key, obj))
        return teammates

    def getTeammateCount(self):
        return len(self.getTeammates())

    def getClosestTeammate(self):
        teammates = self.getTeammates()
        if not teammates:
            return None
        return min(teammates, key=lambda item: item[1].get("dist", 9999))
