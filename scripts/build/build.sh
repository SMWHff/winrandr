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

echo "==> 清除旧构建..."
rm -rf dist/*

# 基础构建参数（--onefile-no-compression：避免低内存环境 zstd 压缩 OOM）
BASE=(--standalone --onefile --onefile-no-compression \
      --output-dir=dist --output-filename=winrandr.exe \
      --company-name=winrandr --product-name=winrandr \
      --file-version="$UV_VERSION" --assume-yes-for-downloads)

if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 13 ]; then
    echo "  (Python ≥ 3.13，使用 Nuitka 内置的 zig 后端，无需 MinGW)"
    uv run nuitka "${BASE[@]}" winrandr
else
    echo "  (Python < 3.13，使用 MinGW 后端)"
    uv run nuitka "${BASE[@]}" --mingw64 winrandr
fi

# 验证产物
if [ ! -f dist/winrandr.exe ]; then
    echo "错误: 构建失败，dist/winrandr.exe 未生成"
    exit 1
fi

echo "==> 构建完成！exe 位于 dist/winrandr.exe ($(du -h dist/winrandr.exe | cut -f1))"
