# CMAES Water Optimization

[中文说明](README.zh-CN.md) · [实验原理与结果](docs/experiment.md)

A small computational chemistry experiment using **CMA-ES** to optimize a
single H₂O molecule, with **PySCF** supplying **B3LYP/6-31G\*** single-point
energies. The optimizer uses energies without requesting analytical gradients.
Both O–H bonds share one length, so the current search has two variables:
the bond length in Å and the H–O–H angle in degrees.

**PySCF is the primary runnable version.** The earlier Gaussian implementation
and its reference input are kept separately in [legacy/gaussian/](legacy/gaussian/README.md).

## Quick start

Use Python 3.10 or newer with a platform supported by
[PySCF](https://pyscf.org/user/install.html).

```bash
git clone https://github.com/weida-feng/CMAES-Water-Optimization.git
cd CMAES-Water-Optimization
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab notebooks/water_optimization_pyscf.ipynb
```

Select this environment's Python kernel, then **Restart Kernel and Run All Cells**.
The notebook checks the initial energy before starting the search. A full run
performs many DFT calculations and can take a few minutes.

For execution without the browser interface:

```bash
mkdir -p outputs
jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=1800 \
  --output-dir=outputs notebooks/water_optimization_pyscf.ipynb
```

If an older manual PySCF installation overrides this environment, inspect
`pyscf.__file__` and remove its `PYTHONPATH` override before restarting the kernel.

## How the search works

1. CMA-ES samples candidate vectors `[bond_length, angle / 100]`.
2. The objective restores the angle to degrees and builds a water Z-matrix
   with equal O–H bond lengths.
3. PySCF evaluates each geometry's energy. Non-converged or non-finite SCF
   results are rejected with a high penalty.
4. CMA-ES ranks the candidates by energy and updates its sampling distribution
   until a stopping condition is reached.

Scaling the angle makes the variables comparable in magnitude. The default
search bounds are 0.5–2.0 Å and 30–170°, with a budget of 80 iterations.
Calculation settings, initial geometry, seed, memory, and threads are grouped
near the start of the notebook.

## Validated PySCF result

A complete run with the default settings produced:

| Shared O–H / Å | H–O–H / ° | Energy / Hartree | Evaluations | Stop condition |
| ---: | ---: | ---: | ---: | --- |
| 0.96866169 | 103.86624878 | -76.407023582773 | 306 | `tolfun = 1e-8` |

The [validation record](docs/validation.md) specifies the environment and check
coverage. These values are a recorded run, rather than a guarantee of identical
results across software versions. Inspect the printed stopping conditions:
`maxiter` indicates that the iteration budget was exhausted.

## Why internal coordinates?

The motivating experiments also considered an MLP surrogate for DFT energies:
collect reference energies, fit a model, then minimize its predicted energy
with CMA-ES. The coordinate representation matters:

| Representation | Variables | Meaning |
| --- | ---: | --- |
| Cartesian, oxygen fixed at the origin | 6 | Two hydrogen positions; rotations change the inputs |
| Internal | 3 | Two O–H lengths and one H–O–H angle |
| Current equal-bond PySCF example | 2 | One shared length and one angle |

The historical surrogate experiments recorded the following results:

| Surrogate input | Test R² | O–H lengths / Å | H–O–H / ° |
| --- | ---: | --- | ---: |
| Cartesian coordinates | 0.7523 | 0.8779, 1.0249 | 78.25 |
| Internal coordinates | 0.9725 | 0.9541, 0.9738 | 105.70 |
| DFT geometry reference | — | 0.9687, 0.9687 | 103.65 |

The internal-coordinate experiment produced a closer equilibrium geometry.
The experiments also changed network size and regularization, so this does not
isolate the effect of coordinates alone. A high energy-fit R² also does not
establish that the predicted minimum or the whole potential energy surface is
accurate.

[docs/experiment.md](docs/experiment.md) contains the full standalone account:
data generation, coordinate conversion, MLP settings, geometry comparisons,
the 80–130° relaxed angle scan, numerical results, and limitations. The current
notebook calls PySCF directly; the historical MLP training workflow and training
dataset are documented, but are not included as executable training artifacts.

## Repository layout

```text
notebooks/
  water_optimization_pyscf.ipynb   # Primary runnable example
docs/
  experiment.md                   # Method, historical experiments, and conclusions
  data/relaxed_scan.csv            # Historical MLP relaxed-scan results
  assets/relaxed_scan.svg          # Energy and bond-length scan figure
  validation.md                   # Current PySCF execution record
legacy/gaussian/
  README.md
  requirements.txt
  water_optimization.ipynb         # Earlier Gaussian backend
  examples/                       # Gaussian reference input and instructions
tests/
  test_notebooks.py               # Backend failure-handling checks
requirements.txt                  # PySCF + CMA-ES + Jupyter
README.zh-CN.md
```

## Checks and scope

```bash
python -m unittest discover -s tests -v
```

The checks cover rejected SCF calculations, spin/method settings, and legacy
Gaussian parsing and process failures. They do not run a full optimization or
require Gaussian. PySCF-specific checks skip if PySCF is absent.

This is an exploratory example for one small molecule with an equal-bond
constraint. Its bounds and results do not establish performance for larger
systems. Coordinate design, symmetry, energy-model reliability, and SCF settings
remain important when extending the experiment.

## References

- [pycma](https://github.com/CMA-ES/pycma): CMA-ES implementation.
- [PySCF molecular structure](https://pyscf.org/user/gto.html): geometry, units, and spin.
- [PySCF DFT guide](https://pyscf.org/user/dft.html): functionals and numerical grids.
