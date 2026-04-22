# Product Sync

商品信息同步应用。

## 功能

- 读取 CSV 或 JSON 商品数据
- 映射到统一平台字段
- 校验 SKU、标题、价格、库存
- 输出同步前的标准化结果

## 用法

```bash
python examples/run_product_sync.py \
  --input-file products.csv \
  --output platform_products.json
```
