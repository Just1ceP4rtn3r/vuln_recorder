import argparse
import sys
from pathlib import Path

from .engine import Engine
from .scenario import Scenario


def main():
    parser = argparse.ArgumentParser(
        prog='vuln_recorder',
        description='Automated vulnerability verification recorder',
    )
    subparsers = parser.add_subparsers(dest='command')

    run_parser = subparsers.add_parser('run', help='Run a scenario')
    run_parser.add_argument('scenario', help='Path to scenario YAML file')
    run_parser.add_argument('--dry-run', action='store_true', help='Parse only, do not execute')

    subparsers.add_parser('check', help='Check dependencies')

    args = parser.parse_args()

    if args.command == 'run':
        if args.dry_run:
            scenario = Scenario(args.scenario)
            data = scenario.load()
            print(f"Scenario: {data['name']}")
            print(f"Steps: {len(data['steps'])}")
            print("Dry run completed successfully.")
            return

        engine = Engine(args.scenario)
        output_dir = engine.run()
        print(f"Recording saved to: {output_dir}")

        outputs_file = Path(output_dir) / "scenario-outputs.yaml"
        if outputs_file.exists():
            print()
            print(outputs_file.read_text())

    elif args.command == 'check':
        engine = Engine('')
        try:
            engine.check_dependencies()
            print("All dependencies are installed.")
        except RuntimeError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
