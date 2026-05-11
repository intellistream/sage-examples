# SAGE OPC

SAGE OPC 是放在 sage-examples 仓库里的一个非侵入式控制台，用来发现、预检、启动、监控和停止现有 app，而不是改写它们的源码。

## 当前能力

- 扫描 `examples/run_*.py` 自动生成 App Catalog
- 为已验证 app 提供端口、健康检查、自带 UI 和文件需求元数据
- 在启动前显示完整命令预览、工作目录、环境变量和 preflight checklist
- 通过后端子进程管理真实 app，采集 stdout / stderr，支持 stop / restart / clone launch
- 提供实例级兼容性检查，当前已验证：
  - `ticket_triage_api`
  - `supply_chain_alert_api`
- 导出 inventory 与 compatibility markdown 报告

## 运行方式

在 `sage` conda 环境里从仓库根目录启动：

```bash
cd /root/SAGE/sage-examples
/root/miniconda3/bin/conda run -n sage python -m opc \
  --host 127.0.0.1 \
  --port 18400 \
  --root-dir /root/SAGE/sage-examples \
  --python-executable /root/miniconda3/envs/sage/bin/python
```

打开 `http://127.0.0.1:18400`。

## 导出文档

导出 inventory：

```bash
cd /root/SAGE/sage-examples
/root/miniconda3/bin/conda run -n sage python -m opc.export_docs inventory > opc/docs/SAGE_EXAMPLES_APP_INVENTORY.md
```

导出 compatibility matrix：

```bash
cd /root/SAGE/sage-examples
/root/miniconda3/bin/conda run -n sage python -m opc.export_docs compatibility > opc/docs/COMPATIBILITY_MATRIX.md
```

## 目录说明

- `opc/server.py`：FastAPI 控制台服务
- `opc/runtime.py`：子进程运行时适配器
- `opc/discovery.py`：App 发现与已验证 manifest
- `opc/static/`：前端页面、样式和交互脚本
- `opc/tests/`：发现层、API 层与运行时测试