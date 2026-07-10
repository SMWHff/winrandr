#!/bin/bash
cd "$(dirname "$0")/../.."
set -euo pipefail

usage() {
    echo "用法: bash scripts/release/publish.sh <patch|minor|major>"
    echo ""
    echo "完整发版流程（8 步，每步确认）："
    echo "  1. 质量门禁 — 运行 test.sh（lint + pytest + 覆盖率）"
    echo "  2. 版本号更新 — pyproject.toml + __init__.py"
    echo "  3. CHANGELOG 检查 — 确认已包含新版条目"
    echo "  4. 构建 exe — Nuitka 编译单文件"
    echo "  5. 提交 + 标签 — git commit + git tag"
    echo "  6. 推送 — git push origin main --tags"
    echo "  7. GitHub Release — gh release create + 上传 exe"
    echo "  8. PyPI 发布 — uv build + uv publish"
    echo ""
    echo "环境要求: gh CLI 已登录, PyPI 令牌已配置"
    exit 1
}

confirm() {
    echo ""
    read -rp "  → 继续? (y/N) " REPLY
    [[ "$REPLY" != "y" ]] && echo "  已取消" && exit 1
}

[[ $# -lt 1 ]] && usage
LEVEL="$1"

# ── 前置检查 ──────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  前置检查                                    ║"
echo "╚══════════════════════════════════════════════╝"

BRANCH=$(git branch --show-current)
if [[ "$BRANCH" != "main" ]]; then
    echo "  ✗ 当前分支为 '$BRANCH'，发版必须从 main 分支执行"
    exit 1
fi
echo "  ✓ 分支: main"

if ! git diff --quiet; then
    echo "  ✗ 工作区有未提交的修改，请先提交或 stash"
    exit 1
fi
echo "  ✓ 工作区干净"

if ! gh auth status 2>&1 | grep -q "Logged in"; then
    echo "  ✗ gh CLI 未登录，请执行 gh auth login"
    exit 1
fi
echo "  ✓ gh CLI 已登录"

CURRENT=$(grep -m1 '^version' pyproject.toml | sed 's/.*"\(.*\)"/\1/')
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "$LEVEL" in
    patch) NEW="$MAJOR.$MINOR.$((PATCH + 1))" ;;
    minor) NEW="$MAJOR.$((MINOR + 1)).0" ;;
    major) NEW="$((MAJOR + 1)).0.0" ;;
    *)     echo "错误: 未知级别 '$LEVEL'，使用 patch|minor|major" && exit 1 ;;
esac
echo "  ✓ 版本: $CURRENT → $NEW"

# ── 1. 质量门禁 ──────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  第 1 步: 质量门禁                           ║"
echo "╚══════════════════════════════════════════════╝"
bash scripts/dev/test.sh
echo "  ✓ 测试通过"

# ── 2. 版本号更新 ──────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  第 2 步: 版本号更新                         ║"
echo "╚══════════════════════════════════════════════╝"
sed -i "s/^version = \"$CURRENT\"/version = \"$NEW\"/" pyproject.toml
sed -i "s/^file-version = \"$CURRENT\"/file-version = \"$NEW\"/" pyproject.toml
sed -i "s/^__version__ = \"$CURRENT\"/__version__ = \"$NEW\"/" winrandr/__init__.py
echo "  ✓ $CURRENT → $NEW"
confirm

# ── 3. CHANGELOG 检查 ──────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  第 3 步: CHANGELOG 检查                     ║"
echo "╚══════════════════════════════════════════════╝"
if grep -q "^## $NEW " docs/CHANGELOG.md 2>/dev/null; then
    echo "  ✓ CHANGELOG 已包含 v$NEW 条目"
else
    echo "  ✗ CHANGELOG 缺少 v$NEW 条目"
    echo ""
    echo "  请编辑 docs/CHANGELOG.md 添加："
    echo ""
    echo "  ## $NEW ($(date +%Y-%m-%d))"
    echo ""
    echo "  ### 新功能 / Bug 修复 / 重构 / 文档 / CI"
    echo "  - ..."
    echo ""
    echo "  恢复版本号: git checkout -- pyproject.toml winrandr/__init__.py"
    exit 1
fi
echo "  当前 CHANGELOG:"
grep -A 30 "^## $NEW " docs/CHANGELOG.md | head -30
confirm

# ── 4. 构建 exe ────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  第 4 步: 构建 exe                           ║"
echo "╚══════════════════════════════════════════════╝"
echo "  构建耗时约 2-5 分钟..."
bash scripts/build/build.sh
echo "  ✓ exe 位于 dist/winrandr.exe"
confirm

# ── 5. 提交 + 标签 ────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  第 5 步: 提交 + 打标签                      ║"
echo "╚══════════════════════════════════════════════╝"
git add pyproject.toml winrandr/__init__.py docs/CHANGELOG.md
git commit -m "bump version: $CURRENT → $NEW"
git tag "v$NEW"
echo "  ✓ commit + tag v$NEW 已创建"
confirm

# ── 6. 推送 ────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  第 6 步: 推送到 GitHub                      ║"
echo "╚══════════════════════════════════════════════╝"
git push origin main
git push origin "v$NEW"
echo "  ✓ 推送完成"
confirm

# ── 7. GitHub Release ─────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  第 7 步: 创建 GitHub Release                ║"
echo "╚══════════════════════════════════════════════╝"
NOTES=$(python -c "
import re
with open('docs/CHANGELOG.md') as f:
    content = f.read()
pattern = r'^## $NEW\s*\(.*?\)\s*\n(.*?)(?=\n## |\Z)'
match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
if match:
    print(match.group(1).strip())
")
gh release create "v$NEW" \
    --title "v$NEW" \
    --notes "$NOTES" \
    dist/winrandr.exe
echo "  ✓ GitHub Release v$NEW 已创建"
echo "    https://github.com/SMWHff/winrandr/releases/tag/v$NEW"
confirm

# ── 8. PyPI 发布 ──────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  第 8 步: 发布到 PyPI                        ║"
echo "╚══════════════════════════════════════════════╝"
uv build
uv publish
echo "  ✓ PyPI 发布完成"
echo "    https://pypi.org/project/winrandr/$NEW/"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  发布完成！v$NEW                            ║"
echo "╚══════════════════════════════════════════════╝"
