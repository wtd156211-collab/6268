"""命令行：evaluate 写 JSONL 结果，report 写统计报告。"""

import argparse
import os
import shutil
import sys
import tempfile

from .cases import CaseError, iter_cases
from .engine import evaluate_record
from .jsonio import dumps_line, dumps_report
from .maps import MapError, load_maps
from .report import attach_raw, build_report
from .textnorm import NonConvergenceError

DEFAULT_REPORT_OUT = os.path.join("var", "report.json")


def _build_parser():
    parser = argparse.ArgumentParser(prog="twinmark", description="标识符归一与同形字检测")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("evaluate", "report"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--map", dest="maps", action="append", required=True,
                         help="混淆映射表，可多次给出并按序合并")
        cmd.add_argument("--cases", dest="cases", action="append", required=True,
                         help="用例 JSONL，可多次给出并按序处理")
        cmd.add_argument("--out", dest="out", default=None,
                         help="输出路径，省略时 evaluate 写 stdout、report 写 var/report.json")
    return parser


class _Output:
    """先写临时文件，全部成功才落位；失败不留输出。"""

    def __init__(self, out_path):
        self.out_path = out_path
        directory = None
        if out_path is not None:
            directory = os.path.dirname(os.path.abspath(out_path))
            os.makedirs(directory, exist_ok=True)
        tmp = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            prefix=".twinmark-", suffix=".tmp", dir=directory, delete=False)
        self._tmp_path = tmp.name
        self._fh = tmp

    def write(self, text):
        self._fh.write(text)

    def commit(self):
        self._fh.close()
        if self.out_path is None:
            with open(self._tmp_path, "r", encoding="utf-8", newline="") as fh:
                shutil.copyfileobj(fh, sys.stdout)
            os.unlink(self._tmp_path)
        else:
            os.replace(self._tmp_path, self.out_path)

    def abort(self):
        self._fh.close()
        os.unlink(self._tmp_path)


def _run_evaluate(cmap, case_paths, out_path):
    output = _Output(out_path)
    try:
        for case in iter_cases(case_paths):
            output.write(dumps_line(evaluate_record(case, cmap)) + "\n")
    except BaseException:
        output.abort()
        raise
    output.commit()


def _run_report(cmap, case_paths, out_path):
    items = []
    for case in iter_cases(case_paths):
        items.append(attach_raw(evaluate_record(case, cmap), case))
    text = dumps_report(build_report(items))
    output = _Output(out_path)
    try:
        output.write(text)
    except BaseException:
        output.abort()
        raise
    output.commit()


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        cmap = load_maps(args.maps)
        out_path = args.out
        if args.command == "report" and out_path is None:
            out_path = DEFAULT_REPORT_OUT
        if args.command == "evaluate":
            _run_evaluate(cmap, args.cases, out_path)
        else:
            _run_report(cmap, args.cases, out_path)
    except (MapError, CaseError, NonConvergenceError) as exc:
        print(f"twinmark: {exc}", file=sys.stderr)
        return 1
    return 0
