#!/usr/bin/env python
"""CLI for Day 10 Data Pipeline & Data Observability Lab.

Usage:
    uv run python script/cli.py phase1          # Run baseline pipeline
    uv run python script/cli.py corruption       # Run corruption flow
    uv run python script/cli.py all              # Run both phases
    uv run python script/cli.py validate         # Validate all artifacts
    uv run python script/cli.py status           # Show current pipeline status
    uv run python script/cli.py agent "question" # Ask agent a question
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.config import load_settings, require_llm_credentials
from core.utils import read_json


def cmd_phase1(args: argparse.Namespace) -> None:
    """Run baseline pipeline."""
    from pipelines.phase1 import main
    main()


def cmd_corruption(args: argparse.Namespace) -> None:
    """Run corruption flow."""
    from pipelines.corruption_flow import main
    main()


def cmd_all(args: argparse.Namespace) -> None:
    """Run both phases sequentially."""
    print("=" * 60)
    print("PHASE 1: Baseline Pipeline")
    print("=" * 60)
    cmd_phase1(args)
    print()
    print("=" * 60)
    print("PHASE 2: Corruption Flow")
    print("=" * 60)
    cmd_corruption(args)
    print()
    print("=" * 60)
    print("ALL PHASES COMPLETE")
    print("=" * 60)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate all pipeline artifacts exist and are consistent."""
    settings = load_settings()
    paths = settings.paths

    checks = {
        "raw/crossref_response.json": paths.raw_api_response,
        "raw/crossref_records.json": paths.raw_records_json,
        "clean/papers_clean.csv": paths.clean_csv,
        "clean/papers_clean.json": paths.clean_json,
        "embeddings/papers_embeddings.json": paths.embeddings_json,
        "eval/test_set.json": paths.eval_testset,
        "results/baseline_metrics.json": paths.baseline_metrics,
        "results/baseline_answers.json": paths.baseline_answers,
        "quality/baseline_quality.json": paths.quality_dir / "baseline_quality.json",
        "quality/freshness_report.json": paths.freshness_report,
        "reports/phase1_report.md": paths.baseline_report,
        # Phase 2
        "results/corruption_log.json": paths.corruption_log,
        "clean/papers_clean_corrupted.csv": paths.corrupted_clean_csv,
        "clean/papers_clean_corrupted.json": paths.corrupted_clean_json,
        "results/corrupted_metrics.json": paths.corrupted_metrics,
        "clean/papers_clean_repaired.csv": paths.repaired_clean_csv,
        "clean/papers_clean_repaired.json": paths.repaired_clean_json,
        "results/repaired_metrics.json": paths.repaired_metrics,
        "reports/corruption_report.md": paths.comparison_report,
    }

    print("=" * 60)
    print("ARTIFACT VALIDATION")
    print("=" * 60)

    all_pass = True
    phase1_ok = True
    phase2_ok = True

    phase1_keys = [
        "raw/crossref_response.json", "raw/crossref_records.json",
        "clean/papers_clean.csv", "clean/papers_clean.json",
        "embeddings/papers_embeddings.json", "eval/test_set.json",
        "results/baseline_metrics.json", "results/baseline_answers.json",
        "quality/baseline_quality.json", "quality/freshness_report.json",
        "reports/phase1_report.md",
    ]

    print("\n--- Phase 1 Artifacts ---")
    for key in phase1_keys:
        path = checks[key]
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        status = f"✅ OK ({size:,} bytes)" if exists and size > 0 else "❌ MISSING"
        print(f"  {key}: {status}")
        if not exists or size == 0:
            phase1_ok = False
            all_pass = False

    phase2_keys = [k for k in checks if k not in phase1_keys]
    print("\n--- Phase 2 Artifacts ---")
    for key in phase2_keys:
        path = checks[key]
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        status = f"✅ OK ({size:,} bytes)" if exists and size > 0 else "❌ MISSING"
        print(f"  {key}: {status}")
        if not exists or size == 0:
            phase2_ok = False
            all_pass = False

    # Validate metrics consistency
    print("\n--- Metrics Validation ---")
    if paths.baseline_metrics.exists():
        baseline = read_json(paths.baseline_metrics)
        print(f"  Baseline retrieval_hit_rate: {baseline.get('retrieval_hit_rate', 'N/A')}")
        print(f"  Baseline mean_token_f1: {baseline.get('mean_token_f1', 'N/A')}")
        print(f"  Baseline samples: {baseline.get('samples', 'N/A')}")

    if paths.corrupted_metrics.exists():
        corrupted = read_json(paths.corrupted_metrics)
        print(f"  Corrupted retrieval_hit_rate: {corrupted.get('retrieval_hit_rate', 'N/A')}")

    if paths.repaired_metrics.exists():
        repaired = read_json(paths.repaired_metrics)
        print(f"  Repaired retrieval_hit_rate: {repaired.get('retrieval_hit_rate', 'N/A')}")

    # Check corruption proves impact
    if paths.baseline_metrics.exists() and paths.corrupted_metrics.exists():
        b_hit = baseline.get("retrieval_hit_rate", 0)
        c_hit = corrupted.get("retrieval_hit_rate", 0)
        if c_hit < b_hit:
            print("  ✅ Corruption impact verified: corrupted < baseline")
        else:
            print("  ⚠️ Warning: corruption did not degrade retrieval_hit_rate")

    print(f"\n{'=' * 60}")
    print(f"Phase 1: {'✅ PASS' if phase1_ok else '❌ FAIL'}")
    print(f"Phase 2: {'✅ PASS' if phase2_ok else '❌ FAIL'}")
    print(f"Overall: {'✅ ALL PASS' if all_pass else '❌ SOME MISSING'}")
    print(f"{'=' * 60}")

    sys.exit(0 if all_pass else 1)


def cmd_status(args: argparse.Namespace) -> None:
    """Show current pipeline status."""
    settings = load_settings()
    paths = settings.paths

    print("=" * 60)
    print("PIPELINE STATUS")
    print("=" * 60)
    print(f"  LLM Provider: {settings.llm_provider}")
    print(f"  LLM Model:    {settings.model_name}")
    print(f"  Embedding:    {settings.embedding_model}")
    print(f"  Source Query:  {settings.source_query}")
    print(f"  Max Results:   {settings.max_results}")
    print(f"  Top-K:         {settings.top_k}")
    print()

    # Check what's been done
    has_raw = paths.raw_records_json.exists()
    has_clean = paths.clean_csv.exists()
    has_index = paths.embeddings_json.exists()
    has_eval = paths.eval_testset.exists()
    has_baseline = paths.baseline_metrics.exists()
    has_corruption = paths.corrupted_metrics.exists()
    has_repaired = paths.repaired_metrics.exists()

    print("  Pipeline Progress:")
    print(f"    [{'x' if has_raw else ' '}] Raw data fetched")
    print(f"    [{'x' if has_clean else ' '}] Data cleaned")
    print(f"    [{'x' if has_index else ' '}] Embedding index built")
    print(f"    [{'x' if has_eval else ' '}] Evaluation set created")
    print(f"    [{'x' if has_baseline else ' '}] Baseline evaluated")
    print(f"    [{'x' if has_corruption else ' '}] Corruption evaluated")
    print(f"    [{'x' if has_repaired else ' '}] Repaired evaluated")

    if has_baseline:
        metrics = read_json(paths.baseline_metrics)
        print(f"\n  Baseline Metrics:")
        for k, v in metrics.items():
            if k != "ragas":
                print(f"    {k}: {v}")


def cmd_agent(args: argparse.Namespace) -> None:
    """Ask the agent a question."""
    settings = load_settings()
    require_llm_credentials(settings)
    paths = settings.paths

    if not paths.embeddings_json.exists():
        print("Error: Index not built yet. Run 'cli.py phase1' first.")
        sys.exit(1)

    from retrieval.index import LocalEmbeddingIndex
    from retrieval.agent import build_agent, run_agent_question

    print(f"Loading index...")
    index = LocalEmbeddingIndex.load(settings)

    print(f"Building agent ({settings.llm_provider}/{settings.model_name})...")
    agent = build_agent(settings, index)

    question = " ".join(args.question)
    print(f"\nQ: {question}")
    answer = run_agent_question(agent, question)
    print(f"A: {answer}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cli",
        description="Day 10 - Data Pipeline & Data Observability Lab CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("phase1", help="Run baseline pipeline (Phase 1)")
    subparsers.add_parser("corruption", help="Run corruption flow (Phase 2)")
    subparsers.add_parser("all", help="Run both phases sequentially")
    subparsers.add_parser("validate", help="Validate all pipeline artifacts")
    subparsers.add_parser("status", help="Show current pipeline status")

    agent_parser = subparsers.add_parser("agent", help="Ask agent a question")
    agent_parser.add_argument("question", nargs="+", help="Question to ask")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "phase1": cmd_phase1,
        "corruption": cmd_corruption,
        "all": cmd_all,
        "validate": cmd_validate,
        "status": cmd_status,
        "agent": cmd_agent,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
