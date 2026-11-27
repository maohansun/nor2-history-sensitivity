
# Characterization-History Dependence of Threshold-Voltage Sensitivity in NOR2 Gate Chains

**Open Research Data and Reproducibility Materials, 2026**

Maohan Sun, Jinghua Sun, and Tianrun Wang

Maohan Sun — First and Corresponding Author

[Zenodo](https://doi.org/10.5281/zenodo.23911543) |
[IEEE DataPort](https://doi.org/10.21227/k9j4-p590) |
[Python Source Code](SCI2_Characterization_History_Dataset_v1/scripts/) |
[Research Data](SCI2_Characterization_History_Dataset_v1/data/) |
[Reproduction Guide](SCI2_Characterization_History_Dataset_v1/README.md)

## Research Overview

This study investigates the dependence of threshold-voltage sensitivity on characterization history in CMOS NOR2 and NAND2 gate chains.

Transistor-level SPICE simulations using 45 nm and 65 nm predictive technology models examine how first-switching and periodic operating conditions affect delay sensitivity and prediction accuracy.

## Key Findings

- Threshold-voltage sensitivity depends on the characterization history of the circuit.
- Sensitivity coefficients extracted under one operating history may not transfer accurately to another.
- Target-condition recharacterization reduced the mean absolute prediction error by 40.1% against 480 full-SPICE reference delay increments.

## Research Methodology

| Parameter | Specification |
|---|---|
| Technology models | PTM 45 nm and 65 nm |
| Circuit structures | NOR2 and NAND2 gate chains |
| Chain length | Seven stages |
| Circuit configurations | 96 |
| Full-SPICE reference records | 480 |
| Characterization conditions | First-switching and periodic |
| Analysis and visualization | Python |

## Repository Contents

| Resource | Contents |
|---|---|
| [Python Scripts](SCI2_Characterization_History_Dataset_v1/scripts/) | Original numerical analysis and plotting programs |
| [Research Data](SCI2_Characterization_History_Dataset_v1/data/) | Supplementary tables, sensitivity coefficients, delay predictions, and waveform data |
| [Reproduction Sources](SCI2_Characterization_History_Dataset_v1/reproduction_sources/) | Original circuit topology netlists and reproduction resources |
| [Reference Figures](SCI2_Characterization_History_Dataset_v1/figures/) | Research figures |
| [Documentation](SCI2_Characterization_History_Dataset_v1/docs/) | Supporting technical documentation |
| [Reproduction Guide](SCI2_Characterization_History_Dataset_v1/README.md) | Original dataset organization and execution instructions |
| [SHA-256 Manifest](SCI2_Characterization_History_Dataset_v1/SHA256SUMS.txt) | Original file-integrity records |

## Open Research Archive

The research data and reproducibility materials were publicly released on November 3, 2026.

- Version: 1.0.0
- Archive: SCI2_DataPort_UPLOAD.zip
- Archive size: 11.4 MB
- Original dataset files: 95
- Supplementary CSV tables: 19
- Circuit topology netlists: 96

[Download Original Research Archive](https://zenodo.org/records/23911543/files/SCI2_DataPort_UPLOAD.zip?download=1)

Original ZIP MD5:

`ec5c80c438628e2b6a30f5fae374f787`

## Reproducibility

The original research archive is preserved in this repository with its directory structure and integrity manifest.

Follow the original [reproduction guide](SCI2_Characterization_History_Dataset_v1/README.md) for software requirements, data processing, figure generation, and simulation procedures.

Third-party PTM model libraries must be obtained separately to reproduce transistor-level simulations.

The DOI-linked Zenodo archive remains the authoritative reference for the released dataset.

## Scope and Limitations

The threshold-voltage perturbations represent controlled numerical scenarios rather than silicon-calibrated BTI lifetime predictions.

The designated evaluation dataset is non-blind. The reported findings are based on transistor-level simulations.

## Related Research

- [Path-State-Dependent Aging-Direction Sensitivity in CMOS NOR2 Chains — IEEE Access, 2026](https://github.com/maohansun/nor2-aging-direction)
- [GF180MCU Ring-Oscillator Test Chip](https://github.com/maohansun/-tt-gf180-ro-aging)

## Citation

Sun, M., Sun, J., and Wang, T. (2026).
Characterization-History Dependence of Threshold-Voltage Sensitivity in NOR2 Gate Chains.
Research data and reproducibility materials, Version 1.0.0.

DOI: 10.5281/zenodo.23911543
