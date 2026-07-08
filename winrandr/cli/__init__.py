"""CLI 入口：argparse 解析 + 主流程编排。"""

import logging
import sys
from argparse import Namespace

from winrandr.api import get_display_props, list_displays, list_providers, set_noprimary
from winrandr.cli.common import (
    _MOD_OP_ATTRS,
    _apply_aliases,
    _check_relative_mutex,
    _fail,
    _is_mod_op,
    _list_available_displays,
    _msg,
    _normalize_name,
    _setup_logging,
)
from winrandr.cli.handlers import (
    _handle_auto,
    _handle_brightness,
    _handle_gamma,
    _handle_identify,
    _handle_listmodes,
    _handle_mode,
    _handle_off,
    _handle_pos,
    _handle_preferred,
    _handle_primary,
    _handle_reflect,
    _handle_relative,
    _handle_rotate,
)
from winrandr.cli.parser import build_parser
from winrandr.formatter import format_displays, format_monitor_list


def _handle_providers(args: Namespace) -> None:
    providers = list_providers()
    if args.json:
        import json

        print(json.dumps(providers, indent=2, ensure_ascii=False))
    elif not providers:
        print("未检测到 GPU 适配器。")
    else:
        print("Providers:")
        for i, p in enumerate(providers):
            print(f"  Provider {i}: {p['string']} ({p['name']})")


def _handle_monitors(args: Namespace) -> None:
    displays = list_displays()
    if args.json:
        import json
        from dataclasses import asdict

        print(json.dumps([asdict(d) for d in displays if d.connected], indent=2, ensure_ascii=False))
    elif not displays:
        print("未检测到显示器。")
    else:
        print(format_monitor_list(displays))


def _handle_list_profiles(args: Namespace) -> None:
    from winrandr.profiles import list_profiles

    profiles = list_profiles()
    if args.json:
        import json

        print(json.dumps(profiles, indent=2, ensure_ascii=False))
    elif not profiles:
        print("暂无存档。")
    else:
        print("已保存的存档：")
        for p in profiles:
            dt = p["created"][:10] if p["created"] else "未知"
            display_names = ", ".join(p.get("displays", [])) if p.get("displays") else ""
            line = f"  {p['name']:20s}  {dt}  {p['display_count']} 台"
            if display_names:
                line += f"  [{display_names}]"
            print(line)


def _handle_save_profile(args: Namespace) -> None:
    if not args.save_profile:
        _fail("存档名不能为空")
    if args.dry_run:
        from winrandr.profiles import preview_save

        for line in preview_save():
            print(line)
    else:
        from winrandr.profiles import save_profile

        if not save_profile(args.save_profile):
            _fail(f"保存存档失败: {args.save_profile}")
        print(f"已保存配置为「{args.save_profile}」")


def _handle_load_profile(args: Namespace) -> None:
    if not args.load_profile:
        _fail("存档名不能为空")
    from winrandr.profiles import diff_profile, load_profile

    if args.dry_run:
        for line in diff_profile(args.load_profile):
            print(line)
    elif not load_profile(args.load_profile):
        _fail(f"加载存档失败: {args.load_profile}")
    else:
        print(f"已加载配置「{args.load_profile}」")


def _handle_delete_profile(args: Namespace) -> None:
    if not args.delete_profile:
        _fail("存档名不能为空")
    from winrandr.profiles import delete_profile

    if not delete_profile(args.delete_profile):
        _fail(f"删除存档失败: {args.delete_profile}")
    print(f"已删除存档「{args.delete_profile}」")


def _handle_query(args: Namespace) -> None:
    displays = list_displays()
    if not displays:
        print("未检测到活动显示器。")
        sys.exit(1)
    if args.output:
        device_name = _normalize_name(args.output)
        displays = [d for d in displays if d.name == device_name]
        if not displays:
            _fail(f"未找到显示器: {args.output}", [_list_available_displays()])
    if args.prop:
        for d in displays:
            d.properties = get_display_props(d.name)
    if args.json:
        import json
        from dataclasses import asdict

        print(json.dumps([asdict(d) for d in displays], indent=2, ensure_ascii=False))
    else:
        print(format_displays(displays))


def _handle_noprimary_only(args: Namespace) -> bool:
    """处理 --noprimary，返回 True 表示已处理完毕。"""
    if not args.dry_run and not set_noprimary():
        _fail("清除主显示器标记失败", ["某些虚拟显示器驱动（如向日葵）可能干扰此功能", "使用 --verbose 查看详细日志"])
    _msg(args, "已清除所有显示器的主显示器标记")
    other_ops = [a for a in _MOD_OP_ATTRS if a != "noprimary"]
    if not any(getattr(args, a, None) for a in other_ops):
        return True
    return False


def _handle_global_ops(args: Namespace) -> None:
    """处理全局亮度/伽马（不指定 --output 时）。"""
    targets = [d for d in list_displays() if d.connected]
    if not targets:
        _fail("没有已连接的显示器")
    for t in targets:
        short = t.name.replace("\\\\.\\", "")
        args.output = short
        if args.brightness is not None:
            _handle_brightness(args, t.name)
        if args.gamma is not None:
            _handle_gamma(args, t.name)


def _dispatch_display_ops(args: Namespace, device_name: str) -> None:  # noqa: C901  # 操作列表长但无简化空间
    """调度各显示操作。"""
    if args.auto:
        _handle_auto(args, device_name)
    if args.mode:
        _handle_mode(args, device_name)
    if args.pos:
        _handle_pos(args, device_name)
    if args.rotate:
        _handle_rotate(args, device_name)
    if args.primary:
        _handle_primary(args, device_name)
    if args.preferred:
        _handle_preferred(args, device_name)
    if args.off:
        _handle_off(args, device_name)
    if args.brightness is not None:
        _handle_brightness(args, device_name)
    if args.reflect:
        _handle_reflect(args, device_name)
    if args.gamma:
        _handle_gamma(args, device_name)
    if args.identify:
        _handle_identify(args, device_name)
    _handle_relative(args, device_name)


def main() -> None:  # noqa: C901  # 调度型函数，分支复杂度本质
    parser = build_parser()
    args = parser.parse_args()
    _setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    _apply_aliases(args)
    _check_relative_mutex(args)

    if args.listproviders:
        _handle_providers(args)
        return
    if args.listmonitors:
        _handle_monitors(args)
        return
    if args.listmodes:
        _handle_listmodes(args, args.json)
        return
    if args.list_profiles:
        _handle_list_profiles(args)
        return
    if args.save_profile is not None:
        _handle_save_profile(args)
        return
    if args.load_profile is not None:
        _handle_load_profile(args)
        return
    if args.delete_profile is not None:
        _handle_delete_profile(args)
        return

    if not _is_mod_op(args):
        _handle_query(args)
        return

    if args.noprimary and _handle_noprimary_only(args):
        return

    # 全局操作：亮度/伽马可不带 --output，应用到所有已连接显示器
    _global_only_attrs = frozenset({"brightness", "gamma"})
    if not args.output:
        mod_attrs = {a for a in _MOD_OP_ATTRS if getattr(args, a, None)}
        if mod_attrs and mod_attrs.issubset(_global_only_attrs):
            _handle_global_ops(args)
            return
        parser.error("--output 为必填参数")

    device_name = _normalize_name(args.output)
    if not any(d.name == device_name for d in list_displays()):
        _fail(f"未找到显示器: {args.output}", [_list_available_displays()])
    _dispatch_display_ops(args, device_name)


if __name__ == "__main__":
    main()
