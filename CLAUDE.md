# winrandr — 项目规范

## 项目概要

Windows 上的 xrandr 替代工具，通过 Win32 `QueryDisplayConfig`/`SetDisplayConfig` API 管理显示器布局、分辨率、刷新率和旋转方向。

## 架构分层

```
main.py                   入口委托（转发到 winrandr.cli）
winrandr/
├── __init__.py           版本号 + 公开 API 重导出
├── __main__.py           python -m winrandr 入口
├── cli.py                CLI 层：argparse + xrandr 风格输出
├── api.py                公开 API：11 个函数（含子模块 re-export）
├── features/
│   ├── gamma.py          伽马校正与亮度
│   └── layout.py         位置/旋转/主屏/关闭/相对定位
├── models.py             数据模型 (DisplayInfo, DisplayMode)
├── constants.py          Win32 常量 + 旋转映射
├── structures.py         ctypes 结构体定义
└── bindings.py           Win32 函数绑定 + 内部工具
```

## 关键设计决策

- **ctypes 而非 pywin32**：零外部依赖，仅需 Python 标准库
- **`ChangeDisplaySettingsEx` 改分辨率**：比 `SetDisplayConfig` 更简洁可靠
- **`SetDisplayConfig` 改位置/旋转/主屏**：`ChangeDisplaySettingsEx` 不支持这些操作
- **`EnumDisplaySettings` 回退**：`QueryDisplayConfig` 返回的 mode 数组可能不含所有显示器的 target mode，此时用 `EnumDisplaySettings` 获取刷新率
- **去重**：Windows 可能为同一个显示器返回多条路径，按 GDI 名去重

## Windows 显示 API 的选择

| 操作 | API |
|------|-----|
| 查询 | `QueryDisplayConfig` |
| 列模式 | `EnumDisplaySettings` 遍历 |
| 改分辨率 | `ChangeDisplaySettingsEx(CDS_UPDATEREGISTRY)` |
| 改位置 | `SetDisplayConfig` → sourceMode.position |
| 改旋转 | `SetDisplayConfig` → targetInfo.rotation |
| 设主屏 | `SetDisplayConfig` → sourceInfo.statusFlags |
| 关显示器 | `SetDisplayConfig` → 移除路径 |

## 代码规范

- **每文件 ≤300 行**（Python 动态语言限制）
- **蛇形命名**（源文件、函数、变量）
- **结构体全大写**（与 Windows SDK 一致）
- **下划线前缀**表示内部（`_query_active_config`）
- **日志用中文消息**
