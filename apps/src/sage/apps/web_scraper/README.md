# Web Scraper

网页内容抓取与表格抽取应用。

## 功能

- 从文本文件读取 URL 列表
- 抓取网页标题与 HTML
- 抽取 HTML table 内容
- 输出 JSON 数组结果

## 用法

```bash
python examples/run_web_scraper.py \
  --url-file urls.txt \
  --output scraped_tables.json
```

输入文件每行一个 URL。
