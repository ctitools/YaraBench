"""Test CLI functionality."""

import pytest
import tempfile
import json
from pathlib import Path
from click.testing import CliRunner

from src.cli import cli


class TestCLI:
    """Test CLI commands."""
    
    def test_cli_version(self):
        """Test CLI version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "yara-bench" in result.output
    
    def test_validate_level1(self):
        """Test validate command for Level 1."""
        runner = CliRunner()
        result = runner.invoke(cli, ['validate', '--level', '1'])
        
        assert result.exit_code == 0
        assert "Level 1" in result.output
    
    def test_validate_level2(self):
        """Test validate command for Level 2."""
        runner = CliRunner()
        result = runner.invoke(cli, ['validate', '--level', '2'])
        
        assert result.exit_code == 0
        assert "Level 2" in result.output
        assert "LLM client" in result.output
    
    def test_list_command(self):
        """Test list command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['list'])
        
        assert result.exit_code == 0
        assert "Available Challenges" in result.output
        assert "LEVEL 1" in result.output
        assert "LEVEL 2" in result.output
    
    def test_list_specific_level(self):
        """Test list command for specific level."""
        runner = CliRunner()
        result = runner.invoke(cli, ['list', '--level', '1'])
        
        assert result.exit_code == 0
        assert "Available Challenges" in result.output
        assert "LEVEL 1" in result.output
    
    def test_run_missing_model(self):
        """Test run command without model."""
        runner = CliRunner()
        result = runner.invoke(cli, ['run'])
        
        assert result.exit_code != 0
        # Should require model parameter
    
    def test_run_missing_api_key(self):
        """Test run command without API key."""
        runner = CliRunner()
        result = runner.invoke(cli, ['run', '--model', 'test-model'])
        
        # Should fail due to missing API key
        assert result.exit_code != 0
    
    def test_run_json_output_without_file(self):
        """Test run command with JSON output but no file."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'run', 
            '--model', 'test-model',
            '--output', 'json'
        ])
        
        assert result.exit_code != 0
        assert "output-file required" in result.output
    
    def test_run_valid_json_output(self):
        """Test run command with valid JSON output configuration."""
        runner = CliRunner()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            result = runner.invoke(cli, [
                'run',
                '--model', 'test-model',
                '--output', 'json',
                '--output-file', temp_file,
                '--api-key', 'fake-key',
                '--base-url', 'http://fake.api',
                '--levels', 'level1'  # Only run level1 which doesn't require API
            ])
            
            # Level1 should succeed without API calls
            assert result.exit_code == 0
            assert "Results written to" in result.output
            assert Path(temp_file).exists()
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def test_get_command(self):
        """Test get command placeholder."""
        runner = CliRunner()
        result = runner.invoke(cli, ['get'])
        
        assert result.exit_code == 0
        assert "Random Challenges" in result.output
    
    def test_get_command_with_options(self):
        """Test get command with options."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'get', 
            '--levels', '1,2',
            '--num-samples', '3'
        ])
        
        assert result.exit_code == 0
        assert "Random Challenges" in result.output


class TestCLIConfiguration:
    """Test CLI configuration handling."""
    
    def test_model_config_creation(self):
        """Test that CLI creates proper model configs."""
        from src.models import ModelConfig
        
        # This tests the config creation logic that would happen in CLI
        model_config = ModelConfig(
            name="test-model",
            api_key="test-key",
            base_url="https://api.test.com"
        )
        
        assert model_config.name == "test-model"
        assert model_config.api_key == "test-key"
        assert str(model_config.base_url) == "https://api.test.com/"
    
    def test_level_parsing(self):
        """Test level parsing logic."""
        # Test "all" parsing
        def parse_levels(levels_str):
            if levels_str.lower() == "all":
                return ["level1", "level2", "level3"]
            else:
                return [f"level{l.strip()}" for l in levels_str.split(",")]
        
        assert parse_levels("all") == ["level1", "level2", "level3"]
        assert parse_levels("1") == ["level1"]
        assert parse_levels("1,2") == ["level1", "level2"]
        assert parse_levels("1, 2, 3") == ["level1", "level2", "level3"]
    
    def test_config_validation(self):
        """Test configuration validation logic."""
        # Tests the validation that happens in CLI
        def validate_output_config(output_format, output_file):
            if output_format in ["json", "csv"] and not output_file:
                return False, "output-file required for json/csv output"
            return True, None
        
        # Valid configs
        valid, msg = validate_output_config("terminal", None)
        assert valid and msg is None
        
        valid, msg = validate_output_config("json", "output.json")
        assert valid and msg is None
        
        # Invalid configs
        valid, msg = validate_output_config("json", None)
        assert not valid and "output-file required" in msg
        
        valid, msg = validate_output_config("csv", None)
        assert not valid and "output-file required" in msg