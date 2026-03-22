import math
from flags import FLAGS

FIELD_WIDTH = 54
FIELD_HEIGHT = 32


def compute_position_two_flags(
    flag1_key: str,
    d1: float,
    flag2_key: str,
    d2: float,
):
    x1, y1 = FLAGS[flag1_key]
    x2, y2 = FLAGS[flag2_key]

    solutions = _solve_two_circles(x1, y1, d1, x2, y2, d2)

    if not solutions:
        return None

    valid = []
    for sx, sy in solutions:
        if -FIELD_WIDTH <= sx <= FIELD_WIDTH and -FIELD_HEIGHT <= sy <= FIELD_HEIGHT:
            valid.append((sx, sy))

    if not valid:
        valid = solutions

    return valid[0]


def _solve_two_circles(x1, y1, d1, x2, y2, d2):
    solutions = []

    EPS = 1e-9

    if abs(x2 - x1) < EPS and abs(y2 - y1) < EPS:
        return []

    if abs(x2 - x1) < EPS:
        y = (y2**2 - y1**2 + d1**2 - d2**2) / (2 * (y2 - y1))
        det = d1**2 - (y - y1) ** 2
        if det < -EPS:
            return []
        det = max(det, 0)
        sq = math.sqrt(det)
        solutions.append((x1 + sq, y))
        solutions.append((x1 - sq, y))
        return solutions

    if abs(y2 - y1) < EPS:
        x = (x2**2 - x1**2 + d1**2 - d2**2) / (2 * (x2 - x1))
        det = d1**2 - (x - x1) ** 2
        if det < -EPS:
            return []
        det = max(det, 0)
        sq = math.sqrt(det)
        solutions.append((x, y1 + sq))
        solutions.append((x, y1 - sq))
        return solutions

    # x = alpha * y + beta
    alpha = (y1 - y2) / (x2 - x1)
    beta = (y2**2 - y1**2 + x2**2 - x1**2 + d1**2 - d2**2) / (2 * (x2 - x1))

    # Подставляем в первое уравнение: (alpha*y + beta - x1)^2 + (y - y1)^2 = d1^2
    # (alpha^2 + 1) * y^2 - 2*(alpha*(x1-beta) + y1)*y + (x1-beta)^2 + y1^2 - d1^2 = 0
    a_coef = alpha**2 + 1
    b_coef = -2 * (alpha * (x1 - beta) + y1)
    c_coef = (x1 - beta) ** 2 + y1**2 - d1**2

    discriminant = b_coef**2 - 4 * a_coef * c_coef

    if discriminant < -EPS:
        return []
    
    discriminant = max(discriminant, 0)

    sq_disc = math.sqrt(discriminant)

    y_sol1 = (-b_coef + sq_disc) / (2 * a_coef)
    y_sol2 = (-b_coef - sq_disc) / (2 * a_coef)

    x_sol1 = alpha * y_sol1 + beta
    x_sol2 = alpha * y_sol2 + beta

    solutions.append((x_sol1, y_sol1))
    if abs(y_sol1 - y_sol2) > EPS or abs(x_sol1 - x_sol2) > EPS:
        solutions.append((x_sol2, y_sol2))

    return solutions


def compute_position_three_flags(
    flag1_key: str, d1: float, flag2_key: str, d2: float, flag3_key: str, d3: float
):
    x1, y1 = FLAGS[flag1_key]
    x2, y2 = FLAGS[flag2_key]
    x3, y3 = FLAGS[flag3_key]

    # Линейная система:
    # 2x(x2 - x1) + 2y(y2 - y1) = d1^2 - d2^2 - x1^2 + x2^2 - y1^2 + y2^2
    # 2x(x3 - x1) + 2y(y3 - y1) = d1^2 - d3^2 - x1^2 + x3^2 - y1^2 + y3^2

    a1 = 2 * (x2 - x1)
    b1 = 2 * (y2 - y1)
    c1 = d1**2 - d2**2 - x1**2 + x2**2 - y1**2 + y2**2

    a2 = 2 * (x3 - x1)
    b2 = 2 * (y3 - y1)
    c2 = d1**2 - d3**2 - x1**2 + x3**2 - y1**2 + y3**2

    det = a1 * b2 - a2 * b1

    if abs(det) < 1e-6:
        return compute_position_two_flags(flag1_key, d1, flag2_key, d2)

    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det

    return (x, y)


def compute_object_position(
    player_x, player_y, flag_key, flag_dist, flag_angle, obj_dist, obj_angle
):
    EPS = 1e-9

    x1, y1 = FLAGS[flag_key]

    # Расстояние от объекта до флага
    angle_diff = abs(flag_angle - obj_angle)
    angle_diff_rad = math.radians(angle_diff)

    d_obj_flag_sq = flag_dist**2 + obj_dist**2 - 2 * flag_dist * obj_dist * math.cos(angle_diff_rad)
    if d_obj_flag_sq < 0:
        d_obj_flag_sq = 0
    d_obj_flag = math.sqrt(d_obj_flag_sq)

    if d_obj_flag < EPS:
        return (x1, y1)

    # решаем систему:
    # obj_dist^2 = (x - player_x)^2 + (y - player_y)^2
    # d_obj_flag^2 = (x - x1)^2 + (y - y1)^2
    solutions = _solve_two_circles(player_x, player_y, obj_dist, x1, y1, d_obj_flag)

    if not solutions:
        return None

    valid = [
        (sx, sy)
        for sx, sy in solutions
        if -FIELD_WIDTH <= sx <= FIELD_WIDTH and -FIELD_HEIGHT <= sy <= FIELD_HEIGHT
    ]
    if not valid:
        valid = solutions

    return valid[0]
