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
    echo "  4. 构建 exe — Nuitka 编译单文件 + 校验"
    echo "  5. 提交 + 标签 — git commit + git tag"
    echo "  6. 推送 — git push origin main --tags"
    echo "  7. GitHub Release — gh release create + 上传 exe"
    echo "  8. PyPI 发布 — uv build + uv publish"
    echo ""
    echo "环境变量:"
    echo "  AUTO_CONFIRM=1    跳过确认，全自动执行"
    echo "  UV_PUBLISH_TOKEN  PyPI 发布令牌（若未设置则提示）"
    exit 1
}

confirm() {
    if [[ "${AUTO_CONFIRM:-}" == "1" ]]; then
        echo "  → 自动继续"
        return
    fi
    echo ""
    read -rp "  → 继续? (y/N) " REPLY
    [[ "$REPLY" != "y" ]] && echo "  已取消" && exit 1
}

die() { echo "  ✗ $*"; exit 1; }
step() { echo ""; echo "╔══════════════════════════════════════════════╗"; echo "║  $1"; echo "╚══════════════════════════════════════════════╝"; }

[[ $# -lt 1 ]] && usage
LEVEL="$1"

# ── 前置检查 ──────────────────────────────────────────────
step "前置检查"
BRANCH=$(git branch --show-current)
[[ "$BRANCH" == "main" ]] || die "当前分支为 '$BRANCH'，发版必须从 main 分支执行"
echo "  ✓ 分支: main"

if ! git diff --quiet; then
    MODIFIED=$(git diff --name-only)
    [[ "$MODIFIED" == "docs/CHANGELOG.md" ]] \
        || die "工作区有未提交的修改，仅允许 CHANGELOG.md 未提交\n\n    修改了: $MODIFIED"
    echo "  ✓ CHANGELOG.md 已更新（将随发版提交）"
else
    echo "  ✓ 工作区干净"
fi

gh auth status 2>&1 | grep -q "Logged in" || die "gh CLI 未登录，执行 gh auth login"
echo "  ✓ gh CLI 已登录"

# 读取当前版本
CURRENT=$(grep -m1 '^version' pyproject.toml | sed 's/.*"\(.*\)"/\1/')
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"
case "$LEVEL" in
    patch) NEW="$MAJOR.$MINOR.$((PATCH + 1))" ;;
    minor) NEW="$MAJOR.$((MINOR + 1)).0" ;;
    major) NEW="$((MAJOR + 1)).0.0" ;;
    *)     die "未知级别 '$LEVEL'，使用 patch|minor|major" ;;
esac
echo "  ✓ 版本: $CURRENT → $NEW"

# ── 1. 质量门禁 ──────────────────────────────────────────
step "第 1 步: 质量门禁"
bash scripts/dev/test.sh
echo "  ✓ 测试通过"

# ── 2. 版本号更新 ──────────────────────────────────────
step "第 2 步: 版本号更新"
sed -i "s/^version = \"$CURRENT\"/version = \"$NEW\"/" pyproject.toml
sed -i "s/^file-version = \"$CURRENT\"/file-version = \"$NEW\"/" pyproject.toml
sed -i "s/^__version__ = \"$CURRENT\"/__version__ = \"$NEW\"/" winrandr/__init__.py
echo "  ✓ $CURRENT → $NEW"
confirm

# ── 3. CHANGELOG 检查 ──────────────────────────────────
step "第 3 步: CHANGELOG 检查"
grep -q "^## $NEW " docs/CHANGELOG.md 2>/dev/null \
    || die "CHANGELOG 缺少 v$NEW 条目，请编辑 docs/CHANGELOG.md 后重试\n\n  恢复版本号: git checkout -- pyproject.toml winrandr/__init__.py"
echo "  ✓ CHANGELOG 已包含 v$NEW 条目"
grep -A 30 "^## $NEW " docs/CHANGELOG.md | head -30
confirm

# ── 4. 构建 exe ────────────────────────────────────────
step "第 4 步: 构建 exe"
echo "  构建耗时约 3-8 分钟..."
bash scripts/build/build.sh
# 验证 exe 是否构建成功
EXE="dist/winrandr.exe"
if [ ! -f "$EXE" ]; then
    die "构建失败：$EXE 未生成"
fi
EXE_SIZE=$(wc -c < "$EXE" 2>/dev/null || echo 0)
if [ "$EXE_SIZE" -lt 1000000 ]; then  # 至少 1MB
    die "构建失败：$EXE 大小异常（${EXE_SIZE} bytes）"
fi
echo "  ✓ $EXE ($(du -h "$EXE" | cut -f1))"
confirm

# ── 5. 提交 + 标签 ────────────────────────────────────
step "第 5 步: 提交 + 打标签"
git add pyproject.toml winrandr/__init__.py docs/CHANGELOG.md
git commit -m "bump version: $CURRENT → $NEW"
git tag "v$NEW"
echo "  ✓ commit + tag v$NEW 已创建"
confirm

# ── 6. 推送 ────────────────────────────────────────────
step "第 6 步: 推送到 GitHub"
git push origin main
git push origin "v$NEW"
echo "  ✓ 推送完成"
confirm

# ── 7. GitHub Release ─────────────────────────────────
step "第 7 步: 创建 GitHub Release"
NOTES_FILE="dist/.release_notes_$NEW.txt"
python -c "
import re, sys
with open('docs/CHANGELOG.md', encoding='utf-8') as f:
    content = f.read()
pattern = r'^## $NEW\s*\(.*?\)\s*\n(.*?)(?=\n## |\Z)'
match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
if match:
    with open('$NOTES_FILE', 'w', encoding='utf-8') as f:
        f.write(match.group(1).strip())
else:
    sys.exit(1)
" || die "CHANGELOG 解析失败"
gh release create "v$NEW" --title "v$NEW" --notes-file "$NOTES_FILE" "$EXE"
rm -f "$NOTES_FILE"
echo "  ✓ GitHub Release v$NEW 已创建"
echo "    https://github.com/SMWHff/winrandr/releases/tag/v$NEW"
confirm

# ── 8. PyPI 发布 ──────────────────────────────────────
step "第 8 步: 发布到 PyPI"
if [ -z "${UV_PUBLISH_TOKEN:-}" ]; then
    echo "  ⚠ UV_PUBLISH_TOKEN 未设置"
    echo "  请粘贴 PyPI 令牌（或按 Ctrl+C 取消）："
    read -rs TOKEN
    echo ""
    export UV_PUBLISH_TOKEN="$TOKEN"
fi
uv build
uv publish
echo "  ✓ PyPI 发布完成"
echo "    https://pypi.org/project/winrandr/$NEW/"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  发布完成！v$NEW                            ║"
echo "╚══════════════════════════════════════════════╝"
