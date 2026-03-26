
import subprocess
import sys
import os
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="GenePattern wrapper for GATK CalculateContamination. "
                    "Calculates the fraction of reads from cross-sample contamination "
                    "in a tumor sample. Supports both tumor-only and matched normal modes."
    )

    # Required parameters
    parser.add_argument(
        "--input_tumor_pileup",
        required=True,
        help="Tumor sample pileup summary table (.table) produced by GATK GetPileupSummaries."
    )
    parser.add_argument(
        "--output_contamination_table",
        required=True,
        help="Name of the output contamination table file (.table)."
    )

    # Optional parameters
    parser.add_argument(
        "--input_normal_pileup",
        required=False,
        default=None,
        help="(Optional) Matched normal sample pileup summary table (.table) from GetPileupSummaries. "
             "When provided, enables matched normal mode for more accurate contamination estimation."
    )
    parser.add_argument(
        "--output_tumor_segmentation",
        required=False,
        default=None,
        help="(Optional) Output filename for the tumor segmentation table (.table). "
             "Highly recommended for aneuploid tumors."
    )
    parser.add_argument(
        "--arguments_file",
        required=False,
        default=None,
        help="(Optional) File of GATK arguments. Each argument should be on a separate line. "
             "Used to pass additional optional, common, or advanced GATK arguments not exposed "
             "as GenePattern parameters."
    )

    return parser.parse_args()


def build_gatk_command(args):
    """Construct the GATK CalculateContamination command."""
    cmd = [
        "gatk", "CalculateContamination",
        "-I", args.input_tumor_pileup,
        "-O", args.output_contamination_table,
    ]

    # Matched normal mode (optional)
    if args.input_normal_pileup:
        cmd.extend(["-matched", args.input_normal_pileup])

    # Tumor segmentation output (optional)
    if args.output_tumor_segmentation:
        cmd.extend(["--tumor-segmentation", args.output_tumor_segmentation])

    # Additional arguments file (optional)
    if args.arguments_file:
        cmd.extend(["--arguments_file", args.arguments_file])

    return cmd


def run_command(cmd):
    """Execute a shell command and handle errors."""
    print("Running command:\n  " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"ERROR: GATK CalculateContamination exited with code {result.returncode}.", file=sys.stderr)
        sys.exit(result.returncode)


def main():
    args = parse_arguments()

    # Validate input files exist
    if not os.path.isfile(args.input_tumor_pileup):
        print(f"ERROR: Tumor pileup file not found: {args.input_tumor_pileup}", file=sys.stderr)
        sys.exit(1)

    if args.input_normal_pileup and not os.path.isfile(args.input_normal_pileup):
        print(f"ERROR: Normal pileup file not found: {args.input_normal_pileup}", file=sys.stderr)
        sys.exit(1)

    if args.arguments_file and not os.path.isfile(args.arguments_file):
        print(f"ERROR: Arguments file not found: {args.arguments_file}", file=sys.stderr)
        sys.exit(1)

    # Log operating mode
    if args.input_normal_pileup:
        print("Mode: Matched Normal Mode (tumor + normal pileup provided)", flush=True)
    else:
        print("Mode: Tumor-Only Mode (no matched normal provided)", flush=True)

    cmd = build_gatk_command(args)
    run_command(cmd)

    print("CalculateContamination completed successfully.", flush=True)
    print(f"  Contamination table: {args.output_contamination_table}", flush=True)
    if args.output_tumor_segmentation:
        print(f"  Tumor segmentation:  {args.output_tumor_segmentation}", flush=True)


if __name__ == "__main__":
    main()
