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
  --nvd-pub-start 2024-01-01T00:00:00.000Z \
  --nvd-pub-end 2024-03-31T23:59:59.999Z \
  --limit 3000 \
  --out data/icpp_demo/nvd_2024_q1_3k \
  --dataset-id nvd-2024-q1-3k
```

Describe the generated dataset:

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src \
python -m sage.apps.sageflow_service_demo.describe_dataset \
  data/icpp_demo/nvd_2024_q1_3k/manifest.json
```

## 2. Build Real Embeddings

Use the local SentenceTransformers deployment for the paper artifact. The cache
is only the deterministic replay artifact; the vectors themselves are produced
by `sentence_transformers.SentenceTransformer("BAAI/bge-small-en-v1.5")` with
normalized 384-dimensional outputs.

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src \
python -m sage.apps.sageflow_service_demo.build_embeddings \
  --provider sentence-transformers \
  --events data/icpp_demo/nvd_2024_q1_3k/events.jsonl \
  --out data/icpp_demo/nvd_2024_q1_3k/embeddings.jsonl \
  --model BAAI/bge-small-en-v1.5 \
  --batch-size 64
```

If an OpenAI-compatible embedding service is preferred, use:

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src \
python -m sage.apps.sageflow_service_demo.build_embeddings \
  --provider openai \
  --events data/icpp_demo/nvd_2024_q1_3k/events.jsonl \
  --out data/icpp_demo/nvd_2024_q1_3k/embeddings.jsonl \
  --base-url http://127.0.0.1:8000/v1 \
  --model BAAI/bge-small-en-v1.5
```

The cache must contain a metadata row plus one row per embedded event. Paper
tables should cite the model name, vector dimension, source count, and record
count from the generated manifest/cache.

For repository storage, the 3k cache is sharded under
`data/icpp_demo/nvd_2024_q1_3k/embeddings/`; `EmbeddingCache` accepts either a
single JSONL file or a directory of JSONL shards.

Sanity-check that cached vectors are real model outputs by recomputing at least
one event with the same model and comparing it to the cache. The current
`nvd_2024_q1_3k` cache was verified with maximum absolute difference below
`1e-7`, which is float roundoff.

The NVD API enforces bounded publication-date ranges; keep the date window to a
quarter-scale range unless an API key and paginated date sharding are added.

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
  --config configs/icpp_demo_zhipu.json \
  --experiment runtime
```

The harness writes one result artifact per runtime configuration and a summary
file with throughput, latency, runtime counters, and weak-label purity where the
selected measurement mode exposes it.
The runtime experiment intentionally uses `runtime_timestamp_mode=sequence`, so
`window_size=128/512` maps to the most recent 128/512 vector arrivals instead
of years of CVE publication time. This keeps SageFlow's indexed strategies in a
streaming regime and makes the parallelism sweep meaningful. The current paper
profile uses the indexed `ivf` strategy over parallelism `1,2,4`; do not
report `bruteforce_lazy` as the main result.

`measurement_mode=engine` is used for the runtime table. It bypasses the
service-level contract builder and measures SageFlow ingest plus drain time over
the real cached vectors. The service-level contract path is still measured in
the LLM experiment, where the goal is evidence faithfulness rather than raw
engine throughput.

## 4. Run API-backed Generation

The paper/demo path uses an OpenAI-compatible chat endpoint after the
SageFlow runtime emits a bounded evidence contract. For the current demo, the
recommended cloud profile is Zhipu GLM. Runtime parameters live in
`configs/icpp_demo_zhipu.json`; only the secret key stays in the shell:

```bash
export ZHIPU_API_KEY=<your-api-key>
```

The `zhipu` provider profile sends `thinking={"type":"disabled"}` so the demo
receives a concise answer in `choices[0].message.content`. A local vLLM service
can still be used by adding another JSON config profile with its own
`llm.base_url` and `llm.model`, for example `Qwen/Qwen2.5-1.5B-Instruct`.

Run the LLM evidence experiment:

```bash
PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src:/path/to/sageFlow/build/lib \
SAGEFLOW_ROOT=/path/to/sageFlow \
python -m sage.apps.sageflow_service_demo.run_experiment \
  --config configs/icpp_demo_zhipu.json \
  --experiment zhipu_llm
```

Do not use `--allow-template-fallback` for paper results. That flag is reserved
for disconnected local tests and produces answers explicitly marked
`template_fallback`.

## 5. Run the Live UI

```bash
cd /path/to/brisksnapshot-ui

PYTHONPATH=/path/to/SAGE/src:/path/to/sage-examples/apps/src:/path/to/sageFlow/build/lib \
SAGEFLOW_ROOT=/path/to/sageFlow \
BRISKSNAPSHOT_DEMO_CONFIG=/path/to/sage-examples/configs/icpp_demo_zhipu.json \
ZHIPU_API_KEY=<your-api-key> \
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
