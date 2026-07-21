# Setup Guide - Synthesized Market Simulation Engine

Welcome to the **Synthesized Market Simulation Engine**, a high-throughput, multi-round simulation platform that instantiates hundreds of LLM-powered synthetic consumer and competitor personas to forecast market behavior, transactions, and business shocks.

This comprehensive guide details the environment prerequisites, installation instructions, command-line usage, and advanced integration workflows.

---

## 🚀 Interactive Quick Start

Setting up the entire repository has been fully automated. Run the following command from the repository root:

```bash
# Automatically initialize directories, configure .env, and install all dependencies
bash scripts/setup.sh
```

---

## 🛠️ Prerequisites

- **Python 3.9+** (tested on Python 3.12)
- **Git**
- *Optional:* **Docker** (for running Qdrant in server mode)
- *Optional:* **Ollama** (for local LLM inference)

---

## 📦 Installation & Configuration

### 1. Manual Installation
If you prefer to install packages manually:

```bash
# Install core package in editable mode
pip install -e .

# Install with development dependencies (pytest, black, ruff, etc.)
pip install -e ".[dev]"
```

### 2. Environment Variables (`.env`)
The engine uses environment variables loaded from a `.env` file at the project root. Copy the template:

```bash
cp .env.example .env
```

Customize your `.env` settings:

```env
# LLM Provider: mock (default), ollama, or openai
LLM_PROVIDER=mock

# Resource Profile: low, balanced, high
RESOURCE_PROFILE=low

# Qdrant Vector Memory Mode: local (embedded) or server
QDRANT_MODE=local

# Seed for deterministic simulation behavior
RANDOM_SEED=42
```

---

## 🧠 Qdrant Vector Memory Setup

The engine persists persona state and decision memory using **Qdrant**.

### Mode A: Local (Default, recommended for Low Resource)
No installation required! The client automatically creates a local, zero-dependency storage directory at `.qdrant_storage/`.

### Mode B: Server (Docker Mode)
For production-grade or high-persona simulations, spin up a Qdrant Docker container:

```bash
docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant:latest
```

Then update your `.env` file:
```env
QDRANT_MODE=server
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## 🤖 LLM Provider Setup

### 1. Mock Mode (Zero-API, Offline)
No setup required. The generator uses deterministic pre-compiled templates, which is perfect for debugging and running smoke tests offline.

### 2. OpenAI Integration
Set the OpenAI provider and API key in `.env`:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Ollama (Local LLM Inference)
To run fully local, open-source models:
1. Download and run Ollama from [ollama.com](https://ollama.com).
2. Pull your model of choice:
   ```bash
   ollama pull llama3.2
   ```
3. Update your `.env`:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   ```

---

## 💻 CLI Commands Reference

Once installed, the unified `sim` CLI executable is registered and available.

### 1. `sim bootstrap`
Initializes environment directories, copies `.env.example` to `.env` if missing, and ensures workspace directories are prepared.
```bash
sim bootstrap
```

### 2. `sim doctor`
Runs a robust series of diagnostic health checks verifying your Python version, configuration files, Qdrant memory status, and LLM provider connectivity.
```bash
sim doctor
```

### 3. `sim ingest`
Ingests market events, products, or competitors from CSV, JSON, or JSONL files.
```bash
sim ingest --path data/sample/competitors.csv --type competitors
```

### 4. `sim personas`
Generates a custom synthetic batch of consumer and competitor personas.
```bash
sim personas --count 50 --ratio 0.8 --output data/sample/my_personas.json
```

### 5. `sim run`
Runs a multi-round market simulation.
```bash
# Run with default environment settings
sim run

# Run with a custom profile config
sim run --config configs/smoke.yaml
```

### 6. `sim report`
Generates an executive PDF report (ReportLab-powered) with charts/KPIs/tables, and computes behavioral drift using Evidently AI.
```bash
sim report --run latest --pdf reports/summary.pdf --evidently reports/drift.html
```

### 7. `sim push`
Mock pushes simulation metrics, code, or configs to GitHub.
```bash
sim push --target SKIP_PUSH
```

---

## 🧪 Running Tests

The test suite is built on top of `pytest`. Execute tests using:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest --cov=sim_engine tests/ -v
```

---

## 🪵 File Structure

```
.
├── configs/             # Config files (default.yaml, smoke.yaml)
├── scripts/             # Setup & bootstrap scripts
│   └── setup.sh
├── src/sim_engine/      # Core package source code
│   ├── cli.py           # Unified entrypoint CLI
│   ├── report.py        # PDF executive report builder
│   ├── memory.py        # Qdrant persistence layer
│   └── ...
├── tests/               # Pytest suite
├── .env.example         # Environment template file
├── Makefile             # Convenient task runner
├── README.md            # Overview documentation
└── SETUP_GUIDE.md       # This file
```
