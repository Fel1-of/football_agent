# Система координат как у друга / rcssserver: x -54..54, y -34..34 (знак y согласован с монитором).
FLAGS = {
    "fc": (0.0, 0.0),
    "ftl50": (-50.0, -39.0), "ftl40": (-40.0, -39.0), "ftl30": (-30.0, -39.0), "ftl20": (-20.0, -39.0),
    "ftl10": (-10.0, -39.0), "ft0": (0.0, -39.0), "ftr10": (10.0, -39.0), "ftr20": (20.0, -39.0),
    "ftr30": (30.0, -39.0), "ftr40": (40.0, -39.0), "ftr50": (50.0, -39.0),
    "fbl50": (-50.0, 39.0), "fbl40": (-40.0, 39.0), "fbl30": (-30.0, 39.0), "fbl20": (-20.0, 39.0),
    "fbl10": (-10.0, 39.0), "fb0": (0.0, 39.0), "fbr10": (10.0, 39.0), "fbr20": (20.0, 39.0),
    "fbr30": (30.0, 39.0), "fbr40": (40.0, 39.0), "fbr50": (50.0, 39.0),
    "flt30": (-57.5, -30.0), "flt20": (-57.5, -20.0), "flt10": (-57.5, -10.0), "fl0": (-57.5, 0.0),
    "flb10": (-57.5, 10.0), "flb20": (-57.5, 20.0), "flb30": (-57.5, 30.0),
    "frt30": (57.5, -30.0), "frt20": (57.5, -20.0), "frt10": (57.5, -10.0), "fr0": (57.5, 0.0),
    "frb10": (57.5, 10.0), "frb20": (57.5, 20.0), "frb30": (57.5, 30.0),
    "fglt": (-52.5, -7.01), "fglb": (-52.5, 7.01), "gl": (-52.5, 0.0), "gr": (52.5, 0.0),
    "fplt": (-36.0, -20.15), "fplc": (-36.0, 0.0), "fplb": (-36.0, 20.15),
    "fgrt": (52.5, -7.01), "fgrb": (52.5, 7.01), "fprt": (36.0, -20.15), "fprc": (36.0, 0.0), "fprb": (36.0, 20.15),
    "flt": (-52.5, -34.0), "fct": (0.0, -34.0), "frt": (52.5, -34.0),
    "flb": (-52.5, 34.0), "fcb": (0.0, 34.0), "frb": (52.5, 34.0),
}


def _name_parts_from_see_obj(ob):
    """Из объекта see (dict с 'p') извлекаем список частей имени: ['b'] или ['f','c'], ['p','teamA',1] и т.д."""
    if not ob or 'p' not in ob or not ob['p']:
        return []
    first = ob['p'][0]
    if isinstance(first, dict) and 'p' in first:
        return first['p']
    return [first]


def obj_name_to_key(name_parts):
    """Ключ для словаря видимых объектов: 'b', 'fc', 'pteamA1' и т.д."""
    return ''.join(str(x).strip('"') for x in name_parts)


def flag_key_from_see(ob):
    """Ключ флага из объекта see, если это известный флаг."""
    key = obj_name_to_key(_name_parts_from_see_obj(ob))
    return key if key in FLAGS else None


def get_visible_objects_from_see(see_res):
    """
    Строит словарь visible_objects из нашего формата see (dict с cmd, p).
    Ключ — obj_name_to_key, значение — {name, dist, dir (angle)}.
    """
    if see_res.get('cmd') != 'see' or len(see_res['p']) < 2:
        return {}
    out = {}
    for i in range(2, len(see_res['p'])):
        ob = see_res['p'][i]
        if not isinstance(ob, dict) or 'p' not in ob or len(ob['p']) < 3:
            continue
        arr = ob['p']
        nums = [x for x in arr if isinstance(x, (int, float))]
        if len(nums) < 2:
            continue
        dist, angle = float(nums[0]), float(nums[1])
        name_parts = _name_parts_from_see_obj(ob)
        if not name_parts:
            continue
        key = obj_name_to_key(name_parts)
        out[key] = {'name': name_parts, 'dist': dist, 'dir': angle}
    return out


def get_visible_flags(see_res):
    """Список {key, dist, angle} для флагов из see (для position_from_three_flags)."""
    objs = get_visible_objects_from_see(see_res)
    return [{'key': k, 'dist': v['dist'], 'angle': v['dir']}
             for k, v in objs.items() if k in FLAGS]
