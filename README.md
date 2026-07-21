# Synthesized Market Simulation Engine

A high-throughput simulation platform that instantiates hundreds of LLM-powered synthetic consumer and competitor personas. The engine ingests real-world scraping data or sample market data, simulates business shocks such as price increases, feature updates, or marketing pivots, and outputs agent transactions, churn forecasts, competitor counter-moves, behavioral drift, and executive PDF reports.

## Features

- **Synthetic Personas**: Generate hundreds of consumer and competitor personas with realistic attributes
- **Vector Memory**: Qdrant-backed memory system for persona state persistence
- **Multi-Agent Orchestration**: Consumer, competitor, analyst, and risk auditor agents
- **Simulation Engine**: Run multi-round simulations with business shocks
- **Analytics**: DuckDB-powered analytics for transaction volume, churn, revenue
- **Drift Monitoring**: Evidently AI integration for behavioral drift detection
- **Executive Reports**: ReportLab PDF reports with KPIs and recommendations

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run health check
sim doctor

# Run smoke test simulation
sim run --config configs/smoke.yaml

# Generate reports
sim report --run latest --pdf reports/summary.pdf --evidently reports/drift.html
```

## Configuration

Edit `configs/default.yaml` or create custom configs. Resource profiles:

- **low**: 20 personas, 3 rounds, mock LLM (default for testing)
- **balanced**: 100 personas, 6 rounds
- **high**: 300 personas, 10 rounds, full LLM

## CLI Commands

```bash
sim bootstrap    # Initialize environment
sim doctor       # Health check
sim ingest       # Ingest market data
sim personas     # Generate personas
sim run          # Run simulation
sim report       # Generate reports
sim push         # Push to GitHub
```

## Documentation

See [SETUP.md](SETUP.md) for complete setup instructions.

## License

MIT
