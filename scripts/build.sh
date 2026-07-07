#!/bin/bash
cd "$(dirname "$0")/.."
echo "==> 安装构建依赖..."
uv sync --dev
echo "==> 使用 Nuitka 编译为单文件 exe..."
uv run nuitka --standalone --onefile --output-dir=dist --mingw64 --assume-yes-for-downloads main.py
[ -f dist/main.exe ] && mv dist/main.exe dist/winrandr.exe
echo "==> 构建完成！exe 位于 dist/winrandr.exe"
