# Voucher Classifier

财务凭证自动分类应用。

## 功能

- 读取 CSV 或文本凭证记录
- 提取 OCR 文本中的金额、日期和类别线索
- 基于规则进行费用分类
- 输出 JSON 分类结果

## 用法

```bash
python examples/run_voucher_classifier.py \
  --input-file vouchers.csv \
  --output voucher_results.json
```
