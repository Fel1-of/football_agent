import re


class MsgParser:
    @staticmethod
    def tokenize(msg: str) -> list[str]:
        msg = msg.rstrip("\x00")
        pattern = r'\(|\)|[-+]?\d+\.?\d*(?:e[-+]?\d+)?|"[^"]*"|[\w]+'
        return re.findall(pattern, msg, re.IGNORECASE)

    @staticmethod
    def parse(tokens: list[str], idx: int = 0):
        result = []
        while idx < len(tokens):
            tok = tokens[idx]
            if tok == "(":
                sublist, idx = MsgParser.parse(tokens, idx + 1)
                result.append(sublist)
            elif tok == ")":
                return result, idx + 1
            else:
                tok_stripped = tok.strip('"')
                try:
                    if "." in tok_stripped or "e" in tok_stripped.lower():
                        val = float(tok_stripped)
                    else:
                        val = int(tok_stripped)
                except ValueError:
                    val = tok_stripped
                result.append(val)
                idx += 1
        return result, idx

    @staticmethod
    def parse_msg(msg: str) -> list | None:
        tokens = MsgParser.tokenize(msg)
        if not tokens:
            return None
        parsed, _ = MsgParser.parse(tokens)
        return parsed[0] if parsed else None
