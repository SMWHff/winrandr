#!/bin/bash
cd "$(dirname "$0")/../.."
set -e

echo "==> 检查 uv..."
if ! command -v uv &>/dev/null; then
    echo "错误: 未安装 uv。请先安装: https://docs.astral.sh/uv/#installation"
    exit 1
fi

echo "==> 创建虚拟环境并安装依赖..."
uv sync --dev

echo "==> 验证安装..."
uv run python -m winrandr --version

echo ""
echo "==> 安装完成！使用方式："
echo "  bash scripts/dev/run.sh              # 运行 winrandr"
echo "  bash scripts/dev/test.sh             # 运行测试"
echo "  bash scripts/build/build.sh          # 构建 exe"
echo "  bash scripts/dev/lint.sh             # Lint 检查"
echo "  bash scripts/build/clean.sh          # 清理缓存"
