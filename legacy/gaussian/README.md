# Legacy Gaussian water optimization

This directory keeps the earlier Gaussian energy backend for historical use.
The primary runnable example uses [PySCF](../../README.md), whose setup does not
require Gaussian. This legacy implementation is not the default project entry.

## Setup and execution

Gaussian must be installed, licensed, and configured separately. From the
repository root, in your chosen Python environment:

```bash
python -m pip install -r legacy/gaussian/requirements.txt
jupyter lab legacy/gaussian/water_optimization.ipynb
```

Set `gaussian_command` in the notebook to the executable name or path, such as
`g09` or `g16`. The notebook uses B3LYP/6-31G* energies to optimize an equal-bond
water geometry, scaling the angle by 100 in the CMA-ES search.

Each candidate overwrites `energy.gjf` and `energy.log` in `gaussian_work/` under
the kernel's working directory. Run evaluations serially. Non-zero exit status,
timeouts, abnormal termination, or missing archive energies are rejected.
A missing executable stops the run so the environment can be corrected.

The [reference input](examples/water_reference.gjf) uses Gaussian's own
`Opt=(Tight,Z-Matrix)` optimizer. See [reference instructions](examples/README.md).

## Historical results

The original 2022 notebooks, before the variable scaling and failure-handling
updates, recorded:

| Calculation | Shared O–H / Å | H–O–H / ° |
| --- | ---: | ---: |
| Gaussian energy + CMA-ES | 0.96878134 | 103.64849749 |
| Earlier PySCF energy + CMA-ES | 0.96891999 | 103.85329792 |
| Recorded Gaussian `Opt=Tight` reference | 0.9687 | 103.6522 |

These are historical outputs from
[`dd400cc`](https://github.com/weida-feng/cmaes_optimizer/tree/dd400ccea1f3b6941d4a3f5a4134ece45e8937e4),
not results of a fresh Gaussian execution. The current machine has no Gaussian
executable; validation covers simulated logs and process failures. Differences
between backends can also reflect functional implementations, integration
schemes, and convergence settings.

For the current primary result, use the [PySCF validation record](../../docs/validation.md).
The [experiment notes](../../docs/experiment.md) explain the coordinate choices,
earlier surrogate-energy experiments, and their limitations.
