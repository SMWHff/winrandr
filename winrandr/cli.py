"""CLI 入口：argparse 解析 + 主流程编排。"""
import argparse
import logging
import sys

from winrandr import __version__
from winrandr.api import list_displays, get_display_props, list_providers, set_noprimary
from winrandr.formatter import format_displays, format_monitor_list
from winrandr.cli_handlers import (
    _setup_logging, _normalize_name, _fail, _msg, _list_available_displays,
    _MOD_OP_ATTRS, _is_mod_op, _apply_aliases, _check_relative_mutex,
    _handle_auto, _handle_mode, _handle_pos, _handle_rotate,
    _handle_primary, _handle_preferred, _handle_off,
    _handle_brightness, _handle_reflect, _handle_gamma,
    _handle_relative, _handle_listmodes, _handle_identify,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="winrandr — 类 xrandr 的 Windows 显示配置工具",
        epilog="""示例：
  winrandr                             列出所有显示器
  winrandr --output DISPLAY1 --mode 1920x1080 --rate 60
  winrandr --output DISPLAY1 --pos 0x0 --rotate normal
  winrandr --output DISPLAY1 --primary --off
  winrandr --output DISPLAY1 --left-of DISPLAY2
  winrandr --brightness 0.7             批量调暗所有显示器
  winrandr --gamma 1.0:0.9:0.8          批量设置伽马
  winrandr --identify --output DISPLAY1
  winrandr --save-profile docked        保存当前配置为存档
  winrandr --load-profile docked        恢复存档配置
  winrandr --list-profiles              列出所有存档""",
    )
    p.add_argument("--version", action="version", version=f"winrandr {__version__}")

    g_query = p.add_argument_group("查询选项")
    g_query.add_argument("--listmodes", action="store_true", help="列出每个显示器所有可用分辨率")
    g_query.add_argument("-q", "--query", action="store_true", help="查询当前显示状态")
    g_query.add_argument("--current", action="store_true", help=argparse.SUPPRESS)
    g_query.add_argument("--prop", "--properties", action="store_true", help="显示显示器扩展属性（设备 ID、状态标志等）")
    g_query.add_argument("--json", action="store_true", help="以 JSON 格式输出显示器信息")
    g_query.add_argument("--listproviders", action="store_true", help="列出 GPU 适配器")
    g_query.add_argument("--listmonitors", action="store_true", help="列出带编号的显示器列表")
    g_query.add_argument("--listactivemonitors", action="store_true", help=argparse.SUPPRESS)

    g_cfg = p.add_argument_group("显示配置")
    g_cfg.add_argument("--output", "-o", help="显示器名（如 DISPLAY1）")
    g_cfg.add_argument("--mode", "-m", help="分辨率（如 1920x1080）")
    g_cfg.add_argument("-s", "--size", help=argparse.SUPPRESS)
    g_cfg.add_argument("--rate", "-r", "--refresh", type=float, help="刷新率（Hz）")
    g_cfg.add_argument("--pos", "-p", help="桌面位置（如 0x0）")
    g_cfg.add_argument("--rotate", choices=["normal", "left", "right", "inverted"], help="旋转方向")
    g_cfg.add_argument("--auto", action="store_true", help="启用显示器并使用首选分辨率")
    g_cfg.add_argument("--preferred", action="store_true", help="设为注册表首选分辨率")
    g_cfg.add_argument("--primary", action="store_true", help="设为主显示器")
    g_cfg.add_argument("--off", action="store_true", help="关闭显示器")
    g_cfg.add_argument("--noprimary", action="store_true", help="清除所有显示器的主显示器标记")
    g_cfg.add_argument("--orientation", choices=["normal", "inverted", "left", "right", "0", "1", "2", "3"], help=argparse.SUPPRESS)

    g_rel = p.add_argument_group("相对定位（互斥）")
    g_rel.add_argument("--left-of", metavar="REF", help="放在参考显示器左侧")
    g_rel.add_argument("--right-of", metavar="REF", help="放在参考显示器右侧")
    g_rel.add_argument("--above", metavar="REF", help="放在参考显示器上方")
    g_rel.add_argument("--below", metavar="REF", help="放在参考显示器下方")
    g_rel.add_argument("--same-as", metavar="REF", help="与参考显示器同位置（镜像）")

    g_img = p.add_argument_group("图像调节")
    g_img.add_argument("--brightness", type=float, help="亮度值（0.1-2.0，1.0 为正常）")
    g_img.add_argument("--gamma", metavar="R:G:B", help="伽马校正（如 1.0:0.9:0.8）")
    g_img.add_argument("--reflect", choices=["normal", "x", "y", "xy"], help="镜像翻转（仅 xy 支持）")
    g_img.add_argument("-x", action="store_true", help=argparse.SUPPRESS)
    g_img.add_argument("-y", action="store_true", help=argparse.SUPPRESS)

    g_profile = p.add_argument_group("存档管理（保存/恢复显示器布局）")
    g_profile.add_argument("--save-profile", metavar="NAME", help="保存当前配置为存档")
    g_profile.add_argument("--load-profile", metavar="NAME", help="加载指定存档并恢复显示器布局")
    g_profile.add_argument("--list-profiles", action="store_true", help="列出所有已保存的存档")
    g_profile.add_argument("--delete-profile", metavar="NAME", help="删除指定存档")

    g_misc = p.add_argument_group("其他")
    g_misc.add_argument("--dry-run", "--dryrun", action="store_true", help="模拟操作，不实际更改配置")
    g_misc.add_argument("--verbose", "-v", action="store_true", help="详细日志输出（调试用）")
    g_misc.add_argument("--identify", action="store_true", help="通过闪烁屏幕识别显示器")
    g_misc.add_argument("--screen", help=argparse.SUPPRESS)
    g_misc.add_argument("--nograb", action="store_true", help=argparse.SUPPRESS)
    return p


def main() -> None:
    parser = _build_parser()
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
