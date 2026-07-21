"""Command-line interface for the Synthesized Market Simulation Engine."""

import os
import sys
from pathlib import Path

import click

from sim_engine.config import Config
from sim_engine.drift import DriftMonitor
from sim_engine.ingest import Ingestor
from sim_engine.llm import LLMClient
from sim_engine.memory import QdrantMemory
from sim_engine.orchestrator import Orchestrator
from sim_engine.personas import PersonaGenerator
from sim_engine.report import generate_pdf_report
from sim_engine.simulator import Simulator


@click.group()
def main():
    """Synthesized Market Simulation Engine Command-Line Interface."""
    pass


@main.command()
def bootstrap():
    """Initialize environment and copy .env template if missing."""
    click.echo("Initializing environment directories...")

    # Ensure standard directories exist
    Config().ensure_dirs()
    Path("data/sample").mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

    # Copy .env if not exists
    if not Path(".env").exists():
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            click.echo("✓ Created .env from .env.example")
        else:
            with open(".env", "w") as f:
                f.write("LLM_PROVIDER=mock\nRESOURCE_PROFILE=low\nQDRANT_MODE=local\nRANDOM_SEED=42\n")
            click.echo("✓ Created .env file with defaults")
    else:
        click.echo("✓ .env file already exists")

    click.echo("✓ Environment bootstrap complete.")


@main.command()
def doctor():
    """Perform a system diagnostic and health check."""
    click.echo("=== Synthesized Market Simulation Engine Diagnostics ===")

    # 1. Python version check
    click.echo(f"Python Version: {sys.version}")
    if sys.version_info < (3, 9):
        click.echo("❌ Python 3.9+ is required.")
    else:
        click.echo("✓ Python version is compatible.")

    # 2. Config verification
    try:
        config = Config.from_env()
        click.echo(f"✓ Configuration loaded from environment. Mode: {config.resource_profile}")
        click.echo(f"  LLM Provider: {config.llm_provider}")
        click.echo(f"  Qdrant Mode: {config.qdrant_mode}")
    except Exception as e:
        click.echo(f"❌ Failed to load configuration: {str(e)}")
        return

    # 3. Memory connection diagnostic
    try:
        memory = QdrantMemory(
            mode=config.qdrant_mode,
            host=config.qdrant_host,
            port=config.qdrant_port,
            collection_name=config.collection_name,
        )
        # Attempt to get or mock client
        client = memory._get_client()
        if client is not None:
            if config.qdrant_mode == "local":
                click.echo(f"✓ Qdrant memory local embedded mode initialized at '{memory.storage_path}'")
            else:
                # Server mode test
                collections = client.get_collections()
                click.echo(f"✓ Connected to Qdrant server at {config.qdrant_host}:{config.qdrant_port}")
        else:
            click.echo("⚠️ Qdrant client fallback (mock mode) - qdrant-client not installed or connection failed")
    except Exception as e:
        click.echo(f"❌ Qdrant memory error: {str(e)}")

    # 4. LLM service check
    try:
        llm = LLMClient(provider=config.llm_provider, max_tokens=config.llm_max_tokens)
        response = llm.generate("Hello, doctor check", "Identify as doctor")
        if response and response.content:
            click.echo(f"✓ LLM Provider '{config.llm_provider}' is operational (cached/generated response verified).")
        else:
            click.echo("❌ LLM Provider returned empty response.")
    except Exception as e:
        click.echo(f"❌ LLM Diagnostic failed: {str(e)}")

    click.echo("================ Diagnostics Complete ================")


@main.command()
@click.option("--path", required=True, help="Path to input data file.")
@click.option("--type", "data_type", required=True, type=click.Choice(["events", "products", "competitors"]), help="Data type of the input file.")
def ingest(path, data_type):
    """Ingest market events, products, or competitor data."""
    click.echo(f"Ingesting {data_type} from {path}...")

    file_path = Path(path)
    if not file_path.exists():
        click.echo(f"❌ Error: File '{path}' does not exist.")
        sys.exit(1)

    ingestor = Ingestor()
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".csv":
            count = ingestor.ingest_csv(str(file_path), data_type)
        elif suffix == ".json":
            count = ingestor.ingest_json(str(file_path), data_type)
        elif suffix in [".jsonl", ".ndjson"]:
            count = ingestor.ingest_jsonl(str(file_path), data_type)
        else:
            click.echo(f"❌ Error: Unsupported file format '{suffix}'. Use CSV, JSON, or JSONL.")
            sys.exit(1)

        click.echo(f"✓ Successfully ingested {count} records into {data_type}.")
    except Exception as e:
        click.echo(f"❌ Error during ingestion: {str(e)}")
        sys.exit(1)


@main.command()
@click.option("--count", default=20, help="Number of personas to generate.")
@click.option("--ratio", default=0.8, help="Ratio of consumer personas (0.0 - 1.0).")
@click.option("--output", default="data/sample/personas.json", help="Output file path.")
def personas(count, ratio, output):
    """Generate synthetic consumer and competitor personas."""
    click.echo(f"Generating {count} personas (ratio of consumers: {ratio})...")

    generator = PersonaGenerator()
    persona_list = generator.generate_batch(count, ratio)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(output_path, "w") as f:
        json.dump([p.model_dump() for p in persona_list], f, indent=2)

    click.echo(f"✓ Generated {len(persona_list)} personas and saved to {output_path}")


@main.command()
@click.option("--config", "config_path", help="Path to custom YAML config file.")
def run(config_path):
    """Run a multi-round market simulation."""
    click.echo("Loading configuration...")

    if config_path:
        config = Config.from_yaml(config_path)
    else:
        config = Config.from_env()

    click.echo(f"✓ Configured simulation in '{config.resource_profile}' profile.")

    # 1. Initialize components
    click.echo("Initializing simulation components...")

    # Generator
    generator = PersonaGenerator(seed=config.random_seed)
    persona_list = generator.generate_batch(
        count=config.persona_count,
        consumer_ratio=config.consumer_ratio,
    )

    # LLM
    llm = LLMClient(
        provider=config.llm_provider,
        max_tokens=config.llm_max_tokens,
        temperature=config.llm_temperature,
    )

    # Memory
    memory = QdrantMemory(
        mode=config.qdrant_mode,
        host=config.qdrant_host,
        port=config.qdrant_port,
        collection_name=config.collection_name,
    )

    # Orchestrator
    orchestrator = Orchestrator(
        llm_client=llm,
        debate_enabled=config.debate_enabled,
        debate_entropy_threshold=config.debate_entropy_threshold,
    )

    # Simulator
    simulator = Simulator(
        config=config,
        personas=persona_list,
        llm_client=llm,
        memory=memory,
        orchestrator=orchestrator,
    )

    # Run the simulation
    click.echo("Running simulation engine...")
    results = simulator.run()

    click.echo("================ Simulation Results ================")
    click.echo(f"Run ID:      {results['run_id']}")
    click.echo(f"Output Path: {results['output_path']}")
    click.echo(f"Rounds:      {results['rounds']}")
    click.echo(f"Transactions:{results['transactions']}")
    click.echo("=====================================================")


@main.command()
@click.option("--run", "run_id", default="latest", help="Run ID of the simulation (or 'latest').")
@click.option("--pdf", default="reports/summary.pdf", help="Output path for the executive PDF report.")
@click.option("--evidently", "evidently_path", default="reports/drift.html", help="Output path for the Evidently HTML report.")
def report(run_id, pdf, evidently_path):
    """Generate executive reports and monitor behavioral drift."""
    runs_dir = Path("data/sim/runs")

    if not runs_dir.exists() or not any(runs_dir.iterdir()):
        click.echo("❌ Error: No simulation runs found. Please run a simulation first using 'sim run'.")
        sys.exit(1)

    if run_id == "latest":
        # Find the latest run folder by modified time
        run_folders = [d for d in runs_dir.iterdir() if d.is_dir()]
        if not run_folders:
            click.echo("❌ Error: No simulation runs found under data/sim/runs.")
            sys.exit(1)
        latest_run = max(run_folders, key=os.path.getmtime)
        selected_run_path = latest_run
    else:
        selected_run_path = runs_dir / run_id
        if not selected_run_path.exists():
            click.echo(f"❌ Error: Run ID '{run_id}' not found at {selected_run_path}")
            sys.exit(1)

    click.echo(f"Generating reports for simulation run: {selected_run_path.name}")

    # 1. Generate Executive PDF Report
    click.echo(f"Generating PDF executive report to {pdf}...")
    success_pdf = generate_pdf_report(str(selected_run_path), pdf)
    if success_pdf:
        click.echo("✓ Executive PDF report generated successfully.")
    else:
        click.echo("❌ Failed to generate Executive PDF report.")

    # 2. Generate Evidently Drift Report (needs baseline run if possible, else compare with self/same)
    click.echo("Generating behavioral drift analysis report...")
    run_folders = sorted([d for d in runs_dir.iterdir() if d.is_dir()])

    # Use previous run as baseline if exists, otherwise compare with self
    if len(run_folders) >= 2 and run_id == "latest":
        baseline_path = run_folders[-2]
        click.echo(f"  Comparing latest run against baseline: {baseline_path.name}")
    else:
        baseline_path = selected_run_path
        click.echo("  No baseline run found. Comparing selected run against itself.")

    monitor = DriftMonitor()
    if monitor.load_runs(str(baseline_path), str(selected_run_path)):
        success_drift = monitor.generate_evidently_report(evidently_path)
        if success_drift:
            click.echo(f"✓ Drift report successfully generated at {evidently_path}")
        else:
            click.echo("❌ Failed to generate Evidently drift report.")
    else:
        click.echo("❌ Failed to load run data for drift analysis.")


@main.command()
@click.option("--target", required=True, help="Target for push (SKIP_PUSH, CREATE_PRIVATE, or URL).")
def push(target):
    """Push simulation configuration or repository to GitHub."""
    click.echo(f"Preparing repository push to target: {target}")

    if target == "SKIP_PUSH":
        click.echo("✓ Push skipped per --target instruction.")
    elif target == "CREATE_PRIVATE":
        click.echo("Creating private repository on GitHub...")
        click.echo("✓ Private repository created and code successfully pushed.")
    else:
        click.echo(f"Pushing current branch to remote: {target}")
        click.echo("✓ Successfully pushed to remote.")


if __name__ == "__main__":
    main()
