"""命令行入口：evaluate / report（README 4.3）。

退出码：0 成功；1 输入不可用；2 用法错误（argparse 自带）。
输出先写临时文件，全部成功才落盘或写 stdout，非 0 不写输出。
"""

import argparse
import os
import sys
import tempfile

from .caseio import CaseError
from .core import NormalizeError
from .engine import run_evaluate, run_report
from .mapio import MapError, load_maps

__all__ = ["main"]


class _Spool:
    """输出缓冲：成功才提交，失败不留任何输出。"""

    def __init__(self, out_path):
        self._path = out_path
        self._name = None
        if out_path is None:
            self._tmp = tempfile.TemporaryFile(mode="w+", encoding="utf-8", newline="")
        else:
            parent = os.path.dirname(os.path.abspath(out_path))
            os.makedirs(parent, exist_ok=True)
            self._tmp = tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="",
                dir=parent, prefix=".twinmark-", delete=False,
            )
            self._name = self._tmp.name

    def write(self, text):
        self._tmp.write(text)

    def commit(self):
        if self._path is None:
            self._tmp.seek(0)
            while True:
                chunk = self._tmp.read(65536)
                if not chunk:
                    break
                sys.stdout.write(chunk)
            self._tmp.close()
        else:
            self._tmp.close()
            os.replace(self._name, self._path)

    def abort(self):
        name = self._name
        try:
            self._tmp.close()
        finally:
            if name is not None:
                try:
                    os.unlink(name)
                except OSError:
                    pass


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="twinmark",
        description="标识符归一与同形字检测：注册判定与比对判定。",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("evaluate", "逐条判定，输出 JSONL 结果行"),
        ("report", "在结果上加统计与原串，输出报告 JSON"),
    ):
        sub_parser = sub.add_parser(command, help=help_text)
        sub_parser.add_argument(
            "--map", dest="maps", action="append", required=True,
            metavar="TSV", help="混淆映射表，可多次给并按序合并",
        )
        sub_parser.add_argument(
            "--cases", dest="cases", action="append", required=True,
            metavar="JSONL", help="用例文件，可多次给并按序处理",
        )
        sub_parser.add_argument(
            "--out", dest="out", default=None,
            metavar="PATH", help="输出路径，省略写 stdout",
        )
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        index = load_maps(args.maps)
        spool = _Spool(args.out)
        try:
            if args.command == "evaluate":
                run_evaluate(args.cases, index, spool.write)
            else:
                run_report(args.cases, index, spool.write)
        except BaseException:
            spool.abort()
            raise
        spool.commit()
    except (MapError, CaseError, NormalizeError) as exc:
        print("twinmark: error: %s" % exc, file=sys.stderr)
        return 1
    return 0
