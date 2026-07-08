"""CLI 入口：argparse 解析 + 主流程编排。"""
import logging
import sys

from winrandr.api import list_displays, get_display_props, list_providers, set_noprimary
from winrandr.formatter import format_displays, format_monitor_list
from winrandr.cli.handlers import (
    _setup_logging, _normalize_name, _fail, _msg, _list_available_displays,
    _MOD_OP_ATTRS, _is_mod_op, _apply_aliases, _check_relative_mutex,
    _handle_auto, _handle_mode, _handle_pos, _handle_rotate,
    _handle_primary, _handle_preferred, _handle_off,
    _handle_brightness, _handle_reflect, _handle_gamma,
    _handle_relative, _handle_listmodes, _handle_identify,
)
from winrandr.cli.parser import build_parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    _apply_aliases(args)
    _check_relative_mutex(args)

    # --listproviders / --listmonitors
    if args.listproviders:
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
        return
    if args.listmonitors:
        displays = list_displays()
        if args.json:
            from dataclasses import asdict
            import json
            print(json.dumps([asdict(d) for d in displays if d.connected], indent=2, ensure_ascii=False))
        elif not displays:
            print("未检测到显示器。")
        else:
            print(format_monitor_list(displays))
        return

    # --listmodes
    if args.listmodes:
        _handle_listmodes(args, args.json)
        return

    # 存档管理（不依赖 --output）
    if args.list_profiles:
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
                displays = ", ".join(p.get("displays", [])) if p.get("displays") else ""
                line = f"  {p['name']:20s}  {dt}  {p['display_count']} 台"
                if displays:
                    line += f"  [{displays}]"
                print(line)
        return
    if args.save_profile is not None:
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
        return
    if args.load_profile is not None:
        if not args.load_profile:
            _fail("存档名不能为空")
        from winrandr.profiles import load_profile, diff_profile
        if args.dry_run:
            for line in diff_profile(args.load_profile):
                print(line)
        elif not load_profile(args.load_profile):
            _fail(f"加载存档失败: {args.load_profile}")
        else:
            print(f"已加载配置「{args.load_profile}」")
        return
    if args.delete_profile is not None:
        if not args.delete_profile:
            _fail("存档名不能为空")
        from winrandr.profiles import delete_profile
        if not delete_profile(args.delete_profile):
            _fail(f"删除存档失败: {args.delete_profile}")
        print(f"已删除存档「{args.delete_profile}」")
        return

    # 查询模式
    if not _is_mod_op(args):
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
            from dataclasses import asdict
            import json
            print(json.dumps([asdict(d) for d in displays], indent=2, ensure_ascii=False))
        else:
            print(format_displays(displays))
        return

    # --noprimary 单独使用
    if args.noprimary:
        if not args.dry_run and not set_noprimary():
            _fail("清除主显示器标记失败", ["某些虚拟显示器驱动（如向日葵）可能干扰此功能", "使用 --verbose 查看详细日志"])
        _msg(args, "已清除所有显示器的主显示器标记")
        other_ops = [a for a in _MOD_OP_ATTRS if a != "noprimary"]
        if not any(getattr(args, a, None) for a in other_ops):
            return

    # 全局操作：亮度/伽马可不带 --output，应用到所有已连接显示器
    _GLOBAL_ONLY_ATTRS = frozenset({"brightness", "gamma"})
    if not args.output:
        mod_attrs = {a for a in _MOD_OP_ATTRS if getattr(args, a, None)}
        if mod_attrs and mod_attrs.issubset(_GLOBAL_ONLY_ATTRS):
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
            return
        parser.error("--output 为必填参数")
    device_name = _normalize_name(args.output)
    if not any(d.name == device_name for d in list_displays()):
        _fail(f"未找到显示器: {args.output}", [_list_available_displays()])

    # 调度各操作
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


if __name__ == "__main__":
    main()
