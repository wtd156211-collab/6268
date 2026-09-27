"""twinmark：标识符归一与同形字检测。"""

from .cases import CaseError, iter_cases
from .engine import compare, evaluate_record, scan_evidence, screen
from .maps import ConfusableMap, MapError, load_maps
from .report import attach_raw, build_report, is_flagged
from .textnorm import NonConvergenceError, normalize

__all__ = [
    "CaseError",
    "ConfusableMap",
    "MapError",
    "NonConvergenceError",
    "attach_raw",
    "build_report",
    "compare",
    "evaluate_record",
    "is_flagged",
    "iter_cases",
    "load_maps",
    "normalize",
    "scan_evidence",
    "screen",
]
