"""argparse 参数解析器定义。"""

import argparse

from winrandr import __version__


def build_parser() -> argparse.ArgumentParser:
    """构建并返回参数解析器。"""
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
    p.add_argument("-v", "--version", action="version", version=f"winrandr {__version__}")

    g_query = p.add_argument_group("查询选项")
    g_query.add_argument("--listmodes", action="store_true", help="列出每个显示器所有可用分辨率")
    g_query.add_argument("-q", "--query", action="store_true", help="查询当前显示状态")
    g_query.add_argument("--current", action="store_true", help=argparse.SUPPRESS)
    g_query.add_argument("--prop", "--properties", action="store_true",
                         help="显示显示器扩展属性（设备 ID、状态标志等）")
    g_query.add_argument("--json", action="store_true", help="以 JSON 格式输出显示器信息")
    g_query.add_argument("--listproviders", action="store_true", help="列出 GPU 适配器")
    g_query.add_argument("--list-providers", action="store_true", dest="listproviders", help=argparse.SUPPRESS)
    g_query.add_argument("--listmonitors", action="store_true", help="列出带编号的显示器列表")
    g_query.add_argument("--list-monitors", action="store_true", dest="listmonitors", help=argparse.SUPPRESS)
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
    g_cfg.add_argument("--orientation",
                       choices=["normal", "inverted", "left", "right", "0", "1", "2", "3"],
                       help=argparse.SUPPRESS)

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
    g_misc.add_argument("--verbose", action="store_true", help="详细日志输出（调试用）")
    g_misc.add_argument("--identify", action="store_true", help="通过闪烁屏幕识别显示器")
    g_misc.add_argument("--screen", help=argparse.SUPPRESS)
    g_misc.add_argument("--nograb", action="store_true", help=argparse.SUPPRESS)
    return p
