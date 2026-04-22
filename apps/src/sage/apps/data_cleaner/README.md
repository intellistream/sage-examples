# Data Cleaner

CSV 数据清洗与标准化示例应用。

## 功能

- 读取 CSV 输入
- 按字段规则做类型转换
- 处理缺失值
- 标记数值异常和重复记录
- 输出 CSV 或 JSON 结果

## 用法

```bash
python examples/run_data_cleaner.py \
  --input raw.csv \
  --output cleaned.csv
```

```bash
python examples/run_data_cleaner.py \
  --input raw.csv \
  --output cleaned.json \
  --type-rules age:int,salary:float,active:bool \
  --numeric-fields age,salary \
  --key-fields email,phone \
  --output-format json
```
