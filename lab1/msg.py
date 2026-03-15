import re


def parse_msg(msg):
    if isinstance(msg, bytes):
        msg = msg.decode('utf-8')
    if msg.endswith('\u0000'):
        msg = msg[:-1]
    tokens = re.findall(r'\(|[-\d.]+|\w+|\)', msg)
    if not tokens:
        return None
    res = {'msg': msg, 'p': []}
    idx = [0]
    parse(tokens, idx, res)
    res['cmd'] = res['p'][0] if res['p'] else None
    return res


def parse(tokens, index, res):
    if index[0] >= len(tokens) or tokens[index[0]] != '(':
        return
    index[0] += 1
    parse_inner(tokens, index, res)
    index[0] += 1


def parse_inner(tokens, index, res):
    while index[0] < len(tokens) and tokens[index[0]] != ')':
        if tokens[index[0]] == '(':
            r = {'p': []}
            parse(tokens, index, r)
            res['p'].append(r)
        else:
            try:
                num = float(tokens[index[0]])
                res['p'].append(num)
            except ValueError:
                res['p'].append(tokens[index[0]])
            index[0] += 1


def parse_all_msgs(msg):
    """Разбирает все s-выражения из строки (один пакет может содержать несколько сообщений)."""
    if isinstance(msg, bytes):
        msg = msg.decode('utf-8')
    if msg.endswith('\u0000'):
        msg = msg[:-1]
    tokens = re.findall(r'\(|[-\d.]+|\w+|\)', msg)
    if not tokens:
        return []
    result = []
    idx = [0]
    while idx[0] < len(tokens) and tokens[idx[0]] == '(':
        res = {'msg': msg, 'p': []}
        parse(tokens, idx, res)
        res['cmd'] = res['p'][0] if res['p'] else None
        result.append(res)
    return result
