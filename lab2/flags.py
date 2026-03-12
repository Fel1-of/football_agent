FLAGS = {
    'ftl50': (-50, 39), 'ftl40': (-40, 39), 'ftl30': (-30, 39), 'ftl20': (-20, 39),
    'ftl10': (-10, 39), 'ft0': (0, 39), 'ftr10': (10, 39), 'ftr20': (20, 39),
    'ftr30': (30, 39), 'ftr40': (40, 39), 'ftr50': (50, 39),
    'fbl50': (-50, -39), 'fbl40': (-40, -39), 'fbl30': (-30, -39), 'fbl20': (-20, -39),
    'fbl10': (-10, -39), 'fb': (0, -39), 'fbr10': (10, -39), 'fbr20': (20, -39),
    'fbr30': (30, -39), 'fbr40': (40, -39), 'fbr50': (50, -39),
    'flt30': (-57.5, 30), 'flt20': (-57.5, 20), 'flt10': (-57.5, 10), 'fl0': (-57.5, 0),
    'flb10': (-57.5, -10), 'flb20': (-57.5, -20), 'flb30': (-57.5, -30),
    'frt30': (57.5, 30), 'frt20': (57.5, 20), 'frt10': (57.5, 10), 'fr0': (57.5, 0),
    'frb10': (57.5, -10), 'frb20': (57.5, -20), 'frb30': (57.5, -30),
    'fglt': (-52.5, 7.01), 'fglb': (-52.5, -7.01), 'gl': (-52.5, 0), 'gr': (52.5, 0),
    'fc': (0, 0),
    'fplt': (-36, 20.15), 'fplc': (-36, 0), 'fplb': (-36, -20.15),
    'fgrt': (52.5, 7.01), 'fgrb': (52.5, -7.01), 'fprt': (36, 20.15), 'fprc': (36, 0), 'fprb': (36, -20.15),
    'flt': (-52.5, 34), 'fct': (0, 34), 'frt': (52.5, 34),
    'flb': (-52.5, -34), 'fcb': (0, -34), 'frb': (52.5, -34),
}


def flag_key_from_see(obj):
    """По разобранному объекту из see (например (f c) или (f t r 10)) строим ключ для FLAGS."""
    if not obj or 'p' not in obj or not obj['p']:
        return None
    name_obj = obj['p'][0]
    if isinstance(name_obj, dict) and 'p' in name_obj:
        parts = name_obj['p']
    else:
        parts = [name_obj]
    key = ''.join(str(int(x)) if isinstance(x, (int, float)) else str(x) for x in parts)
    return key if key in FLAGS else None


def get_visible_flags(see_res):
    """Из результата parse_msg(see) извлекаем список {key, dist, angle} для известных флагов."""
    if see_res.get('cmd') != 'see' or len(see_res['p']) < 2:
        return []
    # p[0]=see, p[1]=time, p[2], p[3], ... — объекты вида {p: [name..., dist, angle, ...]}
    out = []
    for i in range(2, len(see_res['p'])):
        ob = see_res['p'][i]
        if not isinstance(ob, dict) or 'p' not in ob or len(ob['p']) < 3:
            continue
        arr = ob['p']
        nums = [x for x in arr if isinstance(x, (int, float))]
        if len(nums) < 2:
            continue
        dist, angle = float(nums[0]), float(nums[1])
        key = flag_key_from_see(ob)
        if key:
            out.append({'key': key, 'dist': float(dist), 'angle': float(angle), 'raw': ob})
    return out
