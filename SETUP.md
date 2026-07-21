# Setup Guide - Synthesized Market Simulation Engine

## Prerequisites

- Python 3.9+ (tested on 3.12)
- Git
- Optional: GitHub CLI (`gh`) for pushing to GitHub
- Optional: Docker for Qdrant server mode

## Installation

### 1. Clone and Install

```bash
cd /workspace
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

### 2. Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
LLM_PROVIDER=mock          # mock, ollama, or openai
RESOURCE_PROFILE=low       # low, balanced, high
QDRANT_MODE=local          # local or server
RANDOM_SEED=42
```

**For OpenAI**: Set `OPENAI_API_KEY` in `.env`
**For Ollama**: Set `OLLAMA_BASE_URL=http://localhost:11434`

## Local Qdrant Setup

The engine uses Qdrant for vector memory. Two modes are supported:

### Mode 1: Local (Default, Recommended for Low Resource)

No setup required. The engine creates a local storage directory at `.qdrant_storage/`.

### Mode 2: Server (Docker)

```bash
docker run -d \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

Then set in `.env`:

```bash
QDRANT_MODE=server
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Optional: Ollama Setup

For local LLM inference:

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Set in .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

## Optional: OpenAI Setup

```bash
# Set in .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

## Optional: Airflow Setup

```bash
pip install -e ".[airflow]"

# Initialize Airflow
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init

# Copy DAG
cp dags/sim_dag.py $AIRFLOW_HOME/dags/

# Start Airflow ( SequentialExecutor )
airflow scheduler &
airflow webserver
```

## Running Smoke Tests

```bash
# Run smoke test configuration (5 personas, 2 rounds)
sim run --config configs/smoke.yaml

# Verify outputs
ls data/sim/runs/
```

Expected outputs:
- `transactions.jsonl`
- `metrics.csv`
- `token_ledger.csv`

## Running Full Simulation

```bash
# Run with default configuration
sim run --config configs/default.yaml

# Or specify custom config
sim run --config configs/my_config.yaml
```

## Generating Reports

```bash
# Generate PDF and Evidently drift report
sim report --run latest --pdf reports/summary.pdf --evidently reports/drift.html

# View PDF
open reports/summary.pdf    # macOS
xdg-open reports/summary.pdf  # Linux
```

## Pushing to GitHub

```bash
# Skip push
sim push --target SKIP_PUSH

# Create private repo and push
sim push --target CREATE_PRIVATE

# Push to existing repo
sim push --target https://github.com/user/repo.git
```

## Troubleshooting

### Qdrant Connection Error

```bash
# For local mode, ensure .qdrant_storage exists
mkdir -p .qdrant_storage

# For server mode, check Docker
docker ps | grep qdrant
```

### LLM Provider Error

```bash
# Verify provider setting
echo $LLM_PROVIDER

# For mock mode, no setup needed
# For Ollama, ensure service is running
curl http://localhost:11434/api/tags

# For OpenAI, verify API key
echo $OPENAI_API_KEY
```

### Import Errors

```bash
# Reinstall in editable mode
pip install -e . --force-reinstall
```

### Memory Issues

Reduce resource profile in `.env`:

```bash
RESOURCE_PROFILE=low
PERSONA_COUNT=20
BATCH_SIZE=4
```

## Resource Tuning

### Low Profile (Testing/Development)

```yaml
persona_count: 20
sim_rounds: 3
llm_max_tokens: 96
memory_top_k: 2
batch_size: 4
debate_enabled: false
qdrant_mode: local
```

### Balanced Profile

```yaml
persona_count: 100
sim_rounds: 6
llm_max_tokens: 160
memory_top_k: 3
batch_size: 8
debate_enabled: true
qdrant_mode: local
```

### High Profile (Production)

```yaml
persona_count: 300
sim_rounds: 10
llm_max_tokens: 256
memory_top_k: 5
batch_size: 16
debate_enabled: true
qdrant_mode: server
```

## Security and Compliance

### Scraping Guidelines

- Only scrape allowlisted domains
- Respect `robots.txt`
- Implement rate limiting (default: 1 request/second)
- Cache responses to avoid repeated requests
- Never store PII

### Secret Management

- Never commit `.env` files
- Use environment variables for all secrets
- Store API keys in secure vaults in production

### Data Handling

- Generated personas are synthetic (no real PII)
- Transaction logs are anonymized
- Memory summaries are truncated (<200 tokens)

## File Structure

```
/workspace
├── src/sim_engine/      # Core engine modules
├── configs/             # YAML configurations
├── data/
│   ├── sample/          # Sample CSV data
│   └── sim/runs/        # Simulation outputs (gitignored)
├── reports/             # Generated reports (gitignored)
├── tests/               # Test suite
├── dags/                # Airflow DAGs
└── scripts/             # Utility scripts
```

## Next Steps

1. Run `sim doctor` to verify setup
2. Run `sim run --config configs/smoke.yaml` for quick test
3. Customize `configs/default.yaml` for your use case
4. Generate reports with `sim report`
