# Changelog

## 0.3.1 (2026-07-08)

### 新增功能

- `--listmodes` 命令行选项：枚举所有显示器所有可用分辨率（含刷新率标记）
- 新增 3 项 pytest 测试（`_check_relative_mutex`），总测试数 139

### 改进

- `--help` 输出按功能分组（查询/显示配置/相对定位/图像调节/其他），更易读
- 相对定位参数互斥校验改为手动检查，避免 argparse 互斥组无法分组显示的局限
- `_enumerate_modes` 提升为公开函数（原 `_enumerate_modes`）
- 提取 `_MOD_OP_ATTRS` 常量消除 `_is_mod_op` 与 `main()` 间的重复列表

## 0.3.0 (2026-07-08)

### 新增功能

- EDID 信息读取（制造商、产品名、序列号、生产日期、物理尺寸），显示于 `--prop` 输出
- 所有 CLI 错误现在附带恢复建议（`建议:` 节），帮助用户快速定位问题

### 架构改进

- `win32/bindings.py`（299 行 → 92 行）分解出 `win32/utils.py`（232 行）：工具函数与原始 API 绑定分离
- `api.py`（297 行 → 208 行）分解出 `edid.py`（105 行）：EDID 逻辑独立维护
- 消除 `api.py` → `formatter.py` 的跨层依赖（`_short_name` 内联）
- 所有模块行数严格 ≤300，目录文件数 ≤8

### 错误处理完善

- **格式改进**：`_fail()` 输出增加 `建议:` 标题 + `  - ` 前缀，恢复建议结构化展示
- **19 处 `_fail()` 调用**全部添加恢复建议，涵盖：
  - 显示器未找到 → 列出可用显示器
  - 分辨率设置失败 → 提示 `--listmodes` 查看可用模式
  - SDC 相关失败 → 提示虚拟显示器驱动干扰可能
  - 亮度/伽马设置失败 → 提示驱动或远程桌面限制
- **feature 层日志增强**：
  - 分辨率失败日志包含具体宽高值
  - 布局操作（set_position/set_rotation/set_primary/set_off）日志标注操作名
  - 伽马/亮度日志包含失败时的输入参数值

### 测试覆盖

- 测试用例从 105 项增加到 **130 项**
- 新增 `tests/test_edid.py`（15 项）：EDID 解析纯逻辑测试（含边界条件）
- 补充 formatter 边缘测试：空列表、全部断连、270° 旋转、无模式列表
- 补充 CLI handler 测试：`_handle_auto`、`_handle_rotate`、`_handle_primary`、`_handle_preferred`、`_handle_off`
- 所有测试通过

### Bug 修复

- EDID 序列号解析越界：序列号超 13 字节时溢出到下一个描述符块
- `api._short_name` 与 `formatter._short_name` 实现不一致导致查询异常
- 测试文件中重复的模块级 import 移到文件顶部

### 文档

- 新增 `docs/architecture.md`：架构设计文档（含 EDID 章节）
- 新增 `discuss/technical-design.md`：技术方案讨论文档
- 更新 `CLAUDE.md`：架构图、Win32 API 选型表
- `README.md`：新增 `--noprimary`、`--properties` 文档，更新项目结构图
- 扩展 `scripts/completions.ps1`：补充 `--properties`、`--noprimary` 补全

## 0.2.0 (2026-07-05)

- 首个公开版本
- 完整实现 xrandr 核心功能集（查询、分辨率、刷新率、位置、旋转、主屏、关闭、亮度、伽马、相对定位、JSON 输出等）
- Nuitka 单文件 exe 构建
- 105 项 pytest 测试
