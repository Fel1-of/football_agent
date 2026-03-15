# -*- coding: utf-8 -*-
"""
Вычисление координат игрока по 2–3 флагам.
Система уравнений: d1²=(x-x1)²+(y-y1)², d2²=(x-x2)²+(y-y2)².
"""
import math
from flags import FLAGS
from config import FIELD_WIDTH, FIELD_HEIGHT, EPS


def _to_rad(deg):
    return deg * math.pi / 180.0


def in_field(x, y):
    """Проверка, что точка в границах поля."""
    return -FIELD_WIDTH <= x <= FIELD_WIDTH and -FIELD_HEIGHT <= y <= FIELD_HEIGHT


def position_from_two_flags(x1, y1, d1, x2, y2, d2):
    """
    Координаты (x,y) игрока по двум флагам. Возвращает список возможных пар (x,y).
    """
    # Вычитаем уравнения: выражаем x через y: x = alpha*y + beta
    denom = 2 * (x2 - x1)
    if abs(denom) < EPS:
        # x1 == x2: считаем y напрямую
        num_y = (y2**2 - y1**2 + d1**2 - d2**2)
        denom_y = 2 * (y2 - y1)
        if abs(denom_y) < EPS:
            return []
        y = num_y / denom_y
        # x из первого уравнения: (x-x1)² = d1² - (y-y1)²
        disc = d1**2 - (y - y1)**2
        if disc < -EPS:
            return []
        sqrt_d = math.sqrt(max(0.0, disc))
        return [(x1 + sqrt_d, y), (x1 - sqrt_d, y)]

    # x = alpha*y + beta; из вычитания уравнений: alpha = (y1-y2)/(x2-x1), beta = (d1²-d2²-x1²+x2²-y1²+y2²)/(2(x2-x1))
    alpha = (y1 - y2) / (x2 - x1)
    beta = (d1**2 - d2**2 - x1**2 + x2**2 - y1**2 + y2**2) / (2 * (x2 - x1))
    # Подстановка в первое уравнение даёт квадратное по y: a*y² + b*y + c = 0
    a = alpha**2 + 1
    b = -2 * (alpha * (x1 - beta) + y1)
    c = (x1 - beta)**2 + y1**2 - d1**2
    disc = b**2 - 4 * a * c
    if disc < -EPS:
        return []
    sqrt_d = math.sqrt(max(0.0, disc))
    ys = [(-b + sqrt_d) / (2 * a), (-b - sqrt_d) / (2 * a)]
    out = []
    for y in ys:
        x = alpha * y + beta
        # Проверка по первому уравнению (x-x1)² + (y-y1)² = d1²
        if abs((x - x1)**2 + (y - y1)**2 - d1**2) < EPS:
            out.append((x, y))
    return out


def position_from_three_flags(flags_list):
    """
    flags_list: список словарей {key, dist, angle} (из get_visible_flags).
    Возвращает (x, y) или None.
    """
    if len(flags_list) < 2:
        return None
    # Берём первые два флага
    f1, f2 = flags_list[0], flags_list[1]
    x1, y1 = FLAGS[f1['key']]
    x2, y2 = FLAGS[f2['key']]
    d1, d2 = f1['dist'], f2['dist']
    candidates = position_from_two_flags(x1, y1, d1, x2, y2, d2)
    if not candidates:
        return None
    # Если есть третий флаг — выбираем решение с минимальной ошибкой
    if len(flags_list) >= 3:
        f3 = flags_list[2]
        x3, y3 = FLAGS[f3['key']]
        d3 = f3['dist']
        best = None
        best_err = float('inf')
        for (x, y) in candidates:
            if not in_field(x, y):
                continue
            err = abs((x - x3)**2 + (y - y3)**2 - d3**2)
            if err < best_err:
                best_err = err
                best = (x, y)
        return best
    for (x, y) in candidates:
        if in_field(x, y):
            return (x, y)
    return candidates[0] if candidates else None


def body_angle_from_flag(my_x, my_y, flag_x, flag_y, see_dist, see_angle_deg):
    """Направление тела игрока (в радианах): по известной позиции и наблюдению одного флага."""
    world_angle = math.atan2(flag_y - my_y, flag_x - my_x)
    see_rad = _to_rad(see_angle_deg)
    return world_angle - see_rad


def object_position_global(my_x, my_y, body_angle_rad, obj_dist, obj_angle_deg):
    """Глобальные координаты объекта по позиции игрока, углу тела и наблюдению (dist, angle)."""
    a = body_angle_rad + _to_rad(obj_angle_deg)
    dx = obj_dist * math.cos(a)
    dy = obj_dist * math.sin(a)
    return (my_x + dx, my_y + dy)


def _get_obj_from_see(see_res, name_first):
    """
    Из see извлекаем объект с именем name_first (например 'b' — мяч, 'p' — игрок).
    Возвращает {dist, angle} или None.
    """
    if see_res.get("cmd") != "see" or len(see_res["p"]) < 3:
        return None
    for i in range(2, len(see_res["p"])):
        ob = see_res["p"][i]
        if not isinstance(ob, dict) or "p" not in ob or len(ob["p"]) < 2:
            continue
        arr = ob["p"]
        name = arr[0]
        if isinstance(name, dict) and "p" in name:
            name_arr = name["p"]
        else:
            name_arr = arr
        if not name_arr or name_arr[0] != name_first:
            continue
        nums = [x for x in arr if isinstance(x, (int, float))]
        if len(nums) >= 2:
            return {"dist": float(nums[0]), "angle": float(nums[1])}
    return None


def get_ball_from_see(see_res):
    """Мяч (b) в see. Возвращает {dist, angle} или None."""
    return _get_obj_from_see(see_res, "b")


def get_opponent_from_see(see_res, my_team=None):
    """
    Первый видимый игрок противоположной команды (p "teamX" num).
    my_team — имя нашей команды, чтобы игнорировать своих.
    """
    if see_res.get("cmd") != "see" or len(see_res["p"]) < 3:
        return None
    for i in range(2, len(see_res["p"])):
        ob = see_res["p"][i]
        if not isinstance(ob, dict) or "p" not in ob or len(ob["p"]) < 3:
            continue
        arr = ob["p"]
        name = arr[0]
        if isinstance(name, dict) and "p" in name:
            name_arr = name["p"]
        else:
            name_arr = arr
        if name_arr[0] != "p":
            continue
        if my_team and len(name_arr) >= 2 and name_arr[1] == my_team:
            continue
        nums = [x for x in arr if isinstance(x, (int, float))]
        if len(nums) >= 2:
            return {"dist": float(nums[0]), "angle": float(nums[1])}
    return None


def get_teammates_from_see(see_res, my_team=None, my_unum=None):
    """
    Видимые игроки своей команды.
    Возвращает список словарей {dist, angle, unum, key}.
    """
    if see_res.get("cmd") != "see" or len(see_res["p"]) < 3 or not my_team:
        return []

    teammates = []
    for i in range(2, len(see_res["p"])):
        ob = see_res["p"][i]
        if not isinstance(ob, dict) or "p" not in ob or len(ob["p"]) < 3:
            continue
        arr = ob["p"]
        name = arr[0]
        if isinstance(name, dict) and "p" in name:
            name_arr = name["p"]
        else:
            name_arr = arr
        if len(name_arr) < 2 or name_arr[0] != "p" or name_arr[1] != my_team:
            continue

        nums = [x for x in arr if isinstance(x, (int, float))]
        if len(nums) < 2:
            continue

        unum = None
        if len(name_arr) >= 3 and isinstance(name_arr[2], (int, float)):
            unum = int(name_arr[2])
        if my_unum is not None and unum == my_unum:
            continue

        teammates.append(
            {
                "dist": float(nums[0]),
                "angle": float(nums[1]),
                "unum": unum,
                "key": f"p_{unum}" if unum is not None else "p_unknown",
            }
        )
    return teammates
