#!/bin/bash
cd "$(dirname "$0")/.."
set -e

PY_MAJOR=$(uv run python -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(uv run python -c "import sys; print(sys.version_info.minor)")


echo "==> 安装构建依赖..."
uv sync --dev

echo "==> 清除 Nuitka 缓存和旧构建..."
rm -rf dist/*
uv run nuitka --clean-cache=all

echo "==> 使用 Nuitka 编译为单文件 exe..."
if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 13 ]; then
    echo "  (Python ≥ 3.13，使用 zig 编译器)"
    uv run nuitka --standalone --onefile --output-dir=dist --output-filename=winrandr.exe --assume-yes-for-downloads winrandr
else
    uv run nuitka --standalone --onefile --output-dir=dist --output-filename=winrandr.exe --mingw64 --assume-yes-for-downloads winrandr
fi

echo "==> 构建完成！exe 位于 dist/winrandr.exe"
