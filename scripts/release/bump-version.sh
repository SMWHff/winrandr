#!/bin/bash
cd "$(dirname "$0")/../.."
set -euo pipefail

source scripts/_common.sh

usage() {
    echo "用法: bash scripts/release/bump-version.sh <patch|minor|major|X.Y.Z>"
    exit 1
}

[[ $# -lt 1 ]] && usage

CURRENT=$(get_version)
NEW=$(next_version "$CURRENT" "$1")

echo "当前版本: $CURRENT"
echo "新版本:    $NEW"
echo ""

if [[ "${AUTO_CONFIRM:-}" != "1" ]]; then
    read -rp "确认 bump 版本? (y/N) " CONFIRM
    [[ "$CONFIRM" != "y" ]] && echo "已取消" && exit 1
fi

update_version_files "$CURRENT" "$NEW"

echo ""
echo "版本已更新: $CURRENT → $NEW"
echo ""
echo "下一步:"
echo "  1. 更新 docs/CHANGELOG.md 添加新版本日志"
echo "  2. 提交: git commit -m \"bump version: $CURRENT → $NEW\""
echo "  3. 打标签: git tag v$NEW"
