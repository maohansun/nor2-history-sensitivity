# Data dictionary notes

`FIELD_DICTIONARY.csv` is the output-column data dictionary carried over from the verified scientific build; its `source_sha256` field identifies the exact locked source table from which an exported table was parsed and reserialized. The separate SHA256SUMS list identifies the current published bytes.

The row-count and uniqueness checks are in `DATA_TABLE_INDEX.csv`. Identifiers such as `src`, `context`, `mos`, `role`, `edge`, `condition` are group/record keys, **not** independently randomized samples. Some S11 fields are intentionally empty because those time crossings are not requested for a given waveform protocol; do not interpolate or replace empty values with zero.

`P0` = source-condition first-order reuse; `P_IS1` = target-condition first-order; `P_IS2` = target-condition diagonal second-order; `P_R2` = role-group second-order; these are not interchangeable fitted BTI models. Units and normalization must be read from the file and manuscript-specific method, not inferred from column suffixes alone.
