## GPUnit Test for `gatk.CalculateContamination`

### Summary
A single, happy-path GPUnit test was generated for the `gatk.CalculateContamination` module. The test exercises **tumor-only mode** using a required pileup summary table and asserts that the contamination output table is produced.

---

### Test File: `test.yml`

```yaml
name: "gatk.CalculateContamination basic tumor-only test"
module: gatk.CalculateContamination
params:
  tumor.pileup.input: /Users/liefeld/Desktop/gatk/tumor_pileup_summary.table
assertions:
  files:
    - contamination.table
```

---

### Design Decisions

| Decision | Rationale |
|---|---|
| **Tumor-only mode** | Covers the most fundamental required-parameter-only use case; matched-normal is optional |
| **`tumor.pileup.input`** | The single required input — maps to the provided `tumor_pileup_summary.table` file |
| **`matched.normal.pileup.input` omitted** | Optional — only needed for matched-normal mode; not included per "required parameters only" rule |
| **Output assertion: `contamination.table`** | GATK CalculateContamination writes `contamination.table` by default; checking for its existence confirms successful execution |
| **No `diffCmd`** | No expected output file is available for bit-for-bit diff; existence check is sufficient for a basic smoke test |
| **`--arguments_file` omitted** | Optional parameter per module spec; not needed for this basic test |

---

### Notes
- The wrapper script supports **both tumor-only and matched-normal mode** via the optional `matched.normal.pileup.input` parameter.
- Optional tool arguments, Common arguments, and Advanced arguments are **not** surfaced as GenePattern parameters; they can be passed in via the optional `--arguments_file` parameter.
