#!/bin/bash
cd "$(dirname "$0")/.."
set -e

PY_MAJOR=$(python -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python -c "import sys; print(sys.version_info.minor)")

echo "==> 安装构建依赖..."
uv sync --dev

echo "==> 使用 Nuitka 编译为单文件 exe..."

if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 13 ]; then
    echo "  (Python ≥ 3.13，使用 MSVC 而非 MinGW)"
    uv run nuitka --standalone --onefile --output-dir=dist --output-name=winrandr --assume-yes-for-downloads winrandr
else
    uv run nuitka --standalone --onefile --output-dir=dist --output-name=winrandr --mingw64 --assume-yes-for-downloads winrandr
fi

echo "==> 构建完成！exe 位于 dist/winrandr.exe"
