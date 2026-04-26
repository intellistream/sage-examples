# Customer Deduplication

客户数据去重应用。

## 功能

- 读取 CSV 客户数据
- 生成标准化指纹
- 基于相似度识别重复客户
- 输出带去重标记的 JSON

## 用法

```bash
python examples/run_customer_deduplication.py \
  --input-file customers.csv \
  --output deduplicated.json
```
