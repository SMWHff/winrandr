#!/bin/bash
cd "$(dirname "$0")/../.."
set -euo pipefail

echo "==> 安装依赖..."
uv sync --dev

echo ""
echo "==> Ruff 代码风格检查..."
uv run ruff check winrandr/ tests/

echo ""
echo "==> 导入完整性检查..."
uv run python -c "
import sys
sys.stdout.write('winrandr 导入成功，版本: ')
exec('import winrandr; print(winrandr.__version__)')
"

echo ""
echo "==> 所有 Lint 检查通过！"
