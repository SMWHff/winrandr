#!/bin/bash
cd "$(dirname "$0")/../.."
set -euo pipefail

usage() {
    echo "用法: bash scripts/release/bump-version.sh <patch|minor|major|X.Y.Z>"
    exit 1
}

[[ $# -lt 1 ]] && usage

CURRENT=$(grep -m1 '^version' pyproject.toml | sed 's/.*"\(.*\)"/\1/')
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "$1" in
    patch) NEW="$MAJOR.$MINOR.$((PATCH + 1))" ;;
    minor) NEW="$MAJOR.$((MINOR + 1)).0" ;;
    major) NEW="$((MAJOR + 1)).0.0" ;;
    *)     NEW="$1" ;;
esac

echo "当前版本: $CURRENT"
echo "新版本:    $NEW"
echo ""

# 确认
read -rp "确认 bump 版本? (y/N) " CONFIRM
[[ "$CONFIRM" != "y" ]] && echo "已取消" && exit 1

# 更新 pyproject.toml（仅 project.version 和 tool.nuitka.file-version）
sed -i "s/^version = \"$CURRENT\"/version = \"$NEW\"/" pyproject.toml
sed -i "s/^file-version = \"$CURRENT\"/file-version = \"$NEW\"/" pyproject.toml

# 更新 winrandr/__init__.py
sed -i "s/^__version__ = \"$CURRENT\"/__version__ = \"$NEW\"/" winrandr/__init__.py

echo ""
echo "版本已更新: $CURRENT → $NEW"
echo ""
echo "下一步:"
echo "  1. 更新 docs/CHANGELOG.md 添加新版本日志"
echo "  2. 提交: git commit -m \"bump version: $CURRENT → $NEW\""
echo "  3. 打标签: git tag v$NEW"
