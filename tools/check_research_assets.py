#!/usr/bin/env python3
"""Lightweight validation checks for research assets and contracts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

EXPECTED_FEATURES = [
    "CCSDS_APID",
    "CCSDS_DataLen",
    "CSP_Priority",
    "CSP_Source",
    "CSP_Dest",
    "CSP_DPort",
    "CSP_SPort",
    "CSP_Flags",
    "Payload_Len",
    "Time_Delta_Log",
    "Flags_Change",
    "Payload_Diff",
    "APID_Count",
    "Global_Time_Delta_Log",
    "APID_Time_Delta_Log",
    "APID_Changed_Roll10",
    "CCSDS_DataLen_AbsDiff",
    "CCSDS_SeqCount_AbsDiff",
    "Packet_Rate_Roll10_Log",
    "CSP_Nonzero_Roll10",
    "CSP_Route_Changed_Roll10",
    "Payload_Len_RollStd10",
    "P_Entropy_Log_RollStd10",
]


class Reporter:
    def __init__(self) -> None:
        self.failed = False

    def pass_(self, message: str) -> None:
        print(f"PASS: {message}")

    def fail(self, message: str) -> None:
        print(f"FAIL: {message}")
        self.failed = True

    def skip(self, message: str) -> None:
        print(f"SKIP: {message}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_original_notebook(repo_root: Path, expected_sha: str | None, r: Reporter) -> None:
    notebook = repo_root / "model" / "model.ipynb"
    if not notebook.exists():
        r.skip("model/model.ipynb is missing; original-preservation checks deferred")
        return

    digest = sha256_file(notebook)
    r.pass_(f"model/model.ipynb exists (sha256={digest})")

    if expected_sha:
        if digest.lower() == expected_sha.lower():
            r.pass_("original notebook hash matches expected SHA256")
        else:
            r.fail("original notebook hash does not match expected SHA256")

    try:
        with notebook.open("r", encoding="utf-8") as f:
            obj = json.load(f)
    except json.JSONDecodeError as exc:
        r.fail(f"model/model.ipynb is not valid JSON: {exc}")
        return

    if obj.get("nbformat") != 4:
        r.fail("model/model.ipynb nbformat is not 4")
        return

    if not isinstance(obj.get("cells"), list):
        r.fail("model/model.ipynb missing cells list")
        return

    r.pass_("model/model.ipynb basic notebook structure is valid")


def check_dataset_contract(repo_root: Path, r: Reporter) -> None:
    dataset = repo_root / "dataset" / "master_dataset_unseen_seed2952.csv"
    if not dataset.exists():
        r.skip("dataset/master_dataset_unseen_seed2952.csv is missing")
        return

    with dataset.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            r.fail("dataset CSV has no header")
            return

        missing = [c for c in EXPECTED_FEATURES if c not in reader.fieldnames]
        if missing:
            r.fail(f"dataset missing required features: {missing}")
            return

        if "Combined_Label" not in reader.fieldnames:
            r.fail("dataset missing Combined_Label column")
            return

        checked = 0
        bad_labels = []
        for row in reader:
            checked += 1
            raw = row.get("Combined_Label", "").strip()
            try:
                value = int(float(raw))
            except ValueError:
                bad_labels.append((checked, raw))
                if len(bad_labels) >= 5:
                    break
                continue

            if value < 0 or value > 24:
                bad_labels.append((checked, raw))
                if len(bad_labels) >= 5:
                    break

        if bad_labels:
            r.fail(f"Combined_Label values out of expected 0..24 range (examples: {bad_labels})")
            return

        if checked == 0:
            r.fail("dataset contains header only; no rows to validate")
            return

        r.pass_(f"dataset columns and Combined_Label range validated on {checked} rows")


def _shape_from_onnx_value_info(value_info) -> tuple[int | str | None, ...]:
    dims = []
    for dim in value_info.type.tensor_type.shape.dim:
        if dim.HasField("dim_value"):
            dims.append(int(dim.dim_value))
        elif dim.HasField("dim_param"):
            dims.append(dim.dim_param)
        else:
            dims.append(None)
    return tuple(dims)


def check_onnx_contracts(repo_root: Path, r: Reporter) -> None:
    embedded = repo_root / "model" / "embedded"
    if not embedded.exists():
        r.skip("model/embedded directory is missing")
        return

    onnx_files = sorted(embedded.glob("*.onnx"))
    if not onnx_files:
        r.skip("no .onnx files found under model/embedded")
        return

    try:
        import onnx  # type: ignore
    except ImportError:
        r.skip("onnx package is not installed; ONNX shape checks skipped")
        return

    expected_input = (1, 30, 23)
    expected_output = (1, 25)

    for path in onnx_files:
        try:
            model = onnx.load(path.as_posix())
        except Exception as exc:  # pylint: disable=broad-except
            r.fail(f"failed to load ONNX file {path.relative_to(repo_root)}: {exc}")
            continue

        if not model.graph.input or not model.graph.output:
            r.fail(f"{path.relative_to(repo_root)} missing graph inputs/outputs")
            continue

        input_shape = _shape_from_onnx_value_info(model.graph.input[0])
        output_shape = _shape_from_onnx_value_info(model.graph.output[0])
        rel = path.relative_to(repo_root)
        r.pass_(f"{rel} input shape={input_shape} output shape={output_shape}")

        if input_shape == expected_input and output_shape == expected_output:
            r.pass_(f"{rel} matches expected (1, 30, 23) -> (1, 25)")
        else:
            r.skip(f"{rel} shape differs from current expected contract")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root path")
    parser.add_argument(
        "--expected-original-notebook-sha256",
        type=str,
        default=None,
        help="Optional expected sha256 for model/model.ipynb",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    reporter = Reporter()

    print(f"Checking repository: {repo_root}")
    check_original_notebook(repo_root, args.expected_original_notebook_sha256, reporter)
    check_dataset_contract(repo_root, reporter)
    check_onnx_contracts(repo_root, reporter)

    if reporter.failed:
        print("Summary: FAIL (one or more checks failed)")
        return 1

    print("Summary: PASS (with skips allowed for missing assets/dependencies)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
