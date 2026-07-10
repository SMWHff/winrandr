#!/bin/bash
cd "$(dirname "$0")/../.."
set -euo pipefail

echo "==> 安装依赖..."
uv sync --dev

echo ""
echo "==> 检查导入..."
uv run python -c "import winrandr; print('导入成功，版本:', winrandr.__version__)"

echo ""
echo "==> 验证所有公开函数..."
uv run python -c "
from winrandr import (
    list_displays, set_resolution, set_preferred_resolution, set_auto,
    set_position, set_position_relative, set_rotation, set_primary,
    set_off, set_noprimary, set_brightness, set_gamma, set_reflect,
    list_providers, get_display_props, get_edid, enumerate_modes,
    identify_display, save_profile, load_profile, list_profiles, delete_profile,
)
print('所有 23 个公开函数均可导入')
"

echo ""
echo "==> Lint 检查..."
uv run ruff check winrandr/ tests/

echo ""
echo "==> 验证 CLI 参数..."
uv run python -m winrandr --help > /dev/null
uv run python -m winrandr --version
echo "CLI 参数正常"

echo ""
echo "==> 列出显示器..."
uv run python -m winrandr 2>/dev/null || echo "(查询失败——可能在无显示器环境)"

echo ""
echo "==> 列出可用模式..."
uv run python -m winrandr --listmodes 2>/dev/null | head -10 || echo "(listmodes 失败)"

echo ""
echo "==> 运行 pytest（含覆盖率收集）..."
uv run pytest tests/ -v --cov

echo ""
echo "==> 覆盖率报告..."
uv run coverage report --show-missing

echo ""
echo "测试完成！"
