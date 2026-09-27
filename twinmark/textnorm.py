"""归一化：大小写、全半角、零宽字符、组合字符，迭代到不动点（最多 4 轮）。"""

import unicodedata

MAX_ROUNDS = 4


class NonConvergenceError(Exception):
    """四轮后仍未收敛，输入不可用。"""


def _round_once(text):
    text = text.casefold()
    text = unicodedata.normalize("NFKC", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    text = unicodedata.normalize("NFC", text)
    return text


def normalize(text):
    """返回归一化结果；幂等：normalize(normalize(x)) == normalize(x)。"""
    for _ in range(MAX_ROUNDS):
        nxt = _round_once(text)
        if nxt == text:
            return nxt
        text = nxt
    raise NonConvergenceError("归一化四轮未收敛")
