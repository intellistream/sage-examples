# PyPI 发布指南

本文档说明如何将 `isage-examples` 和 `isage-apps` 发布到 PyPI。

## 📦 包结构

此仓库包含两个独立的 PyPI 包：

1. **isage-examples** - 主包，包含教程和示例代码
   - 位置：仓库根目录
   - 配置：`pyproject.toml`
   - 版本：在 `pyproject.toml` 中的 `version` 字段

2. **isage-apps** - 应用包，包含生产级应用示例
   - 位置：`sage-apps/` 子目录
   - 配置：`sage-apps/pyproject.toml`
   - 版本：在 `sage-apps/src/sage/apps/_version.py` 中的 `__version__`

## 🔧 前置准备

### 1. 安装构建工具

```bash
pip install --upgrade build twine
```

### 2. 配置 PyPI 凭证

创建 `~/.pypirc` 文件：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-API-TOKEN-HERE
```

**获取 API Token：**
- PyPI: https://pypi.org/manage/account/token/
- TestPyPI: https://test.pypi.org/manage/account/token/

## 📝 发布前检查清单

- [ ] 更新版本号
  - [ ] `isage-examples`: 编辑 `pyproject.toml` 中的 `version`
  - [ ] `isage-apps`: 编辑 `sage-apps/src/sage/apps/_version.py` 中的 `__version__`
- [ ] 更新 CHANGELOG（如果有）
- [ ] 确保所有测试通过
- [ ] 检查依赖版本是否正确
- [ ] 更新 README.md（如需要）

## 🚀 发布流程

### 自动发布（推荐）

使用提供的构建脚本：

```bash
# 1. 构建和检查（不上传）
./build.sh

# 2. 上传到 TestPyPI 测试
./build.sh test

# 3. 测试安装
pip install --index-url https://test.pypi.org/simple/ isage-examples
pip install --index-url https://test.pypi.org/simple/ isage-apps

# 4. 确认无误后，发布到正式 PyPI
./build.sh release
```

### 手动发布

#### 发布 isage-examples

```bash
# 1. 清理旧文件
rm -rf dist/ build/ *.egg-info

# 2. 构建包
python -m build

# 3. 检查包
twine check dist/*

# 4. 上传到 TestPyPI（测试）
twine upload --repository testpypi dist/*

# 5. 测试安装
pip install --index-url https://test.pypi.org/simple/ isage-examples

# 6. 上传到正式 PyPI
twine upload dist/*
```

#### 发布 isage-apps

```bash
# 1. 进入 sage-apps 目录
cd sage-apps

# 2. 清理旧文件
rm -rf dist/ build/ *.egg-info

# 3. 构建包
python -m build

# 4. 检查包
twine check dist/*

# 5. 上传到 TestPyPI（测试）
twine upload --repository testpypi dist/*

# 6. 测试安装
pip install --index-url https://test.pypi.org/simple/ isage-apps

# 7. 上传到正式 PyPI
twine upload dist/*

# 8. 返回根目录
cd ..
```

## 🔍 发布后验证

### 检查 PyPI 页面

- isage-examples: https://pypi.org/project/isage-examples/
- isage-apps: https://pypi.org/project/isage-apps/

### 测试安装

```bash
# 创建新虚拟环境测试
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 安装并测试
pip install isage-examples
pip install isage-apps[all]

# 运行示例
python -c "from tutorials import hello_world"
python -m sage.apps.video.video_intelligence_pipeline --help

# 清理
deactivate
rm -rf test_env
```

## 📋 版本管理策略

遵循语义化版本规范 (SemVer)：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的新功能
- **PATCH**: 向后兼容的问题修复

### 版本号示例

- `0.1.0` - 初始发布
- `0.1.1` - Bug 修复
- `0.2.0` - 新功能添加
- `1.0.0` - 稳定版本，API 冻结

## 🐛 常见问题

### 问题：上传失败 "File already exists"

**解决方案：** PyPI 不允许重新上传相同版本。需要：
1. 增加版本号
2. 重新构建并上传

### 问题：依赖安装失败

**解决方案：** 检查 `pyproject.toml` 中的依赖版本约束：
- 确保 SAGE 核心包已发布到 PyPI
- 验证版本号格式正确
- 测试依赖是否可安装

### 问题：模块导入失败

**解决方案：** 检查包结构：
- 确保 `__init__.py` 文件存在
- 验证 `pyproject.toml` 中的 `packages.find` 配置
- 检查 MANIFEST.in 是否包含必要文件

## 📚 参考资源

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Documentation](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
- [Twine Documentation](https://twine.readthedocs.io/)

## 🔐 安全注意事项

1. **永远不要提交 API Token 到代码仓库**
2. **使用 Token 而不是用户名密码**
3. **定期轮换 API Token**
4. **为不同项目使用不同的 Token**
5. **限制 Token 的作用域（scope）**

## ✅ 发布检查清单（完整版）

**发布前：**
- [ ] 代码审查通过
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] 依赖版本已验证

**发布中：**
- [ ] 清理旧构建文件
- [ ] 构建包成功
- [ ] twine check 通过
- [ ] TestPyPI 上传成功
- [ ] TestPyPI 安装测试通过

**发布后：**
- [ ] PyPI 上传成功
- [ ] PyPI 页面显示正确
- [ ] 正式环境安装测试通过
- [ ] 创建 Git tag
- [ ] 更新 GitHub Release Notes

## 📞 获取帮助

如有问题，请：
1. 查看 [PyPI 帮助文档](https://pypi.org/help/)
2. 在 SAGE 仓库提 Issue
3. 联系维护者：shuhao_zhang@hust.edu.cn
