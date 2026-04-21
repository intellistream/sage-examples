# Log Parser

日志解析与结构化示例应用。

## 功能

- 读取文本日志或 JSON 日志
- 解析常见日志格式
- 按级别过滤关键日志
- 提取错误码等辅助字段
- 输出 JSON 结果

## 用法

```bash
python examples/run_log_parser.py \
  --log-file app.log \
  --output structured.json
```

```bash
python examples/run_log_parser.py \
  --log-file app.log \
  --output structured.json \
  --error-levels ERROR,CRITICAL \
  --console \
  --verbose
```
