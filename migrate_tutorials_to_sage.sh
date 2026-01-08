#!/bin/bash
# Migration script to move tutorials to SAGE main repository
# This script prepares the tutorials directory for migration

set -e

SAGE_REPO="/home/shuhao/SAGE"
EXAMPLES_REPO="/home/shuhao/sage-examples"

echo "🚀 SAGE Tutorials Migration Script"
echo "===================================="
echo ""
echo "This script will:"
echo "1. Copy tutorials/ directory to SAGE repository"
echo "2. Preserve git history (manual git operations needed)"
echo "3. Update SAGE documentation"
echo ""

# Check if SAGE repo exists
if [ ! -d "$SAGE_REPO" ]; then
    echo "❌ Error: SAGE repository not found at $SAGE_REPO"
    exit 1
fi

# Check if tutorials directory exists
if [ ! -d "$EXAMPLES_REPO/tutorials" ]; then
    echo "❌ Error: tutorials directory not found at $EXAMPLES_REPO/tutorials"
    exit 1
fi

echo "📂 Source: $EXAMPLES_REPO/tutorials"
echo "📂 Target: $SAGE_REPO/tutorials"
echo ""

read -p "❓ Continue with migration? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 1
fi

echo ""
echo "📋 Step 1: Backing up current tutorials..."
cd "$EXAMPLES_REPO"
if [ -d "tutorials" ]; then
    tar -czf "tutorials_backup_$(date +%Y%m%d_%H%M%S).tar.gz" tutorials/
    echo "✅ Backup created"
fi

echo ""
echo "📋 Step 2: Copying tutorials to SAGE repository..."
cp -r "$EXAMPLES_REPO/tutorials" "$SAGE_REPO/"
echo "✅ Tutorials copied to $SAGE_REPO/tutorials"

echo ""
echo "📋 Step 3: Creating migration documentation in SAGE..."

cat > "$SAGE_REPO/tutorials/README.md.new" << 'EOF'
# SAGE Tutorials

Complete tutorials covering all layers of the SAGE framework (L1-L6).

## 🚀 Quick Start

```bash
# 30-second introduction
python tutorials/hello_world.py

# 5-minute guide
cat tutorials/QUICK_START.md

# Start learning from L1
python tutorials/L1-common/hello_world.py
```

## 📚 Tutorial Structure

Tutorials are organized by SAGE's 6-layer architecture:

- **L1-common/**: Foundation layer (config, logging, unified client)
- **L2-platform/**: Platform services (scheduler, storage)
- **L3-kernel/**: Execution engine (batch, stream, operators)
- **L3-libs/**: Algorithms (RAG, Agents, Embeddings, LLM)
- **L4-middleware/**: Domain operators (vector DB, time-series DB)
- **L5-apps/**: Application patterns
- **L6-interface/**: CLI and UI examples

## 🎯 Learning Paths

See `QUICK_START.md` for recommended learning paths based on your goals.

## 📖 More Information

- **Quick Reference**: `docs/QUICK_REFERENCE.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **SAGE Documentation**: https://intellistream.github.io/SAGE

## 🔗 Related

- **Application Examples**: https://github.com/intellistream/sage-examples
- **SAGE Benchmark**: https://github.com/intellistream/sage-benchmark

---

**Note**: Tutorials were migrated from sage-examples repository to keep them synchronized with the core framework.
EOF

echo "✅ Created new README for SAGE tutorials"

echo ""
echo "📋 Step 4: Git operations (manual steps required)..."
echo ""
echo "To preserve git history, you need to manually:"
echo ""
echo "1. In sage-examples repository:"
echo "   cd $EXAMPLES_REPO"
echo "   git add -A"
echo "   git commit -m 'docs: prepare for tutorials migration to SAGE main repo'"
echo ""
echo "2. In SAGE repository:"
echo "   cd $SAGE_REPO"
echo "   git add tutorials/"
echo "   git commit -m 'feat: add tutorials from sage-examples'"
echo ""
echo "3. Update SAGE main README.md to mention tutorials"
echo ""
echo "4. Push both repositories"
echo ""
echo "✅ Migration preparation complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Review copied tutorials in $SAGE_REPO/tutorials"
echo "  2. Update SAGE README.md"
echo "  3. Run tests in SAGE to ensure tutorials work"
echo "  4. Commit and push changes"
echo "  5. In sage-examples, remove tutorials directory"
echo ""
