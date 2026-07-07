#!/bin/bash
cd "$(dirname "$0")/.."
set -e

echo "==> 类型检查..."
uv run python -c "import winrandr; print('导入成功，版本:', winrandr.__version__)"

echo ""
echo "==> 验证所有公开函数..."
uv run python -c "
from winrandr import (
    list_displays, set_resolution, set_position,
    set_position_relative, set_rotation, set_primary,
    set_off, set_brightness, set_gamma, set_reflect,
)
print('所有 10 个公开函数均可导入')
"

echo ""
echo "==> 验证 CLI 参数..."
uv run python -m winrandr --help > /dev/null
uv run python -m winrandr --version
echo "CLI 参数正常"

echo ""
echo "==> 列出显示器..."
uv run python -m winrandr 2>/dev/null || echo "(查询失败——可能在无显示器环境)"

echo ""
echo "==> 运行 pytest..."
uv run pytest tests/ -v

echo ""
echo "测试完成！"
