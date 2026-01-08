#!/bin/bash
# ============================================================================
# SAGE Examples Quick Start Script
# ============================================================================
# 快速设置开发环境并安装依赖
# ============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

info "SAGE Examples 快速启动脚本"
echo ""

# 检查 Python 版本
info "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
info "Python 版本: $python_version"

# 检查是否在虚拟环境中
if [[ -z "$VIRTUAL_ENV" ]] && [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    warn "建议在虚拟环境中运行此脚本"
    read -p "是否继续？(yes/no): " continue_install
    if [ "$continue_install" != "yes" ]; then
        echo "已取消"
        exit 0
    fi
fi

# 选择安装模式
echo ""
echo "选择安装模式："
echo "1. 最小安装（仅教程）- 适合学习基础功能"
echo "2. 完整安装（教程 + 应用）- 包含所有示例"
echo "3. 开发安装（完整 + 开发工具）- 适合贡献代码"
echo ""
read -p "请选择 (1/2/3): " install_mode

case $install_mode in
    1)
        info "安装最小依赖（教程）..."
        pip install -r requirements.txt
        ;;
    2)
        info "安装完整依赖（教程 + 应用）..."
        pip install -r requirements.txt
        cd sage-apps && pip install -e ".[all]" && cd ..
        ;;
    3)
        info "安装开发依赖..."
        pip install -r requirements.txt
        cd sage-apps && pip install -e ".[all,dev]" && cd ..
        pip install pytest pytest-cov black ruff mypy
        ;;
    *)
        warn "无效选择，使用最小安装"
        pip install -r requirements.txt
        ;;
esac

echo ""
info "安装完成！"
echo ""
echo "🚀 快速开始："
echo "  python tutorials/hello_world.py"
echo ""
echo "📚 查看更多教程："
echo "  ls tutorials/"
echo ""
echo "🎯 运行应用示例（需要完整安装）："
echo "  python apps/run_video_intelligence.py --help"
echo ""
info "查看 README.md 获取更多信息"
