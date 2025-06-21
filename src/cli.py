"""CLI interface for YaraBench."""

import os
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table

# Try to load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from . import __version__
from .models import Config, ModelConfig
from .benchmark import Benchmark

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="yara-bench")
def cli():
    """YaraBench - A benchmark for evaluating LLM-generated YARA rules."""
    pass


@cli.command()
@click.option(
    "--model", "-m",
    multiple=True,
    required=True,
    help="Model(s) to benchmark (can specify multiple)"
)
@click.option(
    "--levels", "-l",
    default="1",
    help="Challenge levels to run (comma-separated or 'all')"
)
@click.option(
    "--base-url",
    envvar="OPENAI_BASE_URL",
    help="API base URL"
)
@click.option(
    "--api-key",
    envvar="OPENAI_API_KEY",
    help="API key"
)
@click.option(
    "--output", "-o",
    type=click.Choice(["terminal", "json", "csv"]),
    default="terminal",
    help="Output format"
)
@click.option(
    "--output-file", "-f",
    type=click.Path(),
    help="Output file (for json/csv formats)"
)
@click.option(
    "--judge",
    help="LLM model to use as judge (optional)"
)
@click.option(
    "--synthetic-count",
    type=int,
    default=10,
    help="Number of synthetic challenges for Level 2"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
def run(
    model: List[str],
    levels: str,
    base_url: Optional[str],
    api_key: Optional[str],
    output: str,
    output_file: Optional[str],
    judge: Optional[str],
    synthetic_count: int,
    verbose: bool
):
    """Run the benchmark on specified models."""
    # Parse levels
    if levels.lower() == "all":
        level_list = ["level1", "level2", "level3"]
    else:
        level_list = [f"level{l.strip()}" for l in levels.split(",")]
    
    # Validate output file requirement
    if output in ["json", "csv"] and not output_file:
        console.print("[red]Error: --output-file required for json/csv output[/red]")
        sys.exit(1)
    
    # Create model configs
    model_configs = []
    for model_name in model:
        model_configs.append(ModelConfig(
            name=model_name,
            base_url=base_url,
            api_key=api_key
        ))
    
    # Create judge config if specified
    judge_config = None
    if judge:
        judge_config = ModelConfig(
            name=judge,
            base_url=os.getenv("JUDGE_MODEL_BASE_URL", base_url),
            api_key=os.getenv("JUDGE_MODEL_API_KEY", api_key)
        )
    
    # Create main config
    config = Config(
        models=model_configs,
        levels=level_list,
        judge_model=judge_config,
        synthetic_count=synthetic_count,
        output_format=output,
        output_file=output_file,
        verbose=verbose
    )
    
    # Run benchmark
    console.print(f"[bold blue]YaraBench v{__version__}[/bold blue]")
    console.print(f"Running benchmark on {len(model_configs)} model(s)...")
    
    try:
        benchmark = Benchmark(config)
        benchmark.run()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--level", "-l",
    type=click.Choice(["1", "2", "3"]),
    help="Challenge level to list"
)
def list(level: Optional[str]):
    """List available challenges."""
    from .levels import Level1, Level2, Level3
    
    console.print("[bold]Available Challenges[/bold]\n")
    
    level_classes = {"1": Level1, "2": Level2, "3": Level3}
    levels_to_check = [level] if level else ["1", "2", "3"]
    
    for level_num in levels_to_check:
        level_instance = level_classes[level_num]()
        
        console.print(f"[yellow]LEVEL {level_num}:[/yellow] {level_instance.name}")
        console.print(f"  {level_instance.description}")
        
        if level_instance.validate():
            challenges = level_instance.get_challenges()
            if challenges:
                console.print(f"  [green]{len(challenges)} challenges available:[/green]")
                for challenge in challenges:
                    actionable = "[green]✓[/green]" if challenge.actionable else "[red]✗[/red]"
                    console.print(f"    {actionable} {challenge.id}: {challenge.description[:80]}...")
            else:
                console.print(f"  [yellow]No challenges available[/yellow]")
        else:
            console.print(f"  [red]Level not configured[/red]")
        console.print()


@cli.command()
@click.option(
    "--level", "-l",
    type=click.Choice(["1", "2", "3"]),
    required=True,
    help="Challenge level to validate"
)
def validate(level: str):
    """Validate challenge files."""
    console.print(f"[bold]Validating Level {level} Challenges[/bold]\n")
    
    from .levels import Level1, Level2, Level3
    
    # Get the appropriate level class
    level_classes = {"1": Level1, "2": Level2, "3": Level3}
    level_class = level_classes[level]
    
    # Create level instance and validate
    if level == "2":
        # Level 2 needs an LLM client, so we just check if it can be instantiated
        level_instance = level_class()
        console.print(f"[yellow]Level {level} requires LLM client for full validation[/yellow]")
        console.print(f"  {level_instance.description}")
        console.print(f"  [green]Level structure valid[/green]")
    else:
        level_instance = level_class()
        if level_instance.validate():
            console.print(f"[green]✓[/green] Level {level} validation passed")
            
            # Show challenge count for Level 1
            if level == "1":
                challenges = level_instance.get_challenges()
                console.print(f"  Found {len(challenges)} valid challenges")
                for challenge in challenges:
                    console.print(f"    • {challenge.id}: {challenge.description[:60]}...")
        else:
            console.print(f"[red]✗[/red] Level {level} validation failed")


@cli.command()
def test():
    """Run tests."""
    import pytest
    
    console.print("[bold]Running YaraBench Tests[/bold]\n")
    
    # Run pytest
    test_dir = Path(__file__).parent.parent / "tests"
    exit_code = pytest.main([str(test_dir), "-v"])
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--levels", "-l",
    default="1",
    help="Challenge levels (comma-separated or 'all')"
)
@click.option(
    "--num-samples", "-n",
    type=int,
    default=1,
    help="Number of challenges to retrieve"
)
def get(levels: str, num_samples: int):
    """Get random challenge(s) for manual testing."""
    import random
    from .levels import Level1, Level2, Level3
    from .models import Challenge
    
    console.print(f"[bold]Random Challenges for Manual Testing[/bold]\n")
    
    # Parse levels
    if levels.lower() == "all":
        level_list = ["1", "2", "3"]
    else:
        level_list = levels.split(",")
    
    # Get challenges from each level
    for level_num in level_list:
        console.print(f"[yellow]Level {level_num}:[/yellow]")
        
        try:
            if level_num == "1":
                level = Level1()
                challenges = level.get_challenges()
                
                if challenges:
                    # Sample random challenges
                    sampled = random.sample(challenges, min(num_samples, len(challenges)))
                    
                    for i, challenge in enumerate(sampled, 1):
                        console.print(f"\n[green]Challenge {i}:[/green]")
                        console.print(f"ID: {challenge.id}")
                        console.print(f"Description: {challenge.description}")
                        console.print(f"Actionable: {'Yes' if challenge.actionable else 'No'}")
                        console.print(f"Expected Strings: {', '.join(challenge.expected_strings[:3])}{'...' if len(challenge.expected_strings) > 3 else ''}")
                        console.print(f"Test Files: {len(challenge.test_files)}")
                else:
                    console.print("  No challenges available")
                    
            elif level_num == "2":
                console.print("  Level 2 requires LLM client for synthetic generation")
                console.print("  Use: yara-bench run --model <model> --levels 2 --synthetic-count 1")
                
            elif level_num == "3":
                level = Level3()
                challenges = level.get_challenges(count=num_samples)
                
                for i, challenge in enumerate(challenges, 1):
                    console.print(f"\n[green]Challenge {i}:[/green]")
                    console.print(f"ID: {challenge.id}")
                    console.print(f"Description: {challenge.description[:100]}...")
                    console.print(f"(Mock challenge - Level 3 not yet implemented)")
                    
        except Exception as e:
            console.print(f"  [red]Error:[/red] {str(e)}")
        
        console.print()


@cli.command()
@click.option(
    "--token", "-t",
    envvar="HF_TOKEN",
    help="HuggingFace token for accessing gated datasets"
)
@click.option(
    "--repo-id",
    default="ctitools/YaraBench",
    help="HuggingFace dataset repository ID"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Force re-download even if data exists"
)
def download(token: Optional[str], repo_id: str, force: bool):
    """Download additional challenge datasets from HuggingFace.
    
    Downloads challenge files from the gated HuggingFace repository and
    overlays them on top of the existing demo challenges in the data/ directory.
    The demo challenges remain for development/testing, while the HF challenges
    are added with '_hf_' prefix to distinguish them.
    """
    from huggingface_hub import snapshot_download, login
    import shutil
    
    console.print(f"[bold]YaraBench Dataset Download[/bold]\n")
    console.print(f"Repository: {repo_id}")
    console.print("This will download additional challenges from HuggingFace")
    console.print("and overlay them with the existing demo challenges.\n")
    
    # Check for token
    if not token:
        console.print("[red]Error: HuggingFace token required![/red]")
        console.print("Please provide a token via --token or HF_TOKEN environment variable")
        console.print("\nGet your token from: https://huggingface.co/settings/tokens")
        console.print("Make sure you have access to the gated repository.")
        sys.exit(1)
    
    # Paths
    base_path = Path(__file__).parent.parent
    data_path = base_path / "data"
    cache_dir = base_path / ".cache" / "huggingface"
    
    # Count existing HF challenges
    import builtins
    existing_hf = builtins.list(data_path.glob("level*/*_hf_*.json"))
    if existing_hf and not force:
        console.print(f"[yellow]Found {len(existing_hf)} existing HuggingFace challenges[/yellow]")
        console.print("Use --force to re-download")
        return
    
    try:
        # Login to HuggingFace
        console.print("🔐 Authenticating with HuggingFace...")
        login(token=token, add_to_git_credential=False)
        
        # Download dataset to cache
        console.print(f"📥 Downloading from {repo_id}...")
        
        downloaded_path = snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            cache_dir=str(cache_dir),
            force_download=force
        )
        
        # Copy files to data directory with _hf_ prefix
        console.print("📁 Installing challenge files...")
        downloaded_path = Path(downloaded_path)
        
        copied_files = 0
        skipped_files = 0
        
        # Check for both direct level* directories and data/level* structure
        level_dirs = builtins.list(downloaded_path.glob("level*")) + builtins.list(downloaded_path.glob("data/level*"))
        
        for level_dir in level_dirs:
            if level_dir.is_dir():
                # Extract just the level name (e.g., "level1" from "data/level1")
                level_name = level_dir.name
                target_dir = data_path / level_name
                target_dir.mkdir(parents=True, exist_ok=True)
                
                for json_file in level_dir.glob("*.json"):
                    # Add _hf_ prefix to distinguish from demo files
                    target_file = target_dir / f"{json_file.stem}_hf_.json"
                    
                    # Skip if exists and not forcing
                    if target_file.exists() and not force:
                        skipped_files += 1
                        continue
                    
                    shutil.copy2(json_file, target_file)
                    console.print(f"  [green]✓[/green] {level_name}/{target_file.name}")
                    copied_files += 1
        
        # Summary
        console.print(f"\n[green]✅ Success![/green]")
        console.print(f"  Downloaded: {copied_files} new challenge files")
        if skipped_files > 0:
            console.print(f"  Skipped: {skipped_files} existing files")
        
        # Count total challenges
        total_challenges = len(builtins.list(data_path.glob("level*/*.json")))
        demo_challenges = total_challenges - len(builtins.list(data_path.glob("level*/*_hf_*.json")))
        
        console.print(f"\nTotal challenges available: {total_challenges}")
        console.print(f"  Demo challenges: {demo_challenges}")
        console.print(f"  HuggingFace challenges: {total_challenges - demo_challenges}")
        
        console.print("\nRun './yara-bench list' to see all available challenges.")
        
    except Exception as e:
        console.print(f"\n[red]Error downloading dataset:[/red] {str(e)}")
        
        if "gated repo" in str(e).lower() or "401" in str(e):
            console.print("\n[yellow]This appears to be a gated repository.[/yellow]")
            console.print(f"Please visit https://huggingface.co/datasets/{repo_id}")
            console.print("and accept the terms to gain access.")
        elif "404" in str(e):
            console.print("\n[yellow]Repository not found.[/yellow]")
            console.print(f"Please check that {repo_id} exists and you have access.")
        
        sys.exit(1)


if __name__ == "__main__":
    cli()