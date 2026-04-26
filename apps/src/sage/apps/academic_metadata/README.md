# Academic Metadata

学术文献元数据抽取应用。

## 功能

- 从目录、单文件或 CSV 读取文献文本
- 提取标题、作者、年份、DOI、邮箱与摘要
- 标准化作者名称
- 输出 JSON 结果

## 用法

```bash
python examples/run_academic_metadata.py \
  --input-path sample_papers \
  --output metadata.json
```
