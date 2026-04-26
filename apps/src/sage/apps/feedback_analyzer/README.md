# Feedback Analyzer

客户反馈关键词提取示例应用。

## 功能

- 读取文本或 CSV 反馈
- 清洗输入文本
- 分词并统计高频关键词
- 输出 JSON 统计结果

## 用法

```bash
python examples/run_feedback_analyzer.py \
  --feedback-file feedback.txt \
  --output keywords.json
```

```bash
python examples/run_feedback_analyzer.py \
  --feedback-file feedback.csv \
  --output keywords.json \
  --top-n 100 \
  --verbose
```
