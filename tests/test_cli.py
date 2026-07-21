"""Tests for the Click Command Line Interface."""

import json
from pathlib import Path

from click.testing import CliRunner

from sim_engine.cli import main


def test_cli_help():
    """Test that the CLI help page displays correctly."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "bootstrap" in result.output
    assert "doctor" in result.output
    assert "run" in result.output


def test_cli_bootstrap(tmp_path):
    """Test that bootstrap initializes directories and configuration files."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["bootstrap"])
        assert result.exit_code == 0
        assert "bootstrap complete" in result.output.lower()
        assert Path(".env").exists()


def test_cli_doctor():
    """Test the doctor system diagnostics command."""
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0
    assert "Diagnostics" in result.output
    assert "Python Version" in result.output


def test_cli_personas(tmp_path):
    """Test generating a batch of personas."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        output_file = "test_personas.json"
        result = runner.invoke(main, ["personas", "--count", "5", "--ratio", "0.6", "--output", output_file])
        assert result.exit_code == 0
        assert "Generated" in result.output

        # Verify the generated file
        assert Path(output_file).exists()
        with open(output_file, "r") as f:
            data = json.load(f)
            assert len(data) == 5


def test_cli_push():
    """Test git push mocking targets."""
    runner = CliRunner()
    result = runner.invoke(main, ["push", "--target", "SKIP_PUSH"])
    assert result.exit_code == 0
    assert "Push skipped" in result.output
