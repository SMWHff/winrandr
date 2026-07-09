"""CLI 通用工具函数（日志、参数校验、辅助函数）。"""

import logging
import os
import sys
from argparse import Namespace
from typing import NoReturn

from winrandr.api import list_displays, list_providers
from winrandr.win32.constants import GDI_DEVICE_PREFIX

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    # 可执行文件打包后，日志输出到 exe 同目录；否则输出到项目根目录下的 logs/
    if getattr(sys, "frozen", False):
        log_dir = os.path.join(os.path.dirname(sys.executable), "logs")
    else:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")

    root.setLevel(logging.WARNING)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stderr),
    ]
    # 文件日志：目录创建失败或不可写时静默降级，不阻塞程序
    try:
        os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(log_dir, "winrandr.log"), encoding="utf-8", delay=True)
        handlers.insert(0, fh)
    except OSError:
        logger.warning("无法创建日志目录 %s，文件日志已禁用", log_dir)

    for h in handlers:
        h.setFormatter(fmt)
        root.addHandler(h)


def _normalize_name(name: str) -> str:
    n = name.strip().upper()
    prefix = GDI_DEVICE_PREFIX
    if n.startswith(prefix):
        return n
    if n.startswith("DISPLAY"):
        return prefix + n
    return prefix + "DISPLAY" + n


def _fail(msg: str, suggestions: list[str] | None = None) -> NoReturn:
    print(f"错误: {msg}", file=sys.stderr)
    if suggestions:
        print("建议:", file=sys.stderr)
        for s in suggestions:
            print(f"  - {s}", file=sys.stderr)
    sys.exit(1)


def _msg(args: Namespace, text: str) -> None:
    print(f"(Dry-Run) {text}" if args.dry_run else text)


def _list_available_displays() -> str:
    names = {d.name.replace(GDI_DEVICE_PREFIX, "") for d in list_displays()}
    for p in list_providers():
        sn = p["name"].replace(GDI_DEVICE_PREFIX, "")
        if sn.startswith("DISPLAY"):
            names.add(sn)

    def _sort_key(n: str) -> tuple[int, int | str]:
        return (0, int(n.replace("DISPLAY", ""))) if n.replace("DISPLAY", "").isdigit() else (1, n)

    sorted_n = sorted(names, key=_sort_key)
    return "可用显示器: " + ", ".join(sorted_n) if sorted_n else "未检测到显示器"


_MOD_OP_ATTRS = [
    "mode",
    "pos",
    "rotate",
    "primary",
    "preferred",
    "off",
    "brightness",
    "night_mode",
    "reflect",
    "gamma",
    "left_of",
    "right_of",
    "above",
    "below",
    "same_as",
    "auto",
    "noprimary",
    "identify",
]


def _is_mod_op(args: Namespace) -> bool:
    return any(getattr(args, a, None) for a in _MOD_OP_ATTRS)


def _apply_aliases(args: Namespace) -> None:
    if args.size and not args.mode:
        args.mode = args.size
    if args.orientation and not args.rotate:
        _ori = {"0": "normal", "1": "normal", "2": "inverted", "3": "left"}
        args.rotate = _ori.get(args.orientation, args.orientation)
    if args.listactivemonitors:
        args.listmonitors = True
    if args.reflect == "normal":
        args.reflect = None
    # --reflect 已显式设置时跳过 -x/-y 的覆盖
    if args.reflect is not None:
        if args.x or args.y:
            logger.warning("检测到 --reflect 与 -x/-y 同时使用，-x/-y 将被忽略")
    else:
        if args.x and args.y:
            args.reflect = "xy"
        elif args.x:
            args.reflect = "x"
        elif args.y:
            args.reflect = "y"


def _check_relative_mutex(args: Namespace) -> None:
    rel_args = [args.left_of, args.right_of, args.above, args.below, args.same_as]
    if sum(1 for r in rel_args if r) > 1:
        _fail("相对定位参数是互斥的，只能使用 --left-of / --right-of / --above / --below / --same-as 之一")
