# Legacy Gaussian reference calculation

`water_reference.gjf` uses Gaussian's own `Opt=(Tight,Z-Matrix)` procedure at
B3LYP/6-31G*. Both O–H bonds share the variable `R`. The explicit `Z-Matrix`
option optimizes these shared variables, preserving the equal-bond constraint.
See the [Gaussian Opt documentation](https://gaussian.com/opt/).

From the repository root, with Gaussian installed and configured:

```bash
mkdir -p outputs
g09 < legacy/gaussian/examples/water_reference.gjf > outputs/water_reference.log
```

Replace `g09` with the configured executable, for example `g16`, and adjust the
CPU and memory directives for your machine. Confirm a completed optimization
and normal termination before comparing the final geometry. This input contains
no precomputed result and has not been run in the current validation environment.

The [legacy notebook](../water_optimization.ipynb) uses energy-only CMA-ES;
this reference uses Gaussian's native geometry optimizer. For the main project
entry, use the [PySCF instructions](../../../README.md).
