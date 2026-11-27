# Characterization-History Dependence of Threshold-Voltage Sensitivity in NOR2 Gate Chains: Simulation Data and Reproducibility Materials

## Dataset scope

This is the SCI2 research dataset supporting the manuscript of the same title, **not** the separate NOR2 aging-direction (SCI1) dataset. Scientific simulations were performed by the authors using ngspice/PTM workflows; the results are numerical simulations on 45/65 nm planar predictive device models. This is **not** a calibrated physical BTI lifetime dataset or a measured critical-path slack dataset.

The dataset consists of **19 canonical electronic supplementary CSV tables** (6,822 total rows across separate tables; the rows are not independent experimental units), source and processed numeric data for **six main and two supplementary scientific figures**, original 96 topology-only seven-stage SPICE decks, publication-figure vector PDFs, and the corresponding Python scientific rendering functions. The 19 CSVs contain the published numerical evidence from existing simulations; reproduction of all original ngspice runs is not promised by this package.

**The original frozen per-record scientific data have not been replaced by the figure data.** Numerical arrays are available separately as published canonical electronic tables, frozen plot inputs and derived figure-specific tables. Derived arrays may duplicate information from the canonical tables; never count their rows as additional independent simulations.

## Files and entrypoints

- `data/electronic/`: 19 canonical supplementary CSVs (S5–S11); see `docs/DATA_TABLE_INDEX.csv` and `docs/FIELD_DICTIONARY.csv`.
- `data/figure_inputs/`: frozen plots' numerical source tables; `fig6/node_waveforms/FIG7A_NODE_WAVEFORMS.csv` contains tabulated historic node waveforms from three configurations, **not** the entire native RAW archive.
- `data/figure_processed/`: derived figure-by-figure numeric tables, statistical replays, 480-record model closure, and Fig. 6 numeric rendering data.
- `data/supporting/`: 192 fully identified historical fresh delays and the 12-value M2 baseline binding; these are supporting tables beyond the 19 electronic supplement tables.
- `data/netlists/SCI2_96_topology_netlists_only.zip`: 96 seven-stage circuit-topology decks, without any third-party PTM or BSIM model library. Decks contain the historical `.include` paths from the VM and **are not directly executable on other computers** without adjusting model paths and obtaining the model card from its authorized source. The original deck bytes have been retained. Their inclusion is for topology/source-documentation purposes; figure plotting does not run SPICE.
- `data/node_samples/`: four historic sampled voltages at the C1 internal node, machine-specific runtime paths removed.
- `figures/`: eight frozen publication figure PDFs for reference. These are graphical outputs, not a replacement for the numeric sources.
- `scripts/`: the reviewed frozen scientific plotting implementation, with one purely local-path fallback adjusted for portability; see `docs/SOURCE_PROVENANCE.csv`.

## Scientific table groups

- **S5:** Temporal sensitivity and internal-node observation. Supplementary_Data_S5_D.csv (544 rows), Supplementary_Data_S5_E.csv (544 rows), Supplementary_Data_S5_F_C1_K1_K4.csv (4 rows).
- **S6:** Window-by-stimulus two-factor sensitivity contrasts. Supplementary_Data_S6_D.csv (56 rows), Supplementary_Data_S6_E.csv (96 rows).
- **S7:** Duty-cycle matched chain-transfer comparisons. Supplementary_Data_S7_D.csv (80 rows).
- **S8:** Original per-device sensitivity/curvature, 480 predictor records and amplitude tests. Supplementary_Data_S8_D.csv (4032 rows), Supplementary_Data_S8_E.csv (480 rows), Supplementary_Data_S8_F.csv (240 rows).
- **S9:** Uniform-shift first-order scenarios; path orders are model estimates only. Supplementary_Data_S9_A.csv (8 rows), Supplementary_Data_S9_B.csv (20 rows), Supplementary_Data_S9_C.csv (6 rows), Supplementary_Data_S9_D.csv (4 rows), Supplementary_Data_S9_F.csv (8 rows), Supplementary_Data_S9_per_config_edge.csv (384 rows).
- **S10:** Multi-device M2 and per-stage load M5 verification. Supplementary_Data_S10_A.csv (48 rows), Supplementary_Data_S10_B.csv (16 rows).
- **S11:** Cell-level slew/load grid and its individual delay readings. Supplementary_Data_S11_C.csv (36 rows), Supplementary_Data_S11_D.csv (216 rows).

## Reproduction and verification

The baseline **data integrity and key scientific-statistic verifier uses Python 3 standard library only**:

```
python scripts/verify_public_dataset.py
```

To rebuild the eight figures from the deposited numeric sources (Python 3.10+, NumPy, Matplotlib, Pillow, lxml; provide a compatible locally installed scientific font if font selection fails):

```
python -m pip install -r scripts/requirements_figures.txt
python scripts/rebuild_public_figures.py --output /path/to/a/new/output_folder
```

The original figure rebuild can be resource intensive at 1000 dpi and might vary with installed fonts; it has not been established as bit-identical in all operating systems. The original figure rebuild is *postprocessing only*, without ngspice, fitting, RAW extraction or network downloads. The reference figure source and original figure algorithms may depend on the exact Matplotlib/font version; a visually different but scientifically identical rendering is not evidence of changed measurements. `scripts/rebuild_public_figures.py` does not run simulations and refuses to overwrite its output path.

Check all SHA256 hashes in `SHA256SUMS.txt` before drawing scientific inferences; the SHA list is generated from the exact files in this proposed release. The dataset has no assigned DOI until formally released in IEEE DataPort.

## Important methodological limits

1. E1 is the first transition and IS the fourth crossing under specified 10 ns target-period waveforms. The original designated test set was executed alongside the 96 configurations and is reported as non-blind, despite earlier prediction commitments.
2. The synthetic threshold drift scenario uses controlled DELVTO perturbations. No silicon calibration, real 10-year lifetime, advanced FinFET generalization or measured industrial path timing is established by the released tables.
3. The first-order path accumulation in S9 is a hypothetical scaling argument, not a measured slack change or an independently run 12-stage aged path.
4. M2, M5 and S11 are distinct follow-up tests, with their own perturbation and observation definitions. M5 couples internal slew and per-stage load; S11 is a separate cell-level sweep. Do not pool their percentage differences as interchangeable effect sizes.
5. `data/figure_processed/` includes tabulated node wave records generated for plotting; this package does not include raw ngspice `.raw` files, all original full simulation logs, or the ECS 680+272 external waveforms.
6. PTM/BSIM model cards, third-party fonts and non-author-owned software are not redistributed. Fetch required third-party model documentation independently under its own licence.

## Source attribution / distribution

Authors: Maohan Sun; Jinghua Sun; Tianrun Wang. The author-designed simulation and analysis data in this archive are intended for a standalone SCI2 IEEE DataPort dataset. No independent SCI2 DOI has been assigned as of preparation of this upload package. IEEE DataPort publication and the licence chosen on the platform determine the eventual public release terms. Any reused third-party assets must be respected under their original licences; none of the PTM/BSIM model cards is bundled.

## Citation

Until IEEE DataPort assigns the SCI2 DOI, cite: Sun, M.; Sun, J.; Wang, T. *Characterization-History Dependence of Threshold-Voltage Sensitivity in NOR2 Gate Chains: Simulation Data and Reproducibility Materials*. Dataset version 1.0, IEEE DataPort (DOI pending, unpublished). **Replace this provisional citation only after actual publication.**
