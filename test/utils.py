from numbers import Number
import os
from typing import List, Tuple
import unittest
import yaml
from deepdiff import DeepDiff

RUNDIR = "run"
PRESERVE_OUTPUT_FILES = False


def grab_content_if_file_exists(file_path: str) -> str:
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read()
    else:
        return ""


def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)] if os.path.exists(d) else []


def run_accelergy(
    inputs: List[str], plug_ins: List[str], run_dir: str, extra_accelergy_args: str = ""
) -> Tuple[str, str, str, str, str]:
    """Run Accelergy and return the output, ERT, ART, ERT verbose, and ART verbose.
    Empty strings are returned if a file does not exist."""
    output_dir = os.path.abspath(run_dir)
    os.makedirs(output_dir, exist_ok=True)
    for to_remove in [
        "ERT.yaml",
        "ART.yaml",
        "ERT_summary_verbose.txt",
        "ART_summary_verbose.txt",
        "output.txt",
    ]:
        if os.path.exists(os.path.join(output_dir, to_remove)):
            os.remove(os.path.join(output_dir, to_remove))

    inputs_str = " ".join(inputs) if inputs else ""
    plug_in_str = f'-e {" ".join(plug_ins)}' if plug_ins else ""
    all_in = f"{inputs_str} {plug_in_str}"
    output_file = os.path.abspath(os.path.join(output_dir, "output.txt"))

    accelergy_cmd = (
        f"accelergy {all_in} -v 1 {extra_accelergy_args} > {output_file} 2>&1"
    )

    print(f"\nRunning: {accelergy_cmd}")
    os.makedirs(output_dir, exist_ok=True)
    # Move into the output directory and run accelergy
    os.chdir(output_dir)
    os.system(accelergy_cmd)
    output = grab_content_if_file_exists("output.txt")
    ert = grab_content_if_file_exists("ERT.yaml")
    art = grab_content_if_file_exists("ART.yaml")
    ert_summary_verbose = grab_content_if_file_exists("ERT_summary_verbose.txt")
    art_summary_verbose = grab_content_if_file_exists("ART_summary_verbose.txt")
    return output, ert, art, ert_summary_verbose, art_summary_verbose


def clear_run_dir(run_dir: str):
    """Clear the run directory."""
    run_dir = os.path.abspath(run_dir)
    if os.path.exists(run_dir):
        for f in os.listdir(run_dir):
            assert f.endswith(".txt") or f.endswith(
                ".yaml"
            ), f"Unexpected file in run dir: {os.path.join(run_dir, f)}"
            os.remove(os.path.join(run_dir, f))
        os.rmdir(run_dir)


def run_accelergy_from_test_dir(
    test_dir_path: str, extra_accelergy_args: str = "", force_input_files=()
) -> Tuple[str, str, str, str, str]:
    """
    Gets the path to the current file and runs accelergy from that directory.
    Returns the output, ERT, ART, ERT verbose, and ART verbose. Empty strings are returned if
    a file does not exist.
    """
    if not force_input_files:
        inputs = listdir_fullpath(os.path.join(test_dir_path, "inputs"))
        inputs += listdir_fullpath(os.path.join(test_dir_path, "input"))
    else:
        inputs = [os.path.join(test_dir_path, f) for f in force_input_files]
    plug_ins = listdir_fullpath(os.path.join(test_dir_path, "plugins"))
    plug_ins += listdir_fullpath(os.path.join(test_dir_path, "plugin"))
    return run_accelergy(
        inputs, plug_ins, os.path.join(test_dir_path, RUNDIR), extra_accelergy_args
    )


class AccelergyUnitTest(unittest.TestCase):
    def setUp(self, test_dir_path: str, extra_accelergy_args="", force_input_files=()):
        # super().__init__()
        self.test_dir_path = test_dir_path
        self.accelergy_out = ""
        self.accelergy_ert = ""
        self.accelergy_art = ""
        self.accelergy_ert_summary_verbose = ""
        self.accelergy_art_summary_verbose = ""
        self.accelergy_ert_yaml = None
        self.accelergy_art_yaml = None
        self.accelergy_ert_summary_verbose_yaml = None
        self.accelergy_art_summary_verbose_yaml = None

        (
            self.accelergy_out,
            self.accelergy_ert,
            self.accelergy_art,
            self.accelergy_ert_summary_verbose,
            self.accelergy_art_summary_verbose,
        ) = run_accelergy_from_test_dir(
            self.test_dir_path, extra_accelergy_args, force_input_files
        )

        if self.accelergy_ert:
            self.accelergy_ert_yaml = yaml.safe_load(self.accelergy_ert)
        if self.accelergy_art:
            self.accelergy_art_yaml = yaml.safe_load(self.accelergy_art)
        if self.accelergy_ert_summary_verbose:
            self.accelergy_ert_summary_verbose_yaml = yaml.safe_load(
                self.accelergy_ert_summary_verbose
            )

    def tearDown(self):
        # Clear the run directory if the test passes
        run_dir = os.path.abspath(os.path.join(self.test_dir_path, RUNDIR))
        if (
            hasattr(self, "_outcome")
            and hasattr(self._outcome, "errors")
            and any([e[1] for e in self._outcome.errors])
        ):
            print(
                f"Test {self._testMethodName} has errors. NOT clearing run directory {run_dir}"
            )
            print(f"Errors: {self._outcome.errors}")
        else:
            if PRESERVE_OUTPUT_FILES:
                print(
                    f"Test {self._testMethodName} passed. Preserving run directory {run_dir}"
                )
            else:
                print(
                    f"Test {self._testMethodName} passed. Clearing run directory {run_dir}"
                )
                clear_run_dir(run_dir)

    def get_accelergy_success(self):
        return self.accelergy_ert_yaml is not None

    def get_energy(self, name: str, action: str) -> float:
        entries = self.accelergy_ert_yaml["ERT"]["tables"]
        for entry in entries:
            if entry["name"] == name:
                for action_entry in entry["actions"]:
                    if action_entry["name"] == action:
                        return action_entry["energy"]
        raise AttributeError(f"Could not find energy for {name} {action}")

    def get_area(self, name: str) -> float:
        entries = self.accelergy_art_yaml["ART"]["tables"]
        for entry in entries:
            if entry["name"] == name:
                return entry["area"]
        raise AttributeError(f"Could not find area for {name}")

    def assert_energy(self, name: str, action: str, expected_energy: float):
        energy = self.get_energy(name, action)
        self.assertAlmostEqual(energy, expected_energy, places=4)

    def assert_area(self, name: str, expected_area: float):
        area = self.get_area(name)
        self.assertAlmostEqual(area, expected_area, places=4)

    def get_file_content(self, file_name: str) -> str:
        return grab_content_if_file_exists(
            os.path.join(self.test_dir_path, RUNDIR, file_name)
        )

    def compare_yamls(self, yaml1: str, yaml2: str, ignore_keys: List = ()):
        yaml1 = yaml1.replace("arguments: null", "arguments: {}")
        yaml2 = yaml2.replace("arguments: null", "arguments: {}")

        yaml1 = yaml.safe_load(yaml1)
        yaml2 = yaml.safe_load(yaml2)
        for k in ignore_keys:
            yaml1 = filter(lambda x: x["name"] != k, yaml1)
            yaml2 = filter(lambda x: x["name"] != k, yaml2)
        # Remove all 'leak' or 'idle' entries
        # yaml1 = filter(lambda x: not isinstance(x, dict) or x.get(
        #     'name', '') not in ['leak', 'idle'], yaml1)
        # yaml2 = filter(lambda x: not isinstance(x, dict) or x.get(
        #     'name', '') not in ['leak', 'idle'], yaml2)

        diff = DeepDiff(
            yaml1,
            yaml2,
            ignore_order=True,
            ignore_numeric_type_changes=True,
            ignore_string_type_changes=True,
            number_format_notation="e",
            significant_digits=3,
        )
        value_change_keys = list(diff.get("values_changed", {}).keys())
        for k in value_change_keys:
            old, new = (
                diff["values_changed"][k]["old_value"],
                diff["values_changed"][k]["new_value"],
            )
            if "['version']" in k:
                diff["values_changed"].pop(k)
                continue
            if not isinstance(old, Number) or not isinstance(new, Number):
                continue
            # Allow slight differences
            if old == 0:
                if new < 0.001:
                    diff["values_changed"].pop(k)
                    print(f"Ignoring rounding error of {old} -> {new}")
            elif abs(old - new) / old < 0.02:
                diff["values_changed"].pop(k)
                print(f"Ignoring rounding error of {old} -> {new}")
        if "values_changed" in diff and not diff["values_changed"]:
            diff.pop("values_changed")
        return diff


if __name__ == "__main__":
    unittest.main()
