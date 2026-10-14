"""Check backend failures without running the notebooks' optimization cells."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]


def load_setup(filename):
    namespace = {}
    notebook = json.loads((ROOT / filename).read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code" and "setup" in cell["metadata"].get("tags", []):
            exec(compile("".join(cell["source"]), filename, "exec"), namespace)
    return namespace


class GaussianTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_setup("legacy/gaussian/water_optimization.ipynb")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ns["gaussian_workdir"] = Path(self.temp.name)
        self.log = Path(self.temp.name) / "energy.log"

    def test_final_archive_energy_and_wrapped_fortran_exponent(self):
        self.log.write_text(
            "\\HF=-75.0\\RMSD=0.0\\\n"
            "\\HF=-7.6408\n 9D+01\\RMSD=0.0\\\n"
            "Normal termination of Gaussian 09\n",
            encoding="utf-8",
        )
        self.assertAlmostEqual(self.ns["energy_extract"](), -76.4089)

    def test_abnormal_or_missing_energy_is_rejected(self):
        for text in [
            "\\HF=-76.4\\RMSD=0\\\nError termination\n",
            "Normal termination of Gaussian 09\nError termination\n",
            "Normal termination of Gaussian 09\n",
        ]:
            with self.subTest(text=text):
                self.log.write_text(text, encoding="utf-8")
                with self.assertRaises((RuntimeError, ValueError)):
                    self.ns["energy_extract"]()

    def test_failed_or_timed_out_process_is_penalized(self):
        failures = [subprocess.CalledProcessError(1, "g09"), subprocess.TimeoutExpired("g09", 120)]
        for failure in failures:
            with self.subTest(failure=failure):
                with patch.object(self.ns["subprocess"], "run", side_effect=failure) as run:
                    with self.assertWarns(RuntimeWarning):
                        value = self.ns["energy"]([1.0, 1.04])
                    self.assertEqual(value, self.ns["penalty"])
                    self.assertTrue(run.call_args.kwargs["check"])
        input_text = (Path(self.temp.name) / "energy.gjf").read_text(encoding="utf-8")
        self.assertIn("\nH 1 1.0 2 104.0\n", input_text)

    def test_missing_executable_is_not_hidden_as_a_candidate_failure(self):
        with patch.object(self.ns["subprocess"], "run", side_effect=FileNotFoundError("g09")):
            with self.assertRaises(FileNotFoundError):
                self.ns["energy"]([1.0, 1.04])


@unittest.skipUnless(importlib.util.find_spec("pyscf"), "PySCF is not installed")
class PySCFTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_setup("notebooks/water_optimization_pyscf.ipynb")
        self.scf = MagicMock()
        self.scf.converged = True
        self.scf.kernel.return_value = -76.4

    def test_nonconverged_nonfinite_and_failed_scf_are_penalized(self):
        for failure in ["nonconverged", "nan", "numerical"]:
            with self.subTest(failure=failure):
                self.scf.converged = failure != "nonconverged"
                self.scf.kernel.return_value = float("nan") if failure == "nan" else -76.4
                self.scf.kernel.side_effect = RuntimeError("SCF failed") if failure == "numerical" else None
                with patch.object(self.ns["gto"], "M"), patch.object(self.ns["dft"], "RKS", return_value=self.scf):
                    with self.assertWarns(RuntimeWarning):
                        value = self.ns["energy"]([1.0, 1.04])
                    self.assertEqual(value, self.ns["penalty"])

    def test_multiplicity_is_translated_to_spin_and_method_is_forwarded(self):
        for method, multiplicity, expected in [("R", 1, "RKS"), ("R", 3, "UKS"), ("RO", 3, "ROKS")]:
            with self.subTest(method=method):
                self.ns["cal_method"] = method
                self.ns["multiplicity"] = multiplicity
                with patch.object(self.ns["gto"], "M") as molecule:
                    with patch.object(self.ns["dft"], expected, return_value=self.scf):
                        self.assertEqual(self.ns["energy"]([1.0, 1.04]), -76.4)
                self.assertEqual(molecule.call_args.kwargs["spin"], multiplicity - 1)
                self.assertEqual(molecule.call_args.kwargs["unit"], "Angstrom")
                self.assertIn("H 1 1.0 2 104.0", molecule.call_args.kwargs["atom"])

    def test_invalid_settings_raise_instead_of_hiding_configuration_errors(self):
        with patch.object(self.ns["gto"], "M", side_effect=ValueError("Unknown basis")):
            with self.assertRaisesRegex(ValueError, "Unknown basis"):
                self.ns["energy"]([1.0, 1.04])


if __name__ == "__main__":
    unittest.main()
