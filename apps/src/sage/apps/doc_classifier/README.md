# Doc Classifier

文档分类应用。

## 功能

- 读取文本、CSV 或 JSON 文档
- 清洗文本并抽取高频词
- 使用规则对文档进行分类
- 输出分类后的 JSON 结果

## 用法

```bash
python examples/run_doc_classifier.py \
  --input-file docs.csv \
  --output classified_docs.json
```
