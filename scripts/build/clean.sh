#!/bin/bash
cd "$(dirname "$0")/../.."
set -e

echo "==> 清理 Nuitka 构建缓存..."
rm -rf dist/winrandr.build dist/winrandr.dist dist/winrandr.onefile-build 2>/dev/null && echo "  dist/ 构建目录已清理" || echo "  部分构建目录正在使用中（跳过）"

echo "==> 清理 Python 缓存..."
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null && echo "  __pycache__ 已清理" || true
find . -type f -name "*.pyc" -delete 2>/dev/null && echo "  .pyc 已清理" || true

echo "==> 清理测试和工具缓存..."
rm -rf .pytest_cache .ruff_cache *.egg-info 2>/dev/null && echo "  .pytest_cache / .ruff_cache / *.egg-info 已清理" || true

echo "==> 清理完成"
