#!/bin/bash
# 共享函数库 — 由 scripts/ 下各脚本 source 使用
# 调用方须已设置 set -euo pipefail

# 从 pyproject.toml 提取当前版本号
get_version() {
    grep -m1 '^version = ' pyproject.toml | sed 's/.*"\(.*\)"/\1/'
}

# 根据级别计算下一个版本号
next_version() {
    local current="$1" level="$2"
    IFS='.' read -r MAJOR MINOR PATCH <<< "$current"
    case "$level" in
        patch) echo "$MAJOR.$MINOR.$((PATCH + 1))" ;;
        minor) echo "$MAJOR.$((MINOR + 1)).0" ;;
        major) echo "$((MAJOR + 1)).0.0" ;;
        *)     echo "$level" ;;
    esac
}

# 更新所有版本号文件
update_version_files() {
    local old="$1" new="$2"
    local old_escaped="${old//./\\.}"
    sed -i "s/^version = \"$old_escaped\"/version = \"$new\"/" pyproject.toml
    sed -i "s/^file-version = \"$old_escaped\"/file-version = \"$new\"/" pyproject.toml
    sed -i "s/^__version__ = \"$old_escaped\"/__version__ = \"$new\"/" winrandr/__init__.py
}

# 验证 exe 产物存在且大小合理
verify_exe() {
    local path="${1:-dist/winrandr.exe}"
    if [ ! -f "$path" ]; then
        echo "错误: $path 未生成" >&2
        exit 1
    fi
    local size
    size=$(wc -c < "$path" 2>/dev/null || echo 0)
    if [ "$size" -lt 1000000 ]; then
        echo "错误: $path 大小异常 (${size} bytes)" >&2
        exit 1
    fi
    echo "$path ($(du -h "$path" | cut -f1))"
}
