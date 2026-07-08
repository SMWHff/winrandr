# Changelog

## 0.7.0 (2026-07-09)

### 架构重构

- `tests/unit/` 目录拆分（9→2 文件）：CLI 测试移入 `cli/`，formatter 测试移入 `formatter/`，
  配置存档测试移入 `profiles/`
- `tests/integration/` 目录拆分（9→4 文件）：5 个 CLI 入口测试移入 `cli/` 子目录
- 消除 `profiles.py` 和 `cli/__init__.py` 中的局部导入（晦涩性坏味道）
- 消除 `cli/handlers.py` 中的冗余局部导入

### 新增

- PowerShell 模块 cmdlet 从 7 个扩展到 14 个：`Set-WinRandrRotation`、`Set-WinRandrOff`、
  `Set-WinRandrAuto`、`Set-WinRandrGamma`、`Set-WinRandrRelative`、`Get-WinRandrProfile`、
  `Remove-WinRandrProfile`；统一错误处理（退出码检查）
- GitHub Issue 模板：Bug 报告 + 功能请求

### CI/构建

- test.yml + release.yml 添加 uv 缓存步骤（基于 uv.lock 哈希）
- 覆盖率失败阈值从 80% 提升至 95%（CI + pyproject.toml）
- 添加 `[tool.coverage.report] fail_under = 95` 本地默认

### Bug 修复

- 修复 `test_profiles_extra.py` 未关闭文件句柄导致的 `ResourceWarning`

### 文档

- CLAUDE.md 更新测试目录架构描述
- CHANGELOG 补充 0.6.0 及 0.7.0 变更

## 0.6.0 (2026-07-08)

### 架构重构

- `winrandr/cli/handlers.py`（309 行）拆分为 `handlers.py`（203 行）+ `common.py`（111 行）
- `winrandr/__init__.py`（113→65 行）：消除 `as X as X` 冗余重导出模式
- 新增 5 个测试文件维持 ≤300 行约束

### 测试

- 395 项，全模块 100% 分支覆盖率（1371 语句）

### Breaking Changes

- `-v` 现在等价于 `--version`（与 xrandr 一致），不再是 `--verbose` 的别名。
  如需详细日志请使用 `--verbose`（长选项不变）。

### 架构重构

- `winrandr/cli.py` + `cli_handlers.py` → `winrandr/cli/__init__.py` + `handlers.py` 子包
- `winrandr/` 目录文件数从 9 降至 7，符合 ≤8 规范

### 新增

- `--list-providers`：`--listproviders` 的兼容别名
- `--list-monitors`：`--listmonitors` 的兼容别名

### 测试

- 395 项（新增 2 项：`-v` 版本测试、解析器 `-v` → version 测试）
- 全模块 100% 分支覆盖率（1345 语句）

## 0.4.0 (2026-07-08)

### 新增功能

- `--brightness` / `--gamma` 支持不带 `--output`：应用到所有已连接显示器（一次性批量调暗/伽马校正）
- 全局操作模式下按显示器名逐条输出进度，单显示器失败不影响其他显示器

### 质量提升

- 全模块 100% 分支覆盖率（cli.py 补齐最后 6 个缺口：空存档名校验、load_profile 失败、identify 调用、displays 空列表分支）
- 测试总数从 373 增至 393 项
- 新增 6 项 CLI 集成测试：全局亮度/伽马（正常、dry-run、无显示器、混用其他操作、带 --output 兼容）

### 文档

- docs/usage.md / CLI --help 示例更新：标注 `--brightness` / `--gamma` 可批量操作
- 覆盖率报告：`cli.py` 100%（192→206 行）

## 0.3.6 (2026-07-08)

### 新增功能

- 配置存档管理（Profile）：`--save-profile` / `--load-profile` / `--list-profiles` / `--delete-profile`
- `--load-profile --dry-run`：预览存档与当前配置的差异，不实际执行
- `--list-profiles --json`：JSON 格式输出存档列表
- `--identify`：闪屏识别显示器（需配合 `--output`）
- `diff_profile()` 公开 API：返回存档与当前配置的人类可读变更列表

### 增强

- `--save-profile --dry-run`：预览将要保存的显示器配置（含分辨率/位置/旋转/主屏状态）
- `--save-profile` / `--load-profile` / `--delete-profile` 空名校验，明确提示"存档名不能为空"
- Bash / PowerShell 补全支持 `--load-profile` / `--delete-profile` 存档名动态补全
- `--list-profiles` 文本输出显示每个存档包含的显示器名及分辨率
- `list_profiles()` 返回新增 `displays` 字段（显示器摘要列表）
- JSON 输出一致性：`--list-profiles --json` / `--listproviders --json` / `--listmonitors --json` 空结果也输出 `[]`
- `load_profile` / `save_profile` 失败时同时输出 stderr 错误信息（不依赖 `--verbose`）
- 消除 profiles.py 中 `__import__("datetime")` 丑陋写法

### 文档

- README.md / CLAUDE.md / docs/usage.md / docs/architecture.md 同步更新
- test count 332 → 361

### 测试

- 测试总数从 328 增至 373 项
- 新增 `tests/unit/test_profiles.py`（26 项）：存档保存/加载/列表/删除/差异/预览/JSON 序列化全覆盖
- 新增 9 项 CLI 集成测试：profile 操作的全路径覆盖（含成功/失败/dry-run 分支）

## 0.3.5 (2026-07-08)

### 质量提升

- 消除所有 ruff 违规（E701/E702/E741/E402/F811），CI 新增 lint 步骤
- 修复 5 处 mock 路径 bug（`_handle_listmodes` 测试 mock 目标错误，测试形同虚设）
- gamma.py 提取 `_apply_gamma()` 消除 set_brightness/set_gamma 间的代码重复
- layout.py 提取 `_require_active_config()` 消除 5 处 SDC 检查 + 配置查询的代码重复
- 精确化 formatter.py/api.py/edid.py 中 6 处类型注解（`list`/`dict` → `list[DisplayInfo]`/`dict[str, str]`）
- 新增 `scripts/completions.bash`：Bash/Zsh Tab 补全（WSL/Cygwin/Git Bash）
- 分支覆盖率提升至 100%（补齐 api.py/cli_handlers.py/resolution.py 的 9 处缺口）

### 测试

- 测试总数从 312 增至 328 项
- 新增测试：noprimary 失败路径、verbose 日志级别、listproviders/monitors 空列表、query 不存在的 output、modop 缺少 output、gamma 异常路径、entry guard、`_setup_logging` 首次调用
- `test_features.py`（390 行）拆分为 `test_gamma.py` / `test_layout.py` / `test_resolution.py`
- tests/ 目录分层重构 → `unit/` / `features/` / `integration/` 三层子目录

### 文档

- CLAUDE.md / README.md 更新测试数（312→328）和覆盖率（99%→100%）
- scripts/test.sh 新增覆盖率报告步骤

## 0.3.4 (2026-07-08)

### 改进

- `query_all_config()` 新增 Module-level 缓存（与 query_active_config 统一失效策略）
- 消除 `_handle_listmodes` 中冗余的 `enumerate_modes()` 调用（list_displays 已枚举所有模式）
- `_invalidate_qdc_cache()` 同时清除 active 和 all 两个缓存
- `_fmt_modes` 升格为公开 API `fmt_modes`（消除跨模块导入私有函数的代码坏味道）
- 修复 `scripts/build.sh` Python 3.13+ 编译器注释（MSVC → zig）
- 修复 `_setup_logging()` ResourceWarning：改用 `delay=True` 延迟打开日志文件 + 单例模式避免重复创建 handler
- 新增 `.github/workflows/test.yml`：GitHub Actions CI（4 个 Python 版本矩阵）
- 补齐 utils.py / formatter.py 多处缺失的类型注解
- `apply_filtered()` 空结果新增 warning 日志
- 配置文件补全脚本：新增 `-v`/`-o`/`-m`/`-r`/`-p` 短选项及 `--refresh`/`--dryrun` 别名

### 测试

- 测试总数增至 250 项
- 新增集成测试：--prop --json、--listmonitors --json、--listmodes 无显示器场景
- 新增 7 项 `filter_valid_paths` 纯逻辑测试（覆盖索引无效、越界、类型不匹配、混合、空数组）
- 新增 `test_invalidate_qdc_cache_both`：验证缓存失效函数同时清除两个缓存
- 新增 `tests/test_api.py`（12 项）：API 函数直接单元测试（list_displays / set_position_relative 全方向 / list_providers / get_display_props 边界）
- layout 模块补充 5 项错误路径测试（set_rotation config_none/device_not_found、set_position 无效 mode 索引、set_off/primary config_none）

### 架构

- 新增 `tests/test_features.py`（27 项）：features/resolution.py + features/gamma.py + features/layout.py 直接 mock 测试
- `test_cli_handlers.py` 新增 10 项非 dry-run 正向测试：验证各 handler 正确调用了 API 函数
- `test_edid.py` 合并入 `test_models.py`（248 行），tests/ 目录保持 8 个文件

## 0.3.3 (2026-07-08)

### 改进

- `test_cli.py` 拆分出 `test_cli_main.py`，单文件从 394 行降至 183 行
- `enumerate_modes` 加入 `__init__.py` 公开 API 导出（共 17 个公开函数）
- main() 集成测试新增 19 项（全覆盖所有 CLI 操作 + listmodes 错误路径 + 无显示器场景）
- 测试总数增至 185 项
- `test_constants.py` 合并入 `test_models.py`，tests/ 目录降至 8 个文件
- 新增未知角度回退测试（_rotation_part 边界情况）
- 新增 --help 关键选项完整性测试
- 新增非 dry-run 正向测试：验证 set_resolution/set_position/set_primary/set_off/set_brightness 实际被调用
- 新增 --current / --dryrun 别名测试
- 修复 docs/architecture.md 公开函数数（16→17）、补充 enumerate_modes/set_noprimary API 文档
- 更新 docs/usage.md --listmodes 输出示例
- 集成测试新增 --listmodes 验证

## 0.3.2 (2026-07-08)

### 新增功能

- `--listmodes` 命令行选项：枚举所有显示器所有可用分辨率和刷新率（支持 `--json`）
- main() 集成测试覆盖全部 CLI 操作路径（12 项 mock Win32 API 测试）

### 改进

- `_enumerate_modes` 提升为公开函数（原 `_enumerate_modes`）
- 提取 `_MOD_OP_ATTRS` 常量消除 `_is_mod_op` 与 `main()` 间的重复列表
- 测试总数增至 159 项

## 0.3.1 (2026-07-08)

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
