## gatk.CalculateContamination Wrapper - Generation Report

### Artifact
- **File:** `gatk_calculate_contamination_wrapper.py`
- **Language:** Python 3
- **Tool:** GATK4 CalculateContamination
- **Status:** SUCCESS

---

### Parameter Mapping

| GenePattern Parameter         | Required | GATK CLI Flag          | Notes                                      |
|-------------------------------|----------|------------------------|--------------------------------------------|
| `--tumor.pileup.input`        | Yes      | `-I`                   | Tumor pileup table from GetPileupSummaries |
| `--output`                    | Yes      | `-O`                   | Contamination output table                 |
| `--matched.normal.input`      | No       | `-matched`             | Enables matched-normal mode when provided  |
| `--tumor.segmentation.output` | No       | `--tumor-segmentation` | Segmentation table for aneuploid tumors    |
| `--arguments.file`            | No       | `--arguments_file`     | Pass-through for extra GATK arguments      |

---

### Key Design Decisions

1. **Dual mode support** - Wrapper automatically detects and logs whether it is running in *tumor-only* mode (no matched normal) or *matched-normal* mode (normal pileup provided), making it easy to audit in GenePattern logs.

2. **Arguments file pass-through** - The `--arguments.file` parameter forwards a plain-text file of extra GATK flags directly to `--arguments_file`, allowing users to supply optional, common, and advanced GATK parameters without needing new GenePattern parameters.

3. **Real-time streaming** - GATK stdout/stderr are streamed directly (not captured) so that GATK progress messages appear live in the GenePattern job log.

4. **Comprehensive input validation** - All input files are checked for existence and read permission before GATK is invoked, producing clear error messages.

5. **Output validation** - After GATK exits 0, the wrapper confirms expected output files were created and logs warnings for any missing outputs.

6. **Precise exit code propagation** - `CalledProcessError.returncode` is forwarded to `sys.exit()` so GenePattern accurately reflects the GATK exit status.

7. **ASCII-only strings** - All log messages and comments use plain ASCII to avoid `UnicodeEncodeError` in restricted container locales.

8. **GenePattern dot-naming** - All `argparse` flags use dot-separated names matching the manifest (`--tumor.pileup.input`, `--matched.normal.input`, etc.) with underscore `dest` aliases for Python attribute access.
