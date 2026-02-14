#!/bin/bash
# SageVDB Quickstart Script
# Sets up development environment and git hooks

set -e

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Print banner
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE}   ____                  __     ______  ____ ${NC}"
echo -e "${BOLD}${BLUE}  / __/__  ___  ___     / /    / __  / / __ )${NC}"
echo -e "${BOLD}${BLUE} _\\ \/ _ \/ _ \/ -_)   / /    / / / / / __  |${NC}"
echo -e "${BOLD}${BLUE}/___/\\___/\\_, /\\__/   /_/    /_/ /_/ /____/ ${NC}"
echo -e "${BOLD}${BLUE}         /___/                               ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}SageVDB Quickstart Setup${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Detect project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo -e "${BLUE}📂 Project root: ${NC}$PROJECT_ROOT"
echo ""

# Step 1: Install git hooks
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}${BOLD}Step 1: Installing Git Hooks${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
TEMPLATE_DIR="$PROJECT_ROOT/hooks"

if [ ! -d "$HOOKS_DIR" ]; then
    echo -e "${RED}✗ Git repository not initialized${NC}"
    echo -e "${YELLOW}Run: git init${NC}"
    exit 1
fi

# Install pre-commit hook
if [ -f "$TEMPLATE_DIR/pre-commit" ]; then
    cp "$TEMPLATE_DIR/pre-commit" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    echo -e "${GREEN}✓ Installed pre-commit hook${NC}"
else
    echo -e "${YELLOW}⚠  pre-commit template not found, skipping${NC}"
fi

# Install pre-push hook
if [ -f "$TEMPLATE_DIR/pre-push" ]; then
    cp "$TEMPLATE_DIR/pre-push" "$HOOKS_DIR/pre-push"
    chmod +x "$HOOKS_DIR/pre-push"
    echo -e "${GREEN}✓ Installed pre-push hook${NC}"
else
    echo -e "${YELLOW}⚠  pre-push template not found, skipping${NC}"
fi

echo ""

# Step 2: Check dependencies
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}${BOLD}Step 2: Checking Dependencies${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check for Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✓ Python found: ${NC}v$PYTHON_VERSION"
    
    # Check Python version (3.10+)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        echo -e "${GREEN}  Python version is 3.10+, good!${NC}"
    else
        echo -e "${RED}  Python 3.10+ required, found $PYTHON_VERSION${NC}"
        echo -e "${YELLOW}  Please upgrade Python${NC}"
    fi
else
    echo -e "${RED}✗ Python not found${NC}"
    echo -e "${YELLOW}  Install: sudo apt install python3 python3-pip${NC}"
fi

# Check for pip
if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓ pip found${NC}"
else
    echo -e "${RED}✗ pip not found${NC}"
    echo -e "${YELLOW}  Install: sudo apt install python3-pip${NC}"
fi
fi

# Check for sage-pypi-publisher
if command -v sage-pypi-publisher &> /dev/null; then
    echo -e "${GREEN}✓ sage-pypi-publisher found${NC}"
else
    echo -e "${YELLOW}⚠  sage-pypi-publisher not found${NC}"
    echo -e "${YELLOW}  Optional for PyPI publishing: pip install sage-pypi-publisher${NC}"
fi

echo ""

# Step 4: Install package
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}${BOLD}Step 4: Installing SAGE Examples${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}Installing package (all dependencies included by default)...${NC}"
cd "$PROJECT_ROOT"

# Check if user wants dev mode
echo -e "${BLUE}Install in development mode?${NC}"
echo -e "  ${GREEN}[y]${NC} Yes, install with dev dependencies (pytest, ruff, mypy)"
echo -e "  ${YELLOW}[n]${NC} No, standard installation only"
echo -n "Your choice [y/n]: "
read -r DEV_MODE

if [[ "$DEV_MODE" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installing in development mode...${NC}"
    pip install -e ".[dev]"
    echo -e "${GREEN}✓ Development mode installed${NC}"
else
    echo -e "${YELLOW}Installing standard mode...${NC}"
    pip install -e .
    echo -e "${GREEN}✓ Standard mode installed${NC}"
fi

# Also install apps package
echo -e "${YELLOW}Installing apps package...${NC}"
cd "$PROJECT_ROOT/apps"
if [[ "$DEV_MODE" =~ ^[Yy]$ ]]; then
    pip install -e ".[dev]"
else
    pip install -e .
fi
echo -e "${GREEN}✓ apps package installed${NC}"

echo ""

# Summary
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}✓ Setup Complete!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}${BOLD}Next Steps:${NC}"
echo -e "  ${CYAN}1.${NC} Run tests: ${CYAN}pytest${NC}"
echo -e "  ${CYAN}2.${NC} Try examples: ${CYAN}python examples/run_video_intelligence.py${NC}"
echo -e "  ${CYAN}3.${NC} Read docs: ${CYAN}cat README.md${NC}"
echo ""
echo -e "${YELLOW}${BOLD}Installation Mode:${NC}"
if [[ "$DEV_MODE" =~ ^[Yy]$ ]]; then
    echo -e "  ${GREEN}•${NC} Development mode (includes pytest, ruff, mypy)"
else
    echo -e "  ${GREEN}•${NC} Standard mode (all application dependencies included)"
fi
echo ""
echo -e "${BLUE}${BOLD}Useful Commands:${NC}"
echo -e "  ${CYAN}pytest${NC}                        - Run tests"
echo -e "  ${CYAN}ruff check .${NC}                  - Check code quality"
echo -e "  ${CYAN}python examples/run_*.py${NC}     - Run any example"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
