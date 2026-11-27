
# Characterization-History Dependence of Threshold-Voltage Sensitivity in NOR2 Gate Chains

**Maohan Sun — First and Corresponding Author**

Open research data and reproducibility materials, November 2026.

[Zenodo](https://doi.org/10.5281/zenodo.23911543) |
[IEEE DataPort](https://doi.org/10.21227/k9j4-p590)

## Research Overview

This study investigates the dependence of threshold-voltage sensitivity on characterization history in CMOS NOR2 and NAND2 gate chains.

Transistor-level SPICE simulations using 45 nm and 65 nm predictive technology models are conducted to examine how first-switching and periodic operating conditions affect delay sensitivity and prediction accuracy.

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

## Open Data and Source Code

The research data and reproducibility materials were publicly released on November 3, 2026.

**Archive:** SCI2_DataPort_UPLOAD.zip

**Version:** 1.0.0

**Size:** 11.4 MB

[Download Original Research Archive](https://zenodo.org/records/23911543/files/SCI2_DataPort_UPLOAD.zip?download=1)

The archived materials include:

- 96 circuit topology netlists
- 19 supplementary CSV tables
- Python analysis and plotting scripts
- Transistor-level sensitivity records
- Delay prediction and numerical verification data
- Selected internal-node waveform data
- Input-slew and output-load characterization results
- Figure-source data and reference figures
- Reproducibility documentation and file-integrity information

### Archive Integrity

MD5 checksum:

`ec5c80c438628e2b6a30f5fae374f787`

## Reproducibility

Download and extract the original research archive, then follow its accompanying README and execution instructions.

Third-party PTM model libraries must be obtained separately to reproduce the transistor-level simulations.

The original DOI-linked archive is the authoritative source for the released research materials.

## Scope and Limitations

The threshold-voltage perturbations represent controlled numerical scenarios rather than silicon-calibrated BTI lifetime predictions.

The designated evaluation dataset is non-blind. The reported findings are based on transistor-level simulations.

## Related Research

**Path-State-Dependent Aging-Direction Sensitivity in CMOS NOR2 Chains**

IEEE Access, 2026.

[Published Article](https://doi.org/10.1109/ACCESS.2026.3753436) |
[GitHub Repository](https://github.com/maohansun/nor2-aging-direction)

**GF180MCU Ring-Oscillator Test Chip**

[Source Code and Technical Documentation](https://github.com/maohansun/-tt-gf180-ro-aging)

## Citation

Sun, M., Sun, J., and Wang, T. (2026).
Characterization-History Dependence of Threshold-Voltage Sensitivity in NOR2 Gate Chains.
Research data and reproducibility materials, Version 1.0.0.

DOI: 10.5281/zenodo.23911543
