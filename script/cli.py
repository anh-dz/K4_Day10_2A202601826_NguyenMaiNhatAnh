import argparse
import sys
import unittest

from pipelines.phase1 import main as run_phase1
from pipelines.corruption_flow import main as run_corruption

def run_test_pipeline():
    # Run tests using unittest discovery
    print("Running unit tests...")
    tests = unittest.TestLoader().discover('script', pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if not result.wasSuccessful():
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="VinAI Data Observability Lab CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: phase1
    subparsers.add_parser("phase1", help="Run Baseline Phase 1 Pipeline")
    
    # Command: corruption
    subparsers.add_parser("corruption", help="Run Data Corruption & Repair Pipeline")
    
    # Command: test
    subparsers.add_parser("test", help="Run Pipeline Unit Tests")
    
    # Command: ui
    subparsers.add_parser("ui", help="Run Streamlit Web UI")
    
    args = parser.parse_args()

    if args.command == "phase1":
        print("🚀 Bắt đầu chạy Phase 1 Baseline Pipeline...")
        run_phase1()
    elif args.command == "corruption":
        print("🚀 Bắt đầu chạy Data Corruption Pipeline...")
        run_corruption()
    elif args.command == "test":
        print("🚀 Bắt đầu chạy Unit Tests...")
        run_test_pipeline()
    elif args.command == "ui":
        print("🚀 Đang khởi động Streamlit Web UI...")
        import subprocess
        from pathlib import Path
        app_path = Path(__file__).parent.parent / "src" / "app.py"
        subprocess.run(["uv", "run", "streamlit", "run", str(app_path)])
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
