#!/bin/bash
# ============================================================================
# SAGE Examples Build Script
# ============================================================================
# 用于构建和发布 isage-examples 和 iapps 包到 PyPI
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 辅助函数
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查依赖
check_dependencies() {
    info "检查构建依赖..."
    
    if ! command -v python3 &> /dev/null; then
        error "Python 3 未安装"
    fi
    
    # 检查并安装构建工具
    if ! python3 -c "import build" &> /dev/null; then
        info "安装构建工具..."
        pip install --upgrade build twine
    fi
}

# 清理构建目录
clean() {
    info "清理旧的构建文件..."
    rm -rf dist/ build/ *.egg-info
    rm -rf apps/dist/ apps/build/ apps/*.egg-info
    info "清理完成"
}

# 构建 isage-examples
build_examples() {
    info "构建 isage-examples..."
    python3 -m build
    info "isage-examples 构建完成"
}

# 构建 iapps
build_apps() {
    info "构建 iapps..."
    cd apps
    python3 -m build
    cd ..
    info "iapps 构建完成"
}

# 检查包
check_packages() {
    info "检查包完整性..."
    
    # 检查 isage-examples
    if [ -d "dist" ]; then
        twine check dist/*
    fi
    
    # 检查 iapps
    if [ -d "apps/dist" ]; then
        twine check apps/dist/*
    fi
    
    info "包检查完成"
}

# 上传到 TestPyPI（测试）
upload_test() {
    warn "上传到 TestPyPI（测试环境）..."
    
    # 上传 isage-examples
    if [ -d "dist" ]; then
        info "上传 isage-examples 到 TestPyPI..."
        twine upload --repository testpypi dist/*
    fi
    
    # 上传 iapps
    if [ -d "apps/dist" ]; then
        info "上传 iapps 到 TestPyPI..."
        twine upload --repository testpypi apps/dist/*
    fi
    
    info "TestPyPI 上传完成"
    info "安装测试: pip install --index-url https://test.pypi.org/simple/ isage-examples"
}

# 上传到 PyPI（正式发布）
upload_prod() {
    warn "上传到 PyPI（正式环境）..."
    read -p "确认要发布到正式 PyPI？(yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        error "用户取消发布"
    fi
    
    # 上传 isage-examples
    if [ -d "dist" ]; then
        info "上传 isage-examples 到 PyPI..."
        twine upload dist/*
    fi
    
    # 上传 iapps
    if [ -d "apps/dist" ]; then
        info "上传 iapps 到 PyPI..."
        twine upload apps/dist/*
    fi
    
    info "PyPI 上传完成"
}

# 显示帮助
show_help() {
    cat << EOF
SAGE Examples 构建脚本

用法:
    $0 [命令]

命令:
    clean       - 清理构建文件
    build       - 构建所有包（examples + apps）
    examples    - 仅构建 isage-examples
    apps        - 仅构建 iapps
    check       - 检查包完整性
    test        - 上传到 TestPyPI
    release     - 发布到正式 PyPI
    all         - 清理 + 构建 + 检查（默认）
    help        - 显示此帮助信息

示例:
    $0              # 默认：清理 + 构建 + 检查
    $0 build        # 仅构建
    $0 test         # 构建并上传到 TestPyPI
    $0 release      # 构建并发布到 PyPI

注意:
    - 发布前请确保已更新版本号
    - isage-examples: pyproject.toml 中的 version
    - iapps: src/sage/apps/_version.py 中的 __version__
EOF
}

# 主函数
main() {
    case "${1:-all}" in
        clean)
            clean
            ;;
        build)
            check_dependencies
            build_examples
            build_apps
            ;;
        examples)
            check_dependencies
            build_examples
            ;;
        apps)
            check_dependencies
            build_apps
            ;;
        check)
            check_packages
            ;;
        test)
            check_dependencies
            clean
            build_examples
            build_apps
            check_packages
            upload_test
            ;;
        release)
            check_dependencies
            clean
            build_examples
            build_apps
            check_packages
            upload_prod
            ;;
        all)
            check_dependencies
            clean
            build_examples
            build_apps
            check_packages
            info "所有任务完成！"
            info "运行 './build.sh test' 上传到 TestPyPI"
            info "运行 './build.sh release' 发布到正式 PyPI"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "未知命令: $1\n使用 '$0 help' 查看帮助"
            ;;
    esac
}

# 运行主函数
main "$@"
