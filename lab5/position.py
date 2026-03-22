# -*- coding: utf-8 -*-
import math
from flags import FLAGS
from config import FIELD_X_MIN, FIELD_X_MAX, FIELD_Y_MIN, FIELD_Y_MAX, EPS


def _to_rad(deg):
    return deg * math.pi / 180.0


def body_angle_from_flag(my_x, my_y, flag_x, flag_y, see_dist, see_angle_deg):
    """Угол тела игрока (радианы) по позиции и наблюдению одного флага."""
    world_angle = math.atan2(flag_y - my_y, flag_x - my_x)
    see_rad = _to_rad(see_angle_deg)
    return world_angle - see_rad


def in_field(x, y):
    return FIELD_X_MIN <= x <= FIELD_X_MAX and FIELD_Y_MIN <= y <= FIELD_Y_MAX


def position_from_two_flags(x1, y1, d1, x2, y2, d2):
    denom = 2 * (x2 - x1)
    if abs(denom) < EPS:
        num_y = (y2**2 - y1**2 + d1**2 - d2**2)
        denom_y = 2 * (y2 - y1)
        if abs(denom_y) < EPS:
            return []
        y = num_y / denom_y
        disc = d1**2 - (y - y1)**2
        if disc < 0:
            return []
        sqrt_d = math.sqrt(disc)
        return [(x1 + sqrt_d, y), (x1 - sqrt_d, y)]
    alpha = (y1 - y2) / (x2 - x1)
    beta = (d1**2 - d2**2 - x1**2 + x2**2 - y1**2 + y2**2) / (2 * (x2 - x1))
    a = alpha**2 + 1
    b = -2 * (alpha * (x1 - beta) + y1)
    c = (x1 - beta)**2 + y1**2 - d1**2
    disc = b**2 - 4 * a * c
    if disc < -EPS:
        return []
    sqrt_d = math.sqrt(disc)
    ys = [(-b + sqrt_d) / (2 * a), (-b - sqrt_d) / (2 * a)]
    out = []
    for y in ys:
        x = alpha * y + beta
        if abs((x - x1)**2 + (y - y1)**2 - d1**2) < EPS:
            out.append((x, y))
    return out


def position_from_three_flags(flags_list):
    if len(flags_list) < 2:
        return None
    f1, f2 = flags_list[0], flags_list[1]
    x1, y1 = FLAGS[f1['key']]
    x2, y2 = FLAGS[f2['key']]
    d1, d2 = f1['dist'], f2['dist']
    candidates = position_from_two_flags(x1, y1, d1, x2, y2, d2)
    if not candidates:
        return None
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
