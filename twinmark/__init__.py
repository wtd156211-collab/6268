"""twinmark：标识符归一与同形字检测。

两个用法：
- 注册判定 ``screen(name, index)``：判这个名字可不可疑，附证据与规则；
- 比对判定 ``compare(left, right, index)``：判两个名字算不算同一个。

``index`` 由 ``load_maps(paths)`` 加载；``normalize`` 幂等。
"""

from .caseio import CaseError, iter_cases
from .core import NormalizeError, compare, fold, normalize, scan_evidence, screen
from .engine import evaluate_case, run_evaluate, run_report
from .mapio import MapError, load_maps

__all__ = [
    "CaseError",
    "MapError",
    "NormalizeError",
    "compare",
    "evaluate_case",
    "fold",
    "iter_cases",
    "load_maps",
    "normalize",
    "run_evaluate",
    "run_report",
    "scan_evidence",
    "screen",
]

__version__ = "1.0.0"
