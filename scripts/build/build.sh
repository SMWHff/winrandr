#!/bin/bash
cd "$(dirname "$0")/../.."
set -euo pipefail

if ! command -v uv &>/dev/null; then
    echo "错误: 未找到 uv，请先安装 https://docs.astral.sh/uv/"
    exit 1
fi

PY_MAJOR=$(uv run python -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(uv run python -c "import sys; print(sys.version_info.minor)")
UV_VERSION=$(grep -m1 '^version' pyproject.toml | sed 's/.*"\(.*\)"/\1/')

echo "==> 安装构建依赖..."
uv sync --dev

echo "==> 清除 Nuitka 缓存和旧构建..."
rm -rf dist/*
uv run nuitka --clean-cache=all

echo "==> 使用 Nuitka 编译为单文件 exe..."
if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 13 ]; then
    echo "  (Python ≥ 3.13，使用 Nuitka 内置的 zig 后端，无需 MinGW)"
    uv run nuitka --standalone --onefile --output-dir=dist --output-filename=winrandr.exe --company-name=winrandr --product-name=winrandr --file-version="$UV_VERSION" --assume-yes-for-downloads winrandr
else
    uv run nuitka --standalone --onefile --output-dir=dist --output-filename=winrandr.exe --company-name=winrandr --product-name=winrandr --file-version="$UV_VERSION" --mingw64 --assume-yes-for-downloads winrandr
fi

echo "==> 构建完成！exe 位于 dist/winrandr.exe"
