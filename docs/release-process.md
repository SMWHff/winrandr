# 发版流程

## 概述

winrandr 每轮发版由以下步骤组成。因 GitHub Actions 暂不可用，所有操作在本地执行。

## 前置条件

- [gh CLI](https://cli.github.com/) 已登录且可访问 `SMWHff/winrandr`
- [PyPI 令牌](https://pypi.org/manage/account/token/)（未设置时会交互式提示输入）
- 当前在 `main` 分支

## 快速发版

```bash
# 交互模式（每步确认）
bash scripts/release/publish.sh patch   # 补丁版（0.9.2 → 0.9.3）
bash scripts/release/publish.sh minor   # 小版本（0.9.2 → 0.10.0）
bash scripts/release/publish.sh major   # 大版本（0.9.2 → 1.0.0）

# 全自动模式（跳过确认）
AUTO_CONFIRM=1 bash scripts/release/publish.sh patch

# 全自动 + 指定 PyPI 令牌
AUTO_CONFIRM=1 UV_PUBLISH_TOKEN="pypi-xxx" bash scripts/release/publish.sh patch
```

脚本依次执行以下 8 步，每步有确认提示（`AUTO_CONFIRM=1` 时自动继续）：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 运行 `test.sh`（lint + pytest + 覆盖率） | 必须 ≥95% |
| 2 | 更新 `pyproject.toml` + `winrandr/__init__.py` 版本号 | 交互确认 |
| 3 | 检查 `docs/CHANGELOG.md` 是否包含新版条目 | 缺失则中止 |
| 4 | Nuitka 编译单文件 exe（约 3-8 分钟） | 自动校验产物 |
| 5 | `git commit` + `git tag vX.Y.Z` | — |
| 6 | `git push origin main --tags` | — |
| 7 | `gh release create` 创建 GitHub Release + 上传 exe | — |
| 8 | `uv build` + `uv publish` 发布到 PyPI | 需令牌 |

## 分步执行

如需手动分步执行：

### 1. 质量门禁

```bash
bash scripts/dev/test.sh
```

### 2. 更新版本号

```bash
bash scripts/release/bump-version.sh patch   # 或 minor / major
```

编辑两个文件：
- `winrandr/__init__.py` — `__version__`
- `pyproject.toml` — `project.version` + `tool.nuitka.file-version`

### 3. CHANGELOG

编辑 `docs/CHANGELOG.md`，在顶部添加：

```markdown
## X.Y.Z (YYYY-MM-DD)

### 新功能 / Bug 修复 / 重构 / 文档 / CI

- ...
```

### 4. 构建 exe

```bash
bash scripts/build/build.sh
# 输出: dist/winrandr.exe
```

### 5. 提交 + 标签

```bash
git add pyproject.toml winrandr/__init__.py docs/CHANGELOG.md
git commit -m "bump version: X.Y.Z → X.Y.Z+1"
git tag vX.Y.Z
```

### 6. 推送

```bash
git push origin main
git push origin vX.Y.Z
```

### 7. GitHub Release

```bash
gh release create vX.Y.Z \
    --title "vX.Y.Z" \
    --notes "发布说明" \
    dist/winrandr.exe
```

### 8. PyPI 发布

```bash
uv build
uv publish
```

## 版本号策略

遵循 [SemVer](https://semver.org/)：

| 级别 | 场景 | 示例 |
|------|------|------|
| patch | Bug 修复、重构、测试、文档 | 0.9.2 → 0.9.3 |
| minor | 新功能、非兼容性改进 | 0.9.2 → 0.10.0 |
| major | 破坏性变更 | 0.9.2 → 1.0.0 |

## CHANGELOG 规范

- 日期格式：`YYYY-MM-DD`
- 按分类组织：`### 新功能` / `### Bug 修复` / `### 重构` / `### 文档` / `### CI` / `### 测试`
- 每个条目以 `-` 开头，描述变更内容
- 如有关联 Issue/PR，尾部标注 `(#123)`

## 回滚

```bash
# 回滚版本号变更（未推送时）
git checkout -- pyproject.toml winrandr/__init__.py

# 删除标签（未推送时）
git tag -d vX.Y.Z

# 删除远程标签（已推送时）
git push origin --delete vX.Y.Z

# 删除 GitHub Release
gh release delete vX.Y.Z

# 从 PyPI 删除（极少使用）
# https://pypi.org/manage/project/winrandr/releases/
```
