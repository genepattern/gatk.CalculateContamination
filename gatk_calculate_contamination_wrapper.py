#!/usr/bin/env python3
"""
Wrapper script for gatk.CalculateContamination GenePattern module.

Calculates the fraction of reads coming from cross-sample contamination,
given pileup summary data produced by GATK GetPileupSummaries.

Supports two modes:
  - Tumor-only mode: only --tumor.pileup.input is provided.
  - Matched normal mode: both --tumor.pileup.input and --matched.normal.input
    are provided. This is the preferred mode when a paired normal is available.

Optional tool arguments not exposed as GenePattern parameters can be passed
via an --arguments.file (a plain-text file with one GATK argument per line).

Usage:
  python gatk_calculate_contamination_wrapper.py
      --tumor.pileup.input  <tumor_pileup.table>
      --output              <contamination.table>
      [--matched.normal.input   <normal_pileup.table>]
      [--tumor.segmentation.output <segments.table>]
      [--arguments.file     <extra_args.txt>]
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging():
    """Configure root logger to write INFO+ messages to stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
    )


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_arguments():
    """Parse command-line arguments following GenePattern dot-name conventions."""
    parser = argparse.ArgumentParser(
        description=(
            "GenePattern wrapper for GATK CalculateContamination. "
            "Estimates cross-sample contamination from pileup summary tables."
        )
    )

    # ------------------------------------------------------------------
    # Required parameters
    # ------------------------------------------------------------------
    parser.add_argument(
        "--tumor.pileup.input",
        dest="tumor_pileup_input",
        required=True,
        metavar="FILE",
        help=(
            "Tumor pileup summary table (.table) produced by GATK "
            "GetPileupSummaries. Tab-delimited file with columns: contig, "
            "position, ref_count, alt_count, allele_frequency, "
            "other_alt_count. Required. Maps to GATK flag: -I / --input."
        ),
    )

    parser.add_argument(
        "--output",
        dest="output",
        required=True,
        metavar="FILE",
        help=(
            "Name of the output contamination table file. The output is a "
            "tab-delimited .table file with columns: sample, contamination, "
            "error. Consumed by FilterMutectCalls via --contamination-table. "
            "Maps to GATK flag: -O / --output."
        ),
    )

    # ------------------------------------------------------------------
    # Optional parameters
    # ------------------------------------------------------------------
    parser.add_argument(
        "--matched.normal.input",
        dest="matched_normal_input",
        default=None,
        metavar="FILE",
        help=(
            "Matched normal pileup summary table (.table) from "
            "GetPileupSummaries run on the paired normal sample. When "
            "provided, enables matched-normal mode for more accurate "
            "contamination estimation. Omit for tumor-only mode. "
            "Maps to GATK flag: -matched / --matched-normal-input."
        ),
    )

    parser.add_argument(
        "--tumor.segmentation.output",
        dest="tumor_segmentation_output",
        default=None,
        metavar="FILE",
        help=(
            "Output filename for the tumor segmentation table. Contains "
            "minor allele fractions per genomic segment (columns: contig, "
            "start, end, minor_allele_fraction). Consumed by "
            "FilterMutectCalls via --tumor-segmentation. Recommended for "
            "aneuploid tumors. Maps to GATK flag: --tumor-segmentation."
        ),
    )

    parser.add_argument(
        "--arguments.file",
        dest="arguments_file",
        default=None,
        metavar="FILE",
        help=(
            "Plain-text file containing additional GATK arguments, one "
            "argument per line. Use this to pass optional, common, or "
            "advanced GATK options not exposed as GenePattern parameters "
            "(e.g. --verbosity INFO, --TMP_DIR /tmp, --QUIET, "
            "--gcs-max-retries 30). Maps to GATK flag: --arguments_file."
        ),
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def validate_inputs(args):
    """
    Validate input files exist and are readable before invoking GATK.

    Returns True if all checks pass, False otherwise (with logged errors).
    """
    valid = True

    # Required: tumor pileup input
    tumor_path = Path(args.tumor_pileup_input)
    if not tumor_path.is_file():
        logging.error(
            "Tumor pileup input file not found: %s", args.tumor_pileup_input
        )
        valid = False
    elif not os.access(str(tumor_path), os.R_OK):
        logging.error(
            "Tumor pileup input file is not readable: %s",
            args.tumor_pileup_input,
        )
        valid = False
    else:
        logging.info("Tumor pileup input: %s", args.tumor_pileup_input)

    # Optional: matched normal input
    if args.matched_normal_input is not None:
        normal_path = Path(args.matched_normal_input)
        if not normal_path.is_file():
            logging.error(
                "Matched normal input file not found: %s",
                args.matched_normal_input,
            )
            valid = False
        elif not os.access(str(normal_path), os.R_OK):
            logging.error(
                "Matched normal input file is not readable: %s",
                args.matched_normal_input,
            )
            valid = False
        else:
            logging.info(
                "Matched normal input: %s", args.matched_normal_input
            )

    # Optional: arguments file
    if args.arguments_file is not None:
        args_path = Path(args.arguments_file)
        if not args_path.is_file():
            logging.error(
                "Arguments file not found: %s", args.arguments_file
            )
            valid = False
        elif not os.access(str(args_path), os.R_OK):
            logging.error(
                "Arguments file is not readable: %s", args.arguments_file
            )
            valid = False
        else:
            logging.info("Arguments file: %s", args.arguments_file)

    # Log run mode for clarity
    if valid:
        if args.matched_normal_input:
            logging.info(
                "Run mode: matched-normal (tumor + normal pileup provided)"
            )
        else:
            logging.info(
                "Run mode: tumor-only (no matched normal pileup provided)"
            )

    return valid


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

def build_command(args):
    """
    Build the GATK CalculateContamination command list.

    Returns a list of strings suitable for subprocess.run().
    """
    cmd = ["gatk", "CalculateContamination"]

    # Required inputs / outputs
    cmd.extend(["-I", args.tumor_pileup_input])
    cmd.extend(["-O", args.output])

    # Optional: matched normal pileup (enables matched-normal mode)
    if args.matched_normal_input:
        cmd.extend(["-matched", args.matched_normal_input])

    # Optional: tumor segmentation output
    if args.tumor_segmentation_output:
        cmd.extend(["--tumor-segmentation", args.tumor_segmentation_output])

    # Optional: extra arguments file
    if args.arguments_file:
        cmd.extend(["--arguments_file", args.arguments_file])

    return cmd


def run_tool(args):
    """
    Execute GATK CalculateContamination as a subprocess.

    Streams stdout/stderr in real time and re-raises CalledProcessError
    on non-zero exit so that the caller can handle the exit code.
    """
    cmd = build_command(args)
    logging.info("Executing command: %s", " ".join(cmd))

    # Stream stdout and stderr directly to the parent process so that GATK's
    # progress messages appear in the GenePattern log in real time.
    try:
        proc = subprocess.run(
            cmd,
            check=True,
            stdout=None,   # inherit stdout -> printed to console
            stderr=None,   # inherit stderr -> printed to console
        )
    except subprocess.CalledProcessError as exc:
        # Re-raise so main() can log and set the correct exit code.
        raise exc

    return proc.returncode


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------

def validate_outputs(args):
    """
    Verify that expected output files were created after GATK completes.

    Logs a warning for each expected output that is missing; does not fail
    the wrapper (GATK itself already returned 0).
    """
    output_path = Path(args.output)
    if output_path.is_file():
        logging.info(
            "Output contamination table created: %s", args.output
        )
    else:
        logging.warning(
            "Expected output contamination table was not found: %s",
            args.output,
        )

    if args.tumor_segmentation_output:
        seg_path = Path(args.tumor_segmentation_output)
        if seg_path.is_file():
            logging.info(
                "Tumor segmentation output created: %s",
                args.tumor_segmentation_output,
            )
        else:
            logging.warning(
                "Expected tumor segmentation output was not found: %s",
                args.tumor_segmentation_output,
            )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point for the GenePattern wrapper."""
    setup_logging()

    logging.info(
        "gatk.CalculateContamination GenePattern wrapper starting"
    )

    # Parse command-line arguments
    args = parse_arguments()

    # Validate inputs before running the tool
    if not validate_inputs(args):
        logging.error(
            "Input validation failed. Please check the error messages above "
            "and ensure all required files exist and are readable."
        )
        sys.exit(1)

    # Run GATK CalculateContamination
    try:
        return_code = run_tool(args)
    except subprocess.CalledProcessError as exc:
        logging.error(
            "GATK CalculateContamination failed with exit code %d.",
            exc.returncode,
        )
        sys.exit(exc.returncode if exc.returncode != 0 else 1)
    except FileNotFoundError:
        logging.error(
            "Could not find 'gatk' executable. Ensure that GATK4 is "
            "installed and available on PATH."
        )
        sys.exit(2)
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Unexpected error during tool execution: %s", exc)
        sys.exit(1)

    # Validate outputs were produced
    validate_outputs(args)

    logging.info(
        "gatk.CalculateContamination GenePattern wrapper finished "
        "successfully."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
