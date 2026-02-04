"""CLI entry point for pipeline execution."""
import argparse
import sys
from orchestration.run_context import RunContext
from orchestration.pipeline import PipelineExecutor
from config.settings import settings


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Loan Engine Pipeline CLI")
    parser.add_argument(
        "--folder",
        type=str,
        default=settings.INPUT_DIR,
        help="Input folder path"
    )
    parser.add_argument(
        "--pdate",
        type=str,
        default=None,
        help="Purchase date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--irr-target",
        type=float,
        default=settings.IRR_TARGET,
        help="IRR target percentage"
    )
    parser.add_argument(
        "--sales-team-id",
        type=int,
        default=None,
        help="Sales team ID"
    )
    
    args = parser.parse_args()
    
    # Create run context
    context = RunContext.create(
        sales_team_id=args.sales_team_id,
        created_by_id=None,
        pdate=args.pdate,
        irr_target=args.irr_target
    )
    context.input_file_path = args.folder
    context.output_dir = f"{args.folder}/output"
    
    # Execute pipeline
    try:
        with PipelineExecutor(context) as executor:
            result = executor.execute(args.folder)
        
        print(f"Pipeline completed successfully!")
        print(f"Run ID: {result['run_id']}")
        print(f"Total Loans: {result['total_loans']}")
        print(f"Total Balance: ${result['total_balance']:,.2f}")
        print(f"Exceptions: {result['exceptions_count']}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Pipeline execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
