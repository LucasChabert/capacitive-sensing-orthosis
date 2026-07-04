<div align="center">

# 🦾 3D-Printed Capacitive Sensors for Exoskeleton Orthoses

### Pressure and position sensing through capacitive measurement in multi-material 3D printing

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![C++ / PlatformIO](https://img.shields.io/badge/firmware-PlatformIO%20%7C%20ESP32-ff7f00.svg)](https://platformio.org/)
[![CAD Fusion 360](https://img.shields.io/badge/CAD-Fusion%20360-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Inria](https://img.shields.io/badge/Inria%2FIRISA-Rainbow%20team-red.svg)](https://team.inria.fr/rainbow/)

*Undergraduate research internship (L1 MPCI) · Inria / IRISA, Rainbow team (Rennes, France) · June–July 2026*

[🇫🇷 Français](README.md) · **🇬🇧 English**

<img src="figures/analysis/C1_C2_vs_d.png" width="620" alt="Hysteresis of capacitances C1 and C2 versus gap d"/>

*The central finding: for the same gap d, the measured capacitance differs between
compression and release of the foam dielectric — a hysteresis interpreted as a
permittivity that depends on the deformation history.*

</div>

---

## 🎯 Context

Upper-limb assistive exoskeletons estimate the user's motion intent through
**3-axis force sensors** — accurate, but heavy, bulky and expensive. This internship
explores an alternative: **embedding capacitive sensors directly into the orthoses**
(the physical human–machine interfaces), fabricated in a single step by
**multi-material 3D printing** — a conductive filament (EEL 90A) for the electrodes,
a soft elastomer (Filaflex 70A) for the deformable zones, and TPU 95A for the frame.

> 🔬 **Question** — Can printed capacitive cells measure pressure (and its location)
> reliably enough to instrument an orthosis?

The work builds on the Rainbow team's research on upper-limb exoskeletons and printed
capacitive sensing [1–4].

## ⚙️ Measurement principle

A parallel-plate capacitor follows `C = εS/d`. To eliminate the poorly known `ε` and
`S`, two cells are measured **differentially**, separated by a known offset `Δd`:

```
d = Δd / (C1/C2 − 1)
```

With stacked electrodes (V3), the two cells see different dielectrics, and the model
is extended with `α = ε1/ε2`, estimated from a rest-state calibration. Measurement
chain: **FDC1004** capacitance-to-digital chip (with active SHLD shielding) →
**M5Stack Core (ESP32)** programmed in C++ with PlatformIO → Teleplot visualization
(±0.001 pF resolution).

## 🔁 Iterative design

| Version | Design | Lesson learned |
|---|---|---|
| **V1** — side-by-side cells | proof of concept, gyroid foam | too sensitive to finger position |
| **V2** — shielding | grounded shield + active SHLD guard | environmental disturbances strongly reduced |
| **V3** — stacked electrodes | both cells share the same deformation | requires the two-permittivity model (α) |
| **V4** — position sensor | complementary triangular electrodes | position from `x = L·C1/(C1+C2)`, bounded ratio → affine calibration |
| **V5** — pillar / soluble support | mechanical variants | outlook |

## 📊 Key results

- **Dielectric hysteresis** evidenced and interpreted: the foam's effective
  permittivity is a **state variable** `ε(H)` depending on the compression history —
  the bijective geometric model `C = εS/d` no longer suffices.
- **Model identification** via least squares (`scipy.optimize.least_squares`): the
  form `C(d) = A/(d+B) + C_b` fits the data, with each parameter physically
  interpretable (contact offset, fringe capacitance, εS).
- The quantity `1/C2 − 1/C1`, predicted constant, is actually **linear in d
  (R² ≈ 0.95)** and less hysteretic: the "rigid" support's compression carries the
  signal → pointing towards a **solid-dielectric sensor**.
- **Single-cell sensor**: one curve `C(d)` fits both loading and unloading
  (R² = 0.91), with hysteresis below measurement uncertainty.
- **Position sensor**: the experimental ratio stays within [0.4, 0.6] instead of
  [0, 1], explained by a parasitic-capacitance model and corrected by an affine
  calibration.

## 📁 Repository layout

```
├── docs/report.pdf        ← full internship report (in French)
├── firmware/              ← ESP32 embedded code (PlatformIO)
│   ├── src/               ← main.cpp + FDC1004 driver (ProtoCentral, MIT)
│   └── variants/          ← simple pressure / position / affine-calibration versions
├── analysis/              ← Python scripts: least-squares fits, hysteresis,
│                            gap reconstruction, uncertainty analysis
├── data/                  ← test-bench measurements (CSV/XLSX) + Teleplot logs
├── cad/                   ← Fusion 360 models + STL/3MF of the 5 prototype versions
└── figures/               ← CAD renders and result figures (reproducible)
```

## 🚀 Quickstart

**Analysis (Python)**:
```bash
pip install -r requirements.txt
cd analysis
python ajustement_C1_modeles_bord_sans_offset_en_d.py   # C1 fits with/without fringe effects
python mesure_capacites_inverse_et_rapport.py           # linearity of 1/C2 − 1/C1
python Retrouver_d.py                                   # gap reconstruction
```
Figures are written to `figures/analysis/`.

**Firmware (ESP32 / M5Stack)**: open `firmware/` with [PlatformIO](https://platformio.org/)
(`pio run -t upload`). See `firmware/variants/README.md` for the other versions.

## 👤 Author

**Lucas Chabert** — 1st-year undergraduate (L1 MPCI), Aix-Marseille Université.
Internship supervised by **Maxime Manzano**, Inria/IRISA, Rainbow team (Rennes).

## 📚 References

1. Aguilar-Segovia, J. E. (2026). *Additive Manufacturing of Deformable Sensing Devices for Human–Machine Interaction…* PhD thesis, INSA Rennes. [HAL](https://theses.hal.science/tel-05587063v1)
2. Aguilar-Segovia et al. (2024). *Multi-material torque sensor embedding one-shot 3D-printed deformable capacitive structures.* IEEE Sensors Letters 8(9). [HAL](https://hal.science/hal-04699911v1)
3. Manzano et al. (2025). *Enhancing the Usability of Upper-Limb Assistive Robots with a Variable Admittance Controller.* IFRATH 2025. [HAL](https://hal.science/hal-05356901)
4. Manzano et al. (2024). *Force-Triggered Control Design for User Intent-Driven Assistive Upper-Limb Robots.* IEEE/RSJ IROS 2024. [HAL](https://hal.science/hal-04774539v1)

---

<div align="center">

**📄 [Full report (PDF)](docs/report.pdf)** · **🏗️ Companion project: [Taipei 101 TMD](https://github.com/LucasChabert/taipei101-tmd)**

</div>
