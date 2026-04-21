# Resume Parser

简历解析与标准化示例应用。

## 功能

- 读取文本简历
- 提取姓名、邮箱、电话、教育和技能信息
- 标准化字段格式
- 校验简历完整度
- 输出 JSON 结果

## 用法

```bash
python examples/run_resume_parser.py \
  --resume-dir ./resumes \
  --output parsed.json
```

```bash
python examples/run_resume_parser.py \
  --resume-files resume1.txt resume2.txt \
  --output parsed.json \
  --verbose
```
