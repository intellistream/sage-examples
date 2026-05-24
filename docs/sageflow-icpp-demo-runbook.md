# SageFlow ICPP Demo Runbook

This runbook records the reproducible path for the ICPP 2026 demo evidence.
The paper should only report numbers generated from these commands or an
equivalent recorded run.

## 1. Build a Real Public Dataset

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src \
python -m sage.apps.sageflow_service_demo.build_dataset \
  --source cisa-kev \
  --source nvd-api \
  --nvd-pub-start 2024-01-01T00:00:00.000 \
  --nvd-pub-end 2024-12-31T23:59:59.999 \
  --limit 1000 \
  --out data/icpp_demo/vuln_public_1k \
  --dataset-id vuln-public-1k
```

Describe the generated dataset:

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src \
python -m sage.apps.sageflow_service_demo.describe_dataset \
  data/icpp_demo/vuln_public_1k/manifest.json
```

## 2. Build Real Embeddings

Use an OpenAI-compatible embedding service. The embedding cache is the
deterministic replay artifact; the vectors themselves must come from a real
embedding model or service.

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src \
python -m sage.apps.sageflow_service_demo.build_embeddings \
  --provider sentence-transformers \
  --events data/icpp_demo/vuln_public_1k/events.jsonl \
  --out data/icpp_demo/vuln_public_1k/embeddings.jsonl \
  --model BAAI/bge-small-en-v1.5
```

If an OpenAI-compatible embedding service is preferred, use:

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src \
python -m sage.apps.sageflow_service_demo.build_embeddings \
  --provider openai \
  --events data/icpp_demo/vuln_public_1k/events.jsonl \
  --out data/icpp_demo/vuln_public_1k/embeddings.jsonl \
  --base-url http://127.0.0.1:8000/v1 \
  --model BAAI/bge-small-en-v1.5
```

The cache must contain a metadata row plus one row per embedded event. Paper
tables should cite the model name, vector dimension, source count, and record
count from the generated manifest/cache.

## 3. Run Runtime Experiments

Build the SageFlow pybind runtime first:

```bash
cd /path/to/sageFlow
cmake -S . -B build -DBUILD_PYTHON_BINDINGS=ON
cmake --build build --target _sage_flow -j
```

Run the experiment harness:

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src:/path/to/sageFlow/build/lib \
SAGEFLOW_ROOT=/path/to/sageFlow \
python -m sage.apps.sageflow_service_demo.run_experiment \
  --events data/icpp_demo/vuln_public_1k/events.jsonl \
  --embedding-cache data/icpp_demo/vuln_public_1k/embeddings.jsonl \
  --out-dir data/icpp_demo/results/vuln_public_1k \
  --limit 1000 \
  --window-size 64 \
  --window-size 256 \
  --parallelism 1 \
  --parallelism 2 \
  --parallelism 4 \
  --similarity-threshold 0.80 \
  --similarity-threshold 0.90
```

The harness writes one JSONL file per runtime configuration and a summary file
with throughput, p50/p95 latency, runtime counters, and weak-label purity.

## 4. Run API-backed Generation

The paper/demo path uses an OpenAI-compatible chat endpoint after the
SageFlow runtime emits a bounded evidence contract. For the current demo, the
recommended cloud profile is Zhipu GLM:

```bash
export SAGEFLOW_DEMO_LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
export SAGEFLOW_DEMO_LLM_MODEL=glm-4.5
export SAGEFLOW_DEMO_LLM_PROVIDER=zhipu
export SAGEFLOW_DEMO_LLM_API_KEY=<your-api-key>
export SAGEFLOW_DEMO_LLM_MAX_TOKENS=384
```

The `zhipu` provider profile sends `thinking={"type":"disabled"}` so the demo
receives a concise answer in `choices[0].message.content`. A local vLLM service
can still be used by setting `SAGEFLOW_DEMO_LLM_BASE_URL` to the vLLM
OpenAI-compatible endpoint and `SAGEFLOW_DEMO_LLM_MODEL` to the served model,
for example `Qwen/Qwen2.5-1.5B-Instruct`.

Run the LLM evidence experiment:

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src:/path/to/sageFlow/build/lib \
SAGEFLOW_ROOT=/path/to/sageFlow \
python -m sage.apps.sageflow_service_demo.run_experiment \
  --events data/icpp_demo/vuln_public_1k/events.jsonl \
  --embedding-cache data/icpp_demo/vuln_public_1k/embeddings.jsonl \
  --out-dir data/icpp_demo/results/vuln_public_1k_llm \
  --limit 100 \
  --window-size 64 \
  --parallelism 1 \
  --similarity-threshold 0.85 \
  --generate-llm
```

Do not use `--allow-template-fallback` for paper results. That flag is reserved
for disconnected local tests and produces answers explicitly marked
`template_fallback`.

## 5. Run the Live UI

```bash
cd /path/to/brisksnapshot-ui

PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src:/path/to/sageFlow/build/lib \
SAGEFLOW_ROOT=/path/to/sageFlow \
BRISKSNAPSHOT_LIVE_EVENTS_JSONL=/path/to/sage-examples/data/icpp_demo/vuln_public_1k/events.jsonl \
SAGEFLOW_DEMO_EMBEDDING_CACHE=/path/to/sage-examples/data/icpp_demo/vuln_public_1k/embeddings.jsonl \
SAGEFLOW_DEMO_LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4 \
SAGEFLOW_DEMO_LLM_MODEL=glm-4.5 \
SAGEFLOW_DEMO_LLM_PROVIDER=zhipu \
SAGEFLOW_DEMO_LLM_API_KEY=<your-api-key> \
python backend/live_demo_server.py
```

Then start the frontend:

```bash
npm run dev -- --host 127.0.0.1 --port 4173
```

The UI should show the real dataset path, cached embedding metadata, SageFlow
runtime counters, snapshot contract, LLM API metadata, prompt hash, evidence
ids, and generated answer.

## 6. Paper Evidence Checklist

- Dataset table row is backed by `manifest.json`.
- Embedding model/dimension comes from `embeddings.jsonl` metadata.
- Runtime latency/throughput comes from `summary.json`.
- LLM latency/token counts come from generated answer rows and are reported
  separately from SageFlow runtime throughput.
- UI figure is a direct screenshot of the live run, not a generated mockup.
- Any disconnected fallback run is excluded from paper results.
