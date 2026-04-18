# Patent Landscape Mapper

`patent_landscape_mapper` is a distinctive SAGE application example for turning a patent corpus into
an actionable technology landscape.

## What It Does

- clusters a patent corpus into technology themes
- summarizes theme concentration by assignee
- identifies whitespace opportunities with low concentration and strong strategic relevance
- builds a small graph view linking assignees, patents, and themes
- produces a watchlist of patents worth closer review

## Why This Example Matters

This app is a good SAGE example because it is not just text summarization. It combines:

- structured records
- feature extraction with `scikit-learn`
- a SAGE runtime pipeline
- graph-shaped output that can later feed UI or downstream services

## Demo Scenario

The built-in demo corpus covers industrial AI patents across four areas:

- industrial safety and edge vision
- predictive maintenance and digital twins
- warehouse robotics orchestration
- cold chain and pharma logistics monitoring

## Run It

From the repository root:

```bash
python examples/run_patent_landscape_mapper.py
python examples/run_patent_landscape_mapper.py --clusters 5
python examples/run_patent_landscape_mapper.py --focus-keywords "cold chain,biologics logistics"
python examples/run_patent_landscape_mapper.py --json
```

## Output

The report includes:

- landscape summary
- clustered themes with top terms and representative patents
- whitespace opportunities
- watchlist patents
- graph nodes and edges in JSON mode

## Extension Ideas

- replace demo data with a CSV or API-backed patent source
- add CPC/IPC code normalization
- enrich assignee rollups with corporate-family resolution
- compare two corpora for competitor benchmarking